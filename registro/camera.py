import cv2
import numpy as np
import os
import platform
from django.conf import settings
from .models import Funcionario, ColetaFaces

class videoCamera(object):
    def __init__(self):
        self.video = None
        self.is_active = False
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Inicializa o reconhecedor LBPH com verificação segura
        if hasattr(cv2, 'face') and hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
            # Parâmetros otimizados de LBPH: radius=1, neighbors=8, grid_x=8, grid_y=8
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
        else:
            self.recognizer = None
            print("[AVISO CAMERA] cv2.face nao encontrado. Inicie o projeto usando o ambiente virtual: .\\.venv\\Scripts\\python.exe manage.py runserver")
            
        self.is_trained = False
        self.id_map = {} # label_id -> {id, nome, cpf, foto_url}
        self.treinar_modelo()

    def __del__(self):
        self.stop()

    def start(self):
        """Inicia a captura de vídeo na webcam caso ainda não esteja aberta."""
        self.is_active = True
        if self.video is None or not self.video.isOpened():
            # No Windows, CAP_DSHOW inicializa e encerra mais rapido sem travar threads assincronas
            if platform.system() == 'Windows':
                self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            else:
                self.video = cv2.VideoCapture(0)
            
            # Ajuste de resolucao padrao para desempenho fluido
            if self.video.isOpened():
                self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        return self.video is not None and self.video.isOpened()

    def stop(self):
        """Para e desliga a webcam fisica imediatamente, apagando a luz do hardware."""
        self.is_active = False
        if self.video is not None:
            try:
                if self.video.isOpened():
                    self.video.release()
            except Exception:
                pass
            self.video = None

    def restart(self):
        self.stop()
        return self.start()

    def _gerar_variacoes(self, face_roi):
        """Gera amostras aumentadas (espelhamento, variacoes de brilho e rotacao) para treinamento robusto."""
        variacoes = [face_roi]
        
        # 1. Espelhamento horizontal (duplica os angulos de face)
        variacoes.append(cv2.flip(face_roi, 1))

        # 2. Variação de iluminação mais clara (simula ambiente bem iluminado)
        face_clara = cv2.convertScaleAbs(face_roi, alpha=1.12, beta=12)
        variacoes.append(face_clara)

        # 3. Variação de iluminação mais escura (simula sombras/luz indireta)
        face_escura = cv2.convertScaleAbs(face_roi, alpha=0.90, beta=-12)
        variacoes.append(face_escura)

        # 4. Leves rotações (+4 graus e -4 graus)
        h, w = face_roi.shape
        centro = (w // 2, h // 2)
        for angulo in [4, -4]:
            matriz_rot = cv2.getRotationMatrix2D(centro, angulo, 1.0)
            face_rot = cv2.warpAffine(face_roi, matriz_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            variacoes.append(face_rot)

        return variacoes

    def treinar_modelo(self):
        """Treina o modelo LBPH aplicando equalizacao de histograma e aumento de dados."""
        if self.recognizer is None:
            self.is_trained = False
            return

        try:
            faces = []
            labels = []
            self.id_map = {}

            funcionarios = Funcionario.objects.all()
            for idx, func in enumerate(funcionarios, start=1):
                self.id_map[idx] = {
                    'id': func.id,
                    'nome': func.nome,
                    'cpf': func.cpf,
                    'foto_url': func.foto.url if func.foto else '',
                }

                caminhos_fotos = []
                if func.foto and os.path.exists(func.foto.path):
                    caminhos_fotos.append(func.foto.path)
                
                for coleta in func.funcionario_coletas.all():
                    if coleta.foto and os.path.exists(coleta.foto.path):
                        caminhos_fotos.append(coleta.foto.path)

                for caminho in caminhos_fotos:
                    img = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                    
                    # Detecta a face com cascade
                    detected = self.face_cascade.detectMultiScale(img, scaleFactor=1.15, minNeighbors=4, minSize=(50, 50))
                    if len(detected) > 0:
                        for (x, y, w, h) in detected:
                            face_recorte = cv2.resize(img[y:y+h, x:x+w], (200, 200))
                            # Equalizacao de histograma normaliza diferencas severas de iluminacao
                            face_equalizada = cv2.equalizeHist(face_recorte)
                            
                            # Gera variacoes para o modelo aprender multiplos cenarios
                            for v in self._gerar_variacoes(face_equalizada):
                                faces.append(v)
                                labels.append(idx)
                    else:
                        # Tenta uma deteccao mais sensivel antes de desistir
                        det2 = self.face_cascade.detectMultiScale(img, scaleFactor=1.08, minNeighbors=2)
                        if len(det2) > 0:
                            x, y, w, h = det2[0]
                            face_recorte = cv2.resize(img[y:y+h, x:x+w], (200, 200))
                            face_equalizada = cv2.equalizeHist(face_recorte)
                            for v in self._gerar_variacoes(face_equalizada):
                                faces.append(v)
                                labels.append(idx)

            if len(faces) > 0 and len(labels) > 0:
                self.recognizer.train(faces, np.array(labels))
                self.is_trained = True
            else:
                self.is_trained = False
        except Exception as e:
            print("Erro ao treinar modelo LBPH:", e)
            self.is_trained = False

    def get_frame(self):
        """Retorna o frame bruto da câmera (se ativa). NÃO reabre se foi desativada."""
        if not self.is_active or self.video is None or not self.video.isOpened():
            return None
        success, image = self.video.read()
        if not success:
            return None
        self.last_frame = image.copy()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def get_frame_with_recognition(self):
        """Retorna o frame com deteccao e classificacao estrita de face. NÃO reabre se camera estiver inativa."""
        if not self.is_active or self.video is None or not self.video.isOpened():
            return None, []

        success, image = self.video.read()
        if not success:
            return None, []

        self.last_frame = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces_rects = self.face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(60, 60))
        pessoas_detectadas = []

        # LIMIAR PARA LBPH:
        # Menor valor de confidence indica maior proximidade (distancia chi-quadrado).
        # - Distancia <= 68.0: Correspondencia valida para webcam ao vivo
        # - Distancia > 68.0: Desconhecido (evita falsos positivos com terceiros)
        LIMIAR_RIGIDO = 68.0

        for (x, y, w, h) in faces_rects:
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
            face_roi = cv2.equalizeHist(face_roi) # Normaliza contraste e sombras na face
            
            nome_display = "Desconhecido"
            cor = (0, 0, 255) # Vermelho padrao para nao cadastrado

            if self.is_trained and self.recognizer is not None:
                label, confidence = self.recognizer.predict(face_roi)
                
                # Somente aceita se a distancia for estritamente menor que o limiar
                if confidence < LIMIAR_RIGIDO and label in self.id_map:
                    info = self.id_map[label]
                    nome_display = info['nome']
                    cor = (0, 255, 0) # Verde se realmente for o funcionario
                    
                    # Converte a distancia em uma porcentagem estimada de confianca
                    similaridade_pct = max(0, min(100, int(100 - (confidence / LIMIAR_RIGIDO) * 40)))
                    
                    pessoas_detectadas.append({
                        'funcionario_id': info['id'],
                        'nome': info['nome'],
                        'cpf': info['cpf'],
                        'foto_url': info['foto_url'],
                        'confidence': round(float(confidence), 1),
                        'similaridade': similaridade_pct
                    })
                    nome_display = f"{info['nome']} ({similaridade_pct}%)"
                else:
                    pessoas_detectadas.append({
                        'funcionario_id': None,
                        'nome': 'Desconhecido',
                        'confidence': round(float(confidence), 1)
                    })
            else:
                pessoas_detectadas.append({
                    'funcionario_id': None,
                    'nome': 'Desconhecido'
                })

            # Desenha o retangulo na face e banner com o nome
            cv2.rectangle(image, (x, y), (x+w, y+h), cor, 2)
            cv2.rectangle(image, (x, max(0, y-30)), (x+w, y), cor, cv2.FILLED)
            cv2.putText(image, nome_display, (x + 6, max(15, y - 8)), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes(), pessoas_detectadas

    def capture_snapshot(self):
        """Captura um snapshot JPEG no momento exato com fallback para o último frame."""
        image = None
        if self.video is not None and self.video.isOpened():
            success, frame = self.video.read()
            if success:
                image = frame

        if image is None and hasattr(self, 'last_frame') and self.last_frame is not None:
            image = self.last_frame

        if image is None:
            return None

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
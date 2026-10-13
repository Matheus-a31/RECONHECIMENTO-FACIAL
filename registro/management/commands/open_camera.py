from django.core.management.base import BaseCommand
import cv2

class Command(BaseCommand):
    help = 'Abre a câmera para reconhecimento facial'

    def handle(self, *args, **kwargs):
        # Inicia a captura de vídeo
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            self.stdout.write(self.style.ERROR('Não foi possível abrir a câmera'))
            return

        self.stdout.write(self.style.SUCCESS('Câmera aberta com sucesso. Pressione "q" para sair.'))

        while True:
            # Captura frame a frame
            ret, frame = cap.read()

            if not ret:
                self.stdout.write(self.style.ERROR('Não foi possível capturar o frame'))
                break

            # Exibe o frame capturado
            cv2.imshow('Camera', frame)

            # Sai do loop se a tecla 'q' for pressionada
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Libera a captura e fecha as janelas
        cap.release()
        cv2.destroyAllWindows()
        self.stdout.write(self.style.SUCCESS('Câmera fechada.'))
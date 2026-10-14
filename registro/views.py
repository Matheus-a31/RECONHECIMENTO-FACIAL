import json
import datetime
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import FuncionarioForm, ColetaFacesForm
from .models import Funcionario, ColetaFaces, RegistroPonto
from .camera import videoCamera
from .acesso import (
    autorizar_funcionario,
    revogar_autorizacao,
    pode_ver_historico,
    mascarar_cpf,
    requer_admin,
    is_admin as checar_is_admin,
    MSG_ACESSO_NEGADO,
)

camera_detection = videoCamera()
# Variável em memória para guardar a última pessoa reconhecida pelo frame stream
last_recognized_person = None

def gen_detected_faces(camera_detection):
    global last_recognized_person
    camera_detection.start()
    consecutive_counts = {}
    try:
        while camera_detection.is_active:
            frame, detectados = camera_detection.get_frame_with_recognition()
            if not camera_detection.is_active or frame is None:
                break

            if detectados:
                reconhecido = next((d for d in detectados if d.get('funcionario_id') is not None), None)
                if reconhecido:
                    fid = reconhecido['funcionario_id']
                    consecutive_counts[fid] = consecutive_counts.get(fid, 0) + 1
                    # Exige pelo menos 2 frames consecutivos consistentes para confirmar o reconhecimento
                    if consecutive_counts[fid] >= 2:
                        last_recognized_person = reconhecido
                else:
                    consecutive_counts.clear()
                    last_recognized_person = {'funcionario_id': None, 'nome': 'Desconhecido'}
            else:
                consecutive_counts.clear()
                last_recognized_person = None

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    except (GeneratorExit, Exception):
        pass
    finally:
        camera_detection.stop()
        last_recognized_person = None


def face_detection(request):
    return StreamingHttpResponse(gen_detected_faces(camera_detection),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def home(request):
    """Tela Inicial: Terminal de Reconhecimento Facial para Ponto Eletrônico."""
    if not checar_is_admin(request.user):
        revogar_autorizacao(request)

    hoje = timezone.localdate()
    pontos_hoje = RegistroPonto.objects.filter(data=hoje).select_related('funcionario').order_by('-id')[:10]
    
    tipo_modo = request.GET.get('tipo', 'ENTRADA').upper()
    if tipo_modo not in ['ENTRADA', 'SAIDA']:
        tipo_modo = 'ENTRADA'

    funcionario_id = request.GET.get('funcionario_id')
    funcionario_alvo = None
    if funcionario_id:
        funcionario_alvo = Funcionario.objects.filter(id=funcionario_id).first()

    context = {
        'pontos_hoje': pontos_hoje,
        'hoje': hoje,
        'tipo_modo': tipo_modo,
        'funcionario_alvo': funcionario_alvo,
    }
    return render(request, 'index_reconhecimento.html', context)

def api_status_reconhecimento(request):
    """Retorna via JSON a pessoa identificada atualmente pela câmera."""
    global last_recognized_person
    if last_recognized_person and last_recognized_person.get('funcionario_id'):
        fid = last_recognized_person['funcionario_id']
        # Autoriza temporariamente a sessão para o funcionário reconhecido facialmente
        autorizar_funcionario(request, fid)
        return JsonResponse({
            'status': 'RECONHECIDO',
            'funcionario': {
                'id': fid,
                'nome': last_recognized_person['nome'],
                'cpf': mascarar_cpf(last_recognized_person.get('cpf', '')),
                'foto_url': last_recognized_person.get('foto_url', ''),
                'confidence': last_recognized_person.get('confidence')
            }
        })
    elif last_recognized_person and last_recognized_person.get('nome') == 'Desconhecido':
        return JsonResponse({
            'status': 'DESCONHECIDO',
            'funcionario': None
        })
    else:
        return JsonResponse({
            'status': 'SEM_FACE',
            'funcionario': None
        })

@csrf_exempt
def api_fechar_camera(request):
    """Fecha e libera a webcam física imediatamente."""
    global last_recognized_person
    camera_detection.stop()
    last_recognized_person = None
    return JsonResponse({'success': True, 'camera_status': 'closed'})

@csrf_exempt
def api_bater_ponto(request):
    """Registra entrada ou saída para o funcionário reconhecido."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
    try:
        data = json.loads(request.body)
        funcionario_id = data.get('funcionario_id')
        tipo = data.get('tipo', 'ENTRADA').upper()

        if not funcionario_id or tipo not in ['ENTRADA', 'SAIDA']:
            return JsonResponse({'error': 'Dados incompletos ou inválidos.'}, status=400)

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        
        # Proteção anti-spoofing: apenas admin ou a pessoa atualmente reconhecida na câmera pode bater o ponto
        if not checar_is_admin(request.user):
            reconhecido_id = last_recognized_person.get('funcionario_id') if last_recognized_person else None
            if not reconhecido_id or int(reconhecido_id) != int(funcionario.id):
                return JsonResponse({
                    'error': 'Operação não autorizada: o rosto atual na câmera não corresponde ao colaborador solicitado.'
                }, status=403)

        # Autoriza temporariamente a sessão para o funcionário que bateu o ponto
        autorizar_funcionario(request, funcionario.id)

        # Salva o registro de ponto
        ponto = RegistroPonto.objects.create(
            funcionario=funcionario,
            tipo=tipo
        )

        # Captura snapshot fotográfico para auditoria
        frame_bytes = camera_detection.capture_snapshot()
        if frame_bytes:
            ponto.foto_registro.save(
                f"ponto_{funcionario.id}_{ponto.data}_{ponto.id}.jpg", 
                ContentFile(frame_bytes), 
                save=True
            )

        # Para e libera a webcam física imediatamente
        camera_detection.stop()

        status_param = 'entrada_sucesso' if tipo == 'ENTRADA' else 'saida_sucesso'

        return JsonResponse({
            'success': True,
            'registro': {
                'id': ponto.id,
                'funcionario_id': funcionario.id,
                'funcionario': funcionario.nome,
                'tipo': ponto.tipo,
                'data': ponto.data.strftime('%d/%m/%Y'),
                'hora': ponto.hora.strftime('%H:%M:%S'),
            },
            'redirect_url': f'/historico/{funcionario.id}/?status={status_param}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def historico_funcionario(request, funcionario_id):
    """Tela com a lista e espelho de entradas e saídas dos últimos 30 dias do funcionário."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    
    # Regra de Privacidade e Acesso:
    # Apenas administradores ou o funcionário com autorização válida na sessão têm acesso aos pontos
    if not pode_ver_historico(request, funcionario.id):
        messages.error(request, MSG_ACESSO_NEGADO)
        return redirect('home')

    is_admin = checar_is_admin(request.user)

    hoje = timezone.localdate()
    data_limite = hoje - datetime.timedelta(days=30)
    
    # Query de registros dos últimos 30 dias
    pontos_query = RegistroPonto.objects.filter(
        funcionario=funcionario,
        data__gte=data_limite
    ).order_by('-data', '-hora')
    
    # Filtro opcional por tipo
    filtro_tipo = request.GET.get('tipo', 'TODOS').upper()
    if filtro_tipo in ['ENTRADA', 'SAIDA']:
        pontos = pontos_query.filter(tipo=filtro_tipo)
    else:
        filtro_tipo = 'TODOS'
        pontos = pontos_query

    # Métricas dos últimos 30 dias
    total_registros = pontos_query.count()
    total_entradas = pontos_query.filter(tipo='ENTRADA').count()
    total_saidas = pontos_query.filter(tipo='SAIDA').count()
    dias_trabalhados = pontos_query.values('data').distinct().count()

    # Status atual de hoje
    pontos_hoje = pontos_query.filter(data=hoje)
    ultimo_hoje = pontos_hoje.first()
    
    if ultimo_hoje and ultimo_hoje.tipo == 'ENTRADA':
        status_hoje = 'EM_EXPEDIENTE'
        status_label = 'Em Expediente'
        status_desc = f"Entrada registrada hoje às {ultimo_hoje.hora.strftime('%H:%M:%S')}"
    elif ultimo_hoje and ultimo_hoje.tipo == 'SAIDA':
        status_hoje = 'EXPEDIENTE_ENCERRADO'
        status_label = 'Expediente Encerrado'
        status_desc = f"Saída registrada hoje às {ultimo_hoje.hora.strftime('%H:%M:%S')}"
    else:
        status_hoje = 'SEM_REGISTRO'
        status_label = 'Sem Registro Hoje'
        status_desc = 'Nenhum ponto registrado na data de hoje'

    # Agrupamento por dia para visualização estruturada
    dias_dict = {}
    for p in pontos:
        dia_key = p.data
        if dia_key not in dias_dict:
            dias_dict[dia_key] = {
                'data': p.data,
                'pontos': [],
                'entradas': 0,
                'saidas': 0,
            }
        dias_dict[dia_key]['pontos'].append(p)
        if p.tipo == 'ENTRADA':
            dias_dict[dia_key]['entradas'] += 1
        elif p.tipo == 'SAIDA':
            dias_dict[dia_key]['saidas'] += 1

    dias_agrupados = list(dias_dict.values())

    # Outros funcionários só são disponibilizados para consulta se for Administrador
    if is_admin:
        outros_funcionarios = Funcionario.objects.exclude(id=funcionario.id).order_by('nome')
    else:
        outros_funcionarios = Funcionario.objects.none()

    context = {
        'funcionario': funcionario,
        'hoje': hoje,
        'data_limite': data_limite,
        'pontos': pontos,
        'dias_agrupados': dias_agrupados,
        'total_registros': total_registros,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'dias_trabalhados': dias_trabalhados,
        'status_hoje': status_hoje,
        'status_label': status_label,
        'status_desc': status_desc,
        'ultimo_ponto': pontos_query.first(),
        'filtro_tipo': filtro_tipo,
        'outros_funcionarios': outros_funcionarios,
        'is_admin': is_admin,
        'status_acao': request.GET.get('status', ''),
    }
    return render(request, 'historico_ponto.html', context)

@requer_admin
def historico_geral(request):
    """Visão geral do histórico de 30 dias com seletor de funcionário (Exclusivo para Administrador)."""
    funcionario_id = request.GET.get('funcionario')
    if funcionario_id:
        return redirect('historico_funcionario', funcionario_id=funcionario_id)

    funcionarios = Funcionario.objects.all().order_by('nome')
    if funcionarios.count() == 1:
        return redirect('historico_funcionario', funcionario_id=funcionarios.first().id)

    hoje = timezone.localdate()
    data_limite = hoje - datetime.timedelta(days=30)
    pontos_recentes = RegistroPonto.objects.filter(data__gte=data_limite).select_related('funcionario').order_by('-data', '-hora')[:50]

    context = {
        'funcionarios': funcionarios,
        'pontos_recentes': pontos_recentes,
        'hoje': hoje,
        'data_limite': data_limite,
        'is_admin': True,
    }
    return render(request, 'historico_geral.html', context)

@requer_admin
def criar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save()
            # Retreina o modelo para incluir o novo funcionário
            camera_detection.treinar_modelo()
            return redirect('criar_coleta_faces', funcionario_id=funcionario.id)
    else:
        form = FuncionarioForm()
    return render(request, 'criar_funcionario.html', {'form': form})

@requer_admin
def criar_coleta_faces(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == 'POST':
        frame_bytes = camera_detection.capture_snapshot()
        if frame_bytes:
            coleta = ColetaFaces(funcionario=funcionario)
            coleta.foto.save(f'{funcionario.slug}_coleta_{funcionario.funcionario_coletas.count() + 1}.jpg', ContentFile(frame_bytes))
        # Retreina com as novas fotos coletadas
        camera_detection.treinar_modelo()
        return redirect('sucesso_funcionario', funcionario_id=funcionario.id)
    
    context = {
        'funcionario': funcionario, 
        'face_detection': face_detection,
    }
    return render(request, 'criar_coleta_faces.html', context)

@requer_admin
def sucesso_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    coletas = funcionario.funcionario_coletas.all()
    context = {
        'funcionario': funcionario,
        'coletas': coletas,
    }
    return render(request, 'sucesso_funcionario.html', context)
from django.urls import path
from registro.views import (
    home,
    criar_funcionario,
    criar_coleta_faces,
    sucesso_funcionario,
    face_detection,
    api_status_reconhecimento,
    api_bater_ponto,
    api_fechar_camera,
    historico_geral,
    historico_funcionario,
)

urlpatterns = [
    # Terminal de Reconhecimento Facial e Ponto
    path('', home, name='home'),
    
    # Lista e Espelho de Ponto (Últimos 30 dias)
    path('historico/', historico_geral, name='historico_geral'),
    path('historico/<int:funcionario_id>/', historico_funcionario, name='historico_funcionario'),

    # Cadastro e Coleta
    path('cadastrar/', criar_funcionario, name='criar_funcionario'),
    path('criar_coleta_faces/<int:funcionario_id>', criar_coleta_faces, name='criar_coleta_faces'),
    path('sucesso/<int:funcionario_id>/', sucesso_funcionario, name='sucesso_funcionario'),
    
    # Streaming de Câmera
    path('face_detection/', face_detection, name='face_detection'),
    path('face_detection/', face_detection, name='url_face_detection'),
    
    # APIs para Reconhecimento, Ponto e Controle de Câmera
    path('api/status-reconhecimento/', api_status_reconhecimento, name='api_status_reconhecimento'),
    path('api/bater-ponto/', api_bater_ponto, name='api_bater_ponto'),
    path('api/fechar-camera/', api_fechar_camera, name='api_fechar_camera'),
]
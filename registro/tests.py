import json
import time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from .models import Funcionario, RegistroPonto
from .acesso import (
    is_admin,
    autorizar_funcionario,
    revogar_autorizacao,
    funcionario_autorizado_id,
    pode_ver_historico,
    mascarar_cpf,
    MSG_ACESSO_NEGADO,
    MSG_SOMENTE_ADMIN,
    CHAVE_SESSAO_AUTORIZACAO,
)
import registro.views as views


class AcessoUnitTests(TestCase):
    """Testes unitários para as funções utilitárias de privacidade e controle de acesso."""

    def test_mascarar_cpf_padrao_com_pontos(self):
        self.assertEqual(mascarar_cpf('123.456.789-01'), '***.456.789-**')

    def test_mascarar_cpf_sem_pontuacao(self):
        self.assertEqual(mascarar_cpf('12345678901'), '***.456.789-**')

    def test_mascarar_cpf_invalido_ou_curto(self):
        self.assertEqual(mascarar_cpf('12345'), '***')

    def test_mascarar_cpf_vazio_ou_nulo(self):
        self.assertEqual(mascarar_cpf(''), '')
        self.assertEqual(mascarar_cpf(None), '')

    def test_is_admin_usuario_anonimo(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertFalse(is_admin(response.wsgi_request.user))

    def test_is_admin_usuario_comum(self):
        user = User.objects.create_user(username='comum', password='123')
        self.assertFalse(is_admin(user))

    def test_is_admin_staff_e_superuser(self):
        staff = User.objects.create_user(username='staff', password='123', is_staff=True)
        superu = User.objects.create_superuser(username='super', password='123')
        self.assertTrue(is_admin(staff))
        self.assertTrue(is_admin(superu))

    def test_autorizacao_sessao_e_ttl(self):
        client = Client()
        session = client.session
        # Simula request mock com dicionário de sessão
        class MockRequest:
            def __init__(self, s, u=None):
                self.session = s
                self.user = u

        req = MockRequest(session)
        autorizar_funcionario(req, 42)
        self.assertEqual(funcionario_autorizado_id(req), 42)
        self.assertTrue(pode_ver_historico(req, 42))
        self.assertFalse(pode_ver_historico(req, 99))

        # Testa revogação
        revogar_autorizacao(req)
        self.assertIsNone(funcionario_autorizado_id(req))
        self.assertFalse(pode_ver_historico(req, 42))

        # Testa expiração por TTL
        autorizar_funcionario(req, 42)
        req.session[CHAVE_SESSAO_AUTORIZACAO]['expira_em'] = time.time() - 10
        self.assertIsNone(funcionario_autorizado_id(req))
        self.assertFalse(pode_ver_historico(req, 42))


class PrivacidadeControleAcessoViewsTests(TestCase):
    """Testes de integração garantindo as regras invioláveis de privacidade entre colaboradores."""

    def setUp(self):
        self.client = Client()
        dummy_img = SimpleUploadedFile(
            name='test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        self.func_a = Funcionario.objects.create(
            nome='Carlos Silva',
            cpf='111.222.333-44',
            foto=dummy_img
        )
        self.func_b = Funcionario.objects.create(
            nome='Mariana Souza',
            cpf='555.666.777-88',
            foto=dummy_img
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@teste.com',
            password='adminpassword'
        )

    def test_usuario_anonimo_sem_reconhecimento_redirecionado_ao_acessar_historico(self):
        """Um colaborador não identificado que tenta acessar /historico/<id>/ deve ser barrado."""
        url = reverse('historico_funcionario', args=[self.func_a.id])
        resp = self.client.get(url, follow=True)
        self.assertRedirects(resp, reverse('home'))
        messages = list(resp.context['messages'])
        self.assertTrue(any(MSG_ACESSO_NEGADO in str(m) for m in messages))

    def test_colaborador_reconhecido_acessa_apenas_seu_proprio_espelho(self):
        """O colaborador A reconhecido tem acesso a /historico/A/, mas NÃO a /historico/B/."""
        # 1. Autoriza a sessão para o funcionário A
        session = self.client.session
        session[CHAVE_SESSAO_AUTORIZACAO] = {
            'id': self.func_a.id,
            'expira_em': time.time() + 180,
        }
        session.save()

        # 2. Acesso ao próprio espelho: DEVE ter sucesso (200 OK)
        resp_proprio = self.client.get(reverse('historico_funcionario', args=[self.func_a.id]))
        self.assertEqual(resp_proprio.status_code, 200)
        self.assertEqual(resp_proprio.context['funcionario'].id, self.func_a.id)
        # O seletor de outros funcionários NÃO pode aparecer para colaborador comum
        self.assertNotContains(resp_proprio, 'id="seletor-outros-funcionarios"')

        # 3. Tentativa de invasão/inspeção do espelho do colega B: DEVE ser barrada
        resp_alheio = self.client.get(reverse('historico_funcionario', args=[self.func_b.id]), follow=True)
        self.assertRedirects(resp_alheio, reverse('home'))
        messages = list(resp_alheio.context['messages'])
        self.assertTrue(any(MSG_ACESSO_NEGADO in str(m) for m in messages))

    def test_administrador_acessa_espelho_de_qualquer_funcionario(self):
        """Administrador autenticado tem acesso aos espelhos de A e de B e visualiza o seletor."""
        self.client.force_login(self.admin)

        resp_a = self.client.get(reverse('historico_funcionario', args=[self.func_a.id]))
        self.assertEqual(resp_a.status_code, 200)
        self.assertContains(resp_a, 'id="seletor-outros-funcionarios"')

        resp_b = self.client.get(reverse('historico_funcionario', args=[self.func_b.id]))
        self.assertEqual(resp_b.status_code, 200)
        self.assertContains(resp_b, 'id="seletor-outros-funcionarios"')

    def test_rotas_administrativas_bloqueadas_para_nao_administradores(self):
        """historico_geral e criar_funcionario redirecionam não-admins com aviso."""
        # Não logado
        resp1 = self.client.get(reverse('historico_geral'), follow=True)
        self.assertRedirects(resp1, reverse('home'))
        messages1 = list(resp1.context['messages'])
        self.assertTrue(any(MSG_SOMENTE_ADMIN in str(m) for m in messages1))

        resp2 = self.client.get(reverse('criar_funcionario'), follow=True)
        self.assertRedirects(resp2, reverse('home'))

        # Logado como admin -> 200 OK
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('historico_geral')).status_code, 200)
        self.assertEqual(self.client.get(reverse('criar_funcionario')).status_code, 200)


class ApiBaterPontoESpoofingTests(TestCase):
    """Testes de segurança da API de batida de ponto e do polling biométrico."""

    def setUp(self):
        self.client = Client()
        dummy_img = SimpleUploadedFile(
            name='test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        self.func_a = Funcionario.objects.create(
            nome='Carlos Silva',
            cpf='111.222.333-44',
            foto=dummy_img
        )
        self.func_b = Funcionario.objects.create(
            nome='Mariana Souza',
            cpf='555.666.777-88',
            foto=dummy_img
        )
        views.last_recognized_person = None

    def tearDown(self):
        views.last_recognized_person = None

    def test_spoofing_tentativa_de_bater_ponto_sem_face_na_camera(self):
        """Se ninguém estiver na câmera, POST para /api/bater-ponto/ deve retornar 403 Forbidden."""
        views.last_recognized_person = None
        payload = {'funcionario_id': self.func_a.id, 'tipo': 'ENTRADA'}
        resp = self.client.post(
            reverse('api_bater_ponto'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(RegistroPonto.objects.count(), 0)

    def test_spoofing_tentativa_de_bater_ponto_para_terceiro(self):
        """Se a câmera reconhecer o funcionário A, o cliente NÃO pode registrar para B."""
        views.last_recognized_person = {
            'funcionario_id': self.func_a.id,
            'nome': self.func_a.nome,
            'cpf': self.func_a.cpf,
        }
        # Cliente tenta bater ponto para o funcionário B
        payload = {'funcionario_id': self.func_b.id, 'tipo': 'ENTRADA'}
        resp = self.client.post(
            reverse('api_bater_ponto'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(RegistroPonto.objects.count(), 0)

    @patch.object(views.camera_detection, 'capture_snapshot', return_value=None)
    @patch.object(views.camera_detection, 'stop')
    def test_batida_ponto_legitima_com_reconhecimento(self, mock_stop, mock_snapshot):
        """Face na câmera coincide com funcionário_id -> 200 OK, ponto registrado e sessão autorizada."""
        views.last_recognized_person = {
            'funcionario_id': self.func_a.id,
            'nome': self.func_a.nome,
            'cpf': self.func_a.cpf,
        }
        payload = {'funcionario_id': self.func_a.id, 'tipo': 'ENTRADA'}
        resp = self.client.post(
            reverse('api_bater_ponto'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(RegistroPonto.objects.count(), 1)
        self.assertEqual(RegistroPonto.objects.first().tipo, 'ENTRADA')
        mock_stop.assert_called_once()

        # Verifica se a sessão foi autorizada e se o colaborador consegue acessar seu espelho
        resp_historico = self.client.get(data['redirect_url'])
        self.assertEqual(resp_historico.status_code, 200)

    def test_api_status_reconhecimento_mascara_cpf_e_autoriza_sessao(self):
        """api_status_reconhecimento retorna CPF mascarado ('***.222.333-**')."""
        views.last_recognized_person = {
            'funcionario_id': self.func_a.id,
            'nome': self.func_a.nome,
            'cpf': self.func_a.cpf,
            'foto_url': '/media/test.jpg',
            'confidence': 95.0
        }
        resp = self.client.get(reverse('api_status_reconhecimento'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'RECONHECIDO')
        self.assertEqual(data['funcionario']['cpf'], '***.222.333-**')
        self.assertEqual(funcionario_autorizado_id(resp.wsgi_request), self.func_a.id)


class SwaggerDocumentationTests(TestCase):
    """Testes para a rota de documentação da API via Swagger /docs e schema OpenAPI."""

    def setUp(self):
        self.client = Client()

    def test_swagger_docs_url_acessivel_com_e_sem_barra(self):
        """Verifica se /docs e /docs/ retornam 200 com Swagger UI renderizado."""
        resp_sem_barra = self.client.get('/docs')
        self.assertEqual(resp_sem_barra.status_code, 200)
        self.assertIn('swagger-ui', resp_sem_barra.content.decode('utf-8'))
        self.assertIn('/docs/schema.json', resp_sem_barra.content.decode('utf-8'))

        resp_com_barra = self.client.get('/docs/')
        self.assertEqual(resp_com_barra.status_code, 200)
        self.assertIn('swagger-ui', resp_com_barra.content.decode('utf-8'))

    def test_openapi_schema_json_completo(self):
        """Verifica se /docs/schema.json retorna especificação OpenAPI 3.0 válida com todas as rotas."""
        resp = self.client.get(reverse('openapi_schema'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('openapi'), '3.0.3')
        self.assertEqual(data.get('info', {}).get('title'), 'BatePonto API — Reconhecimento Facial & Ponto Eletrônico')
        
        # Verifica se todas as rotas de API esperadas estão presentes
        paths = data.get('paths', {})
        self.assertIn('/api/status-reconhecimento/', paths)
        self.assertIn('/api/bater-ponto/', paths)
        self.assertIn('/api/fechar-camera/', paths)
        self.assertIn('/face_detection/', paths)
        self.assertIn('/historico/{funcionario_id}/', paths)
        self.assertIn('/historico/', paths)
        self.assertIn('/cadastrar/', paths)
        self.assertIn('/criar_coleta_faces/{funcionario_id}', paths)

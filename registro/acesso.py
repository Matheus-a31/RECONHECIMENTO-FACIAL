"""
Regras de acesso e privacidade do BatePonto.

Centraliza:
- quem é administrador;
- a autorização temporária concedida a um colaborador após o reconhecimento
  facial (sessão com prazo de validade);
- o mascaramento de dados pessoais expostos pela API do terminal.

Ver REGRA 3 do AGENTS.md e a seção 3 de specs/behavior.md.
"""
import re
import time
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

# Chave de sessão que guarda {'id': <funcionario_id>, 'expira_em': <epoch>}
CHAVE_SESSAO_AUTORIZACAO = 'funcionario_reconhecido'

# Tempo (segundos) que o colaborador reconhecido pode consultar o próprio espelho.
# Curto de propósito: o navegador do quiosque é compartilhado entre colaboradores.
TTL_AUTORIZACAO_PADRAO = 180

MSG_ACESSO_NEGADO = (
    'Acesso negado: cada colaborador só pode consultar o próprio espelho de ponto '
    'logo após ser reconhecido pela câmera.'
)
MSG_SOMENTE_ADMIN = 'Acesso restrito a administradores.'


def is_admin(user):
    """Retorna True apenas para usuários autenticados com perfil staff ou superusuário."""
    return bool(
        user is not None
        and user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


def _ttl_segundos():
    return getattr(settings, 'PONTO_SESSAO_TTL_SEGUNDOS', TTL_AUTORIZACAO_PADRAO)


def autorizar_funcionario(request, funcionario_id):
    """Concede à sessão atual acesso temporário ao espelho de UM colaborador."""
    request.session[CHAVE_SESSAO_AUTORIZACAO] = {
        'id': int(funcionario_id),
        'expira_em': time.time() + _ttl_segundos(),
    }


def revogar_autorizacao(request):
    """Remove qualquer autorização de colaborador da sessão atual."""
    request.session.pop(CHAVE_SESSAO_AUTORIZACAO, None)


def funcionario_autorizado_id(request):
    """
    Retorna o ID do colaborador autorizado na sessão, ou None.
    Autorizações expiradas ou malformadas são descartadas.
    """
    dados = request.session.get(CHAVE_SESSAO_AUTORIZACAO)
    if not isinstance(dados, dict):
        return None
    try:
        funcionario_id = int(dados['id'])
        expira_em = float(dados['expira_em'])
    except (KeyError, TypeError, ValueError):
        revogar_autorizacao(request)
        return None
    if time.time() > expira_em:
        revogar_autorizacao(request)
        return None
    return funcionario_id


def pode_ver_historico(request, funcionario_id):
    """Administradores veem todos; colaboradores apenas o próprio, dentro do prazo."""
    if is_admin(request.user):
        return True
    return funcionario_autorizado_id(request) == int(funcionario_id)


def mascarar_cpf(cpf):
    """'123.456.789-09' -> '***.456.789-**'. Valores fora do padrão viram '***'."""
    digitos = re.sub(r'\D', '', cpf or '')
    if len(digitos) != 11:
        return '***' if digitos else ''
    return f'***.{digitos[3:6]}.{digitos[6:9]}-**'


def requer_admin(view_func):
    """Decorator: redireciona para o terminal com aviso se o usuário não for administrador."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, MSG_SOMENTE_ADMIN)
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped

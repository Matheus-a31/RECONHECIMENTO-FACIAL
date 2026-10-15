from .acesso import is_admin


def permissoes(request):
    """Expõe `is_admin` a todos os templates (fonte única para esconder/mostrar controles)."""
    return {'is_admin': is_admin(getattr(request, 'user', None))}

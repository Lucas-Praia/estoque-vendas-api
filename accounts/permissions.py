from rest_framework.permissions import SAFE_METHODS, BasePermission

from .roles import Role, get_role, has_role


class HasAnyRole(BasePermission):

    message = 'Seu usuário não tem perfil de acesso. Peça a um administrador.'

    def has_permission(self, request, view):
        return get_role(request.user) is not None


class IsManager(BasePermission):
    message = 'Ação permitida apenas para gerente ou administrador.'

    def has_permission(self, request, view):
        return has_role(request.user, Role.MANAGER)


class IsAdmin(BasePermission):
    message = 'Ação permitida apenas para administrador.'

    def has_permission(self, request, view):
        return has_role(request.user, Role.ADMIN)


class ReadOnlyOrManager(BasePermission):
    """Todos os perfis consultam; só gerente ou administrador cria, altera ou exclui."""

    message = 'Somente gerente ou administrador pode alterar cadastros.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return get_role(request.user) is not None
        return has_role(request.user, Role.MANAGER)

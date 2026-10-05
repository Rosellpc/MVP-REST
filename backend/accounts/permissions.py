from rest_framework.permissions import BasePermission


class HasAreaPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active
                    and request.user.has_perm(view.required_permission))

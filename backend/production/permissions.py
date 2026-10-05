from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def require_permission(actor, permission):
    if not actor.is_authenticated or not actor.is_active or not actor.has_perm(f"production.{permission}"):
        raise PermissionDenied("No tienes permiso para esta operación.")


def allowed_stations(actor):
    if not actor.is_authenticated or not actor.is_active:
        return []
    return [station for station in ("KITCHEN", "BAR")
            if actor.has_perm(f"production.view_{station.lower()}_ticket")]


class CanReadTickets(BasePermission):
    def has_permission(self, request, view):
        return bool(allowed_stations(request.user))


class CanReleaseOrders(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active
                    and request.user.has_perm("production.release_order"))

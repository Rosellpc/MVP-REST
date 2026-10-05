from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .permissions import HasAreaPermission
from .roles import user_payload
from .serializers import LoginSerializer


class LoginThrottle(SimpleRateThrottle):
    scope = "staff_login"
    rate = "10/min"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


@method_decorator(never_cache, name="dispatch")
class SessionView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


class CsrfView(SessionView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(SessionView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request=request, **serializer.validated_data)
        if user is None:
            return Response({"detail": "Usuario o contraseña incorrectos."}, status=400)
        if not any(user.has_perm(f"accounts.access_{area}") for area in ("staff", "kitchen", "bar")):
            return Response({"detail": "Esta cuenta no tiene acceso al área del personal."}, status=403)
        login(request, user)
        return Response({"user": user_payload(user), "csrfToken": get_token(request)})


class MeView(SessionView):
    def get(self, request):
        return Response(user_payload(request.user))


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(SessionView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"csrfToken": get_token(request)})


class AreaView(SessionView):
    permission_classes = [HasAreaPermission]
    required_permission = ""

    def get(self, request):
        return Response({"detail": "Acceso autorizado", "permission": self.required_permission})

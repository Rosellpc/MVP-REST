"""User OAuth access to the MCP's two fixed, read-only API routes."""
from hashlib import sha256

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from oauth2_provider.models import get_access_token_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .views import LoginThrottle


class StaffOAuthForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.has_perm("accounts.access_staff"):
            raise ValidationError("Esta cuenta no tiene acceso al dashboard.", code="no_access")


@method_decorator(never_cache, name="dispatch")
class StaffOAuthLoginView(LoginView):
    template_name = "accounts/oauth_login.html"
    authentication_form = StaffOAuthForm
    next_page = "/oauth/connected/"

    def post(self, request, *args, **kwargs):
        throttle = LoginThrottle()
        if not throttle.allow_request(request, self):
            return JsonResponse({"detail": "Espera un minuto antes de volver a intentarlo."}, status=429)
        return super().post(request, *args, **kwargs)


@login_required
@never_cache
def oauth_connected(request):
    return render(request, "accounts/oauth_connected.html")


def oauth_metadata(request):
    issuer = settings.MCP_AUTH_ISSUER
    return JsonResponse({
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/o/authorize/",
        "token_endpoint": f"{issuer}/o/token/",
        "revocation_endpoint": f"{issuer}/o/revoke_token/",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "client_id_metadata_document_supported": True,
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "scopes_supported": list(settings.OAUTH2_PROVIDER["SCOPES"]),
    })


class McpOAuthAuthentication(BaseAuthentication):
    """Validate opaque tokens against their issuing database on every call.

    The audience is the public MCP URL, even though this fixed backend route
    performs validation for it. Browser session cookies are never accepted here.
    """
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != b"bearer" or len(header[1]) > 4096:
            raise AuthenticationFailed("Autorización inválida.")
        checksum = sha256(header[1]).hexdigest()
        token = get_access_token_model().objects.select_related("user", "application").filter(
            token_checksum=checksum,
        ).first()
        if (token is None or not token.is_valid() or token.resource != [settings.MCP_RESOURCE_URL]
                or token.application is None or token.user is None or not token.user.is_active):
            raise AuthenticationFailed("Conecta de nuevo tu cuenta de RestaurantOS.")
        return token.user, token

    def authenticate_header(self, request):
        return 'Bearer realm="restaurantos"'

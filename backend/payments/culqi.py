"""Fixed-host Culqi adapter. Never log credentials, tokens or raw provider payloads."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

from django.conf import settings
from rest_framework.exceptions import APIException


class CulqiUnavailable(APIException):
    status_code = 503
    default_detail = "No se pudo verificar Culqi. Conservamos el intento; consulta su estado antes de volver a pagar."


def configured():
    return (getattr(settings, "PAYMENTS_ENABLED", False)
            and getattr(settings, "PAYMENTS_ENVIRONMENT", "test") == "test"
            and getattr(settings, "PRODUCTION_DEMO_ENABLED", False)
            and getattr(settings, "CULQI_PUBLIC_KEY", "").startswith("pk_test_")
            and getattr(settings, "CULQI_SECRET_KEY", "").startswith("sk_test_"))


def require_configured():
    if not configured():
        raise CulqiUnavailable("Configura las llaves de integración, PAYMENTS_ENABLED y la producción de prueba.")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api(method, path, payload=None):
    require_configured()
    request = Request("https://api.culqi.com/v2/" + path, method=method,
                      data=json.dumps(payload).encode() if payload is not None else None,
                      headers={"Authorization": "Bearer " + settings.CULQI_SECRET_KEY,
                               "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with build_opener(NoRedirect).open(request, timeout=15) as response:
            status, raw = response.status, response.read(2_000_000)
    except HTTPError as exc:
        status, raw = exc.code, exc.read(2_000_000)
    except (URLError, TimeoutError, OSError):
        raise CulqiUnavailable() from None
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError):
        raise CulqiUnavailable() from None
    if not isinstance(data, dict) or status >= 500:
        raise CulqiUnavailable()
    return status, data


def get_charge(charge_id):
    if not re.fullmatch(r"chr_test_[A-Za-z0-9]+", charge_id):
        raise CulqiUnavailable("Referencia de cargo inválida para integración.")
    status, charge = api("GET", "charges/" + charge_id)
    if status != 200:
        raise CulqiUnavailable()
    return charge


def list_charges(since, after=None):
    params = {"creation_date_from": int(since.timestamp()) - 60, "limit": 100}
    if after:
        params["after"] = after
    status, result = api("GET", "charges?" + urlencode(params))
    if status != 200 or not isinstance(result.get("data"), list):
        raise CulqiUnavailable()
    return result

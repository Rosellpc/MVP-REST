from base64 import urlsafe_b64encode
from datetime import timedelta
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.test import APIClient

from orders.models import Order


class McpAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("manager", password="local-test-password")
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label="accounts", codename="access_staff"))
        Application = get_application_model()
        self.application = Application.objects.create(
            name="MCP test", client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="https://chatgpt.com/connector/oauth/test")
        self.client = APIClient()
        self.dashboard = "/api/v1/mcp/dashboard/"
        self.sales = "/api/v1/mcp/sales/summary/"

    def token(self, *, scope="dashboard:read sales:read", resource=None, expires=None):
        raw = uuid4().hex
        token = get_access_token_model().objects.create(
            user=self.user, application=self.application, token=raw, scope=scope,
            expires=expires or timezone.now() + timedelta(hours=1),
            resource=[settings.MCP_RESOURCE_URL] if resource is None else resource)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        return token

    def test_authentication_audience_expiry_scope_and_permission(self):
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)
        self.token(resource=[])
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)
        self.token(resource=["https://other.example/mcp"])
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)
        self.token(expires=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)
        self.token(scope="sales:read")
        self.assertEqual(self.client.get(self.dashboard).status_code, 403)
        token = self.token()
        self.assertEqual(self.client.get(self.dashboard).status_code, 200)
        self.user.user_permissions.clear()
        self.assertEqual(self.client.get(self.dashboard).status_code, 403)
        token.revoke()
        self.assertEqual(self.client.get(self.dashboard).status_code, 401)

    def test_read_only_reports_match_dashboard_and_exclude_customers(self):
        for total, status in [(10, "READY"), (20, "CANCELLED")]:
            Order.objects.create(idempotency_key=uuid4(), request_hash="test",
                                 customer_name="PRIVATE_CUSTOMER", fulfillment="PICKUP",
                                 total=total, production_status=status)
        self.token()
        report = self.client.get(self.dashboard)
        sales = self.client.get(self.sales)
        self.assertEqual(report.status_code, 200)
        self.assertEqual(sales.status_code, 200)
        for key in ("amount", "orders", "average_ticket", "all_orders", "cancelled", "partial_excluded", "units"):
            self.assertEqual(report.data["metrics"][key], sales.data["metrics"][key])
        self.assertEqual(sales.data["metrics"]["amount"], "10.00")
        self.assertTrue(sales.data["demo"])
        self.assertNotIn("PRIVATE_CUSTOMER", str(report.data))
        self.assertEqual(self.client.post(self.dashboard, {}).status_code, 405)
        self.assertEqual(self.client.get(self.sales + "?start=bad").status_code, 400)
        self.assertEqual(self.client.get(self.dashboard + "?start=2020-01-01&end=2026-01-01").status_code, 400)
        self.assertIn("no-store", report["Cache-Control"])

    def test_pkce_authorization_code_can_read_report(self):
        self.client.force_login(self.user)
        verifier = "m" * 64
        challenge = urlsafe_b64encode(sha256(verifier.encode()).digest()).decode().rstrip("=")
        params = {
            "client_id": self.application.client_id, "response_type": "code",
            "redirect_uri": self.application.redirect_uris, "scope": "dashboard:read sales:read",
            "resource": settings.MCP_RESOURCE_URL, "state": "test-state",
            "code_challenge": challenge, "code_challenge_method": "S256",
        }
        consent = self.client.get("/o/authorize/", params)
        self.assertEqual(consent.status_code, 200)
        response = self.client.post("/o/authorize/", {**params, "allow": "Authorize"})
        self.assertEqual(response.status_code, 302)
        code = parse_qs(urlsplit(response["Location"]).query)["code"][0]
        token = self.client.post("/o/token/", {
            "grant_type": "authorization_code", "client_id": self.application.client_id,
            "redirect_uri": self.application.redirect_uris, "code": code,
            "code_verifier": verifier, "resource": settings.MCP_RESOURCE_URL,
        })
        self.assertEqual(token.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.json()['access_token']}")
        self.assertEqual(self.client.get(self.dashboard).status_code, 200)

    def test_chatgpt_client_document_registration_and_host_restriction(self):
        client_id = "https://chatgpt.com/oauth/test/client.json"
        document = {
            "client_id": client_id, "client_name": "ChatGPT",
            "redirect_uris": [self.application.redirect_uris],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"], "token_endpoint_auth_method": "private_key_jwt",
            "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"],
        }
        self.client.force_login(self.user)
        params = {
            "client_id": client_id, "response_type": "code",
            "redirect_uri": self.application.redirect_uris,
            "scope": "dashboard:read", "resource": settings.MCP_RESOURCE_URL,
            "code_challenge": "a" * 43, "code_challenge_method": "S256",
        }
        config = {**settings.OAUTH2_PROVIDER, "CIMD_ENABLED": True,
                  "CIMD_METADATA_FETCHER": "accounts.mcp_oauth_client.ChatGPTMetadataFetcher",
                  "CIMD_ALLOWED_HOSTS": ["chatgpt.com"],
                  "CIMD_REGISTRATION_PERMISSION_CLASSES": ("oauth2_provider.cimd.HostAllowlistCIMDPermission",)}
        with override_settings(OAUTH2_PROVIDER=config):
            with patch("oauth2_provider.cimd.SafeMetadataFetcher.fetch", return_value=(document, 300)) as fetch:
                response = self.client.get("/o/authorize/", params)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(get_application_model().objects.filter(client_id=client_id).exists())
                fetch.assert_called_once_with(client_id)
            with patch("oauth2_provider.cimd.SafeMetadataFetcher.fetch") as fetch:
                response = self.client.get("/o/authorize/", {**params, "client_id": "https://other.example/client.json"})
                self.assertEqual(response.status_code, 400)
                fetch.assert_not_called()

    def test_cimd_does_not_downgrade_private_only_client(self):
        from accounts.mcp_oauth_client import ChatGPTMetadataFetcher
        document = {"token_endpoint_auth_method": "private_key_jwt",
                    "token_endpoint_auth_methods_supported": ["private_key_jwt"]}
        with patch("oauth2_provider.cimd.SafeMetadataFetcher.fetch", return_value=(document, 300)):
            metadata, _ = ChatGPTMetadataFetcher().fetch("https://chatgpt.com/oauth/test/client.json")
            self.assertEqual(metadata["token_endpoint_auth_method"], "private_key_jwt")
        document["token_endpoint_auth_methods_supported"] = ["none", "private_key_jwt"]
        with patch("oauth2_provider.cimd.SafeMetadataFetcher.fetch", return_value=(document, 300)):
            metadata, _ = ChatGPTMetadataFetcher().fetch("https://other.example/client.json")
            self.assertEqual(metadata["token_endpoint_auth_method"], "private_key_jwt")

    def test_https_login_keeps_csrf_protection_and_same_origin_referrer(self):
        client = APIClient(enforce_csrf_checks=True)
        page = client.get("/oauth/login/", secure=True)
        self.assertContains(page, '<meta name="referrer" content="same-origin">')
        csrf = client.cookies["csrftoken"].value
        data = {"username": "manager", "password": "local-test-password",
                "csrfmiddlewaretoken": csrf, "next": "/o/authorize/"}
        self.assertEqual(client.post("/oauth/login/", data, secure=True).status_code, 403)
        self.assertEqual(client.post("/oauth/login/", data, secure=True,
                                    HTTP_REFERER="https://other.example/login/").status_code, 403)
        response = client.post("/oauth/login/", data, secure=True,
                               HTTP_REFERER="https://testserver/oauth/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/o/authorize/")

    def test_direct_login_has_valid_destination(self):
        response = self.client.post("/oauth/login/", {
            "username": "manager", "password": "local-test-password",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/oauth/connected/")
        self.assertContains(self.client.get(response["Location"]), "Sesión iniciada")

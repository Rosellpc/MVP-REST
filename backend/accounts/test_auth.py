from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


class StaffAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        for role in ("ADMIN", "KITCHEN", "BAR"):
            user = get_user_model().objects.create_user(role.lower(), password="test-password-123")
            user.groups.add(Group.objects.get(name=role))

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def post(self, path, data=None):
        token = self.client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        return self.client.post(path, data or {}, format="json", HTTP_X_CSRFTOKEN=token)

    def login(self, name="kitchen"):
        return self.post("/api/v1/auth/login/", {"username": name, "password": "test-password-123"})

    def test_login_session_and_logout(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.json()["user"])
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["roles"], ["KITCHEN"])
        self.assertEqual(self.post("/api/v1/auth/logout/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/kitchen/access/").status_code, 403)

    def test_anonymous_access_denied(self):
        for area in ("staff", "kitchen", "bar"):
            self.assertEqual(self.client.get(f"/api/v1/{area}/access/").status_code, 403)

    def test_station_permissions(self):
        for role, allowed in (("kitchen", {"kitchen"}), ("bar", {"bar"}), ("admin", {"staff", "kitchen", "bar"})):
            self.assertEqual(self.login(role).status_code, 200)
            for area in ("staff", "kitchen", "bar"):
                self.assertEqual(self.client.get(f"/api/v1/{area}/access/").status_code, 200 if area in allowed else 403)

    def test_csrf_required_on_login_and_logout(self):
        self.assertEqual(self.client.post("/api/v1/auth/login/", {"username": "kitchen", "password": "test-password-123"}).status_code, 403)
        self.login()
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)

    def test_invalid_and_inactive_credentials(self):
        self.assertEqual(self.post("/api/v1/auth/login/", {"username": "kitchen", "password": "wrong"}).status_code, 400)
        get_user_model().objects.filter(username="kitchen").update(is_active=False)
        self.assertEqual(self.login().status_code, 400)

    def test_cannot_elevate_own_permissions(self):
        self.login()
        self.assertEqual(self.post("/api/v1/auth/me/", {"roles": ["ADMIN"], "is_superuser": True}).status_code, 405)
        self.assertEqual(self.client.get("/api/v1/staff/access/").status_code, 403)

    def test_revoked_role_applies_next_request(self):
        self.login()
        get_user_model().objects.get(username="kitchen").groups.clear()
        self.assertEqual(self.client.get("/api/v1/kitchen/access/").status_code, 403)

    def test_deactivated_session_denied(self):
        self.login()
        get_user_model().objects.filter(username="kitchen").update(is_active=False)
        self.assertEqual(self.client.get("/api/v1/kitchen/access/").status_code, 403)

    def test_setup_roles_idempotent_and_no_user_admin_permissions(self):
        call_command("setup_roles", verbosity=0)
        self.assertEqual(Group.objects.filter(name__in=["ADMIN", "KITCHEN", "BAR"]).count(), 3)
        self.assertFalse(Group.objects.get(name="ADMIN").permissions.filter(codename="change_user").exists())

    def test_login_throttled(self):
        for _ in range(10):
            self.post("/api/v1/auth/login/", {"username": "missing", "password": "wrong"})
        self.assertEqual(self.login().status_code, 429)

    def test_csrf_rotated_and_session_response_not_cached(self):
        old = self.client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        response = self.login()
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.post("/api/v1/auth/logout/", {}, HTTP_X_CSRFTOKEN=old).status_code, 403)

    def test_account_without_area_cannot_login(self):
        get_user_model().objects.create_user("visitor", password="test-password-123")
        self.assertEqual(self.login("visitor").status_code, 403)

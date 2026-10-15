from unittest.mock import patch
from django.test import TestCase


class HealthTests(TestCase):
    def test_health_checks_database_without_exposing_details(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertIn('no-store', response['Cache-Control'])

    def test_database_failure_is_sanitized(self):
        with patch('core.health.connection.cursor', side_effect=RuntimeError('private host/password')):
            response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})

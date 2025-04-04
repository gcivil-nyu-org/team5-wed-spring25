from django.test import TestCase, override_settings
from django.conf import settings


class SettingsTests(TestCase):
    def test_allowed_hosts(self):
        """Verify ALLOWED_HOSTS is properly configured"""
        self.assertTrue(
            len(settings.ALLOWED_HOSTS) > 0,
            "ALLOWED_HOSTS should contain at least one host",
        )

    def test_security_middleware(self):
        """Verify security middleware is installed"""
        self.assertIn(
            "django.middleware.security.SecurityMiddleware",
            settings.MIDDLEWARE,
            "SecurityMiddleware should be installed",
        )

    def test_secure_cookie_settings(self):
        """Verify secure cookie settings"""
        self.assertTrue(
            settings.SESSION_COOKIE_SECURE,
            "SESSION_COOKIE_SECURE should be True in production",
        )
        self.assertTrue(
            settings.CSRF_COOKIE_SECURE,
            "CSRF_COOKIE_SECURE should be True in production",
        )

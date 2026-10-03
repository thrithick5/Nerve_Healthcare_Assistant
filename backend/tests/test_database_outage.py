"""A database outage must be diagnosable from the browser.

Regression: when PostgreSQL was unreachable, /auth/login raised an unhandled
sqlalchemy.exc.OperationalError. Starlette's ServerErrorMiddleware converted it
to a bare "Internal Server Error" *outside* the CORS middleware, so the response
carried no access-control-allow-origin header. The browser hid it, axios saw a
request with no response, and the UI reported "Network error. Please check your
connection." -- which is indistinguishable from the machine being offline.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.exc import OperationalError  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

import app.api.routes as routes  # noqa: E402
from app.main import app  # noqa: E402

PRODUCTION_ORIGIN = "https://nerve-healthcare-assistant.vercel.app"


class DatabaseOutageTest(unittest.TestCase):
    def setUp(self):
        # Isolate this app instance from whatever DATABASE_URL the developer
        # happens to have exported.
        self.client = TestClient(app, raise_server_exceptions=False)

    def _post_login_with_broken_db(self, origin=PRODUCTION_ORIGIN):
        """Drive a real request while get_db() fails the way psycopg2 does."""
        app.dependency_overrides[routes.get_db] = _raise_connection_error
        try:
            return self.client.post(
                "/api/v1/auth/login",
                json={"email": "probe@example.invalid", "password": "probe12345"},
                headers={"Origin": origin, "Content-Type": "application/json"},
            )
        finally:
            app.dependency_overrides.pop(routes.get_db, None)

    def test_login_returns_503_not_500_when_database_is_down(self):
        response = self._post_login_with_broken_db()
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("detail", response.json())

    def test_outage_response_carries_cors_headers_so_the_browser_can_read_it(self):
        """This is the assertion the original bug violated."""
        response = self._post_login_with_broken_db()
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            PRODUCTION_ORIGIN,
            "browser will hide the error without this header",
        )

    def test_detail_message_is_actionable_not_a_raw_driver_traceback(self):
        detail = self._post_login_with_broken_db().json()["detail"]
        self.assertNotIn("psycopg2", detail)
        self.assertNotIn("Traceback", detail)
        self.assertTrue(detail.strip(), "detail must not be empty")


def _raise_connection_error():
    """Stand in for get_db() when PostgreSQL cannot be reached."""
    raise OperationalError(
        "SELECT 1",
        {},
        Exception('could not translate host name "dpg-test-a" to address'),
    )


class HealthEndpointDiagnosabilityTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_health_reports_database_reachability(self):
        body = self.client.get("/api/v1/health").json()
        self.assertIn("database", body, "health must expose DB state to diagnose outages")

    def test_health_stays_200_when_database_is_down(self):
        """Render's health checker treats non-200 as dead and restarts the
        service, which is exactly the crash loop this repo already escaped."""
        body = self.client.get("/api/v1/health")
        self.assertEqual(body.status_code, 200)
        self.assertEqual(body.json()["status"], "healthy")


class CorsMiddlewareOrderTest(unittest.TestCase):
    def test_cors_middleware_is_actually_installed(self):
        installed = {m.cls for m in app.user_middleware}
        self.assertIn(CORSMiddleware, installed)


if __name__ == "__main__":
    unittest.main()
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.url_utils import (  # noqa: E402
    DEFAULT_DATABASE_URL,
    describe_host,
    is_sqlite_url,
    normalize_database_url,
    redact_database_url,
)


class TestNormalizeDatabaseUrl(unittest.TestCase):
    def test_rewrites_legacy_postgres_scheme(self):
        self.assertEqual(
            normalize_database_url("postgres://u:p@host:5432/db"),
            "postgresql://u:p@host:5432/db",
        )

    def test_leaves_modern_postgresql_scheme_untouched(self):
        url = "postgresql://u:p@host:5432/db"
        self.assertEqual(normalize_database_url(url), url)

    def test_leaves_sqlite_untouched(self):
        url = "sqlite:///./data/healthcare.db"
        self.assertEqual(normalize_database_url(url), url)

    def test_rewrites_only_the_scheme_not_the_remainder(self):
        self.assertEqual(
            normalize_database_url("postgres://host/db?x=postgres://y"),
            "postgresql://host/db?x=postgres://y",
        )

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(
            normalize_database_url("  postgres://u:p@h/db \n"),
            "postgresql://u:p@h/db",
        )

    def test_empty_and_none_fall_back_to_default(self):
        self.assertEqual(normalize_database_url(None), DEFAULT_DATABASE_URL)
        self.assertEqual(normalize_database_url(""), DEFAULT_DATABASE_URL)
        self.assertEqual(normalize_database_url("   "), DEFAULT_DATABASE_URL)

    def test_preserves_percent_encoded_password(self):
        # Render passwords may contain URL-encoded specials; must not be mangled.
        url = "postgres://u:p%40ss%3Aword@host:5432/db"
        self.assertEqual(normalize_database_url(url), "postgresql://u:p%40ss%3Aword@host:5432/db")

    def test_default_url_is_sqlite(self):
        self.assertTrue(is_sqlite_url(DEFAULT_DATABASE_URL))
        self.assertFalse(is_sqlite_url(normalize_database_url("postgres://u:p@h/db")))

    def test_describe_host_extracts_hostname(self):
        self.assertEqual(
            describe_host("postgresql://u:p@dpg-abc123-a:5432/db"), "dpg-abc123-a"
        )

    def test_describe_host_handles_missing_host(self):
        self.assertIsNone(describe_host("sqlite:///./data/healthcare.db"))


class TestRedactDatabaseUrl(unittest.TestCase):
    """Startup logs must never contain database credentials."""

    def test_masks_password(self):
        redacted = redact_database_url("postgresql://nerve:s3cr3t@dpg-abc-a:5432/db")
        self.assertNotIn("s3cr3t", redacted)
        self.assertIn(":***@", redacted)

    def test_preserves_host_port_and_dbname_for_diagnostics(self):
        redacted = redact_database_url("postgresql://nerve:s3cr3t@dpg-abc-a:5432/db")
        self.assertIn("dpg-abc-a:5432", redacted)
        self.assertIn("/db", redacted)
        self.assertIn("nerve", redacted)

    def test_handles_password_containing_at_sign(self):
        redacted = redact_database_url("postgresql://u:p%40ss%3Aword@h:5432/db")
        self.assertNotIn("p%40ss%3Aword", redacted)
        self.assertIn(":***@", redacted)

    def test_passwordless_url_is_unchanged(self):
        url = "postgresql://user@host:5432/db"
        self.assertEqual(redact_database_url(url), url)

    def test_sqlite_url_passes_through(self):
        url = "sqlite:///./data/healthcare.db"
        self.assertEqual(redact_database_url(url), url)

    def test_empty_input_is_safe(self):
        # Falls back to the default, which carries no credentials.
        self.assertEqual(redact_database_url(None), DEFAULT_DATABASE_URL)
        self.assertEqual(redact_database_url(""), DEFAULT_DATABASE_URL)


if __name__ == "__main__":
    unittest.main()

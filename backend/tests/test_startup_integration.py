"""Integration checks that exercise a real SQLAlchemy engine.

The mocked unit tests in test_run_migrations.py cannot catch argument-shape
bugs in create_engine(); these do.
"""
import os
import sys
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_migrations import main, probe_database, wait_for_database  # noqa: E402


class QuietLogger:
    def warning(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass


class EnvCapturingLogger(QuietLogger):
    def __init__(self):
        self.lines = []

    def _rec(self, msg, *a):
        self.lines.append(msg % a if a else str(msg))

    warning = _rec
    error = _rec
    info = _rec


class TestProbeDatabaseRealEngine(unittest.TestCase):
    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        self.url = f"sqlite:///{self.path}"

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_probe_succeeds_on_reachable_sqlite(self):
        probe_database(self.url)  # must not raise

    def test_probe_raises_on_unreachable_sqlite_path(self):
        with self.assertRaises(Exception):
            probe_database("sqlite:////nonexistent-dir-xyz/db.sqlite")

    def test_probe_raises_on_legacy_postgres_scheme(self):
        # Exercises the postgres connect_args branch against an unroutable host.
        with self.assertRaises(Exception):
            probe_database("postgres://u:p@127.0.0.1:1/db")

    def test_wait_for_database_succeeds_on_real_sqlite(self):
        ok = wait_for_database(
            self.url, attempts=1, sleep=lambda _: None, logger=QuietLogger()
        )
        self.assertTrue(ok)

    def test_main_applies_migrations_to_real_sqlite(self):
        logger = EnvCapturingLogger()
        os.environ["DATABASE_URL"] = self.url
        try:
            exit_code = main(
                env=os.environ,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                sleep=lambda _: None,
                attempts=2,
                logger=logger,
            )
        finally:
            os.environ.pop("DATABASE_URL", None)
        self.assertEqual(exit_code, 0)
        conn = sqlite3.connect(self.path)
        try:
            tables = {
                r[0]
                for r in conn.execute("select name from sqlite_master where type='table'")
            }
        finally:
            conn.close()
        self.assertIn("alembic_version", tables, "migrations did not run")

    def test_startup_logs_do_not_leak_password(self):
        logger = EnvCapturingLogger()
        os.environ["DATABASE_URL"] = "postgres://nerve:s3cr3t@dpg-abc-a:5432/db"
        try:
            # Unreachable host -> wait fails fast, then we assert on the logs.
            main(
                env=os.environ,
                cwd="/app",
                sleep=lambda _: None,
                attempts=1,
                logger=logger,
            )
        finally:
            os.environ.pop("DATABASE_URL", None)
        joined = " ".join(logger.lines)
        self.assertNotIn("s3cr3t", joined)
        self.assertIn("dpg-abc-a", joined)


if __name__ == "__main__":
    unittest.main()

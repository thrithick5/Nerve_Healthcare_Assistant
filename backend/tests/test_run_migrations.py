import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_migrations import (  # noqa: E402
    DEFAULT_ATTEMPTS,
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_DELAY,
    main,
    run_alembic_upgrade,
    wait_for_database,
)


class TestDefaultWaitBudget(unittest.TestCase):
    """The default wait must not stall the Render deploy window."""

    def test_default_worst_case_wait_is_bounded(self):
        delays, delay = [], DEFAULT_BASE_DELAY
        for _ in range(DEFAULT_ATTEMPTS - 1):  # no sleep after final attempt
            delays.append(delay)
            delay = min(delay * 2, DEFAULT_MAX_DELAY)
        self.assertLessEqual(sum(delays), 60, f"default wait too long: {sum(delays)}s")

    def test_defaults_are_positive(self):
        self.assertGreaterEqual(DEFAULT_ATTEMPTS, 1)
        self.assertGreater(DEFAULT_BASE_DELAY, 0)
        self.assertGreaterEqual(DEFAULT_MAX_DELAY, DEFAULT_BASE_DELAY)


class RecordingLogger:
    def __init__(self):
        self.warnings = []
        self.errors = []

    def warning(self, msg, *args):
        self.warnings.append(msg % args if args else msg)

    def error(self, msg, *args):
        self.errors.append(msg % args if args else msg)

    def info(self, msg, *args):
        pass


def probe_sequence(*outcomes):
    """probe that consumes `outcomes` in order, then repeats the last one.

    An outcome that is an exception instance is raised; any other value
    (including ``None``) means the probe succeeds. Repeating the tail lets a
    single-error sequence model a permanently unreachable host.
    """
    calls = {"n": 0}

    def probe(url):
        i = calls["n"]
        calls["n"] += 1
        calls["last_url"] = url
        if not outcomes:
            return
        outcome = outcomes[min(i, len(outcomes) - 1)]
        if isinstance(outcome, BaseException):
            raise outcome

    probe.calls = calls
    return probe


class TestWaitForDatabase(unittest.TestCase):
    def test_returns_true_on_first_success_without_sleeping(self):
        sleeps = []
        probe = probe_sequence()
        ok = wait_for_database(
            "postgresql://u:p@h/db", attempts=5, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertTrue(ok)
        self.assertEqual(sleeps, [])
        self.assertEqual(probe.calls["n"], 1)

    def test_retries_until_success(self):
        sleeps = []
        # Two failures then success (None is the success sentinel).
        probe = probe_sequence(OSError("dns"), OSError("dns"), None)
        ok = wait_for_database(
            "postgresql://u:p@h/db", attempts=5, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertTrue(ok)
        self.assertEqual(probe.calls["n"], 3)
        self.assertEqual(sleeps, [1, 2])

    def test_returns_false_after_exhausting_attempts(self):
        sleeps = []
        probe = probe_sequence(OSError("dns"))
        ok = wait_for_database(
            "postgresql://u:p@h/db", attempts=3, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertFalse(ok)
        self.assertEqual(probe.calls["n"], 3)
        # Must NOT sleep after the final attempt.
        self.assertEqual(sleeps, [1, 2])

    def test_backoff_doubles_and_is_capped_at_max_delay(self):
        sleeps = []
        probe = probe_sequence(OSError("dns"))
        wait_for_database(
            "postgresql://u:p@h/db", attempts=6, base_delay=1, max_delay=4,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertEqual(sleeps, [1, 2, 4, 4, 4])

    def test_swallows_unexpected_exception_types(self):
        sleeps = []
        probe = probe_sequence(ValueError("boom"), KeyError("nope"))
        ok = wait_for_database(
            "postgresql://u:p@h/db", attempts=3, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertFalse(ok)

    def test_dns_resolution_failure_is_not_fatal(self):
        # The exact failure from the Render incident.
        import socket

        sleeps = []
        probe = probe_sequence(socket.gaierror(-2, "Name or service not known"))
        ok = wait_for_database(
            "postgresql://u:p@dpg-abc-a:5432/db", attempts=2, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertFalse(ok)

    def test_logs_error_on_exhaustion(self):
        logger = RecordingLogger()
        probe = probe_sequence(OSError("dns"))
        wait_for_database(
            "postgresql://u:p@h/db", attempts=1, base_delay=1, max_delay=8,
            probe=probe, sleep=lambda _: None, logger=logger,
        )
        self.assertTrue(any("database" in m.lower() for m in logger.errors))

    def test_attempts_must_be_at_least_one(self):
        sleeps = []
        probe = probe_sequence(OSError("dns"))
        ok = wait_for_database(
            "postgresql://u:p@h/db", attempts=0, base_delay=1, max_delay=8,
            probe=probe, sleep=sleeps.append, logger=RecordingLogger(),
        )
        self.assertFalse(ok)
        self.assertEqual(probe.calls["n"], 0)


class FakeCompleted:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRunAlembicUpgrade(unittest.TestCase):
    def test_returns_subprocess_returncode(self):
        seen = {}

        def runner(cmd, cwd=None, capture_output=None, text=None):
            seen["cmd"] = cmd
            seen["cwd"] = cwd
            return FakeCompleted(0, "ok")

        rc = run_alembic_upgrade(cwd="/app", runner=runner, python_executable="python")
        self.assertEqual(rc, 0)
        self.assertEqual(seen["cmd"], ["python", "-m", "alembic", "upgrade", "head"])
        self.assertEqual(seen["cwd"], "/app")

    def test_propagates_failure_returncode(self):
        rc = run_alembic_upgrade(cwd="/app", runner=lambda *a, **k: FakeCompleted(2, "", "boom"))
        self.assertEqual(rc, 2)


class TestMainNeverBlocksBoot(unittest.TestCase):
    """The container must always reach uvicorn, even when Postgres is unreachable."""

    def _run(self, *, reachable, alembic_rc=0):
        state = {"alembic_calls": 0, "uvicorn_would_start": False}

        def probe(url):
            if not reachable:
                raise OSError("could not translate host name to address")

        def runner(cmd, cwd=None, capture_output=None, text=None):
            state["alembic_calls"] += 1
            return FakeCompleted(alembic_rc, "", "")

        exit_code = main(
            env={"DATABASE_URL": "postgres://u:p@dpg-x-a:5432/db"},
            cwd="/app",
            probe=probe,
            runner=runner,
            sleep=lambda _: None,
            attempts=2,
            logger=RecordingLogger(),
            python_executable="python",
        )
        return exit_code, state

    def test_returns_zero_when_database_unreachable(self):
        exit_code, state = self._run(reachable=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(state["alembic_calls"], 0, "must not run alembic without a DB")

    def test_returns_zero_when_alembic_fails(self):
        exit_code, state = self._run(reachable=True, alembic_rc=1)
        self.assertEqual(exit_code, 0)
        self.assertEqual(state["alembic_calls"], 1)

    def test_returns_zero_on_success(self):
        exit_code, state = self._run(reachable=True, alembic_rc=0)
        self.assertEqual(exit_code, 0)
        self.assertEqual(state["alembic_calls"], 1)

    def test_normalizes_url_before_probing(self):
        seen = {}

        def probe(url):
            seen["url"] = url

        main(
            env={"DATABASE_URL": "postgres://u:p@h:5432/db"},
            cwd="/app",
            probe=probe,
            runner=lambda *a, **k: FakeCompleted(0),
            sleep=lambda _: None,
            attempts=1,
            logger=RecordingLogger(),
            python_executable="python",
        )
        self.assertEqual(seen["url"], "postgresql://u:p@h:5432/db")

    def test_missing_database_url_falls_back_to_sqlite(self):
        seen = {}

        def probe(url):
            seen["url"] = url

        main(
            env={},
            cwd="/app",
            probe=probe,
            runner=lambda *a, **k: FakeCompleted(0),
            sleep=lambda _: None,
            attempts=1,
            logger=RecordingLogger(),
            python_executable="python",
        )
        self.assertTrue(seen["url"].startswith("sqlite:///"))

    def test_alembic_failure_does_not_log_captured_output(self):
        """Alembic errors can echo DATABASE_URL; they must not be logged raw."""
        logger = RecordingLogger()
        secrets = []

        def runner(cmd, cwd=None, capture_output=None, text=None):
            secrets.append("s3cr3t")
            return FakeCompleted(1, f"could not connect using s3cr3t@host", "boom")

        main(
            env={"DATABASE_URL": "postgres://u:s3cr3t@h:5432/db"},
            cwd="/app",
            probe=lambda url: None,
            runner=runner,
            sleep=lambda _: None,
            attempts=1,
            logger=logger,
            python_executable="python",
        )
        joined = " ".join(logger.errors + logger.warnings)
        self.assertNotIn("s3cr3t@host", joined)

    def test_real_dns_failure_does_not_crash_main(self):
        """End-to-end: the reported error must not produce a non-zero exit."""
        import socket

        def probe(url):
            raise socket.gaierror(-2, "could not translate host name to address")

        exit_code = main(
            env={"DATABASE_URL": "postgres://u:p@dpg-d9pachvlk1mc73dlvm50-a:5432/db"},
            cwd="/app",
            probe=probe,
            runner=lambda *a, **k: self.fail("alembic must not run"),
            sleep=lambda _: None,
            attempts=2,
            logger=RecordingLogger(),
            python_executable="python",
        )
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

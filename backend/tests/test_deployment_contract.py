"""Guards the Render deployment contract.

A region mismatch between the web service and the database is the root cause
of the "could not translate host name" startup failure, and it is invisible in
local runs because render.yaml is never executed. These checks read the file.
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RENDER_YAML = os.path.join(REPO_ROOT, "render.yaml")
DOCKERFILE = os.path.join(REPO_ROOT, "backend", "Dockerfile")
MIGRATIONS = os.path.join(REPO_ROOT, "backend", "scripts", "run_migrations.py")


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class TestRenderYamlContract(unittest.TestCase):
    def setUp(self):
        self.text = _read(RENDER_YAML)

    def test_database_declares_a_region(self):
        self.assertRegex(self.text, r"databaseName:.*\n(?:.*\n)*?\s*region:")

    def test_service_and_database_regions_match(self):
        regions = re.findall(r"region:\s*(\S+)", self.text)
        self.assertGreaterEqual(
            len(regions), 2, "both database and service must declare a region"
        )
        self.assertEqual(
            len(set(regions)),
            1,
            f"region mismatch will break the internal database hostname: {regions}",
        )

    def test_database_url_comes_from_the_database_resource(self):
        self.assertIn("fromDatabase:", self.text)
        self.assertIn("connectionString", self.text)


class TestDockerfileContract(unittest.TestCase):
    def setUp(self):
        self.text = _read(DOCKERFILE)

    def test_uses_the_resilient_migration_runner(self):
        self.assertIn("scripts/run_migrations.py", self.text)

    def test_migrations_do_not_short_circuit_uvicorn(self):
        """`alembic && uvicorn` means a DB outage prevents the API from booting."""
        cmd = [l for l in self.text.splitlines() if l.startswith("CMD")]
        self.assertTrue(cmd, "Dockerfile has no CMD")
        self.assertNotRegex(
            cmd[0], r"alembic[^|;&]*&&[^|;&]*uvicorn",
            "uvicorn must not be gated behind the migration exit code",
        )

    def test_migration_runner_exists(self):
        self.assertTrue(os.path.isfile(MIGRATIONS))


if __name__ == "__main__":
    unittest.main()

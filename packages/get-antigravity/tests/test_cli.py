#!/usr/bin/env python3
"""CLI tests for get-antigravity."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = PACKAGE_ROOT / "bin"
CLI_SCRIPT = BIN_DIR / "get_antigravity.py"

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import get_antigravity_core as core
import bin.get_antigravity as cli


class TestGetAntigravityCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)
        self.skip_file = self.tmp / "skip.json"
        os.environ["GET_ANTIGRAVITY_SKIP_FILE"] = str(self.skip_file)
        os.environ["GET_ANTIGRAVITY_SKIP_REMOTE_CHECK"] = "1"

    def tearDown(self):
        os.environ.pop("GET_ANTIGRAVITY_SKIP_FILE", None)
        os.environ.pop("GET_ANTIGRAVITY_SKIP_REMOTE_CHECK", None)
        self.temp_dir.cleanup()

    def test_cli_skip_and_unskip_workflow(self):
        # 1. Skip a package
        exit_code = cli.main(["skip", "agy-waypoints", "--action", "install"])
        self.assertEqual(exit_code, 0)
        
        skips = core.load_skip_list(str(self.skip_file))
        self.assertEqual(skips, {"agy-waypoints": "install"})

        # 2. List skips
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = cli.main(["skips"])
        self.assertEqual(exit_code, 0)
        self.assertIn("agy-waypoints", buf.getvalue())
        self.assertIn("skip install", buf.getvalue())

        # 3. Unskip package
        exit_code = cli.main(["unskip", "agy-waypoints"])
        self.assertEqual(exit_code, 0)
        skips = core.load_skip_list(str(self.skip_file))
        self.assertEqual(skips, {})

    def test_cli_list_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = cli.main(["list", "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        pkg_names = [p["name"] for p in data]
        self.assertIn("get-antigravity", pkg_names)
        self.assertIn("agy-free-agent", pkg_names)

    def test_cli_plan_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = cli.main(["plan", "--json"])
        self.assertEqual(exit_code, 0)
        plan = json.loads(buf.getvalue())
        self.assertIn("missing", plan)
        self.assertIn("outdated", plan)
        self.assertIn("skipped", plan)
        self.assertIn("has_actions", plan)

    def test_cli_plan_with_only_flag(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = cli.main(["plan", "--only", "agy-free-agent", "--json"])
        self.assertEqual(exit_code, 0)
        plan = json.loads(buf.getvalue())
        self.assertEqual(plan["catalog_count"], 1)

    def test_cli_apply_dry_run(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = cli.main(["apply", "--dry-run"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Applying Antigravity Suite package installation", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

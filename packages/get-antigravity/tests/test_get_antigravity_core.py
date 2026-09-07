#!/usr/bin/env python3
"""Comprehensive unit tests for get_antigravity_core."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import get_antigravity_core as core


class TestGetAntigravityCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- JSON Loading & Saving ---

    def test_load_json_missing_file_returns_empty(self):
        self.assertEqual(core.load_json(str(self.tmp / "nonexistent.json")), {})

    def test_load_json_corrupted_file_returns_empty(self):
        bad_file = self.tmp / "bad.json"
        bad_file.write_text("{not valid json: 123", encoding="utf-8")
        self.assertEqual(core.load_json(str(bad_file)), {})

    def test_save_json_atomic_creates_directories_and_writes_data(self):
        dest = self.tmp / "nested" / "deep" / "data.json"
        core.save_json_atomic(str(dest), {"status": "ok", "count": 42})
        self.assertTrue(dest.is_file())
        self.assertEqual(core.load_json(str(dest)), {"status": "ok", "count": 42})

    # --- Skip List Management ---

    def test_load_skip_list_missing_returns_empty(self):
        self.assertEqual(core.load_skip_list(str(self.tmp / "skip.json")), {})

    def test_set_and_remove_skip(self):
        initial = {"pkg-a": "install"}
        step1 = core.set_skip(initial, "pkg-b", "update")
        self.assertEqual(step1, {"pkg-a": "install", "pkg-b": "update"})

        step2 = core.set_skip(step1, "pkg-c", "invalid-action")  # defaults to "both"
        self.assertEqual(step2["pkg-c"], "both")

        step3 = core.remove_skip(step2, "pkg-a")
        self.assertEqual(step3, {"pkg-b": "update", "pkg-c": "both"})

    def test_save_and_load_skip_list_roundtrip(self):
        skip_path = str(self.tmp / "test-skip.json")
        data = {"agy-audit-loose-ends": "install", "agy-waypoints": "both"}
        core.save_skip_list(skip_path, data)
        loaded = core.load_skip_list(skip_path)
        self.assertEqual(loaded, data)

    def test_filter_missing_by_skip(self):
        missing = ["pkg-1", "pkg-2", "pkg-3", "pkg-4"]
        skip_list = {
            "pkg-1": "install",
            "pkg-2": "both",
            "pkg-3": "update",  # update skip does NOT filter out missing install
        }
        filtered = core.filter_missing_by_skip(missing, skip_list)
        self.assertEqual(filtered, ["pkg-3", "pkg-4"])

    def test_filter_outdated_by_skip(self):
        outdated = [
            {"name": "pkg-1", "installed_version": "0.1.0", "remote_version": "0.2.0"},
            {"name": "pkg-2", "installed_version": "0.1.0", "remote_version": "0.2.0"},
            {"name": "pkg-3", "installed_version": "0.1.0", "remote_version": "0.2.0"},
            {"name": "pkg-4", "installed_version": "0.1.0", "remote_version": "0.2.0"},
        ]
        skip_list = {
            "pkg-1": "update",
            "pkg-2": "both",
            "pkg-3": "install",  # install skip does NOT filter out update
        }
        filtered = core.filter_outdated_by_skip(outdated, skip_list)
        names = [item["name"] for item in filtered]
        self.assertEqual(names, ["pkg-3", "pkg-4"])

    # --- Version Parsing & Semantics ---

    def test_parse_version(self):
        self.assertEqual(core.parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(core.parse_version("v0.10.4"), (0, 10, 4))
        self.assertEqual(core.parse_version("2.0.0-rc1"), (2, 0, 0))
        self.assertEqual(core.parse_version("1.0"), (1, 0))
        self.assertIsNone(core.parse_version("not-a-version"))
        self.assertIsNone(core.parse_version(None))

    def test_remote_is_newer(self):
        # Strict increments
        self.assertTrue(core.remote_is_newer("0.1.0", "0.2.0"))
        self.assertTrue(core.remote_is_newer("1.9.0", "1.10.0"))
        self.assertTrue(core.remote_is_newer("0.1", "0.1.1"))

        # Equal / older
        self.assertFalse(core.remote_is_newer("1.0.0", "1.0.0"))
        self.assertFalse(core.remote_is_newer("0.4", "0.4.0"))
        self.assertFalse(core.remote_is_newer("2.0.0", "1.9.9"))

        # Missing / None
        self.assertFalse(core.remote_is_newer(None, "1.0.0"))
        self.assertFalse(core.remote_is_newer("1.0.0", None))
        self.assertFalse(core.remote_is_newer("", "1.0.0"))

    # --- Catalog Loading & Filtering ---

    def test_load_catalog(self):
        pkg_dir = self.tmp / "packages"
        pkg1 = pkg_dir / "pkg-one"
        pkg1.mkdir(parents=True)
        (pkg1 / "plugin.json").write_text(json.dumps({
            "name": "pkg-one",
            "version": "1.0.0",
            "description": "First Package",
            "category": "tools",
        }), encoding="utf-8")
        (pkg1 / "skills" / "skill-a").mkdir(parents=True)

        pkg2 = pkg_dir / "pkg-two"
        pkg2.mkdir(parents=True)
        (pkg2 / "plugin.json").write_text(json.dumps({
            "name": "pkg-two",
            "version": "2.1.0",
            "category": "system",
        }), encoding="utf-8")

        catalog = core.load_catalog(str(pkg_dir))
        self.assertEqual(len(catalog), 2)
        
        c1 = next(c for c in catalog if c["name"] == "pkg-one")
        self.assertEqual(c1["version"], "1.0.0")
        self.assertEqual(c1["skills"], ["skill-a"])
        self.assertEqual(c1["category"], "tools")

    def test_filter_catalog_by_selection(self):
        catalog = [
            {"name": "a", "dir_name": "a", "category": "tools"},
            {"name": "b", "dir_name": "b", "category": "system"},
            {"name": "c", "dir_name": "c", "category": "tools"},
        ]
        # By name
        self.assertEqual([e["name"] for e in core.filter_catalog_by_selection(catalog, names=["a", "c"])], ["a", "c"])
        # By category
        self.assertEqual([e["name"] for e in core.filter_catalog_by_selection(catalog, category="system")], ["b"])
        # Both (AND logic)
        self.assertEqual([e["name"] for e in core.filter_catalog_by_selection(catalog, names=["a", "b"], category="tools")], ["a"])

    # --- Missing, Outdated & Plan Generation ---

    def test_compute_missing_and_outdated(self):
        catalog = [
            {"name": "get-antigravity", "version": "1.0.0"},
            {"name": "pkg-a", "version": "1.0.0"},
            {"name": "pkg-b", "version": "2.0.0"},
            {"name": "pkg-c", "version": "1.5.0"},
        ]
        installed = {
            "pkg-a": {"version": "1.0.0"},
            "pkg-b": {"version": "1.0.0"},  # outdated
        }
        remote_versions = {
            "pkg-b": "2.0.0",
            "pkg-c": "1.5.0",
        }

        missing = core.compute_missing(catalog, installed, self_name="get-antigravity")
        self.assertEqual(missing, ["pkg-c"])

        outdated = core.compute_outdated(catalog, installed, remote_versions, self_name="get-antigravity")
        self.assertEqual(len(outdated), 1)
        self.assertEqual(outdated[0]["name"], "pkg-b")
        self.assertEqual(outdated[0]["installed_version"], "1.0.0")
        self.assertEqual(outdated[0]["remote_version"], "2.0.0")

    def test_generate_plan_with_skips(self):
        catalog = [
            {"name": "get-antigravity", "dir_name": "get-antigravity", "version": "1.0.0", "category": "system"},
            {"name": "pkg-missing", "dir_name": "pkg-missing", "version": "1.0.0", "category": "tools"},
            {"name": "pkg-skipped-install", "dir_name": "pkg-skipped-install", "version": "1.0.0", "category": "tools"},
            {"name": "pkg-outdated", "dir_name": "pkg-outdated", "version": "2.0.0", "category": "tools"},
        ]
        installed = {
            "pkg-outdated": {"version": "1.0.0"},
        }
        remotes = {
            "pkg-outdated": "2.0.0",
        }
        skips = {
            "pkg-skipped-install": "install",
        }

        plan = core.generate_plan(
            catalog=catalog,
            installed=installed,
            remote_versions=remotes,
            skip_list=skips,
        )

        self.assertEqual(plan["missing"], ["pkg-missing"])
        self.assertEqual(len(plan["outdated"]), 1)
        self.assertEqual(plan["outdated"][0]["name"], "pkg-outdated")
        self.assertTrue(plan["has_actions"])
        self.assertEqual(len(plan["skipped"]), 1)

    # --- Daily Refresh & Stamping ---

    def test_refresh_stamp_lifecycle(self):
        stamp_file = str(self.tmp / "refresh.json")
        self.assertTrue(core.should_refresh(stamp_file, "2026-09-08"))

        core.save_refresh_state(stamp_file, "2026-09-08", {"pkg-a": "1.2.0"})
        self.assertFalse(core.should_refresh(stamp_file, "2026-09-08"))
        self.assertTrue(core.should_refresh(stamp_file, "2026-09-09"))

        cached = core.load_cached_versions(stamp_file)
        self.assertEqual(cached, {"pkg-a": "1.2.0"})

    # --- Notification Banner Formatting ---

    def test_format_nudge(self):
        self.assertEqual(core.format_nudge([], []), "")
        banner = core.format_nudge(
            missing=["pkg-x"],
            outdated=[{"name": "pkg-y", "installed_version": "1.0", "remote_version": "1.1"}],
        )
        self.assertIn("+ pkg-x (not installed)", banner)
        self.assertIn("^ pkg-y 1.0 -> 1.1", banner)
        self.assertIn("get-antigravity", banner)


if __name__ == "__main__":
    unittest.main()

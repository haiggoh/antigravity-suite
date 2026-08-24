#!/usr/bin/env python3
"""Smoke tests for Antigravity Sync Engine (sync_engine.py)"""

import os
import sys
import json
import shutil
import tempfile
import unittest

# Add bin/ to sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "bin"))

from sync_engine import (
    expand_placeholders,
    deep_merge,
    LOCAL_EXCLUSIVE_KEYS,
    sync_local_config,
    sync_rules,
    sync_statusline,
    sync_workspace_root,
    cleanup_legacy_antigravity_dir,
)


class TestSyncEngineSmoke(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="agy_test_")
        self.home_dir = os.path.join(self.test_dir, "home")
        self.workspace_dir = os.path.join(self.test_dir, "workspace")
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.workspace_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_expand_placeholders_string(self):
        template = "python3 {HOME}/.gemini/status.py in {WORKSPACE} for {USER}"
        res = expand_placeholders(template, home_dir="/custom/home", workspace_dir="/custom/ws", username="devuser")
        self.assertEqual(res, "python3 /custom/home/.gemini/status.py in /custom/ws for devuser")

    def test_expand_placeholders_nested(self):
        data = {
            "statusLine": {"command": "{HOME}/status.py"},
            "paths": ["{WORKSPACE}/repo1", "{HOME}/data"],
            "number": 42,
            "bool": True
        }
        res = expand_placeholders(data, home_dir="/my/home", workspace_dir="/my/ws", username="test")
        self.assertEqual(res["statusLine"]["command"], "/my/home/status.py")
        self.assertEqual(res["paths"], ["/my/ws/repo1", "/my/home/data"])
        self.assertEqual(res["number"], 42)
        self.assertEqual(res["bool"], True)

    def test_deep_merge_preserves_local_keys(self):
        target = {
            "email": "user1@company.com",
            "tokens": {"oauth": "secret-token-123"},
            "trustedWorkspaces": ["/workspace/one"],
            "model": "old-model",
            "permissions": {"allow": ["command(cat)"]}
        }
        source = {
            "email": "template@shared.com",
            "tokens": {"oauth": "should-not-overwrite"},
            "trustedWorkspaces": ["/workspace/shared"],
            "model": "Gemini 3.7 Flash",
            "permissions": {"allow": ["command(git)"]}
        }
        merged = deep_merge(target, source)
        # Local keys preserved
        self.assertEqual(merged["email"], "user1@company.com")
        self.assertEqual(merged["tokens"]["oauth"], "secret-token-123")
        self.assertEqual(merged["trustedWorkspaces"], ["/workspace/one"])
        # Non-local keys updated / unioned
        self.assertEqual(merged["model"], "Gemini 3.7 Flash")
        self.assertIn("command(cat)", merged["permissions"]["allow"])
        self.assertIn("command(git)", merged["permissions"]["allow"])

    def test_sync_rules(self):
        rules_src = os.path.join(self.test_dir, "rules_src")
        os.makedirs(rules_src, exist_ok=True)
        with open(os.path.join(rules_src, "test_rule.md"), "w", encoding="utf-8") as f:
            f.write("# Rule Test")

        # Test dry-run returns cleanly without writing to system paths
        sync_rules(rules_src, dry_run=True)
        self.assertTrue(os.path.isfile(os.path.join(rules_src, "test_rule.md")))

    def test_sync_workspace_root(self):
        # Create mock repo root with templates
        fake_repo = os.path.join(self.test_dir, "fake_repo")
        os.makedirs(os.path.join(fake_repo, "templates", "agents"), exist_ok=True)
        
        with open(os.path.join(fake_repo, "templates", "workspace-GEMINI.md"), "w", encoding="utf-8") as f:
            f.write("# Workspace Guide")
        with open(os.path.join(fake_repo, "templates", "agents", "auto_approve.py"), "w", encoding="utf-8") as f:
            f.write("import json; print('{}')")

        target_ws = os.path.join(self.test_dir, "target_workspace")
        os.makedirs(target_ws, exist_ok=True)

        sync_workspace_root(target_ws, fake_repo, dry_run=False)

        self.assertTrue(os.path.isfile(os.path.join(target_ws, "GEMINI.md")))
        self.assertTrue(os.path.isfile(os.path.join(target_ws, ".agents", "auto_approve.py")))


if __name__ == "__main__":
    unittest.main()

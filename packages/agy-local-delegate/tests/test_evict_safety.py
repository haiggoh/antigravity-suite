import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))

import agy_local_delegate_core as core


class EvictionSafetyTests(unittest.TestCase):
    def test_claude_base_url_marks_port_attached(self):
        process_table = MagicMock()
        process_table.stdout = (
            "123  claude --model claude-opus-5 "
            "CLAUDE_IS_LOCAL=true "
            "ANTHROPIC_BASE_URL=http://localhost:8000\n"
        )

        with patch(
            "agy_local_delegate_core.subprocess.run",
            return_value=process_table,
        ):
            attached, reliable = core.get_attached_client_ports()

        self.assertTrue(reliable)
        self.assertEqual(attached[8000], ["Claude Code"])

    def test_agy_proxy_protects_proxy_and_upstream(self):
        process_table = MagicMock()
        process_table.stdout = (
            "456  agy "
            "GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:9191\n"
        )

        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = (
            b'{"upstream":"http://127.0.0.1:8001/v1"}'
        )

        with patch(
            "agy_local_delegate_core.subprocess.run",
            return_value=process_table,
        ), patch(
            "agy_local_delegate_core.urllib.request.urlopen",
            return_value=response,
        ):
            attached, reliable = core.get_attached_client_ports()

        self.assertTrue(reliable)
        self.assertEqual(attached[9191], ["AGY"])
        self.assertEqual(attached[8001], ["AGY"])

    def test_client_inspection_failure_is_reported_unreliable(self):
        with patch(
            "agy_local_delegate_core.subprocess.run",
            side_effect=OSError("ps unavailable"),
        ):
            attached, reliable = core.get_attached_client_ports()

        self.assertEqual(attached, {})
        self.assertFalse(reliable)

    def test_explicit_attached_target_is_protected_without_force(self):
        server = {
            "port": 8000,
            "pid": 12345,
            "backend": "rapid-mlx",
            "command": "rapid-mlx serve model --port 8000",
            "rss_mb": 12000.0,
            "etime": "01:00",
            "attached": True,
            "attached_clients": ["Claude Code"],
            "rank": 3,
        }

        with patch.object(
            core,
            "list_resident_servers",
            return_value=[server],
        ), patch.object(core.os, "kill") as kill:
            results = core.evict_servers(port=8000)

        self.assertEqual(results[0]["action"], "protected_attached")
        kill.assert_not_called()

    def test_all_skips_attached_but_keeps_idle_server_eligible(self):
        attached = {
            "port": 8000,
            "pid": 100,
            "backend": "rapid-mlx",
            "command": "rapid-mlx serve attached",
            "rss_mb": 10000.0,
            "etime": "10:00",
            "attached": True,
            "attached_clients": ["Claude Code"],
            "rank": 3,
        }
        idle = {
            "port": 8001,
            "pid": 101,
            "backend": "rapid-mlx",
            "command": "rapid-mlx serve idle",
            "rss_mb": 9000.0,
            "etime": "09:00",
            "attached": False,
            "attached_clients": [],
            "rank": 1,
        }

        with patch.object(
            core,
            "list_resident_servers",
            return_value=[idle, attached],
        ):
            results = core.evict_servers(
                evict_all=True,
                dry_run=True,
            )

        actions = {
            result["pid"]: result["action"] for result in results
        }
        self.assertEqual(actions[100], "protected_attached")
        self.assertEqual(actions[101], "would_evict")

    def test_default_selects_idle_server_before_attached_server(self):
        attached = {
            "port": 8000,
            "pid": 100,
            "backend": "rapid-mlx",
            "command": "rapid-mlx serve attached",
            "rss_mb": 20000.0,
            "etime": "10:00",
            "attached": True,
            "attached_clients": ["Claude Code"],
            "rank": 3,
        }
        idle = {
            "port": 8001,
            "pid": 101,
            "backend": "rapid-mlx",
            "command": "rapid-mlx serve idle",
            "rss_mb": 9000.0,
            "etime": "09:00",
            "attached": False,
            "attached_clients": [],
            "rank": 1,
        }

        with patch.object(
            core,
            "list_resident_servers",
            return_value=[idle, attached],
        ):
            results = core.evict_servers(dry_run=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["pid"], 101)
        self.assertEqual(results[0]["action"], "would_evict")


if __name__ == "__main__":
    unittest.main()

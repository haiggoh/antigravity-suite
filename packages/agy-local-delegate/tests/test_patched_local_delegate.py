import importlib.util
import io
import json
import os
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import agy_local_delegate_core as core

spec = importlib.util.spec_from_file_location("agy_local_proxy", PACKAGE / "bin" / "agy_local_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class PatchedDelegateTests(unittest.TestCase):
    def test_custom_model_is_not_replaced_by_default(self):
        payload = core.build_chat_payload("hello", "org/custom-model")
        self.assertEqual(payload["model"], "org/custom-model")

    def test_alias_resolution_and_matching(self):
        resolved = core.resolve_model_reference("qwen-3.8-operator")
        self.assertEqual(resolved["model_id"], "mlx-community/Qwen3.8-27B-4bit")
        self.assertTrue(core.model_names_match("qwen3.8-27b-4bit", "qwen-3.8-operator"))
        self.assertFalse(core.model_names_match("unrelated", "qwen-3.8-operator"))

    def test_matching_server_skips_unrelated_server(self):
        servers = [
            {"port": 8000, "endpoint": "http://127.0.0.1:8000/v1", "models": ["unrelated"]},
            {"port": 8001, "endpoint": "http://127.0.0.1:8001/v1", "models": ["qwen3.8-27b-4bit"]},
        ]
        with patch.object(core, "find_active_model_servers", return_value=servers):
            self.assertEqual(core.find_matching_model_server("qwen-3.8-operator")["port"], 8001)

    def test_menu_stdout_contains_only_selected_alias(self):
        old_argv, old_stdin = sys.argv, sys.stdin
        sys.argv = [str(PACKAGE / "bin" / "agy_local_delegate.py"), "menu"]
        sys.stdin = io.StringIO("\n")
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with patch.object(core, "scan_local_models_dir", return_value={"installed_catalog": []}), \
                 patch.object(core, "find_active_model_servers", return_value=[]), \
                 redirect_stdout(stdout), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exit_info:
                    runpy.run_path(str(PACKAGE / "bin" / "agy_local_delegate.py"), run_name="__main__")
            self.assertEqual(exit_info.exception.code, 0)
        finally:
            sys.argv, sys.stdin = old_argv, old_stdin
        self.assertEqual(stdout.getvalue(), "qwen-3.8-operator\n")
        self.assertIn("Selection [1]:", stderr.getvalue())

    def test_tool_call_round_trip(self):
        request = {
            "contents": [{"role": "user", "parts": [{"text": "read"}]}],
            "tools": [{"functionDeclarations": [{
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "OBJECT", "properties": {"path": {"type": "STRING"}}},
            }]}],
        }
        translated = proxy.gemini_request_to_openai(request, "local")
        self.assertEqual(translated["tools"][0]["function"]["name"], "read_file")
        self.assertEqual(translated["tools"][0]["function"]["parameters"]["type"], "object")
        self.assertEqual(
            translated["tools"][0]["function"]["parameters"]["properties"]["path"]["type"],
            "string",
        )

        response = {"model": "local", "choices": [{
            "index": 0,
            "finish_reason": "tool_calls",
            "message": {"content": None, "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"path":"a.py"}'},
            }]},
        }]}
        call = proxy.openai_response_to_gemini(response)["candidates"][0]["content"]["parts"][0]["functionCall"]
        self.assertEqual(call["args"], {"path": "a.py"})
        self.assertEqual(call["id"], "call_1")

    def test_proxy_smoke_parser(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "LOCAL"}]}}]
        }).encode()
        with patch("urllib.request.urlopen", return_value=response):
            result = core.smoke_test_gemini_proxy("http://127.0.0.1:9191", timeout=1)
        self.assertTrue(result["success"])
        self.assertEqual(result["reply"], "LOCAL")


if __name__ == "__main__":
    unittest.main()

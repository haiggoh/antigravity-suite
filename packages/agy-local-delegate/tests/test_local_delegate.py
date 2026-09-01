import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_local_delegate_core as core


def test_bundle_file_attachments():
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "test1.txt")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("Line 1 in test 1")

        f2 = os.path.join(tmpdir, "test2.txt")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("Line 2 in test 2")

        bundled = core.bundle_file_attachments([f1, f2])
        assert "ATTACHED FILE CONTEXT" in bundled
        assert "test1.txt" in bundled
        assert "Line 1 in test 1" in bundled
        assert "test2.txt" in bundled


def test_build_chat_payload():
    payload = core.build_chat_payload(
        prompt="Review database adapter",
        model_alias="qwen-3.6-operator",
    )
    assert payload["model"] == "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit"
    assert len(payload["messages"]) == 2
    assert payload["messages"][1]["content"] == "Review database adapter"


def test_check_server_health_offline():
    res = core.check_server_health("http://127.0.0.1:9999/v1", timeout=0.1)
    assert res["online"] is False
    assert "error" in res


def test_dispatch_local_prompt_mocked():
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Refactored function successfully.",
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json_bytes = (
        '{"choices": [{"message": {"role": "assistant", "content": "Refactored function successfully."}}], "usage": {"prompt_tokens": 50, "completion_tokens": 20}}'
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = core.dispatch_local_prompt("Refactor code", model_alias="qwen-3.6-operator")
        assert res["success"] is True
        assert res["reply"] == "Refactored function successfully."

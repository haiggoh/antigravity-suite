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


def test_build_chat_payload_default_qwen38():
    payload = core.build_chat_payload(
        prompt="Review database adapter",
        model_alias="qwen-3.8-operator",
    )
    assert payload["model"] == "mlx-community/Qwen3.8-27B-4bit"
    assert len(payload["messages"]) == 2
    assert payload["messages"][1]["content"] == "Review database adapter"


def test_scan_local_models_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a catalog model directory
        qwen_dir = os.path.join(tmpdir, "Qwen3.8-27B-4bit")
        os.makedirs(qwen_dir, exist_ok=True)
        with open(os.path.join(qwen_dir, "weights.bin"), "w") as f:
            f.write("mock weights")

        # Create an unregistered model directory
        custom_dir = os.path.join(tmpdir, "Custom-Experimental-14B")
        os.makedirs(custom_dir, exist_ok=True)
        with open(os.path.join(custom_dir, "weights.bin"), "w") as f:
            f.write("mock custom weights")

        scan = core.scan_local_models_dir(tmpdir)
        assert scan["exists"] is True
        installed_aliases = [m["alias"] for m in scan["installed_catalog"]]
        assert "qwen-3.8-operator" in installed_aliases
        assert "qwen-3.8-thinking" in installed_aliases

        unregistered_names = [u["name"] for u in scan["unregistered_models"]]
        assert "Custom-Experimental-14B" in unregistered_names


def test_check_server_health_offline():
    res = core.check_server_health("http://127.0.0.1:9999/v1", timeout=0.1)
    assert res["online"] is False
    assert "error" in res


def test_dispatch_local_prompt_mocked():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = (
        '{"choices": [{"message": {"role": "assistant", "content": "Refactored function successfully."}}], "usage": {"prompt_tokens": 50, "completion_tokens": 20}}'
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = core.dispatch_local_prompt("Refactor code", model_alias="qwen-3.8-operator", skip_ram_preflight=True)
        assert res["success"] is True
        assert res["reply"] == "Refactored function successfully."


def test_find_free_port():
    port = core.find_free_port(9500, 9550)
    assert 9500 <= port <= 9550


def test_ram_preflight_check():
    with patch("agy_local_delegate_core.get_available_system_ram_gb", return_value=(64.0, 128.0)), \
         patch("agy_local_delegate_core.get_model_weights_size_gb", return_value=15.0), \
         patch("agy_local_delegate_core.find_active_model_servers", return_value=[]):
        res = core.ram_preflight_check("qwen-3.8-operator", floor_gb=16.0, overhead_gb=6.0)
        assert res["fits"] is True
        assert res["need_gb"] == 21.0
        assert res["available_gb"] == 64.0
        assert res["already_served"] is False


def test_ram_preflight_already_served():
    mock_servers = [{"port": 8000, "endpoint": "http://127.0.0.1:8000/v1", "models": ["mlx-community/Qwen3.8-27B-4bit"]}]
    with patch("agy_local_delegate_core.find_active_model_servers", return_value=mock_servers):
        res = core.ram_preflight_check("qwen-3.8-operator")
        assert res["fits"] is True
        assert res["already_served"] is True
        assert res["served_port"] == 8000


def test_evict_servers_dry_run():
    mock_servers = [{
        "port": 8000,
        "pid": 12345,
        "backend": "rapid-mlx",
        "command": "rapid-mlx --model qwen",
        "rss_mb": 14500.0,
        "etime": "01:20:00",
        "attached": False,
        "rank": 1,
    }]
    with patch("agy_local_delegate_core.list_resident_servers", return_value=mock_servers):
        results = core.evict_servers(dry_run=True)
        assert len(results) == 1
        assert results[0]["pid"] == 12345
        assert results[0]["action"] == "would_evict"
        assert results[0]["rss_mb"] == 14500.0


def test_dispatch_local_prompt_ram_preflight_block():
    mock_preflight = {
        "fits": False,
        "already_served": False,
        "message": "Tight memory (would breach 16GB floor)",
    }
    with patch("agy_local_delegate_core.ram_preflight_check", return_value=mock_preflight):
        res = core.dispatch_local_prompt("Refactor code", model_alias="qwen-3.8-operator")
        assert res["success"] is False
        assert "RAM preflight safety check failed" in res["error"]





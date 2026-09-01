import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_audit_core as core


def test_redact_secret_text():
    sample = "Anthropic key: sk-ant-api03-1234567890abcdef1234567890abcdef and Google: AIzaSyD1234567890abcdef1234567890abcdef"
    redacted, count = core.redact_secret_text(sample)
    assert count == 2
    assert "sk-ant-" not in redacted or "REDACTED" in redacted
    assert "AIza" not in redacted or "REDACTED" in redacted


def test_scan_workspace_records():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create clean file
        with open(os.path.join(tmpdir, "clean.md"), "w", encoding="utf-8") as f:
            f.write("# Clean Document\nEverything is properly formatted.\n")

        # Create file with loose task
        with open(os.path.join(tmpdir, "GEMINI.md"), "w", encoding="utf-8") as f:
            f.write("## Tasks\n- [ ] TODO: Implement OAuth login\n")

        # Create file with secret
        with open(os.path.join(tmpdir, "config.txt"), "w", encoding="utf-8") as f:
            f.write("GH_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxy\n")

        report = core.scan_workspace_records(tmpdir)
        assert report["scanned_files_count"] == 3
        assert len(report["secrets_found"]) == 1
        assert report["secrets_found"][0]["type"] == "GitHub Personal Access Token"
        assert len(report["loose_tasks"]) == 1
        assert "Implement OAuth login" in report["loose_tasks"][0]["task"]

        report_str = core.format_audit_report(report)
        assert "Exposed Secrets Detected" in report_str
        assert "Unreconciled / Open Task Items" in report_str

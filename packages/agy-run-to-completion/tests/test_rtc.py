import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_rtc_core as core


def test_parse_gate_reason():
    res1 = core.parse_gate_reason("G1: choose between JSON or YAML format")
    assert res1["tier"] == "G1"
    assert res1["rank"] == 1
    assert "choose between" in res1["detail"]

    res2 = core.parse_gate_reason("ENV: docker daemon must be running")
    assert res2["tier"] == "ENV"
    assert res2["rank"] == 5

    res3 = core.parse_gate_reason("WAIT: depends on authentication module")
    assert res3["tier"] == "WAIT"
    assert res3["rank"] == 6


def test_triage_task_list():
    sample_lines = [
        "- [ ] Implement core math helpers",
        "- [ ] Refactor heavy database architecture (heavy)",
        "- [ ] Configure cloud OAuth credentials (blocked: G1: need client secret from dashboard)",
        "- [ ] Run integration smoke tests (blocked: ENV: test server online)",
        "- [x] Setup repository gitignore",
    ]

    triage = core.triage_task_list(sample_lines)
    assert len(triage["tier1_do_now"]) == 1
    assert "Implement core math helpers" in triage["tier1_do_now"][0]["title"]

    assert len(triage["tier2_heavy"]) == 1
    assert "Refactor heavy database" in triage["tier2_heavy"][0]["title"]

    assert len(triage["gated"]) == 2
    # G1 (rank 1) should sort before ENV (rank 5)
    assert triage["gated"][0]["gate_info"]["tier"] == "G1"
    assert triage["gated"][1]["gate_info"]["tier"] == "ENV"

    assert len(triage["completed"]) == 1
    assert "Setup repository gitignore" in triage["completed"][0]["title"]


def test_format_reports():
    sample_lines = [
        "- [ ] Simple task",
        "- [ ] Blocked item (blocked: G1: pick a name)",
    ]
    triage = core.triage_task_list(sample_lines)

    summary = core.format_triage_summary(triage)
    assert "Tier 1: Do Now" in summary
    assert "Gated Tasks" in summary

    ungate_qs = core.format_ungate_questions(triage["gated"])
    assert "Attended Ungating Pass" in ungate_qs
    assert "[G1] Blocked item" in ungate_qs
    assert "What is your decision" in ungate_qs

    closeout = core.format_closeout_report(["Simple task"], triage["gated"])
    assert "Completed & Shipped Work" in closeout
    assert "Remaining Gated Work" in closeout

import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_cost_tracker_core as core


def test_price_tokens():
    # Gemini 3.7 Flash: 0.15e-6 in, 0.60e-6 out
    cost = core.price_tokens("gemini-3.7-flash", 1_000_000, 1_000_000)
    assert cost == pytest.approx(0.75, rel=1e-3)

    # Claude Sonnet 5: 3.00e-6 in, 15.00e-6 out
    cost_sonnet = core.price_tokens("claude-sonnet-5", 1_000_000, 1_000_000)
    assert cost_sonnet == pytest.approx(18.00, rel=1e-3)


def test_format_statusline():
    line = core.format_statusline(today_spend=12.34, cap_usd=40.0, local_saved=4.50)
    assert "today: cloud $12.34/$40.00" in line
    assert "local saved $4.50" in line

    line_no_local = core.format_statusline(today_spend=5.00, cap_usd=50.0)
    assert line_no_local == "today: cloud $5.00/$50.00"


def test_tally_daily_spend_and_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        conv_dir = os.path.join(tmpdir, "test-session-123", ".system_generated", "logs")
        os.makedirs(conv_dir, exist_ok=True)
        transcript_file = os.path.join(conv_dir, "transcript.jsonl")

        sample_records = [
            {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Hello world", "usage": {"input_tokens": 10000, "output_tokens": 0}},
            {"type": "PLANNER_RESPONSE", "source": "MODEL", "content": "Hi there! How can I help?", "usage": {"input_tokens": 0, "output_tokens": 5000}},
        ]
        with open(transcript_file, "w", encoding="utf-8") as f:
            for r in sample_records:
                f.write(json.dumps(r) + "\n")

        # Tally spend in this tmp brain dir
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).date().isoformat()
        tally = core.tally_daily_spend(brain_dir=tmpdir, target_date_utc=today_str)
        assert tally["session_count"] == 1
        assert tally["total_spend_usd"] > 0

        table = core.format_report_table(tally, cap_usd=40.0)
        assert "test-session-123" in table
        assert "Daily Cap: $40.00" in table


def test_learn_cap_from_transcripts():
    with tempfile.TemporaryDirectory() as tmpdir:
        conv_dir = os.path.join(tmpdir, "refused-session-456", ".system_generated", "logs")
        os.makedirs(conv_dir, exist_ok=True)
        transcript_file = os.path.join(conv_dir, "transcript.jsonl")

        refusal_record = {
            "type": "ERROR_MESSAGE",
            "source": "SYSTEM",
            "content": "Budget has been exceeded! Key=sk-v1-xyz Current cost: 40.12, Max budget: 40.0",
        }
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(refusal_record) + "\n")

        learned = core.learn_cap_from_transcripts(brain_dir=tmpdir)
        assert learned is not None
        assert learned["cap_usd"] == 40.0
        assert learned["conversation_id"] == "refused-session-456"

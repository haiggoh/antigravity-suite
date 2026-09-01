import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_resume_core as core


def test_analyze_transcript_limit_kill():
    with tempfile.TemporaryDirectory() as tmpdir:
        transcript_path = os.path.join(tmpdir, "transcript.jsonl")
        records = [
            {"type": "USER_INPUT", "content": "Refactor authentication system", "status": "DONE"},
            {"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "view_file"}], "content": "Analyzing files", "status": "DONE"},
            {"type": "PLANNER_RESPONSE", "content": "Error: RESOURCE_EXHAUSTED - Rate limit exceeded", "status": "ERROR"},
        ]
        with open(transcript_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analysis = core.analyze_transcript(transcript_path, "test-conv-123")
        assert analysis is not None
        assert analysis["conversation_id"] == "test-conv-123"
        assert analysis["reason"] == "limit_kill"
        assert "Refactor authentication system" in analysis["last_user_prompt"]
        assert "view_file" in analysis["recent_tools"]


def test_analyze_transcript_stalled_turn():
    with tempfile.TemporaryDirectory() as tmpdir:
        transcript_path = os.path.join(tmpdir, "transcript.jsonl")
        records = [
            {"type": "USER_INPUT", "content": "Deploy changes to production", "status": "DONE"},
        ]
        with open(transcript_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analysis = core.analyze_transcript(transcript_path, "test-conv-456")
        assert analysis is not None
        assert analysis["reason"] == "stalled_turn"
        assert "Deploy changes" in analysis["last_user_prompt"]


def test_find_interrupted_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_dir = os.path.join(tmpdir, "brain")
        conv_dir = os.path.join(brain_dir, "conv-abc", ".system_generated", "logs")
        os.makedirs(conv_dir, exist_ok=True)
        
        transcript_path = os.path.join(conv_dir, "transcript.jsonl")
        records = [
            {"type": "USER_INPUT", "content": "Run database migration", "status": "DONE"},
            {"type": "PLANNER_RESPONSE", "content": "API Error: Request rejected", "status": "ERROR"},
        ]
        with open(transcript_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        found = core.find_interrupted_sessions(brain_dir=brain_dir)
        assert len(found) == 1
        assert found[0]["conversation_id"] == "conv-abc"

        prompt_str = core.format_resumption_prompt(found[0])
        assert "[Resume Interrupted Session: `conv-abc`]" in prompt_str
        assert "Run database migration" in prompt_str

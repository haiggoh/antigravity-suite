"""Pure, unit-testable core for agy-resume-interrupted.

Detects when a previous Antigravity session was cut off mid-task due to:
  1. LIMIT KILL: Google quota / rate limit errors (RESOURCE_EXHAUSTED, 429).
  2. STALLED / CRASH: Last user prompt was not answered, or planner crashed.
  3. TOOL FAILURE: Trajectory ended in an unhandled tool exception.

Scans ~/.gemini/antigravity-cli/brain/<conversation-id>/.system_generated/logs/transcript.jsonl
and generates a structured resumption summary.

Design rules:
  * Pure standard library, fail-safe (missing/malformed files return empty structures).
  * Read-only, safe across platforms.
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


LIMIT_ERROR_KEYWORDS = (
    "resource_exhausted",
    "resourceexhausted",
    "quota exceeded",
    "rate limit",
    "429",
    "budget has been exceeded",
    "usage limit",
)


def get_home_dir() -> str:
    return os.environ.get("AGY_HOME_OVERRIDE") or os.path.expanduser("~")


def get_brain_dir() -> str:
    return os.environ.get("AGY_BRAIN_DIR") or os.path.join(
        get_home_dir(), ".gemini", "antigravity-cli", "brain"
    )


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """Fail-safe JSONL parser: returns list of parsed JSON objects."""
    records = []
    if not os.path.isfile(path):
        return records
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return records


def analyze_transcript(transcript_path: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Analyze a single conversation transcript for interruption patterns."""
    records = read_jsonl(transcript_path)
    if not records:
        return None

    last_user_prompt = ""
    last_step = records[-1]
    turn_count = 0
    tools_called = []
    has_error = False
    interruption_reason = None

    for rec in records:
        rec_type = rec.get("type", "")
        content = str(rec.get("content", "") or "")
        status = rec.get("status", "")

        if rec_type == "USER_INPUT":
            last_user_prompt = content
            turn_count += 1
        elif rec_type == "PLANNER_RESPONSE":
            tool_calls = rec.get("tool_calls", [])
            for tc in tool_calls:
                if isinstance(tc, dict) and "name" in tc:
                    tools_called.append(tc["name"])

        # Check for limit kills or explicit errors
        lower_content = content.lower()
        if status == "ERROR" or any(kw in lower_content for kw in LIMIT_ERROR_KEYWORDS):
            has_error = True
            if any(kw in lower_content for kw in LIMIT_ERROR_KEYWORDS):
                interruption_reason = "limit_kill"
            else:
                interruption_reason = "error_crash"

    # If the last step is a user input, the session stalled before responding
    if last_step.get("type") == "USER_INPUT":
        interruption_reason = "stalled_turn"
    elif last_step.get("status") == "ERROR" and not interruption_reason:
        interruption_reason = "error_crash"

    if not interruption_reason:
        return None

    try:
        mtime = os.path.getmtime(transcript_path)
        timestamp_str = datetime.fromtimestamp(mtime).isoformat()
    except Exception:
        timestamp_str = ""

    return {
        "conversation_id": conversation_id,
        "transcript_path": transcript_path,
        "reason": interruption_reason,
        "last_user_prompt": last_user_prompt.strip(),
        "turn_count": turn_count,
        "recent_tools": list(dict.fromkeys(tools_called[-5:])),  # last 5 unique tools
        "timestamp": timestamp_str,
    }


def find_interrupted_sessions(brain_dir: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Scan brain directory and return list of interrupted sessions sorted by recency."""
    target_dir = brain_dir or get_brain_dir()
    if not os.path.isdir(target_dir):
        return []

    candidates = []
    for conv_id in os.listdir(target_dir):
        conv_folder = os.path.join(target_dir, conv_id)
        if not os.path.isdir(conv_folder):
            continue

        transcript_path = os.path.join(
            conv_folder, ".system_generated", "logs", "transcript.jsonl"
        )
        if not os.path.isfile(transcript_path):
            continue

        analysis = analyze_transcript(transcript_path, conv_id)
        if analysis:
            candidates.append(analysis)

    # Sort by timestamp descending
    candidates.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return candidates[:limit]


def get_recommended_resume(brain_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get the single most recent interrupted session candidate."""
    sessions = find_interrupted_sessions(brain_dir=brain_dir, limit=1)
    return sessions[0] if sessions else None


def format_resumption_prompt(session_info: Dict[str, Any]) -> str:
    """Format an actionable resumption prompt for the agent or user."""
    cid = session_info.get("conversation_id", "")
    reason = session_info.get("reason", "interrupted")
    prompt = session_info.get("last_user_prompt", "(No prompt text recorded)")
    tools = session_info.get("recent_tools", [])

    lines = [
        f"[Resume Interrupted Session: `{cid}`]",
        f"- Interruption Type: `{reason}`",
        f"- Last Goal/Prompt: {prompt}",
    ]
    if tools:
        lines.append(f"- Recent Tools Used: {', '.join(tools)}")
    lines.append("- Action: Resume task execution from where the previous session stopped.")
    return "\n".join(lines)

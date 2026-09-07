"""Pure, unit-testable core for agy-transcript-distiller (v0.8.0).

Turns Antigravity JSONL session trajectories into clean, line-addressable,
human-readable Markdown capsules with tool execution summaries, step indexes,
and multi-session chronology.

Guarantees:
  * Pure standard library (json, os, re, datetime, typing).
  * Fail-safe: handles truncated records and malformed JSONL gracefully.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple


def get_home_dir() -> str:
    return os.environ.get("AGY_HOME_OVERRIDE") or os.path.expanduser("~")


def get_brain_dir() -> str:
    return os.environ.get("AGY_BRAIN_DIR") or os.path.join(
        get_home_dir(), ".gemini", "antigravity-cli", "brain"
    )


def read_jsonl(path: str) -> List[Dict[str, Any]]:
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


def format_tool_call_summary(tool_call: Any) -> str:
    """Format a single tool call into a compact markdown representation."""
    if not isinstance(tool_call, dict):
        return f"`{tool_call}`"

    name = tool_call.get("name") or "tool"
    args = tool_call.get("args") or {}
    
    # Extract high-signal arguments
    summary_parts = []
    if isinstance(args, dict):
        for k in ("CommandLine", "TargetFile", "AbsolutePath", "SearchPath", "Query", "Url", "Prompt"):
            if k in args and args[k]:
                val = str(args[k]).replace("\n", " ").strip()
                if len(val) > 80:
                    val = val[:79] + "…"
                summary_parts.append(f"{k}=`{val}`")
                break
    
    args_str = f" ({', '.join(summary_parts)})" if summary_parts else ""
    return f"- ⚙️ **`{name}`**{args_str}"


def distill_step(step: Dict[str, Any], include_thinking: bool = False) -> str:
    """Format a single transcript record into a markdown section."""
    step_idx = step.get("step_index", "?")
    source = step.get("source", "")
    step_type = step.get("type", "")
    created_at = step.get("created_at") or ""
    content = str(step.get("content") or "").strip()
    thinking = str(step.get("thinking") or "").strip()
    tool_calls = step.get("tool_calls") or []

    ts_str = f" `{created_at}`" if created_at else ""
    lines = []

    if step_type == "USER_INPUT" or source == "USER_EXPLICIT":
        lines.append(f"### 👤 User (Turn {step_idx}){ts_str}\n")
        lines.append(content if content else "*(Empty prompt)*")

    elif step_type == "PLANNER_RESPONSE" or source == "MODEL":
        lines.append(f"### 🤖 Agent (Turn {step_idx}){ts_str}\n")
        
        if include_thinking and thinking:
            lines.append(f"> 💭 **Thinking:** {thinking}\n")

        if content:
            lines.append(content)

        if tool_calls:
            lines.append("\n**Tools Executed:**")
            for tc in tool_calls:
                lines.append(format_tool_call_summary(tc))

    elif step_type in ("ERROR_MESSAGE", "SYSTEM") or step.get("status") == "ERROR":
        lines.append(f"### ⚠️ System Event (Turn {step_idx}){ts_str}\n")
        lines.append(f"```text\n{content}\n```")

    elif content:
        lines.append(f"### 📋 Event (Turn {step_idx}){ts_str}\n")
        lines.append(content)

    return "\n".join(lines)


def distill_transcript(
    transcript_path: str,
    conversation_id: str = "",
    include_thinking: bool = False,
) -> str:
    """Distill a single transcript JSONL file into a structured markdown capsule."""
    records = read_jsonl(transcript_path)
    if not records:
        return f"# Antigravity Session Capsule: `{conversation_id or 'unknown'}`\n\n*(No records found)*\n"

    cid = conversation_id or os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(transcript_path))))
    start_time = records[0].get("created_at") or "unknown"
    end_time = records[-1].get("created_at") or "unknown"
    
    # Calculate stats
    user_turns = sum(1 for r in records if r.get("type") == "USER_INPUT" or r.get("source") == "USER_EXPLICIT")
    tool_invocations = sum(len(r.get("tool_calls", [])) for r in records)

    header = [
        f"# 📜 Antigravity Session Capsule: `{cid}`",
        "",
        f"- **Start Time:** {start_time}",
        f"- **End Time:** {end_time}",
        f"- **Total Events:** {len(records)} ({user_turns} user turns, {tool_invocations} tool calls)",
        "",
        "---",
        "",
    ]

    body = []
    for r in records:
        step_md = distill_step(r, include_thinking=include_thinking)
        if step_md.strip():
            body.append(step_md)

    return "\n".join(header) + "\n\n---\n\n".join(body) + "\n"


def find_available_sessions(brain_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available session transcripts in the brain directory."""
    target_dir = brain_dir or get_brain_dir()
    if not os.path.isdir(target_dir):
        return []

    sessions = []
    for cid in os.listdir(target_dir):
        conv_folder = os.path.join(target_dir, cid)
        if not os.path.isdir(conv_folder):
            continue
        transcript_path = os.path.join(conv_folder, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.isfile(transcript_path):
            continue

        try:
            mtime = os.path.getmtime(transcript_path)
            iso_time = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            size = os.path.getsize(transcript_path)
        except Exception:
            iso_time = ""
            size = 0

        sessions.append({
            "conversation_id": cid,
            "transcript_path": transcript_path,
            "timestamp": iso_time,
            "size_bytes": size,
        })

    sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return sessions


def bundle_sessions(session_ids: List[str], brain_dir: Optional[str] = None) -> str:
    """Bundle multiple session transcripts chronologically into a master capsule."""
    target_dir = brain_dir or get_brain_dir()
    capsules = []
    
    for cid in session_ids:
        transcript_path = os.path.join(target_dir, cid, ".system_generated", "logs", "transcript.jsonl")
        if os.path.isfile(transcript_path):
            cap = distill_transcript(transcript_path, conversation_id=cid)
            capsules.append(cap)

    if not capsules:
        return "# Antigravity Multi-Session Bundle\n\n*(No valid sessions found)*\n"

    header = [
        "# 📚 Antigravity Multi-Session Work Bundle",
        f"- Sessions Included: {len(capsules)}",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "=" * 72,
        "",
    ]
    return "\n".join(header) + "\n\n" + ("\n\n" + "=" * 72 + "\n\n").join(capsules)

"""Pure, unit-testable core for agy-cost-tracker.

Provides daily token spend telemetry, gateway budget cap learning and calibration,
and per-session cost reporting for Antigravity.

Guarantees:
  * Pure standard library (json, os, re, datetime, typing).
  * Fail-safe: malformed transcripts or missing ledgers return safe empty structures.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import re
import json
from datetime import datetime, timezone, timedelta, date
from typing import List, Dict, Any, Optional, Tuple

# Default rate table ($ per token)
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    # Gemini 3.7 / 2.5 series
    "gemini-3.7-flash": {
        "input": 0.15e-6,
        "output": 0.60e-6,
        "cache_read_mult": 0.25,
    },
    "gemini-3.7-pro": {
        "input": 1.25e-6,
        "output": 5.00e-6,
        "cache_read_mult": 0.25,
    },
    "gemini-2.5-flash": {
        "input": 0.15e-6,
        "output": 0.60e-6,
        "cache_read_mult": 0.25,
    },
    "gemini-2.5-pro": {
        "input": 1.25e-6,
        "output": 5.00e-6,
        "cache_read_mult": 0.25,
    },
    # Claude Sonnet series
    "claude-sonnet-5": {
        "input": 3.00e-6,
        "output": 15.00e-6,
        "cache_read_mult": 0.1,
    },
    "claude-sonnet-4-6": {
        "input": 3.00e-6,
        "output": 15.00e-6,
        "cache_read_mult": 0.1,
    },
    "claude-opus-4": {
        "input": 15.00e-6,
        "output": 75.00e-6,
        "cache_read_mult": 0.1,
    },
}

DEFAULT_CAP_USD = 40.0
DEFAULT_WARN_PCT = 0.75

REFUSAL_CAP_REGEX = re.compile(
    r"(?:Budget has been exceeded!.*?Max budget:\s*([0-9]+(?:\.[0-9]+)?)|"
    r"daily budget limit of \$?([0-9]+(?:\.[0-9]+)?)|"
    r"quota cap of \$?([0-9]+(?:\.[0-9]+)?))",
    re.IGNORECASE,
)


def get_home_dir() -> str:
    return os.environ.get("AGY_HOME_OVERRIDE") or os.path.expanduser("~")


def get_brain_dir() -> str:
    return os.environ.get("AGY_BRAIN_DIR") or os.path.join(
        get_home_dir(), ".gemini", "antigravity-cli", "brain"
    )


def get_cost_ledger_dir() -> str:
    return os.environ.get("AGY_COST_LEDGER_DIR") or os.path.join(
        get_home_dir(), ".gemini", "cost-ledger"
    )


def get_configured_cap() -> float:
    env_cap = (
        os.environ.get("AGY_BUDGET_CAP_USD")
        or os.environ.get("COST_TRACKER_CAP_USD")
        or os.environ.get("BUDGET_TALLY_CAP_USD")
    )
    if env_cap:
        try:
            return float(env_cap)
        except ValueError:
            pass
    return DEFAULT_CAP_USD


def price_tokens(model_name: str, input_tokens: int, output_tokens: int, cache_read_tokens: int = 0) -> float:
    """Calculate USD spend for given token volumes against model pricing."""
    norm = model_name.lower().strip()
    matched_key = None
    for k in DEFAULT_PRICING:
        if k in norm:
            matched_key = k
            break
    if not matched_key:
        matched_key = "gemini-3.7-flash"

    rate = DEFAULT_PRICING[matched_key]
    cost = input_tokens * rate["input"] + output_tokens * rate["output"]
    if cache_read_tokens > 0:
        cost += cache_read_tokens * rate["input"] * rate.get("cache_read_mult", 0.25)
    return round(cost, 6)


def read_jsonl_records(path: str) -> List[Dict[str, Any]]:
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


def parse_session_cost_from_transcript(transcript_path: str) -> Dict[str, Any]:
    """Parse session transcript and compute token usage and estimated cloud spend."""
    records = read_jsonl_records(transcript_path)
    total_in = 0
    total_out = 0
    total_cache_read = 0
    model_detected = "gemini-3.7-flash"
    last_timestamp = ""

    for rec in records:
        ts = rec.get("created_at") or rec.get("timestamp") or ""
        if ts:
            last_timestamp = ts
        
        # Check token usage fields if present
        usage = rec.get("usage") or rec.get("token_usage") or {}
        if isinstance(usage, dict):
            total_in += usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            total_out += usage.get("completion_tokens") or usage.get("output_tokens") or 0
            total_cache_read += usage.get("cache_read_input_tokens") or 0

        # Fallback estimation if explicit token numbers are missing
        content = rec.get("content") or ""
        if not usage and content:
            char_count = len(str(content))
            approx_tokens = max(1, char_count // 4)
            if rec.get("source") == "USER_EXPLICIT" or rec.get("type") == "USER_INPUT":
                total_in += approx_tokens
            else:
                total_out += approx_tokens

    cost = price_tokens(model_detected, total_in, total_out, total_cache_read)
    return {
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cache_read_tokens": total_cache_read,
        "model": model_detected,
        "cost_usd": cost,
        "last_timestamp": last_timestamp,
    }


def tally_daily_spend(
    brain_dir: Optional[str] = None,
    target_date_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Tally cloud API spend across all sessions for a specific UTC date."""
    target_dir = brain_dir or get_brain_dir()
    date_str = target_date_utc or datetime.now(timezone.utc).date().isoformat()
    sessions = []
    total_spend = 0.0

    if not os.path.isdir(target_dir):
        return {
            "date": date_str,
            "total_spend_usd": 0.0,
            "session_count": 0,
            "sessions": [],
        }

    for conv_id in os.listdir(target_dir):
        conv_folder = os.path.join(target_dir, conv_id)
        if not os.path.isdir(conv_folder):
            continue

        transcript_path = os.path.join(
            conv_folder, ".system_generated", "logs", "transcript.jsonl"
        )
        if not os.path.isfile(transcript_path):
            continue

        try:
            mtime = os.path.getmtime(transcript_path)
            file_date = datetime.fromtimestamp(mtime, tz=timezone.utc).date().isoformat()
        except Exception:
            file_date = ""

        if file_date == date_str:
            data = parse_session_cost_from_transcript(transcript_path)
            data["conversation_id"] = conv_id
            sessions.append(data)
            total_spend += data["cost_usd"]

    return {
        "date": date_str,
        "total_spend_usd": round(total_spend, 6),
        "session_count": len(sessions),
        "sessions": sessions,
    }


def learn_cap_from_transcripts(brain_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Scan transcripts for gateway budget refusal messages to learn the current cap."""
    target_dir = brain_dir or get_brain_dir()
    if not os.path.isdir(target_dir):
        return None

    newest_match = None
    newest_mtime = 0.0

    for conv_id in os.listdir(target_dir):
        conv_folder = os.path.join(target_dir, conv_id)
        if not os.path.isdir(conv_folder):
            continue

        transcript_path = os.path.join(
            conv_folder, ".system_generated", "logs", "transcript.jsonl"
        )
        if not os.path.isfile(transcript_path):
            continue

        records = read_jsonl_records(transcript_path)
        for rec in records:
            content = str(rec.get("content") or "")
            m = REFUSAL_CAP_REGEX.search(content)
            if m:
                cap_val = float(m.group(1) or m.group(2) or m.group(3))
                try:
                    mtime = os.path.getmtime(transcript_path)
                except Exception:
                    mtime = 0.0
                if mtime >= newest_mtime:
                    newest_mtime = mtime
                    newest_match = {
                        "cap_usd": cap_val,
                        "conversation_id": conv_id,
                        "provenance_turn": content[:120],
                        "timestamp": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat() if mtime else "",
                    }

    return newest_match


def format_statusline(
    today_spend: float,
    cap_usd: float = DEFAULT_CAP_USD,
    local_saved: Optional[float] = None,
) -> str:
    """Format single-line statusline ticker output."""
    parts = [f"today: cloud ${today_spend:.2f}/${cap_usd:.2f}"]
    if local_saved is not None:
        parts.append(f"local saved ${local_saved:.2f}")
    return " · ".join(parts)


def format_report_table(daily_data: Dict[str, Any], cap_usd: float = DEFAULT_CAP_USD) -> str:
    """Format structured report table."""
    date_str = daily_data.get("date", "")
    total = daily_data.get("total_spend_usd", 0.0)
    sessions = daily_data.get("sessions", [])

    lines = [
        f"=== Antigravity Spend Report ({date_str}) ===",
        f"Daily Cap: ${cap_usd:.2f} | Total Spend: ${total:.4f} ({len(sessions)} session(s))",
        "-" * 72,
        f"{'Session ID':<38} {'Model':<18} {'Cost (USD)':<12}",
        "-" * 72,
    ]
    for s in sessions:
        cid = s.get("conversation_id", "")[:36]
        mod = s.get("model", "")[:16]
        cost = f"${s.get('cost_usd', 0.0):.4f}"
        lines.append(f"{cid:<38} {mod:<18} {cost:<12}")

    lines.append("-" * 72)
    return "\n".join(lines)

"""Pure, unit-testable core for run-to-completion and autonomous task execution.

Provides:
  1. Queue Triaging: Scores tasks into Tier 1 (Do Now), Tier 2 (Heavy), and Gated.
  2. Gate Classification: Classifies blocker markers (G1, G2, G3, G4, ENV, WAIT, EXT)
     and calculates cheapness ranking for attended release.
  3. Close-out Generator: Formats clean close-out ledger with gated blocker menu.

Design rules:
  * Pure standard library, fail-safe.
  * Preserves original task IDs / text.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import re
from typing import List, Dict, Any, Tuple, Optional


# Gate Tier definitions ordered by cheapness of resolution
GATE_TIERS = {
    "G1": {"rank": 1, "label": "One decision / value away", "type": "attended_quick"},
    "G2": {"rank": 2, "label": "Bundled setup script needed", "type": "attended_script"},
    "G3": {"rank": 3, "label": "Custom installation / setup", "type": "attended_heavy"},
    "G4": {"rank": 4, "label": "Requires interactive human GUI driver", "type": "human_interactive"},
    "ENV": {"rank": 5, "label": "External environment precondition", "type": "precondition"},
    "WAIT": {"rank": 6, "label": "Waiting on another queue item", "type": "self_releasing"},
    "EXT": {"rank": 7, "label": "Waiting on external party/upstream", "type": "external_wait"},
}


def parse_gate_reason(reason_text: str) -> Dict[str, Any]:
    """Parse gate reason string to extract tier marker, explanation, and cheapness."""
    text = (reason_text or "").strip()
    m = re.match(r"^(G[1-4]|ENV|WAIT|EXT)\s*:\s*(.*)$", text, re.IGNORECASE)
    if m:
        tier_code = m.group(1).upper()
        detail = m.group(2).strip()
        tier_info = GATE_TIERS.get(tier_code, {"rank": 10, "label": "Unknown", "type": "unknown"})
        return {
            "tier": tier_code,
            "rank": tier_info["rank"],
            "label": tier_info["label"],
            "type": tier_info["type"],
            "detail": detail,
            "raw": text,
        }
    
    # Heuristic inference if no explicit marker is present
    lower = text.lower()
    if "decision" in lower or "choice" in lower or "pick" in lower or "confirm" in lower:
        tier_code = "G1"
    elif "script" in lower or "command" in lower or "setup" in lower:
        tier_code = "G2"
    elif "gui" in lower or "interactive" in lower or "browser" in lower:
        tier_code = "G4"
    elif "wait" in lower or "depends on" in lower:
        tier_code = "WAIT"
    elif "pr" in lower or "upstream" in lower:
        tier_code = "EXT"
    else:
        tier_code = "G1"  # Default to G1 for unclassified blocked items

    tier_info = GATE_TIERS.get(tier_code, {"rank": 10, "label": "Unclassified", "type": "unknown"})
    return {
        "tier": tier_code,
        "rank": tier_info["rank"],
        "label": tier_info["label"],
        "type": tier_info["type"],
        "detail": text,
        "raw": f"{tier_code}: {text}" if text else "G1: unspecified blocker",
    }


def parse_markdown_task_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single markdown checkbox task line into structured task object."""
    # Match: - [ ] Task description <!-- blocked: G1: reason --> or (G1: reason)
    m = re.match(r"^\s*-\s*\[([ xX])\]\s+(.*?)$", line)
    if not m:
        return None

    is_checked = m.group(1).lower() == "x"
    body = m.group(2).strip()

    # Check for gate reason comments or tags
    gate_reason = ""
    gate_match = re.search(r"(?:<!--\s*blocked:\s*(.*?)\s*-->|\((?:blocked|gate):\s*(.*?)\))", body, re.IGNORECASE)
    if gate_match:
        gate_reason = (gate_match.group(1) or gate_match.group(2) or "").strip()
        body = re.sub(r"(?:<!--\s*blocked:\s*.*?\s*-->|\((?:blocked|gate):\s*.*?\))", "", body).strip()
    elif "blocked:" in body.lower():
        parts = re.split(r"blocked:\s*", body, flags=re.IGNORECASE)
        body = parts[0].strip()
        gate_reason = parts[1].strip()

    is_heavy = bool(re.search(r"\b(heavy|complex|large|migration|refactor)\b", body, re.IGNORECASE))

    return {
        "completed": is_checked,
        "title": body,
        "is_heavy": is_heavy,
        "gate_reason": gate_reason,
        "raw_line": line,
    }


def triage_task_list(task_lines: List[str]) -> Dict[str, Any]:
    """Triage a list of markdown task lines into autonomous tiers and sorted gated items."""
    tier1_do_now = []
    tier2_heavy = []
    gated_items = []
    completed_items = []

    for line in task_lines:
        task = parse_markdown_task_line(line)
        if not task:
            continue

        if task["completed"]:
            completed_items.append(task)
            continue

        if task["gate_reason"]:
            gate_info = parse_gate_reason(task["gate_reason"])
            task["gate_info"] = gate_info
            gated_items.append(task)
        elif task["is_heavy"]:
            tier2_heavy.append(task)
        else:
            tier1_do_now.append(task)

    # Sort gated items by cheapness rank ascending
    gated_items.sort(key=lambda t: t["gate_info"]["rank"])

    return {
        "tier1_do_now": tier1_do_now,
        "tier2_heavy": tier2_heavy,
        "gated": gated_items,
        "completed": completed_items,
    }


def format_triage_summary(triage_result: Dict[str, Any]) -> str:
    """Format human-readable triage ledger."""
    lines = ["# Autonomous Execution Queue Triage", ""]
    t1 = triage_result["tier1_do_now"]
    t2 = triage_result["tier2_heavy"]
    gated = triage_result["gated"]
    done = triage_result["completed"]

    lines.append(f"- **Tier 1 (Do Now - Autonomous)**: {len(t1)}")
    lines.append(f"- **Tier 2 (Heavy - Autonomous)**: {len(t2)}")
    lines.append(f"- **Gated (Blocked / Needs Input)**: {len(gated)}")
    lines.append(f"- **Already Completed**: {len(done)}")
    lines.append("")

    if t1:
        lines.append("## 🟢 Tier 1: Do Now (Immediate Autonomous Execution)")
        for item in t1:
            lines.append(f"- [ ] {item['title']}")
        lines.append("")

    if t2:
        lines.append("## 🟡 Tier 2: Heavy Autonomous Tasks")
        for item in t2:
            lines.append(f"- [ ] {item['title']}")
        lines.append("")

    if gated:
        lines.append("## 🔴 Gated Tasks (Sorted by Resolution Cheapness)")
        for item in gated:
            gi = item["gate_info"]
            lines.append(f"- `[{gi['tier']}]` {item['title']} — *Reason:* {gi['detail']}")
        lines.append("")

    return "\n".join(lines)


def format_ungate_questions(gated_items: List[Dict[str, Any]]) -> str:
    """Format the list of single clarifying questions to release blocked items."""
    lines = ["# Attended Ungating Pass: Clarification Questions", ""]
    if not gated_items:
        lines.append("✅ No gated tasks pending. The entire queue is actionable!")
        return "\n".join(lines)

    lines.append("> Answer each question below to release the corresponding gate into the autonomous queue:\n")
    for idx, item in enumerate(gated_items, 1):
        gi = item["gate_info"]
        lines.append(f"### {idx}. [{gi['tier']}] {item['title']}")
        lines.append(f"- **Blocker:** {gi['detail']}")
        if gi["tier"] == "G1":
            lines.append(f"- **Question:** What is your decision or preferred value for `{item['title']}`?")
        elif gi["tier"] == "G2":
            lines.append(f"- **Question:** Should we execute the setup command/script for `{item['title']}` now?")
        elif gi["tier"] == "G4":
            lines.append(f"- **Status:** Requires live human interaction in UI/browser.")
        elif gi["tier"] == "WAIT":
            lines.append(f"- **Status:** Self-releasing upon prerequisite task completion.")
        elif gi["tier"] == "ENV":
            lines.append(f"- **Question:** Is the external precondition currently met?")
        else:
            lines.append(f"- **Question:** How would you like to proceed with `{item['title']}`?")
        lines.append("")

    return "\n".join(lines)


def format_closeout_report(
    completed_items: List[str],
    gated_items: List[Dict[str, Any]],
    consumed_summary: str = "",
) -> str:
    """Format clean end-of-run close-out ledger with remaining gated work."""
    lines = ["# Autonomous Run Close-Out & State Reconciliation", ""]

    if completed_items:
        lines.append("## ✅ Completed & Shipped Work")
        for item in completed_items:
            lines.append(f"- {item}")
        lines.append("")

    if consumed_summary:
        lines.append(f"**Resource Accounting:** {consumed_summary}\n")

    if gated_items:
        lines.append("## ⏸️ Remaining Gated Work (Menu for Next Session)")
        for item in gated_items:
            gi = item.get("gate_info", parse_gate_reason(item.get("gate_reason", "")))
            lines.append(f"- **[{gi['tier']}]** {item['title']}")
            lines.append(f"  - *Reason:* {gi['detail']}")
            lines.append(f"  - *Next Action:* Resolve `{gi['tier']}` gate to resume.")
        lines.append("")
    else:
        lines.append("🎉 **All open queue items completed successfully!**\n")

    lines.append("---")
    lines.append("*Durable records reconciled. Working tree clean.*")
    return "\n".join(lines)

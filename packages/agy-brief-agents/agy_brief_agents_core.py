"""Pure, unit-testable core for agy-brief-agents.

Scans the durable rule layers and available custom skills an Antigravity orchestrator
session sees — but a freshly-spawned subagent does NOT — and compiles them into a
compact "agent briefing index" (~/.gemini/agent-briefing-index.md).

The orchestrator can reference or inject this briefing index into subagents
(via invoke_subagent or define_subagent) so delegated tasks adhere to project
conventions, global rules, and active workflows instead of violating them blindly.

Design rules:
  * Pure standard library, fail-safe (missing/malformed files return empty structures).
  * Fast SHA-256 fingerprint caching: skips rebuilding if rule sources haven't changed.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import re
import json
import hashlib
from typing import List, Tuple, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Path resolution (overridable via environment variables for tests)
# ---------------------------------------------------------------------------

def get_home_dir() -> str:
    return os.environ.get("AGY_HOME_OVERRIDE") or os.path.expanduser("~")


def global_rules_dir() -> str:
    return os.environ.get("AGY_GLOBAL_RULES_DIR") or os.path.join(
        get_home_dir(), ".gemini", "config", "rules"
    )


def index_output_path() -> str:
    return os.environ.get("AGY_BRIEFING_INDEX_FILE") or os.path.join(
        get_home_dir(), ".gemini", "agent-briefing-index.md"
    )


def fingerprint_path() -> str:
    return os.environ.get("AGY_FINGERPRINT_FILE") or os.path.join(
        get_home_dir(), ".gemini", ".agy-brief-agents-fingerprint"
    )


# ---------------------------------------------------------------------------
# Fail-safe utilities
# ---------------------------------------------------------------------------

def read_text(path: str) -> str:
    """Fail-safe text read: missing/unreadable -> ''."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _collapse(text: str, limit: int = 140) -> str:
    """Collapse whitespace to single spaces and truncate."""
    s = re.sub(r"\s+", " ", text or "").strip()
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s


# ---------------------------------------------------------------------------
# Markdown section extraction
# ---------------------------------------------------------------------------

def _gist_after_header(lines: List[str], header_idx: int) -> str:
    """Extract the first meaningful non-blank, non-header prose line after a header."""
    for j in range(header_idx + 1, len(lines)):
        ln = lines[j].strip()
        if not ln:
            continue
        if ln.startswith("#"):
            break
        # Strip bullet points, quotes, and markdown formatting
        ln = re.sub(r"^[>*\-]\s*", "", ln)
        return _collapse(ln, 120)
    return ""


def scan_markdown_sections(text: str) -> List[Tuple[str, str]]:
    """Extract (header, one-line-gist) pairs from markdown text."""
    if not text:
        return []
    lines = text.splitlines()
    sections = []
    for i, raw in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*\S)\s*$", raw)
        if not m:
            continue
        header = _collapse(m.group(2), 90)
        gist = _gist_after_header(lines, i)
        sections.append((header, gist))
    return sections


# ---------------------------------------------------------------------------
# Source Scanners
# ---------------------------------------------------------------------------

def scan_global_rules(rules_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scan all markdown files in the global rules directory."""
    target_dir = rules_dir or global_rules_dir()
    results = []
    if not os.path.isdir(target_dir):
        return results

    for filename in sorted(os.listdir(target_dir)):
        if filename.endswith(".md"):
            filepath = os.path.join(target_dir, filename)
            content = read_text(filepath)
            sections = scan_markdown_sections(content)
            results.append({
                "source": "global_rule",
                "name": filename,
                "path": filepath,
                "sections": sections,
            })
    return results


def find_workspace_guidelines(cwd: str) -> List[Dict[str, Any]]:
    """Find GEMINI.md or AGENTS.md in current directory or parent directory."""
    results = []
    curr = os.path.abspath(cwd)
    checked = set()

    for _ in range(3):  # Check cwd and up to 2 parent directories
        if curr in checked:
            break
        checked.add(curr)
        for name in ["GEMINI.md", "AGENTS.md", "CLAUDE.md"]:
            target = os.path.join(curr, name)
            if os.path.isfile(target):
                content = read_text(target)
                sections = scan_markdown_sections(content)
                rel_path = os.path.relpath(target, cwd)
                results.append({
                    "source": "workspace_guidelines",
                    "name": name,
                    "path": target,
                    "relative_path": rel_path,
                    "sections": sections,
                })
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    return results


def scan_skills(skills_dirs: List[str]) -> List[Dict[str, Any]]:
    """Scan custom skills directories for SKILL.md definitions."""
    results = []
    for sdir in skills_dirs:
        if not os.path.isdir(sdir):
            continue
        for item in sorted(os.listdir(sdir)):
            skill_folder = os.path.join(sdir, item)
            skill_md = os.path.join(skill_folder, "SKILL.md")
            if os.path.isfile(skill_md):
                content = read_text(skill_md)
                # Parse frontmatter or top header
                desc_match = re.search(r"description:\s*(.*?)(?=\n---|\n[a-z_]+:|$)", content, re.DOTALL)
                desc = _collapse(desc_match.group(1), 120) if desc_match else ""
                results.append({
                    "source": "skill",
                    "name": item,
                    "path": skill_md,
                    "description": desc,
                })
    return results


# ---------------------------------------------------------------------------
# Fingerprint & Compilation
# ---------------------------------------------------------------------------

def compute_sources_fingerprint(
    global_rules: List[Dict[str, Any]],
    workspace_rules: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
) -> str:
    """Compute deterministic SHA-256 fingerprint over all input sources."""
    hasher = hashlib.sha256()
    for item in global_rules + workspace_rules + skills:
        hasher.update(item.get("path", "").encode("utf-8"))
        try:
            mtime = str(os.path.getmtime(item["path"]))
            hasher.update(mtime.encode("utf-8"))
        except Exception:
            pass
    return hasher.hexdigest()


def compile_briefing_index(
    global_rules: List[Dict[str, Any]],
    workspace_rules: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    cwd: str,
) -> str:
    """Render compact markdown briefing index."""
    lines = [
        "# Antigravity Agent Briefing Index",
        "> Auto-generated compact briefing index for delegated subagents.",
        f"> Workspace: `{cwd}`",
        "",
        "## 1. Global & Environment Rules",
    ]

    if not global_rules:
        lines.append("- *(No global rules configured)*")
    else:
        for gr in global_rules:
            lines.append(f"- **{gr['name']}** (`{gr['path']}`)")
            for header, gist in gr.get("sections", []):
                gist_part = f": {gist}" if gist else ""
                lines.append(f"  - `{header}`{gist_part}")

    lines.append("")
    lines.append("## 2. Workspace Guidelines")
    if not workspace_rules:
        lines.append("- *(No workspace GEMINI.md found)*")
    else:
        for wr in workspace_rules:
            lines.append(f"- **{wr['name']}** (`{wr['path']}`)")
            for header, gist in wr.get("sections", []):
                gist_part = f": {gist}" if gist else ""
                lines.append(f"  - `{header}`{gist_part}")

    lines.append("")
    lines.append("## 3. Active Custom Skills")
    if not skills:
        lines.append("- *(No custom skills detected)*")
    else:
        for sk in skills:
            desc_part = f" — {sk['description']}" if sk['description'] else ""
            lines.append(f"- `{sk['name']}`{desc_part}")

    lines.append("")
    lines.append("---")
    lines.append("*Subagent Directive: Review applicable rules above before performing file or environment operations.*")
    lines.append("")
    return "\n".join(lines)


def build_and_save_index(cwd: str, force: bool = False) -> Tuple[str, bool]:
    """Compile and write index if fingerprint changed or force is True."""
    g_rules = scan_global_rules()
    w_rules = find_workspace_guidelines(cwd)

    # Search common skill directories
    home = get_home_dir()
    skill_dirs = [
        os.path.join(home, ".gemini", "antigravity-cli", "skills"),
        os.path.join(home, ".gemini", "config", "skills"),
        os.path.join(cwd, "skills"),
    ]
    skills = scan_skills(skill_dirs)

    new_fp = compute_sources_fingerprint(g_rules, w_rules, skills)
    fp_file = fingerprint_path()
    old_fp = read_text(fp_file).strip()

    out_path = index_output_path()
    if not force and old_fp == new_fp and os.path.isfile(out_path):
        return out_path, False

    content = compile_briefing_index(g_rules, w_rules, skills, cwd)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    os.makedirs(os.path.dirname(fp_file), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(fp_file, "w", encoding="utf-8") as f:
        f.write(new_fp)

    return out_path, True


def format_subagent_prompt(task_prompt: str, cwd: str) -> str:
    """Wrap a user task prompt with the condensed subagent briefing directive."""
    index_file, _ = build_and_save_index(cwd)
    briefing_directive = (
        f"[Context Briefing: Refer to '{index_file}' for workspace guidelines & global rules.]\n\n"
    )
    return briefing_directive + task_prompt

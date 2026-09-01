# agy-brief-agents

**Subagent Context Briefing Compiler & Rule Injector for Google Antigravity (AGY)**

## Problem
Delegated subagents (`invoke_subagent`) run in isolated conversation contexts and do not automatically inherit your global rules, workspace `GEMINI.md`, or active skill constraints. Without briefing, a subagent can violate project coding guidelines, create messy edits, or miss essential repository rules.

## Solution
`agy-brief-agents` scans your global rules (`~/.gemini/config/rules/`), workspace guidelines (`GEMINI.md`), and active custom skills into a compact, single-line-gist index (`~/.gemini/agent-briefing-index.md`) and provides seamless prompt injection wrappers.

## Features
- **Deterministic Fingerprinting**: Rebuilds only when source files change.
- **Fail-Safe & Cross-Platform**: Standard library only, runs cleanly on macOS, Linux, and Windows.
- **CLI & Skill**: Includes `bin/agy_brief_agents.py` and `skills/brief-agents`.

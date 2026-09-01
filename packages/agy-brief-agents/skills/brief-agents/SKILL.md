---
name: brief-agents
description: Pre-brief delegated subagents with workspace guidelines, global rules, and active suite skills before launching invoke_subagent or define_subagent.
---

# brief-agents Skill

## Purpose
Spawned subagents do not inherit your dynamic conversation memory, full prompt history, or active workspace rules automatically.
Use this skill whenever delegating complex architectural, refactoring, or file modifications to subagents (`invoke_subagent` or `define_subagent`) to ensure they adhere to project guidelines and never violate workspace rules blindly.

## Workflow

1. **Verify or Rebuild Briefing Index**:
   ```bash
   python3 packages/agy-brief-agents/bin/agy_brief_agents.py build
   ```
2. **Review Key Constraints**:
   Point the subagent to `~/.gemini/agent-briefing-index.md` or prepend the briefing directive:
   ```text
   [Context Briefing: Refer to ~/.gemini/agent-briefing-index.md for workspace guidelines & global rules.]
   ```
3. **Dispatch Subagent**:
   Include the directive at the start of the subagent's prompt in `invoke_subagent`.

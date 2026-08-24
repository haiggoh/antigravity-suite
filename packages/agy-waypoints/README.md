# agy-waypoints 🧭

An **Antigravity Plugin** that surfaces open tasks, follow-ups, and to-dos as a persistent startup banner — staying visible across sessions until each item is explicitly marked done.

---

## Features

- **PreInvocation Hook**: Formats and injects active waypoints into your Antigravity context window at the start of a turn/session.
- **Progressive Skill**: Teaches the agent how to add, complete, list, and manage waypoints during natural conversation.
- **Fail-Safe Backend**: Uses `~/.gemini/waypoints.json` (or `$WAYPOINTS_FILE`) with atomic JSON writes and zero-latency fallbacks.

---

## Directory Structure

```text
agy-waypoints/
├── plugin.json               # Antigravity Plugin manifest
├── hooks.json                # PreInvocation hook definition
├── waypoints_core.py         # Pure Python task store engine
├── bin/
│   └── waypoints.py          # Command-line utility for manual/scripted task management
├── hooks/
│   └── agy_waypoints_hook.py # Antigravity lifecycle hook runner
├── skills/
│   └── waypoints/
│       └── SKILL.md          # Antigravity model skill instructions
└── tests/
    └── test_waypoints.py     # Unit test suite
```

---

## Installation & Usage

### Installing in Antigravity

Add to your `~/.gemini/config/plugins.json`:

```json
{
  "entries": [
    { "path": "D:/antigravity/projects/agy-waypoints" }
  ]
}
```

### CLI Usage

```sh
python bin/waypoints.py list
python bin/waypoints.py add "Refactor auth middleware" --point "check OAuth tokens"
python bin/waypoints.py show refactor-auth-middleware
python bin/waypoints.py done refactor-auth-middleware --as "OAuth tokens verified and refactored"
```

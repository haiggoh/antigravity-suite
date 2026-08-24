# Antigravity Workspace (`antigravity`)

Welcome to the **Antigravity Tooling & Plugin Workspace** maintained by [@haiggoh](https://github.com/haiggoh).
This workspace contains dedicated Antigravity plugins, rules, skills, and utilities shared across macOS and Windows.

---

## Workspace Structure

```text
<workspace_root>/                    # e.g., D:\antigravity (Windows) or ~/antigravity (macOS)
├── GEMINI.md                        # Root workspace guidelines & coding rules
├── .agents/                         # Workspace-level agent customizations
│   ├── hooks.json                   # Workspace lifecycle hooks
│   ├── auto_approve.py              # Hook handler scripts
│   ├── rules/                       # Workspace-specific rules
│   └── skills/                      # Workspace skills
└── antigravity-suite/               # Central monorepo suite & sync engine
    ├── bin/                         # Sync engine (sync_engine.py)
    ├── packages/                    # Dedicated Antigravity packages & plugins (agy-*)
    │   ├── agy-measure-twice/       # Pre-execution inspection skill
    │   ├── agy-no-hidden-changes/   # Transparent code modification rule
    │   └── agy-waypoints/           # Lifecycle hook & banner plugin
    ├── rules/                       # Global rules (synced to ~/.gemini/config/rules/)
    │   └── user_global.md
    ├── statusline/                  # Telemetry & statusline scripts
    ├── templates/                   # Shared settings template
    ├── install.py                   # Setup & workspace synchronizer
    └── push.ps1 / push.bat          # Quick commit & push utilities
```

---

## Workspace Guidelines & Standards

1. **Monorepo Packages**: All Antigravity plugins live inside `antigravity-suite/packages/` as clean directories tracked directly in Git (no nested `.git` submodules).
2. **Cross-Platform Portability**:
   - All plugins, hooks, and scripts must execute seamlessly on both **macOS** (POSIX/zsh/bash, `python3`) and **Windows** (PowerShell/cmd, `python`).
   - Use dedicated `.py` files for lifecycle hooks in `hooks.json` to prevent Windows shell quote-stripping issues.
3. **Plugin Architecture**:
   - Each package inside `packages/` should have a valid `plugin.json` manifest.
   - Optional modular components: `hooks.json`, `rules/`, and `skills/`.
4. **Synchronization**:
   - Run `python install.py` (or `python3 install.py`) inside `antigravity-suite` to sync global rules, telemetry status lines, and settings templates.

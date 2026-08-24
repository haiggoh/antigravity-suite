# antigravity-suite

A comprehensive power-user suite and synchronization toolkit for **Google Antigravity (AGY)** across **macOS and Windows**.

Synchronizes configuration, status line telemetry, custom skills, rules, and tool permissions seamlessly between devices and local environments, with built-in multi-repository workspace synchronization and conflict-free autostash.

---

## Key Features

* 🔄 **Cross-OS Compatibility (macOS & Windows)**: Automatically normalizes path separators, executables (`python3` vs `python`), and console codepages.
* 👤 **Account & Workspace Isolation**: Machine-local variables (such as active Google login email, session tokens, and `trustedWorkspaces`) remain isolated to each host.
* 📊 **Real-time Status Line**: Displays active model, agent state, context meter, working directory, live Google model quota with reset countdown, token telemetry, and rotating tips.
* 🛡️ **Workspace Sync with Auto-Stash**: One-command safe synchronization across all repositories in your workspace with automatic stashing of uncommitted edits (`--workspace-sync`).
* 🖥️ **Cross-App Local Sync**: Automatically synchronizes configuration between local CLI and Desktop / IDE app configurations on the same machine.
* 🔒 **Secure Asynchronous Transport**: Uses private Git repositories for zero-open-port, asynchronous synchronization across devices.

---

## Quick Start

### 1. Install & Sync

```bash
# macOS / Linux:
python3 install.py

# Windows (PowerShell):
python install.py
```

### 2. Workspace Multi-Repo Sync

Safely pull updates across all git repositories in your workspace without losing dirty uncommitted work:

```bash
python install.py --workspace-sync
```

### 3. Automated Workspace Migration

Migrate legacy project folders or root `GEMINI.md` into the suite structure:

```bash
python install.py --migrate
```

---

## Project Structure

```text
antigravity-suite/
├── README.md
├── install.py                  # Standalone cross-platform installer & synchronizer
├── uninstall.py                # Uninstaller
├── bin/
│   └── sync_engine.py          # Core sync engine, migration & workspace sync
├── packages/                   # Monorepo packages & plugins (agy-*)
│   ├── agy-statusline/         # Cross-platform live telemetry & quota status line
│   ├── agy-measure-twice/      # Pre-execution inspection skill
│   ├── agy-no-hidden-changes/  # Transparent code modification rule
│   └── agy-waypoints/          # Lifecycle hook & banner plugin
├── templates/
│   ├── shared-settings.json    # Shared settings template ({HOME} placeholders)
│   ├── workspace-GEMINI.md     # Workspace root guidelines template
│   └── agents/                 # Workspace-level agent configuration (.agents/)
├── rules/                      # Synced global rules (~/.gemini/config/rules/)
├── skills/
│   ├── antigravity-sync/       # Companion Antigravity sync skill
│   └── local-delegate/         # Local MLX model delegation skill
└── docs/
    └── SYNC-ARCHITECTURE.md    # Transport & security architecture
```

---

## License

MIT © Heiko Brantsch

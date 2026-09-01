# Antigravity Suite (`antigravity-suite`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-brightgreen.svg)]()
[![Antigravity](https://img.shields.io/badge/Google-Antigravity%20CLI%20%2F%20IDE-orange.svg)]()

A modular, production-ready power-user monorepo and configuration synchronization suite for **Google Antigravity (`agy`)** across **macOS, Windows, and Linux**.

---

## 🌟 Included Monorepo Packages & Plugins

| Package | Type | Description |
| :--- | :--- | :--- |
| [**`agy-statusline`**](packages/agy-statusline) | Plugin / Telemetry | High-performance status line with sub-millisecond local quota discovery, token metrics, context meters, and non-blocking tips. |
| [**`agy-sync`**](packages/agy-sync) | Plugin / Core Engine | Universal settings & rules synchronizer with conflict-free workspace auto-stash and bilateral standalone repo syncing. |
| [**`agy-brief-agents`**](packages/agy-brief-agents) | Delegation Plugin | Compiles global rules & workspace conventions into a compact briefing index for delegated subagents. |
| [**`agy-resume-interrupted`**](packages/agy-resume-interrupted) | Continuity Plugin | Detects rate-limited, stalled, or crashed prior sessions and formats exact continuation prompts. |
| [**`agy-audit-loose-ends`**](packages/agy-audit-loose-ends) | Audit Plugin | End-of-task reconciliation for task stores, `GEMINI.md`, and atomic credential/secret leak redaction. |
| [**`agy-measure-twice`**](packages/agy-measure-twice) | Skill Plugin | Pre-execution inspection skill guiding agents to survey existing capabilities before writing custom scripts. |
| [**`agy-no-hidden-changes`**](packages/agy-no-hidden-changes) | Rule Plugin | Enforces transparent, honest, and reversible code modifications. Prevents phantom workarounds. |
| [**`agy-waypoints`**](packages/agy-waypoints) | Hook Plugin | Execution lifecycle banner system and structured milestone manager. |
| [**`local-delegate`**](skills/local-delegate) | Skill | Offline local model offloading to Apple MLX / Ollama for zero-quota local tasks. |

> 🗺️ **Evolution Roadmap**: For upcoming features ported from the Claude Code `haiggoh` suite (Transcript Distiller, Run-To-Completion, MCP Probe Harness), see [docs/ROADMAP.md](docs/ROADMAP.md).

---

## 🚀 Quick Start

### 1. Installation & Synchronize

Clone the suite inside your workspace root (e.g., `~/AntigravityWorkspace/antigravity-suite` or `D:\antigravity\antigravity-suite`):

```bash
# macOS / Linux
cd ~/AntigravityWorkspace/antigravity-suite
python3 install.py

# Windows (PowerShell)
cd D:\antigravity\antigravity-suite
python install.py
```

`install.py` automatically:
1. Pulls the latest suite commits from GitHub (with safe `--autostash`).
2. Syncs global rules to `~/.gemini/config/rules/`.
3. Auto-discovers and syncs all package skills to `~/.gemini/antigravity-cli/skills/` and `~/.gemini/config/skills/`.
4. Installs statusline telemetry scripts to `~/.gemini/statusline/`.
5. Deploys root workspace guidelines (`GEMINI.md`) and hooks (`.agents/`) into your parent workspace.
6. Cleans up legacy ad-hoc directories.

---

## 🔄 Universal Multi-Device Sync

The synchronization engine (`bin/sync_engine.py`) is completely platform-agnostic:

* **Any Host Topology**: Supports macOS ⟷ macOS, Windows ⟷ Windows (any drive letter: `C:`, `D:`, `E:`), macOS ⟷ Windows, and Linux.
* **Account & Token Isolation**: Machine-local variables (`email`, session tokens, `trustedWorkspaces`) remain strictly isolated per machine. You can sync settings across work and personal accounts with zero credential bleed.
* **Workspace Auto-Stash (`--workspace-sync`)**: Automatically discovers all Git repositories in your workspace root and pulls updates with conflict-free rebase & auto-stash.
* **Dynamic Package Discovery**: Automatically discovers packages in `packages/` and links skills, rules, and binaries cleanly.

---

## 📁 Repository Structure

```text
antigravity-suite/
├── install.py                  # Cross-platform installer & synchronizer
├── uninstall.py                # Safe uninstaller & backup restore pointer
├── CHANGELOG.md                # Version history & release notes
├── bin/
│   ├── sync_engine.py          # Core configuration and workspace engine
│   └── sync_standalone_fork.py # Bi-directional package / fork synchronizer
├── packages/                   # First-class Antigravity packages (agy-*)
│   ├── agy-statusline/         # Live telemetry & quota status line
│   ├── agy-brief-agents/       # Subagent briefing index & rule injector
│   ├── agy-resume-interrupted/ # Interrupted session detector & resumer
│   ├── agy-audit-loose-ends/   # Durable record & secret audit engine
│   ├── agy-measure-twice/      # Pre-execution inspection skill
│   ├── agy-no-hidden-changes/  # Transparent code modification rule
│   └── agy-waypoints/          # Lifecycle hook & banner plugin
├── templates/
│   ├── shared-settings.json    # Shared settings template ({HOME} & {WORKSPACE} dynamic vars)
│   ├── workspace-GEMINI.md     # Workspace root guidelines template
│   └── agents/                 # Workspace-level agent configuration (.agents/)
├── rules/                      # Synced global rules (~/.gemini/config/rules/)
│   └── user_global.md
├── skills/                     # Workspace-level skill definitions
├── tests/                      # Smoke test suite for engine & packages
└── docs/                       # Architecture, sync documentation & roadmap
    ├── ROADMAP.md              # Feature parity roadmap
    └── SYNC-ARCHITECTURE.md    # Multi-device sync architecture
```

---

## 🧪 Testing

Run pytest across all monorepo packages:

```bash
pytest packages
```

---

## 📄 License

MIT © [Heiko Brantsch](https://github.com/haiggoh)

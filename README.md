# Antigravity Suite (`antigravity-suite`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-brightgreen.svg)]()
[![Antigravity](https://img.shields.io/badge/Google-Antigravity%20CLI%20%2F%20IDE-orange.svg)]()

A modular, production-ready power-user monorepo and configuration synchronization suite for **Google Antigravity (`agy`)** across **macOS, Windows, and Linux**.

---

## 🌟 Included Monorepo Packages & Skills

| Package | Skills Provided | Description |
| :--- | :--- | :--- |
| [**`agy-local-delegate`**](packages/agy-local-delegate) | `local-delegate` | Offline local model offloading to Apple Silicon MLX / Rapid (Qwen 3.8, DeepSeek R1, KAT Coder, Gemma 4). |
| [**`agy-run-to-completion`**](packages/agy-run-to-completion) | `run-to-completion`, `autopilot`, `triage-for-autonomy`, `execute-unattended`, `ungate-queue`, `close-out-the-run` | Autonomous multi-step execution loop, queue scoring, and attended blocker ungating. |
| [**`agy-brief-agents`**](packages/agy-brief-agents) | `brief-agents` | Compiles global rules & workspace conventions into a compact briefing index for delegated subagents. |
| [**`agy-resume-interrupted`**](packages/agy-resume-interrupted) | `resume-interrupted` | Detects rate-limited, stalled, or crashed prior sessions and formats exact continuation prompts. |
| [**`agy-audit-loose-ends`**](packages/agy-audit-loose-ends) | `audit-loose-ends` | End-of-task reconciliation for task stores, `GEMINI.md`, and atomic credential/secret leak redaction. |
| [**`agy-statusline`**](packages/agy-statusline) | *(Statusline Telemetry)* | High-performance status line with sub-millisecond local quota discovery, token metrics, and context meters. |
| [**`agy-sync`**](packages/agy-sync) | `antigravity-sync` | Universal settings & rules synchronizer with conflict-free workspace auto-stash. |
| [**`agy-measure-twice`**](packages/agy-measure-twice) | `measure-twice` | Pre-execution inspection skill guiding agents to survey existing capabilities before writing custom scripts. |
| [**`agy-no-hidden-changes`**](packages/agy-no-hidden-changes) | *(Rule)* | Enforces transparent, honest, and reversible code modifications without phantom edits. |
| [**`agy-waypoints`**](packages/agy-waypoints) | `waypoints` | Execution lifecycle banner system and structured milestone manager. |

> 🗺️ **Evolution Roadmap**: For details on upcoming Phase 4 (Package Hub & Sync) and Phase 5 features, see [docs/ROADMAP.md](docs/ROADMAP.md).

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
1. Pulls latest suite commits with safe `--autostash`.
2. Syncs global rules to `~/.gemini/config/rules/`.
3. Auto-discovers and syncs all package skills to `~/.gemini/antigravity-cli/skills/` and `~/.gemini/config/skills/` (using clean skill names without prefixes).
4. Installs statusline telemetry scripts to `~/.gemini/statusline/`.
5. Deploys root workspace guidelines (`GEMINI.md`) and hooks (`.agents/`) into your parent workspace.
6. Cleans up legacy ad-hoc directories.

---

## 🧠 Local Apple Silicon Model Offloading (`local-delegate`)

`local-delegate` connects directly to local Rapid-MLX (for MLX models), llama.cpp (for GGUF), or OpenAI-compatible endpoints with zero cloud quota usage:

* **Default Operator**: `qwen-3.8-operator` (27B 4-bit) & `qwen-3.8-thinking`.
* **Model Profiles (13 total)**: `deepseek-r1-architect`, `kat-coder-optiq`, `gemma-4-26b`, `kimi-vl-thinking`, `devstral-2-123b`, `ministral-14b`, `nemotron-omni`, `llama-scout`.
* **🎛️ Interactive Model Selection (`agy-csl`)**:
  ```bash
  # Launch interactive disk-aware model picker:
  agy-csl
  ```
* **🧠 RAM Preflight Safety**:
  ```bash
  # Check if model fits in unified memory before loading:
  python3 packages/agy-local-delegate/bin/agy_local_delegate.py preflight --model qwen-3.8-operator
  ```
* **🧹 Safe Memory Eviction Fallback (`agy-evict`)**:
  ```bash
  # Inspect resident model servers, RSS, and safety ranks:
  agy-evict --status

  # Evict orphaned/idle servers without touching active AGY sessions:
  agy-evict
  ```
* **📦 Live On-Disk Scanner**:
  ```bash
  python3 packages/agy-local-delegate/bin/agy_local_delegate.py scan
  ```

---

## 🔄 Universal Multi-Device Sync

The synchronization engine (`bin/sync_engine.py`) is completely platform-agnostic:

* **Any Host Topology**: Supports macOS ⟷ macOS, Windows ⟷ Windows (any drive letter: `C:`, `D:`, `E:`), macOS ⟷ Windows, and Linux.
* **Account & Token Isolation**: Machine-local variables (`email`, session tokens, `trustedWorkspaces`) remain strictly isolated per machine.
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
├── packages/                   # Monorepo packages (agy-*)
│   ├── agy-local-delegate/     # Apple Silicon MLX local model offloading (Qwen 3.8, DeepSeek R1, KAT)
│   ├── agy-run-to-completion/  # Autonomous execution & ungate engine (6 skills)
│   ├── agy-brief-agents/       # Subagent briefing index & rule injector
│   ├── agy-resume-interrupted/ # Interrupted session detector & resumer
│   ├── agy-audit-loose-ends/   # Durable record & secret audit engine
│   ├── agy-statusline/         # Live telemetry & quota status line
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

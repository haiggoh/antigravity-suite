# Changelog - Antigravity Suite (`antigravity-suite`)

All notable changes to the **Antigravity Suite** monorepo are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.3.1] - 2026-09-01
 
### 🚀 Local Architecture Enhancements (`agy-local-delegate`)

#### 🎛️ Interactive Model Selection: `agy-csl`
* Added `csl`-style interactive model selection picker (`bin/agy-csl`, `agy-local-mode --menu`):
  * Inspects `~/.models` to display live `[Installed <size> GB ✅]` badges.
  * Queries local ports `8000–8015` to indicate `[Active Port <port> 🔌]` running servers.
  * Allows choosing any registered profile or supplying custom model IDs/paths.

#### 🧠 RAM Preflight Safety & Unified Memory Protection
* Implemented cross-platform RAM preflight engine (`agy_local_delegate.py preflight` / `ram_preflight_check`):
  * **Mandatory in-flight guard**: Automatically runs before any local dispatch execution (`dispatch_local_prompt`), preventing unified memory freeze.
  * **Zero-RAM short-circuit**: Detects if requested model is already served on ports `8000–8015` and reuses it without allocating duplicate memory.
  * **Resident size calculation**: Evaluates on-disk model weight size + runtime overhead against live free system RAM (`vm_stat`/`sysctl`).
  * **16.0 GB Floor**: Enforces a strict safe memory floor to avoid Apple Silicon UI and Terminal freezes.

#### 📋 Automatic Offload Rule (`local-agents-offload.md`)
* Added standing rule `local-agents-offload.md` to fix the evaluation catch-22:
  * **Upfront Planning**: Decides per-step execution target (`local:operator` vs `cloud:<reason>`) during task decomposition before cloud tokens are spent.
  * **Default to Operator**: Flips the burden of proof so bulk, mechanical, and repetitive work defaults to `local:operator` ($0 per token).
  * **Supervised Ground-Truth Verification**: Keeps high-level judgment and orchestration on cloud while verifying local model outputs against tests and real diffs.

#### 🔌 Dynamic Port Discovery & Slot Allocation
* Replaced hardcoded ports with dynamic slot hunting:
  * Backend auto-discovery across ports `8000–8015` (Rapid-MLX, llama.cpp).
  * Proxy dynamic slot finder across `9191–9205`, completely eliminating `Address already in use` socket conflicts.
  * Enabled socket address reuse (`SO_REUSEADDR`) and automatic stale zombie process cleanup.

#### 🧹 Safe Memory Eviction Utility: `agy-evict`
* Created `bin/agy-evict` (adapted from `la-evict.sh` for AGY):
  * Discovers all resident local servers (`rapid-mlx`, `llama-server`, `mlx-lm`, `agy-proxy`) with RSS breakdown and uptime.
  * Protects active attached AGY sessions (`Rank #3`).
  * Supports `--status`, `--dry-run`, `--all`, `--port <port>`, and single highest-priority candidate eviction (`Rank #0` / `#1`).
* Symlinked `agy-csl` and `agy-evict` to `~/.local/bin/` via `install.py`.

---

## [v1.3.0] - 2026-09-01

### 🚀 Phase 3: Hardware Offload & Local Intelligence

#### 📦 New Monorepo Package: `agy-local-delegate`
* **`agy-local-delegate`** (`packages/agy-local-delegate`, Skill: `local-delegate`):
  * Upgraded default local operator to **Qwen 3.8 27B** (`qwen-3.8-operator`, `qwen-3.8-thinking`, `qwen-3.8-8bit`, `qwen-3.8-mtp`).
  * Expanded model catalog across 13 registered profiles:
    * `qwen-3.8-operator` (Default fast 27B coding workhorse)
    * `qwen-3.8-thinking` (Deep chain-of-thought reasoning)
    * `qwen-3.8-8bit` (High-precision 8-bit operator)
    * `qwen-3.8-mtp` (Multi-Token Prediction accelerated operator)
    * `qwen-80b-thinking` (Heavyweight 80B architecture model)
    * `deepseek-r1-architect` (DeepSeek R1 logic & architectural reasoning)
    * `kat-coder-optiq` (KAT Coder V2.5 Dev OptiQ code generation)
    * `devstral-2-123b` (Heavyweight 123B code refactoring engine)
    * `gemma-4-26b` (Google Gemma 4 26B instruction & analysis)
    * `kimi-vl-thinking` (Multimodal vision & reasoning utility)
    * `ministral-14b` (Fast reasoning & inspection model)
    * `nemotron-omni` (NVIDIA Nemotron 3 Nano Omni multimodal model)
    * `llama-scout` (Lightweight classification & utility)
  * **On-Disk Model Scanner**: Added `scan_local_models_dir` and CLI command (`bin/agy_local_delegate.py scan`) to inspect installed models in `~/.models` with disk usage breakdown.
  * Safe multi-file context bundling with automatic overflow protection (`bundle_file_attachments`).
  * Unit test suite: `tests/test_local_delegate.py` (100% passing).

#### 🗺️ Roadmap Update
* Completed Phase 3 (`local-delegate`).
* Deferred `mcp-smoke-test` and `turn-speak` to Phase 5 (post-Phase 4).

---

## [v1.2.0] - 2026-09-01

### 🚀 Phase 2: Autonomous Multi-Step Execution Loop

#### 📦 New Monorepo Package: `agy-run-to-completion`
* **`agy-run-to-completion`** (`packages/agy-run-to-completion`):
  * Composable 6-skill autonomous task engine:
    * `run-to-completion`: Continuous execution offer for multi-step plans without stalling between non-destructive steps.
    * `autopilot`: End-to-end 4-phase unattended queue runner (Kickoff → Triage → Execute → Closeout).
    * `triage-for-autonomy`: Pre-execution queue scoring (Tier 1 Do-Now, Tier 2 Heavy, Gated G1-G4/ENV/WAIT).
    * `execute-unattended`: In-run execution loop with wrap-and-switch on unexpected blockers.
    * `ungate-queue`: Attended blocker resolution pass converting gate reasons into single clarifying questions sorted by cheapness.
    * `close-out-the-run`: State reconciliation, clean git check, and structured gated work handoff menu.
  * Clean skill names (without `agy-` prefixes) for seamless integration inside Antigravity agents.
  * Triage & closeout CLI utility: `bin/agy_rtc.py` (`triage`, `ungate`).
  * Unit test suite: `tests/test_rtc.py` (100% passing).

---

## [v1.1.0] - 2026-09-01

### 🚀 Phase 1: Core Session Continuity & Delegation Intelligence

#### 📦 New Monorepo Packages
* **`agy-brief-agents`** (`packages/agy-brief-agents`, Skill: `brief-agents`):
  * Compiles global rules (`~/.gemini/config/rules/`), workspace `GEMINI.md`, and custom skills into a compact single-line gist index (`~/.gemini/agent-briefing-index.md`).
  * Fast SHA-256 fingerprint caching and prompt injection wrapper CLI (`bin/agy_brief_agents.py`).
* **`agy-resume-interrupted`** (`packages/agy-resume-interrupted`, Skill: `resume-interrupted`):
  * Scans Antigravity conversation transcripts in `~/.gemini/antigravity-cli/brain/` for interrupted trajectories.
  * Accurately detects quota limits / 429 errors (`limit_kill`), stalled turns (`stalled_turn`), and unhandled tool crashes.
  * Generates structured resumption summaries and continuation prompts via CLI (`bin/agy_resume_interrupted.py`).
* **`agy-audit-loose-ends`** (`packages/agy-audit-loose-ends`, Skill: `audit-loose-ends`):
  * End-of-task reconciliation engine for waypoints, open task items in `GEMINI.md`, and workspace notes.
  * Scans files for exposed API credentials (Google, Anthropic, OpenAI, GitHub, Slack) and provides atomic secret redaction (`bin/agy_audit_loose_ends.py redact`).

#### 🔄 Sync Engine Upgrades
* **Dynamic Package Discovery**: `bin/sync_engine.py` automatically discovers and deploys package skills and rules from `packages/*/skills/` and `packages/*/rules/` into `~/.gemini/` without manual path wiring.
* **Auto-Chmod Executables**: Ensures all package CLI binaries in `packages/*/bin/` receive executable permissions on POSIX systems.

---

## [v1.0.0] - 2026-08-25

### 🚀 Initial Public Release

#### 📦 Monorepo Architecture & Packages
* **Clean Monorepo Layout**: Integrated all custom Antigravity plugins into `packages/` as standard directories tracked directly in Git.
* **`agy-statusline`**: High-performance telemetry status line with sub-millisecond local quota discovery, token usage metrics, and non-blocking tips.
* **`agy-sync`**: Official configuration sync package, supporting cross-platform settings merging, rule deployment, and workspace multi-repo synchronization.
* **`agy-measure-twice`**: Pre-execution survey skill ensuring agents match real events and inspect platform capabilities before building custom scripts.
* **`agy-no-hidden-changes`**: Enforces transparent, honest, and reversible file modifications with no phantom edits.
* **`agy-waypoints`**: Execution lifecycle hooks and stage banner system.

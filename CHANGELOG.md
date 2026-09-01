# Changelog - Antigravity Suite (`antigravity-suite`)

All notable changes to the **Antigravity Suite** monorepo are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.4.1] - 2026-09-01

### 🔧 CLI Executable Permission Repair

* Restored executable mode on the Transcript Distiller CLI.
* Restored executable mode on both `get-antigravity` entry points.
* Verified that file contents remain byte-for-byte identical to `v1.4.0`.
* Revalidated Bash and Python syntax after the mode correction.

## [v1.4.0] - 2026-09-01

### 🚀 Verified Full Local AGY Sessions

#### `agy-local-delegate` 0.2.0
* Fixed no-argument startup so `agy-local-mode` selects the default operator without capturing menu prompts.
* Preserved the interactive picker through `agy-csl` and `--menu`.
* Added owned Rapid-MLX server startup using `rapid-mlx serve`.
* Reuses only servers that advertise the requested model.
* Allocates model ports from `8000–8015` and proxy ports from `9191–9205`.
* Never kills unrelated listeners merely because a port is occupied.
* Added upstream-aware proxy health checks and mandatory end-to-end inference smoke testing.
* Requires AGY's Gemini provider configuration to prevent accidental cloud fallback.
* Added Gemini/OpenAI function-tool translation, basic SSE responses, and `countTokens`.
* Added focused regression coverage for model resolution, menu output, server matching, proxy inference, and tool calls.

## [v1.3.3] - 2026-09-01

### 🛡️ Audit Fixture Suppression

* Bumped `agy-audit-loose-ends` from `0.1.0` to `0.1.1`.
* Added an explicit `# noaudit` line marker for intentional secret fixtures.
* Added regression coverage proving marked lines are excluded from secret scans.
* Kept redaction behavior unchanged for unmarked content.

## [v1.3.2] - 2026-09-01

### 🛠️ Fixes & Documentation

#### 🗺️ Waypoints Banner — Bootstrap Fix
* Added `bin/waypoints.py` standalone CLI to `agy-waypoints` package (was missing from the installed CLI bin path).
* Created `~/.gemini/waypoints.json` bootstrap helper so the pre-invocation session banner appears immediately on a fresh install without requiring a manual first-run setup.
* `install.py` now ensures `waypoints.py` is symlinked alongside other CLI utilities.

#### 📄 README Audit & Sync to v1.3.1
* Corrected version badge from `1.1.0` → `1.3.1` (was stale by two major revisions).
* Added missing packages to the packages table: `agy-transcript-distiller`, `get-antigravity`.
* Expanded `agy-local-delegate` description to include `agy-local-mode` (Gemini→OpenAI proxy).
* Updated `agy-waypoints` description to reflect full `waypoints.py` CLI interface.
* Added step 7 to `install.py` install notes: symlinking of CLI utilities to `~/.local/bin/`.
* Updated repository structure tree to include all 12 packages (was missing `agy-sync`, `agy-transcript-distiller`, `get-antigravity`).
* Corrected RAM preflight description to note mandatory 16 GB floor enforcement.

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

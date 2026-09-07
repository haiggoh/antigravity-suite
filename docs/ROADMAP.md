# Antigravity Suite - Feature Parity & Evolution Roadmap

This roadmap defines the architectural alignment, version tracking, and implementation plan to bring full feature parity from the Claude Code `haiggoh` plugin suite to the cross-platform **Google Antigravity (AGY) Suite**.

*(Note: Standalone universal tools like `human-shell` are maintained separately and do not require suite-specific ports).*

---

## 1. Architectural Mapping (Claude Code vs. Antigravity)

| Claude Code Primitive | Antigravity / Gemini Equivalent | Purpose |
| :--- | :--- | :--- |
| `hooks/` (`SessionStart`, `PreToolUse`, `PreInvocation`) | Statusline inline indicators, briefing index (`agent-briefing-index.md`), and workspace rules | Proactive context injection and background monitoring. |
| `.claude/CLAUDE.md`, rules | `~/.gemini/config/rules/` and workspace `GEMINI.md` | Durable behavioral guidelines and project instructions. |
| Agent / Workflow tools | AGY Subagents (`define_subagent`, `invoke_subagent`) | Context-isolated task delegation. |
| `.claude/projects/` (`.jsonl`) | `~/.gemini/antigravity-cli/brain/<id>/.../transcript.jsonl` | Raw event, turn, and tool execution logs. |
| `installed_plugins.json` / catalog | `packages/`, `get-antigravity`, `install.py`, and `settings.json` | Package management, distribution, skip-lists, and configuration. |

---

## 2. Feature Parity & Version Matrix

| Domain / Package | Claude Source & Version | Antigravity Suite Status | Parity & Evolution Goals |
| :--- | :--- | :--- | :--- |
| **Package Hub & Updater** | `get-haiggoh` (v0.4.0) | `get-antigravity` (**v1.0.0**) ✅ | **Complete**: Catalog scanner, atomic skip-list (`.agy-skip.json`), version drift detection, selective sync (`--only`, `--category`), and execution planner (`plan` / `apply`). |
| **Persistent Task To-Dos** | `waypoints` (**v0.8.0**) | `agy-waypoints` (v0.1.0 port) ⚠️ | **Upgrade to v0.8.0**: Standalone interactive terminal CSL (`waypoints_menu.py` token-free TUI), startup print banner integration via statusline & briefing index, `pin --because`, multi-target `waiting_on`, and `recover` backup ring. |
| **Local Model Delegation** | `local-agents` (**v0.13.9**) | `agy-local-delegate` (v0.2.1) ⚠️ | **Upgrade to v0.13.9**: Automated routing classifier, launcher profile controls, Rapid venv watchers, multiple model backends (MLX, Ollama, OpenAI-compatible), and process evict safety. |
| **Durable Record Reconciliation** | `audit-loose-ends` (**v0.5.5**) | `agy-audit-loose-ends` (v0.1.1) ⚠️ | **Upgrade to v0.5.5**: Match window optimization, secret redaction, orphan clean-up, and `noaudit` fixture markers. |
| **Session Continuity / Crash Recovery** | `resume-interrupted` (**v0.4.0**) | `agy-resume-interrupted` (v0.1.0) ⚠️ | **Upgrade to v0.4.0**: Multi-session brain trajectory scanner, structured crash triage, rate-limit cutoff resumption prompts. |
| **Autonomous Queue Execution** | `run-to-completion` (**v0.5.0**) | `agy-run-to-completion` (v0.1.0) ⚠️ | **Upgrade to v0.5.0**: Refined G1-G4 gate triage, post-push dogfooding verification loop, and unattended auto-switch mechanics. |
| **Subagent Briefing Index** | `brief-agents` (**v0.1.4**) | `agy-brief-agents` (v0.1.0) ⚠️ | **Upgrade to v0.1.4**: Live rule cache, full marketplace discovery index, and auto-briefing injection. |
| **Transparent File Modification** | `no-hidden-changes` (**v1.4.3**) | `agy-no-hidden-changes` (v1.0.0 rules) ⚠️ | **Tooling Upgrade**: Active hook inspection, hermetic test suite, and shadow file guards. |
| **Transcript Distillation** | `claude-code-transcript-distiller` (**v0.8.0**) | `agy-transcript-distiller` (v0.1.0 skeleton) ⏳ | **Port v0.8.0**: Chronological multi-session ordering, markdown capsule generator, artifact exporter, and CLI. |
| **Cost & Token Telemetry** | `cost-tracker` (**v0.4.0**) | `agy-statusline` (telemetry only) ⏳ | **Add `agy-cost-tracker`**: Gateway quota calibration and token cost projection. |
| **Desktop / IDE Sync** | `claude-code-desktop-sync` (**v1.0.2**) | `bin/sync_engine.py` (partial) ⏳ | **Add `agy-desktop-sync`**: Bidirectional MCP and settings mirror between Antigravity CLI and IDE. |
| **Session Compaction** | `compact-session` (**v0.1.0**) | *(None)* ⏳ | **Port `agy-compact-session`**: Context compaction & branch pruning. |
| **App MCP Probe Harness** | `mcp-smoke-test` (**v0.2.0**) | *(None)* ⏳ | **Tabled**: 4-part probe & test harness for app-controlling MCP servers (DaVinci Resolve, Blender, Adobe). |
| **Voice / Speech Readback** | `claude-turn-speak` (**v0.1.7**) | *(None)* ⏳ | **Tabled**: macOS `say` and OpenAI TTS integration for hands-free voice workflows. |

---

## 3. Execution Phases

### Phase 1: Distribution & Core Interactive To-Dos (Completed)
- [x] **`get-antigravity` (v1.0.0)**: Package Hub, skip-list manager, and distribution updater with 100% test coverage.
- [x] **`agy-waypoints` (v0.8.0 Upgrade)**:
  - Port `waypoints_core.py` v0.8.0 (`pin`, `waiting_on`, `recover`, atomic journal, backup ring).
  - Port `waypoints_menu.py` (Standalone interactive terminal CSL / TTY menu).
  - Add statusline banner indicator and briefing index compiler so open items surface automatically.
  - Full test suite: unit tests, CLI tests, menu composition tests.

### Phase 2: Local Intelligence & Session Continuity Upgrades (Completed)
- [x] **`agy-local-delegate` (v0.13.9 Upgrade)**: Auto-classifier, profile controls, savings ledger, Rapid venv watcher.
- [x] **`agy-audit-loose-ends` (v0.5.5 Upgrade)** & **`agy-resume-interrupted` (v0.4.0 Upgrade)**: Match window fixes, secret scanner, deep trajectory crash analyzer.
- [x] **`agy-run-to-completion` (v0.5.0 Upgrade)**: Full 5-tier autonomous execution loop and post-push verification.
- [x] **`agy-brief-agents` (v0.1.4 Upgrade)**: Comprehensive briefing index with live rule cache.

### Phase 3: Advanced Tooling, Distillation & Desktop Bridge
- [ ] **`agy-transcript-distiller` (v0.8.0 Port)**: Line-addressable markdown capsule generator and CLI.
- [ ] **`agy-cost-tracker` (v0.4.0 Port)**: Token cost projector and gateway calibrator.
- [ ] **`agy-desktop-sync` (v1.0.2 Port)**: Bidirectional MCP and settings synchronization between CLI and IDE.
- [ ] **`agy-compact-session` (v0.1.0 Port)**: Session history compaction.
- [ ] **`agy-no-hidden-changes` (v1.4.3 Tooling)**: Hermetic validation harness and shadow file guards.

### Phase 4: Media MCP & Audio Helpers (Tabled)
- [ ] **`agy-mcp-smoke-test`**: Verification harness for media MCP servers.
- [ ] **`agy-turn-speak`**: On-demand response audio playback.

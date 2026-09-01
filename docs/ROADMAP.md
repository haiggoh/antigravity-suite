# Antigravity Suite - Feature Parity & Evolution Roadmap

This roadmap defines the architectural alignment and step-by-step implementation plan to bring full feature parity from the Claude Code `haiggoh` plugin suite to the cross-platform **Google Antigravity (AGY) Suite**.

---

## 1. Architectural Mapping (Claude Code vs. Antigravity)

| Claude Code Primitive | Antigravity / Gemini Equivalent | Purpose |
| :--- | :--- | :--- |
| `hooks/` (`SessionStart`, `PreToolUse`) | Lifecycle hooks / statusline integration / workspace `.agents/` | Proactive context injection and background monitoring. |
| `.claude/CLAUDE.md`, rules | `~/.gemini/config/rules/` and workspace `GEMINI.md` | Durable behavioral guidelines and project instructions. |
| Agent / Workflow tools | AGY Subagents (`define_subagent`, `invoke_subagent`) | Context-isolated task delegation. |
| `.claude/projects/` (`.jsonl`) | `~/.gemini/antigravity-cli/brain/<id>/.../transcript.jsonl` | Raw event, turn, and tool execution logs. |
| `installed_plugins.json` / catalog | `packages/`, `install.py`, and `shared-settings.json` | Package management, distribution, and configuration. |

---

## 2. Feature Parity Matrix

| Feature | Claude Source Plugin | Antigravity Target Package / Module | Status |
| :--- | :--- | :--- | :--- |
| **Telemetry & Quota Statusline** | *(None / External)* | `packages/agy-statusline` | ✅ Complete |
| **Transparent Modification Rules** | `no-hidden-changes` | `packages/agy-no-hidden-changes` | ✅ Complete |
| **Pre-Execution Architectural Survey** | `measure-twice` | `packages/agy-measure-twice` | ✅ Complete |
| **Persistent Task Banners (To-Dos)** | `waypoints` | `packages/agy-waypoints` | ✅ Complete |
| **Workspace Git Auto-Stash Sync** | `claude-code-desktop-sync` | `bin/sync_engine.py` (`--workspace-sync`) | ✅ Complete |
| **Subagent Context Briefing** | `brief-agents` | `packages/agy-brief-agents` | ✅ Complete |
| **Session Continuity / Crash Recovery** | `resume-interrupted` | `packages/agy-resume-interrupted` | ✅ Complete |
| **Durable Record Reconciliation** | `audit-loose-ends` | `packages/agy-audit-loose-ends` | ✅ Complete |
| **Autonomous Multi-Step Execution** | `run-to-completion` | `packages/agy-run-to-completion` | ⏳ Phase 2 |
| **Transcript Distillation & Capsules** | `claude-code-transcript-distiller` | `packages/agy-transcript-distiller` | ⏳ Phase 2 |
| **Local Model Delegation (MLX)** | `local-agents` | `packages/agy-local-agents` (`skills/local-delegate`) | ⏳ Phase 3 |
| **MCP Verification & Probe Harness** | `mcp-smoke-test` | `packages/agy-mcp-smoke-test` | ⏳ Phase 3 |
| **On-Demand Speech / TTS** | `claude-turn-speak` | `packages/agy-turn-speak` | ⏳ Phase 3 |
| **Package Catalog & Auto-Updater** | `get-haiggoh` | `get-antigravity` (`install.py` v2) | ⏳ Phase 4 |
| **Desktop / IDE MCP Synchronizer** | `claude-code-desktop-sync` | `bin/sync_engine.py` (Desktop MCP module) | ⏳ Phase 4 |

---

## 3. Implementation Phases

### Phase 1: Core Session Continuity & Delegation Intelligence
- [x] **`agy-brief-agents`**:
  - Compiles `~/.gemini/config/rules/user_global.md`, workspace `GEMINI.md`, and active custom skills into `~/.gemini/agent-briefing-index.md`.
  - Injects condensed context into subagent prompts during delegation (`invoke_subagent`).
  - Unit tests + CLI tooling (`bin/agy_brief_agents.py`).
- [x] **`agy-resume-interrupted`**:
  - Scans `~/.gemini/antigravity-cli/brain/` for aborted trajectories, tool timeout crashes, or rate-limit cutoffs.
  - Generates seamless resumption prompts and status summaries.
  - Unit tests + CLI tooling (`bin/agy_resume_interrupted.py`).
- [x] **`agy-audit-loose-ends`**:
  - End-of-task reconciliation skill for waypoints, memory records, task lists, and `GEMINI.md`.
  - Secret redaction and orphan cleaner.
  - Unit tests + SKILL definition.

### Phase 2: Autonomous Execution & Distillation
- [ ] **`agy-run-to-completion`**:
  - `run-to-completion`: Front-loads clarification, runs multi-step tasks without stalling at non-destructive seams.
  - `ungate-queue`: Interactive blocker release workflow.
  - `close-out-the-run`: Clean wrap and remaining-blocker persistence.
- [ ] **`agy-transcript-distiller`**:
  - Distills AGY `transcript.jsonl` into line-addressable, noise-free markdown capsules.

### Phase 3: Hardware Offload, App Probing & Audio Helpers
- [ ] **`agy-local-agents`**:
  - Local MLX delegation overlay for Apple Silicon (Qwen / Llama).
- [ ] **`agy-mcp-smoke-test`**:
  - 4-part probe & test harness for app-controlling MCP servers (DaVinci Resolve, Blender, Adobe).
- [ ] **`agy-turn-speak`**:
  - macOS `say` and OpenAI TTS integration for hands-free voice workflows.

### Phase 4: Suite Distribution & Package Management
- [ ] **`get-antigravity` (Package Hub & Updater)**:
  - Version-drift checks, skip-lists (`.agy-skip.json`), selective package install/sync (`--only`, `--category`).
- [ ] **`agy-desktop-sync`**:
  - Full bidirectional MCP and config mirror between Antigravity CLI and Desktop / IDE.

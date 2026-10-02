# Antigravity Suite - Feature Parity & Evolution Roadmap

This roadmap defines the architectural alignment, version tracking, and implementation plan to bring full feature parity from the Claude Code `haiggoh` plugin suite to the cross-platform **Google Antigravity (AGY) Suite**.

*(Note: Standalone universal tools like `human-shell` are maintained separately and do not require suite-specific ports.)*

---

## 1. Architectural Mapping (Claude Code vs. Antigravity)

| Claude Code Primitive | Antigravity / Gemini Equivalent | Purpose |
| :--- | :--- | :--- |
| `hooks/` (`SessionStart`, `PreToolUse`, `PreInvocation`) | Statusline inline indicators, briefing index (`agent-briefing-index.md`), and workspace rules | Proactive context injection and background monitoring. |
| `.claude/CLAUDE.md`, rules | `~/.gemini/config/rules/` and workspace `GEMINI.md` | Durable behavioral guidelines and project instructions. |
| Agent / Workflow tools | AGY Subagents (`define_subagent`, `invoke_subagent`) | Context-isolated task delegation. |
| `.claude/projects/` (`.jsonl`) | `~/.gemini/antigravity-cli/brain/<cid>/.../transcript.jsonl` | Raw event, turn, and tool execution logs. |
| `installed_plugins.json` / catalog | `packages/`, `get-antigravity`, `install.py`, and `settings.json` | Package management, distribution, skip-lists, and configuration. |

---

## 2. Feature Parity & Version Matrix

| Domain / Package | Claude Source & Version | Antigravity Suite Status | Parity & Evolution Goals |
| :--- | :--- | :--- | :--- |
| **Package Hub & Updater** | `get-haiggoh` (v0.4.0) | `get-antigravity` (**v1.0.0**) ✅ | **Complete**: Catalog scanner, atomic skip-list (`.agy-skip.json`), version drift detection, selective sync (`--only`, `--category`), and execution planner (`plan` / `apply`). |
| **Persistent Task To-Dos** | `waypoints` (**v0.8.0**) | `agy-waypoints` (v0.1.0 port) ⚠️ | **Upgrade to v0.8.0**: Interactive 21-action terminal menu; four-tier archive (open → done → archived → deleted, never auto-destroys); append-only journal (`waypoints-journal.jsonl`, permanent, never pruned) with `journal [--id] [--since]`; triage system (`do-now/heavy/gated/waiting`) with multi-target `waiting_on "<id> @ <milestone>"` + auto-release on close; `pin --because` (tier-preserving promotion, reason required); corrupt-store detection (refuses to operate, preserves evidence outside backup ring); output-size-bounded pagination (`--limit`, `--max-chars`, `--page`); `done --as "resolution"` title rewrite; `list --json` with versioned `contract` payload; 10-snapshot + 30-daily backup ring (pending). |
| **Local Model Delegation** | `local-agents` (**v0.13.9**) | `agy-local-delegate` (v0.2.1) ⚠️ | **Upgrade to v0.13.9**: `csl` interactive model picker menu; role routing (`operator/reasoner/validator/utility`, never hardcoded model names); `la-ram-preflight.sh` (3-question cheapest-first OOM prevention); `la-evict.sh` (escalating emergency memory recovery, least-costly first, never kills a session on first pass); `la-disk-inventory.sh` (orphan + NOPAYLOAD detection); model-asset symlink-farm overlay (shadow assets without duplicating weights); `la-stream-render.py` session watcher; 7 delegation skills (`offload-to-local`, `compose-the-payload`, `brief-the-delegate`, `isolate-parallel-work`, `guard-shared-runtime`, `verify-delegated-work`); Auto Mode local classifier on same port; specced: portable manifests (`.local-model-manifest.json` beside weights, atomic downloader write — v0.14.0); runtime profiles (3 JSON files separating artifact from runtime identity — v0.15.0); oMLX backend lane (persistent cross-restart KV cache — v0.16.0) (pending). |
| **Durable Record Reconciliation** | `audit-loose-ends` (**v0.5.5**) | `agy-audit-loose-ends` (v0.1.1) ⚠️ | **Upgrade to v0.5.5**: `audit-scan.py` transcript digest (~600× compression, streams JSONL externally, groups by surface: memory/plans/waypoints/CLAUDE.md/hooks/automation, prints compression ratio, GAPS section); trigger model fires on wrap-up signals OR when durable records changed — not length-based; `redact-secret.py` 5-layer scanner (L1 word boundary, L2 vendor shapes, L3 entropy gate for generic `sk-`, L4 keyword=value only, L5 value sanity) with `--explain-filtered`, `--self-test` corpus seeded from historical false positives, same-length redaction preserving inode; `waypoints.py resolve` integration for auto-releasing unblocked items (pending). |
| **Session Continuity / Crash Recovery** | `resume-interrupted` (**v0.4.0**) | `agy-resume-interrupted` (v0.1.0) ✅ | **Upgrade complete**: Multi‑session brain scan, rate‑limit detection, and resumable prompts. |
| **Autonomous Queue Execution** | `run-to-completion` (**v0.5.0**) | `agy-run-to-completion` (v0.1.0) ✅ | **Upgrade complete**: 5‑tier execution loop, gate triage, and post‑push verification. |
| **Subagent Briefing Index** | `brief-agents` (**v0.1.4**) | `agy-brief-agents` (v0.1.0) ⚠️ | **Upgrade to v0.1.4**: Generates `~/.gemini/agent-briefing-index.md` (CLAUDE.md section gists + Memory entries + **literal** SessionStart nudge text per plugin); sorted-mtime fingerprint (reorder-safe rebuild trigger); PreToolUse **hard-deny** for un-briefed Agent/Task (`[no-brief]` opt-out); **soft reminder** for Workflow; fail-safe (any error → allow, never crash); CLI: `generate / show / path / stale`; companion `brief-agents` skill (pending). |
| **Transparent File Modification** | `no-hidden-changes` (**v1.4.3**) | `agy-no-hidden-changes` (v1.0.0 rules) ⚠️ | **Tooling Upgrade**: SessionStart nudge + PreToolUse enforcement, fingerprint‑based regeneration, automation census, per‑machine marker, soft‑gate for Workflow, hard‑deny for Agent/Task (pending). |
| **Cost & Token Telemetry** | `cost-tracker` (**v0.4.0**) | `agy-cost-tracker` (v0.4.0) ⚠️ | **Expand to full model**: Three-axis spend reporting (session lifetime / today / local saved); `calibrate` exits 1 on measured undercount (gateway-vs-ledger external check — the only verification that doesn't self-agree); `cap --learn` reads cap from gateway refusal message; quarantine model (invalid records listed with reason, never clamped — clamping hid $16.07 of spend); resumed-session reset attribution (negative delta → floor marked `*`); local traffic isolated by endpoint not env flag; `doctor` command (quarantined records grouped by reason + session); `COST_TRACKER_SAVINGS_CMD` auto-discovers local-agents savings ledger; mutation-tested suite (pending). |
| **Desktop / IDE Sync** | `claude-code-desktop-sync` (**v1.0.2**) | `agy-desktop-sync` (partial) ⏳ | **Bidirectional MCP sync with conflict detection, content‑based reconciliation, manual‑step instructions for HTTP/connector servers, companion `desktop-sync` skill, absolute‑path handling, backups** (pending). |
| **Transcript Distillation** | `claude-code-transcript-distiller` (**v0.8.0**) | `agy-transcript-distiller` (v0.1.0 skeleton) ⏳ | **Port v0.8.0**: Generates indexed markdown capsule and compact JSONL per session; interactive multi‑session selector; deterministic fingerprint & preservation of thinking, file‑history; CLI with base64 handling, conflict detection, and archival options (pending). |
| **App MCP Probe Harness** | `mcp-smoke-test` (**v0.2.0**) | *(None)* ⏳ | **Tabled**: 4‑part probe & test harness for media MCP servers (pending). |
| **Voice / Speech Readback** | `claude-turn-speak` (**v0.1.7**) | *(None)* ⏳ | **Tabled**: On-demand macOS `say` + optional OpenAI TTS (no auto-hooks, intentionally); CLI: `speak-text`, `speak-latest-claude`, `stop`; configurable voice preference list, rate, `maxCharacters`; quality presets (`macos-modern`, `macos-auto`, `openai-natural`); Spotlight/Raycast-launchable stop app (`install-stop-app`); OpenAI key stored in Keychain (never in config); `doctor` health check; emergency cleanup for stale auto-read hooks from early versions (pending). |
| **Statusline Enhancements** | `agy-statusline` v1.1.0 | `agy-statusline` (v1.1.0) ✅ | **Enhancements**: Sub‑ms loopback scanner, rotating productivity tips, Windows support, cache directory standardization. |

---

## 3. Execution Phases

### Phase 1: Distribution & Core Interactive To-Dos (Completed)
- [x] **`get-antigravity` (v1.0.0)**: Package Hub, skip‑list manager, and distribution updater with full test coverage.
- [x] **`agy-waypoints` (v0.8.0 Upgrade)**: Ported core, interactive TUI, statusline banner, and backup ring.

### Phase 2: Local Intelligence & Session Continuity Upgrades (Completed)
- [x] **`agy-local-delegate` (v0.13.9 Upgrade)**: Model delegation, classifier, and safe eviction.
- [x] **`agy-audit-loose-ends` (v0.5.5 Upgrade)** & **`agy-resume-interrupted` (v0.4.0 Upgrade)**: Secret scanner, orphan cleanup, and crash resumption.
- [x] **`agy-run-to-completion` (v0.5.0 Upgrade)**: Full autonomous execution loop.
- [x] **`agy-brief-agents` (v0.1.4 Upgrade)**: Global rule briefing for subagents.

### Phase 3: Advanced Tooling, Distillation & Desktop Bridge
- [ ] **`agy-transcript-distiller` (v0.8.0 Port)**: Markdown capsule generation (pending).
- [ ] **`agy-desktop-sync` (v1.0.2 Port)**: Bidirectional MCP sync (pending).
- [ ] **`agy-no-hidden-changes` (v1.4.3 Tooling)**: Hermetic validation harness (pending).
- [ ] **`agy-waypoints` (v0.8.0 Upgrade)**: Full journal, triage system, and corrupt-store guard (pending).
- [ ] **`agy-audit-loose-ends` (v0.5.5 Upgrade)**: Transcript digest + 5-layer secret scanner (pending).
- [ ] **`agy-cost-tracker` (full model)**: Three-axis reporting, calibrate command, quarantine model (pending).
- [ ] **`agy-local-delegate` (v0.13.9 Upgrade)**: csl menu, role routing, RAM preflight, 7 skills, Auto Mode (pending).
- [ ] **`agy-brief-agents` (v0.1.4 Upgrade)**: Briefing index literal nudge text, hard-deny enforcement, CLI (pending).

### Phase 4: Media MCP & Audio Helpers (Tabled)
- [ ] **`agy-mcp-smoke-test`**: Media MCP server probe harness (pending).
- [ ] **`agy-turn-speak`**: Voice playback integration (pending).

# Changelog - Antigravity Suite (`antigravity-suite`)

All notable changes to the **Antigravity Suite** monorepo are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0] - 2026-08-25

### 🚀 Initial Public Release

#### 📦 Monorepo Architecture & Packages
* **Clean Monorepo Layout**: Integrated all custom Antigravity plugins into `packages/` as standard directories tracked directly in Git.
* **`agy-statusline`**: High-performance telemetry status line with sub-millisecond local quota discovery, multi-language Windows support (`ABHÖREN`), token usage metrics, and non-blocking tips.
* **`agy-sync`**: Official configuration sync package, supporting cross-platform settings merging, rule deployment, and workspace multi-repo synchronization.
* **`agy-measure-twice`**: Pre-execution survey skill ensuring agents match real events and inspect platform capabilities before building custom scripts.
* **`agy-no-hidden-changes`**: Enforces transparent, honest, and reversible file modifications with no phantom edits.
* **`agy-waypoints`**: Execution lifecycle hooks and stage banner system.
* **`local-delegate`**: Offline local model offloading skill for Apple MLX / Ollama.

#### 🔄 Universal Synchronization Engine
* **Universal Multi-Host Topology**: Supports syncing between any combination of macOS, Windows (any drive letter: `C:`, `D:`, `E:`), and Linux.
* **Dynamic Placeholders**: Enhanced template parser supporting `{HOME}`, `{WORKSPACE}`, and `{USER}` placeholders.
* **Multi-Account & Auth Isolation**: Machine-local variables (`email`, OAuth tokens, session keys, `trustedWorkspaces`) are preserved locally and protected against cross-account leaks.
* **Workspace Auto-Stash (`--workspace-sync`)**: Safe batch `git pull --rebase --autostash` across all repositories in the workspace root.
* **Parent Workspace Deployment**: Automatically syncs and deploys root guidelines (`GEMINI.md`) and hooks (`.agents/`) to parent workspace directories.
* **Bi-directional Standalone Sync**: Built-in tool (`bin/sync_standalone_fork.py`) to easily push/pull suite packages to and from standalone GitHub repositories and fetch upstream patches.

#### 🧹 Storage & Directory Standardization
* **Standard Paths**: Migrated all status line scripts to `~/.gemini/statusline/`, cache to `~/.gemini/cache/statusline/`, rules to `~/.gemini/config/rules/`, and backups to `~/.gemini/backups/`.
* **Automated Cleanup**: Installer automatically detects and cleans up legacy `~/.antigravity/` directories.

#### 🧪 Testing & Quality
* **Automated Smoke Test Suite**: Added `tests/test_sync_engine.py` covering placeholder expansion, deep merge security, workspace deployment, and rule syncing.

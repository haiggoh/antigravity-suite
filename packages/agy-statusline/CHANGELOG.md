# Changelog - Antigravity Status Line (`agy-statusline`)

All notable changes and fork enhancements against upstream `60ke/antigravity-statusline` are documented in this file.

---

## [v1.1.0] - 2026-08-25

### 🚀 Enhancements & Performance
* **Sub-millisecond Direct Loopback Scanner**: Replaced slow external shell commands (`netstat`, `lsof`) with direct TCP loopback socket probing, discovering the local language server in < 2ms.
* **Smart Productivity Tips Engine**: Added non-blocking, rotating productivity tips (e.g. `/goal`, `/grill-me`, `/schedule`) with persisted interval cache.

### 🌐 Cross-Platform & Windows Compatibility
* **Full Windows Support**: Native Windows console initialization (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`) with seamless ANSI color rendering.
* **International Locale Support**: Added regex parsing for localized Windows `netstat` state strings (e.g. `ABHÖREN` on German Windows).
* **Native Windows Installer**: Added `install.ps1` for automated one-command setup in PowerShell.

### 🧹 Directory Standardization
* **Clean Storage Architecture**: Migrated all cache and state files from ad-hoc `~/.antigravity/` to `~/.gemini/cache/statusline/`.
* **Standardized Install Directory**: Updated `install.sh`, `uninstall.sh`, and `install.ps1` to install scripts into `~/.gemini/statusline/` and configuration backups into `~/.gemini/backups/`.

---

## [v1.0.0] - Upstream Base

* Initial status line renderer for Antigravity CLI.
* Token metrics and model display.
* Basic Unix `lsof` language server discovery.

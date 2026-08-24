# agy-sync

The core cross-platform configuration synchronizer and multi-repository workspace engine for **Google Antigravity (AGY)**.

---

## Capabilities

* 🔄 **Universal Multi-Host Sync**: Synchronizes Antigravity CLI and Desktop settings seamlessly across any topology:
  - macOS ⟷ macOS
  - Windows ⟷ Windows (supporting any drive letter: `C:`, `D:`, `E:`, etc.)
  - macOS ⟷ Windows
  - Linux ⟷ macOS / Windows
* 👤 **Account & Auth Isolation**: Machine-local variables (such as active Google login email, session tokens, and `trustedWorkspaces`) are preserved locally and protected from accidental cross-account overwrites.
* 🛡️ **Workspace Multi-Repo Pull with Auto-Stash**: Safely synchronizes all git repositories across your workspace root with automatic uncommitted changes stashing (`--workspace-sync`).
* 📦 **Bi-directional Standalone Fork Sync**: Effortlessly exports and imports suite packages to and from standalone GitHub repositories (`sync_standalone_fork.py`).
* 📁 **Standard Directory Deployment**: Deploys global rules to `~/.gemini/config/rules/` and status lines to `~/.gemini/statusline/`.

---

## Usage

```bash
# Standard sync (CLI & Desktop settings, rules, statusline, workspace root):
python install.py

# Multi-repo workspace sync (pulls all workspace repos with safe autostash):
python install.py --workspace-sync

# Preview changes without modifying files:
python install.py --dry-run
```

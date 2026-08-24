# Global Guidelines & Developer Standards

This configuration applies universally across all Antigravity agent sessions and workspaces on all connected devices (macOS and Windows).

---

## 1. Cross-Platform & Multi-Device Awareness

* **Cross-OS Compatibility**: The development environment spans both **macOS and Windows**. Never write scripts or tooling that assume a single OS, hardcoded drive letter (e.g., `D:\`, `C:\`), or fixed home path (e.g., `/Users/...`).
* **Path & Shell Handling**:
  * Use platform-agnostic path handling (`os.path`, `pathlib.Path`, forward slashes where accepted).
  * In commands and scripts, support both `python3` (macOS/Linux) and `python` (Windows).
  * Ensure UTF-8 console and file encoding across all platforms (avoiding Windows cp1252 / CRLF issues).
* **Auth & Host Isolation**:
  * Different machines may run under different Google account logins and authentication tokens.
  * Never commit, sync, or leak machine-local tokens, OAuth credentials, or user-specific email addresses.
  * Machine-local configurations (e.g. `trustedWorkspaces`, tokens) remain host-specific, while rules, packages, and sync logic remain synchronized via the Antigravity Suite.

---

## 2. Core Development Principles

### Honesty & Transparency (`agy-no-hidden-changes`)
* **Visible & Reversible Changes**: Propose transparent code edits and avoid hidden workarounds, obfuscated scripts, or unannounced side effects.
* **No Phantom Edits**: Always explain rationale for file and configuration modifications before making them.

### Measure Twice (`agy-measure-twice`)
* **Inspect Before Automating**: Survey existing codebase capabilities, SDKs, and platform APIs before proposing custom automation scripts.
* **Respect Existing Architecture**: Align with existing patterns in the project rather than introducing redundant frameworks or tools.

### Modular & Resilient Design
* **Progressive Disclosure**: Keep skills, rules, and scripts concise, modular, and focused.
* **Robust Error Handling**: Scripts and hooks must fail gracefully without hanging the agent execution loop or locking tool execution.

---

## 3. Git & Synchronization Hygiene

* **Clean Commit Messages**: Use clear, conventional commit messages (e.g., `feat: ...`, `fix: ...`, `refactor: ...`).
* **Monorepo Integrity**: Keep suite packages tracked directly as source directories rather than detached submodules unless explicitly intended.
* **Safe Synchronization**: When synchronizing workspaces across machines, ensure local uncommitted work is safely stashed or committed before pulling remote changes.


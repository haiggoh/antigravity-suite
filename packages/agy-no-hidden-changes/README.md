# agy-no-hidden-changes 🛡️

An **Antigravity Rule Plugin** that steers AI agents toward visible, honest, and reversible code modifications — preventing hidden-state workarounds that deceive users or obscure application status.

---

## Directives Overview

- **Visible Outcomes**: Never resolve bugs by suppressing UI elements or zeroing arrays silently.
- **Honest Fallbacks**: Report API and tool call failures transparently instead of returning false successes.
- **Empirical Debugging**: Trace errors back to real logs rather than swallowing exceptions.

---

## Installation

Add to your `~/.gemini/config/plugins.json`:

```json
{
  "entries": [
    { "path": "D:/antigravity/projects/agy-no-hidden-changes" }
  ]
}
```

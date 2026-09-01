# agy-audit-loose-ends

**Durable Record Reconciliation & Secret Audit Engine for Google Antigravity (AGY)**

## Problem
Complex coding sessions often leave stale to-do items in workspace markdown files or risk leaking credentials (API tokens, private keys) into project notes or configuration.

## Solution
`agy-audit-loose-ends` scans workspace records, detects orphaned in-progress items, checks for exposed tokens across 7 major provider patterns, and provides safe, atomic redaction.

## Features
- **Secret Detection**: Scans for Google, Anthropic, OpenAI, GitHub, and Slack keys.
- **Task Reconciliation**: Flags uncompleted WIP/TODO items in `GEMINI.md` and task stores.
- **Fail-Safe & Standard Library**: Standard library only, runs cleanly cross-platform.

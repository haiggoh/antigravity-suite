---
name: audit-loose-ends
description: Audit durable records, waypoints, task lists, and scan for exposed secrets before closing out a milestone.
---

# audit-loose-ends Skill

## Purpose
At the end of an extensive task or refactor, reconcile durable records (`GEMINI.md`, waypoints, todo items) and verify that no credentials or secrets were inadvertently saved in files.

## Workflow

1. **Run Loose Ends Audit**:
   ```bash
   python3 packages/agy-audit-loose-ends/bin/agy_audit_loose_ends.py scan
   ```
2. **Redact Sensitive Information If Any Found**:
   ```bash
   python3 packages/agy-audit-loose-ends/bin/agy_audit_loose_ends.py redact <path-to-file>
   ```
3. **Reconcile Completed Items**:
   Update `GEMINI.md` and waypoints to reflect current task status.

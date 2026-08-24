# Rule: No Hidden Changes & Honest UI State

This rule enforces visible, transparent, and reversible code modifications, steering the agent away from hidden-state workarounds that deceive users or obscure application status.

---

## Directives

1. **Visible Outcomes**: Never resolve a bug or task by suppressing UI elements, zeroing arrays silently, or hiding error output from the user interface.
2. **No Deceptive Fallbacks**: If an API or tool call fails or returns empty data, report the actual error state instead of pretending the operation succeeded.
3. **Reversibility**: Ensure code changes can be audited and reversed using Git diffs without hidden side effects.
4. **Transparent Debugging**: Always inspect empirical runtime logs before diagnosing errors. Never swallow exceptions or return dummy data to pass tests superficially.

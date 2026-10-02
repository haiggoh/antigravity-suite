# Local Agent Offloading Guidelines

## 1. Decide Upfront at Decomposition (Fixing the Catch-22)
* **Eliminate the False Dilemma**: Avoid the trap of classifying tasks as either "too trivial to offload" or "too difficult to offload" (which previously caused 100% of work to remain on expensive cloud models).
* **Upfront Step Annotation**: When decomposing any multi-step task involving file inspections, log analysis, code summaries, mechanical refactoring, or boilerplate generation, explicitly decide where each step runs before executing:
  * `local:operator` — delegated to local Apple Silicon compute ($0 per token).
  * `cloud:<reason>` — kept on the cloud model with the specific rationale named.

## 2. Default to Local Operator
* **Flip the Burden of Proof**: Bulk, repetitive, or mechanical legwork defaults to `local:operator` (Qwen 3.8 / local MLX) unless there is an explicit justification:
  * `cloud:frontier-reasoning` — complex novel architectural design, intricate multi-file logic puzzles, security-critical authentication/crypto.
  * `cloud:final-verification` — final gatekeeper verification, synthesis, and shipping approval.
  * `cloud:not-worth-offloading` — a one-liner micro-operation where briefing overhead exceeds the token saving.
* **Keep Orchestration on Cloud, Delegate Legwork**: The cloud agent acts as the coordinator and evaluator; local compute executes the legwork.

## 3. Supervised Delegation & Ground-Truth Verification
* **Self-Contained Stateless Briefings**: Every local dispatch is stateless. Include the task description, target file paths, and exact output format specification.
* **Verify Against Ground Truth**: Never accept local model outputs blindly. Verify results against observable facts (running tests, checking diffs, inspecting output status).
* **RAM Preflight Enforcement**: Ensure RAM preflight passes before spinning up heavy weights. If unified memory is congested, employ `agy-evict` to reclaim resident memory.

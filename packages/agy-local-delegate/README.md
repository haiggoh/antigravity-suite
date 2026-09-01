# agy-local-delegate

**Local Model Delegation & Apple Silicon MLX Offloading for Google Antigravity (AGY)**

## Overview
Offloads token-heavy operations (large file audits, first-pass code reviews, summaries, formatting) to local Apple Silicon MLX models via OpenAI-compatible endpoints with zero quota consumption.

## Features
- **Model Aliases**: Pre-configured profiles for Qwen 2.5/3.6, DeepSeek R1, Gemma, and Devstral.
- **Context Bundling**: Bounded, safe file attachment packaging with overflow protection.
- **Fail-Safe Dispatch**: Clean error messages and non-blocking fallbacks.
- **CLI & Skill**: Provides `bin/agy_local_delegate.py` and clean skill `local-delegate`.

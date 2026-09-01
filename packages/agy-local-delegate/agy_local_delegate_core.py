"""Pure, unit-testable core for local model delegation (MLX / Apple Silicon / Ollama).

Allows Antigravity sessions to offload mechanical analysis, summaries, reviews,
or code inspections to free local LLMs running via OpenAI-compatible endpoints
(e.g., MLX LM, vLLM-MLX, Ollama, LM Studio).

Design rules:
  * Pure standard library (urllib.request, json), fail-safe.
  * Configurable endpoint via environment (AGY_LOCAL_MODEL_ENDPOINT).
  * Safe file attachments handling with bounded sizes.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/v1"

# Standard local model catalog with capabilities
MODEL_CATALOG = {
    "qwen-3.6-operator": {
        "description": "Fast 27B general-purpose coding & operations model",
        "default_model_id": "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
        "context_window": 32768,
    },
    "qwen-3.6-thinking": {
        "description": "Reasoning model with chain-of-thought capability",
        "default_model_id": "mlx-community/Qwen2.5-32B-Instruct-4bit",
        "context_window": 32768,
    },
    "deepseek-r1-architect": {
        "description": "DeepSeek R1 architecture and complex logic reasoning",
        "default_model_id": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "context_window": 65536,
    },
    "gemma-4-26b": {
        "description": "Google Gemma 4 26B instruction-tuned model",
        "default_model_id": "mlx-community/gemma-2-27b-it-4bit",
        "context_window": 8192,
    },
    "devstral-2-123b": {
        "description": "Heavyweight 123B code refactoring model",
        "default_model_id": "mlx-community/Devstral-Small-24B-v0.1-4bit",
        "context_window": 32768,
    },
    "llama-scout": {
        "description": "Fast low-latency inspection utility model",
        "default_model_id": "mlx-community/Llama-3.2-3B-Instruct-4bit",
        "context_window": 8192,
    },
}


def get_endpoint_url() -> str:
    """Return local OpenAI-compatible API base URL."""
    return os.environ.get("AGY_LOCAL_MODEL_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")


def check_server_health(endpoint: Optional[str] = None, timeout: float = 2.0) -> Dict[str, Any]:
    """Health check local inference server."""
    base_url = endpoint or get_endpoint_url()
    models_url = f"{base_url}/models"
    try:
        req = urllib.request.Request(models_url, headers={"User-Agent": "Antigravity-Local-Delegate"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                return {"online": True, "endpoint": base_url, "available_models": models}
    except Exception as e:
        return {"online": False, "endpoint": base_url, "error": str(e)}
    return {"online": False, "endpoint": base_url, "error": "Unknown status"}


def bundle_file_attachments(filepaths: List[str], max_total_chars: int = 150000) -> str:
    """Read attached files and format as bounded markdown context."""
    if not filepaths:
        return ""
    
    sections = ["\n\n--- ATTACHED FILE CONTEXT ---"]
    current_chars = 0

    for path in filepaths:
        norm_path = os.path.abspath(path)
        if not os.path.isfile(norm_path):
            sections.append(f"\n[Warning: File not found: {path}]")
            continue
        try:
            with open(norm_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if current_chars + len(content) > max_total_chars:
                allowed = max(0, max_total_chars - current_chars)
                content = content[:allowed] + "\n... [Context truncated to prevent overflow] ..."
            sections.append(f"\n### File: `{path}`\n```\n{content}\n```")
            current_chars += len(content)
            if current_chars >= max_total_chars:
                break
        except Exception as e:
            sections.append(f"\n[Error reading file {path}: {e}]")

    return "\n".join(sections)


def build_chat_payload(
    prompt: str,
    model_alias: str = "qwen-3.6-operator",
    files: Optional[List[str]] = None,
    system_instruction: str = "You are a specialized local AI assistant. Provide concise, accurate responses.",
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Construct OpenAI-compatible chat completion request payload."""
    alias_info = MODEL_CATALOG.get(model_alias, MODEL_CATALOG["qwen-3.6-operator"])
    model_id = alias_info["default_model_id"]

    context_text = bundle_file_attachments(files or [])
    full_user_content = prompt + context_text

    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": full_user_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def dispatch_local_prompt(
    prompt: str,
    model_alias: str = "qwen-3.6-operator",
    files: Optional[List[str]] = None,
    endpoint: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """Send prompt to local model endpoint and return parsed response."""
    base_url = endpoint or get_endpoint_url()
    completions_url = f"{base_url}/chat/completions"
    payload = build_chat_payload(prompt, model_alias=model_alias, files=files)

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        completions_url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Antigravity-Local-Delegate",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices", [])
            reply = choices[0]["message"]["content"] if choices else ""
            usage = body.get("usage", {})
            return {
                "success": True,
                "reply": reply,
                "model": payload["model"],
                "usage": usage,
            }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Local model server unreachable at {base_url}: {e.reason}",
            "hint": "Start your local MLX / vLLM / Ollama server on port 8000.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Local inference error: {str(e)}",
        }

"""Pure, unit-testable core for local model delegation (Apple Silicon MLX / Rapid / Ollama).

Allows Antigravity sessions to offload mechanical analysis, summaries, reviews,
or code inspections to free local LLMs running via OpenAI-compatible endpoints
(e.g., Rapid-MLX for MLX, llama.cpp / llama-server for GGUF, Ollama, LM Studio).

Features:
  * Full catalog updated to Qwen 3.8 (replacing Qwen 3.6 as default operator),
    DeepSeek R1, KAT Coder, Gemma 4, Kimi-VL, Devstral, Nemotron, and Llama Scout.
  * Live on-disk model scanner for ~/.models with size and availability reporting.
  * Bounded file context bundler with overflow protection.
  * Pure standard library (urllib.request, json, os), fail-safe.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/v1"
DEFAULT_MODELS_DIR = os.path.expanduser("~/.models")

# Comprehensive local model catalog with capabilities & on-disk directories
MODEL_CATALOG = {
    # --- Qwen 3.8 Series (Default Workhorse) ---
    "qwen-3.8-operator": {
        "description": "Fast 27B general-purpose coding & operations workhorse (Default)",
        "default_model_id": "mlx-community/Qwen3.8-27B-4bit",
        "subdir": "Qwen3.8-27B-4bit",
        "context_window": 32768,
        "is_default": True,
    },
    "qwen-3.8-thinking": {
        "description": "Qwen 3.8 reasoning model with chain-of-thought analysis",
        "default_model_id": "mlx-community/Qwen3.8-27B-4bit",
        "subdir": "Qwen3.8-27B-4bit",
        "context_window": 32768,
    },
    "qwen-3.8-8bit": {
        "description": "Qwen 3.8 27B higher-precision 8-bit operator",
        "default_model_id": "mlx-community/Qwen3.8-27B-8bit",
        "subdir": "Qwen3.8-27B-8bit",
        "context_window": 32768,
    },
    "qwen-3.8-mtp": {
        "description": "Qwen 3.8 with Multi-Token Prediction (MTP) acceleration",
        "default_model_id": "mlx-community/Qwen3.8-27B-MTP-4bit",
        "subdir": "Qwen3.8-27B-MTP-4bit",
        "context_window": 32768,
    },
    "qwen-80b-thinking": {
        "description": "Heavyweight 80B architecture and synthesis model",
        "default_model_id": "mlx-community/Qwen3-Next-80B-A3B-Thinking-4bit",
        "subdir": "qwen3-next-80b-thinking-mlx",
        "context_window": 32768,
    },

    # --- Reasoning & Architecture ---
    "deepseek-r1-architect": {
        "description": "DeepSeek R1 complex architectural reasoning and logic",
        "default_model_id": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "subdir": "DeepSeek-R1-Distill-Qwen-32B-4bit",
        "context_window": 65536,
    },

    # --- Specialized Coding ---
    "kat-coder-optiq": {
        "description": "KAT Coder V2.5 Dev OptiQ specialized code synthesis",
        "default_model_id": "mlx-community/KAT-Coder-V2.5-Dev-OptiQ-4bit",
        "subdir": "KAT-Coder-V2.5-Dev-OptiQ-4bit",
        "context_window": 32768,
    },
    "devstral-2-123b": {
        "description": "Heavyweight 123B code refactoring and translation engine",
        "default_model_id": "mlx-community/Devstral-2-123B-Instruct-2512-4bit",
        "subdir": "Devstral-2-123B-Instruct-2512-4bit",
        "context_window": 32768,
    },

    # --- Multimodal & Vision ---
    "gemma-4-26b": {
        "description": "Google Gemma 4 26B instruction & analysis model",
        "default_model_id": "unsloth/gemma-4-26b-a4b-it-MLX-8bit",
        "subdir": "_override_gemma-4-26b-a4b-it-MLX-8bit",
        "context_window": 8192,
    },
    "kimi-vl-thinking": {
        "description": "Kimi-VL compact multimodal vision & reasoning utility",
        "default_model_id": "mlx-community/Kimi-VL-A3B-Thinking-2506-6bit",
        "subdir": "Kimi-VL-A3B-Thinking-2506-6bit",
        "context_window": 16384,
    },

    # --- Fast Utility & Diagnostics ---
    "ministral-14b": {
        "description": "Ministral 14B fast reasoning & inspection model",
        "default_model_id": "mlx-community/Ministral-3-14B-Reasoning-2512-8bit",
        "subdir": "ministral14-reasoning-8bit",
        "context_window": 16384,
    },
    "nemotron-omni": {
        "description": "NVIDIA Nemotron 3 Nano Omni reasoning model",
        "default_model_id": "mlx-community/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-6bit",
        "subdir": "nemotron-omni-6bit",
        "context_window": 16384,
    },
    "llama-scout": {
        "description": "Llama 4 Scout fast low-latency utility & classification",
        "default_model_id": "mlx-community/Llama-4-Scout-17B-16E-Instruct-4bit",
        "subdir": "Llama-4-Scout-17B-16E-Instruct-4bit",
        "context_window": 8192,
    },
}


def get_endpoint_url() -> str:
    """Return local OpenAI-compatible API base URL."""
    return os.environ.get("AGY_LOCAL_MODEL_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")


def get_models_dir() -> str:
    """Return on-disk models directory path."""
    return os.environ.get("AGY_MODELS_DIR", DEFAULT_MODELS_DIR)


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


def get_directory_size_gb(path: str) -> float:
    """Compute approximate disk size in gigabytes."""
    total_bytes = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_bytes += os.path.getsize(fp)
                except Exception:
                    pass
    except Exception:
        pass
    return round(total_bytes / (1024 ** 3), 1)


def scan_local_models_dir(models_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scan the local model directory on disk and report available models."""
    target_dir = models_dir or get_models_dir()
    installed_catalog = []
    unregistered_models = []

    if not os.path.isdir(target_dir):
        return {
            "models_dir": target_dir,
            "exists": False,
            "installed_catalog": [],
            "unregistered_models": [],
        }

    disk_dirs = set(os.listdir(target_dir))

    # Check catalog entries
    for alias, info in MODEL_CATALOG.items():
        subdir = info.get("subdir", "")
        is_installed = subdir in disk_dirs if subdir else False
        size_gb = 0.0
        if is_installed:
            model_full_path = os.path.join(target_dir, subdir)
            size_gb = get_directory_size_gb(model_full_path)
            installed_catalog.append({
                "alias": alias,
                "description": info["description"],
                "subdir": subdir,
                "size_gb": size_gb,
                "installed": True,
            })

    # Check for models on disk that are not registered in catalog
    catalog_subdirs = {info.get("subdir") for info in MODEL_CATALOG.values() if info.get("subdir")}
    for item in sorted(disk_dirs):
        full_item_path = os.path.join(target_dir, item)
        if os.path.isdir(full_item_path) and not item.startswith("."):
            if item not in catalog_subdirs:
                size_gb = get_directory_size_gb(full_item_path)
                unregistered_models.append({
                    "name": item,
                    "size_gb": size_gb,
                    "path": full_item_path,
                })

    return {
        "models_dir": target_dir,
        "exists": True,
        "installed_catalog": installed_catalog,
        "unregistered_models": unregistered_models,
    }


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
    model_alias: str = "qwen-3.8-operator",
    files: Optional[List[str]] = None,
    system_instruction: str = "You are a specialized local AI assistant. Provide concise, accurate responses.",
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Construct OpenAI-compatible chat completion request payload."""
    alias_info = MODEL_CATALOG.get(model_alias, MODEL_CATALOG["qwen-3.8-operator"])
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
    model_alias: str = "qwen-3.8-operator",
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
            "hint": "Start your local MLX / Rapid / vLLM / Ollama server on port 8000.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Local inference error: {str(e)}",
        }

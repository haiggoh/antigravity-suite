#!/usr/bin/env python3
"""
agy-local-proxy — Gemini API → OpenAI-compatible translation proxy.

Translates Google Gemini generateContent / streamGenerateContent API requests
from AGY CLI into OpenAI chat/completions format and forwards them to a local
inference server (Rapid-MLX for MLX, llama.cpp / llama-server for GGUF, Ollama, etc.).

This enables running any OpenAI-compatible local model as the main AGY engine
by setting GOOGLE_GEMINI_BASE_URL to point here.

Architecture:
  AGY CLI ──(Gemini format)──► agy-local-proxy:9191
                                  │
                              Translation
                                  │
                              ──(OpenAI format)──► Rapid-MLX:8000

Usage:
  # 1. Start your local model server (e.g. rapid-mlx)
  # 2. Run this proxy:
  python3 agy_local_proxy.py [--port 9191] [--upstream http://127.0.0.1:8000/v1] [--model mlx-community/Qwen3.8-27B-4bit]
  # 3. In another shell, start agy:
  GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:9191 agy

Options:
  --port        Port to listen on (default: 9191)
  --upstream    OpenAI-compatible local model base URL (default: http://127.0.0.1:8000/v1)
  --model       Model ID to use (default: mlx-community/Qwen3.8-27B-4bit)
  --timeout     Upstream request timeout in seconds (default: 180)
  --debug       Enable verbose request/response logging
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Gemini → OpenAI Translation Helpers
# ---------------------------------------------------------------------------

def gemini_contents_to_openai_messages(contents: List[Dict]) -> List[Dict]:
    """Convert Gemini 'contents' array to OpenAI 'messages' array."""
    messages = []
    for item in contents:
        role = item.get("role", "user")
        # Gemini roles: "user" | "model" → OpenAI: "user" | "assistant"
        openai_role = "assistant" if role == "model" else "user"
        parts = item.get("parts", [])
        # Concatenate all text parts
        text_parts = []
        for part in parts:
            if isinstance(part, dict):
                if "text" in part:
                    text_parts.append(part["text"])
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    text_parts.append(
                        f"[Function call: {fc.get('name')}({json.dumps(fc.get('args', {}))})]"
                    )
                elif "functionResponse" in part:
                    fr = part["functionResponse"]
                    text_parts.append(
                        f"[Function result for {fr.get('name')}: {json.dumps(fr.get('response', {}))}]"
                    )
            elif isinstance(part, str):
                text_parts.append(part)
        messages.append({"role": openai_role, "content": "\n".join(text_parts)})
    return messages


def gemini_request_to_openai(body: Dict, model_id: str) -> Dict:
    """Translate a Gemini generateContent request body to OpenAI chat.completions."""
    contents = body.get("contents", [])
    messages = gemini_contents_to_openai_messages(contents)

    # Extract system instruction if present
    system_instruction = body.get("systemInstruction", {})
    if system_instruction:
        sys_parts = system_instruction.get("parts", [])
        sys_texts = [p.get("text", "") for p in sys_parts if isinstance(p, dict) and "text" in p]
        sys_text = "\n".join(sys_texts)
        if sys_text:
            messages.insert(0, {"role": "system", "content": sys_text})

    # Generation config
    gen_config = body.get("generationConfig", {})
    max_tokens = gen_config.get("maxOutputTokens", 8192)
    temperature = gen_config.get("temperature", 0.2)
    top_p = gen_config.get("topP", None)
    stop_sequences = gen_config.get("stopSequences", None)

    oai_payload: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if top_p is not None:
        oai_payload["top_p"] = top_p
    if stop_sequences:
        oai_payload["stop"] = stop_sequences

    return oai_payload


def openai_response_to_gemini(oai_resp: Dict) -> Dict:
    """Translate an OpenAI chat.completions response to Gemini generateContent format."""
    choices = oai_resp.get("choices", [])
    candidates = []
    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content", "")
        finish_reason = choice.get("finish_reason", "stop")
        # Map OpenAI finish reasons to Gemini
        gemini_finish = {
            "stop": "STOP",
            "length": "MAX_TOKENS",
            "content_filter": "SAFETY",
        }.get(finish_reason, "STOP")

        candidates.append({
            "content": {
                "parts": [{"text": content}],
                "role": "model",
            },
            "finishReason": gemini_finish,
            "index": choice.get("index", 0),
        })

    usage = oai_resp.get("usage", {})
    return {
        "candidates": candidates,
        "usageMetadata": {
            "promptTokenCount": usage.get("prompt_tokens", 0),
            "candidatesTokenCount": usage.get("completion_tokens", 0),
            "totalTokenCount": usage.get("total_tokens", 0),
        },
        "modelVersion": oai_resp.get("model", "local"),
    }


def make_gemini_models_response(model_id: str) -> Dict:
    """Return a minimal Gemini /v1beta/models list with our local model."""
    friendly_name = model_id.split("/")[-1] if "/" in model_id else model_id
    return {
        "models": [
            {
                "name": f"models/{model_id}",
                "baseModelId": model_id,
                "version": "001",
                "displayName": f"Local: {friendly_name}",
                "description": f"Local OpenAI-compatible model via agy-local-proxy ({model_id})",
                "inputTokenLimit": 32768,
                "outputTokenLimit": 8192,
                "supportedGenerationMethods": ["generateContent", "streamGenerateContent"],
                "temperature": 0.2,
                "maxTemperature": 2.0,
                "topP": 0.95,
                "topK": 40,
            }
        ]
    }


# ---------------------------------------------------------------------------
# HTTP Proxy Request Handler
# ---------------------------------------------------------------------------

class GeminiToOpenAIHandler(BaseHTTPRequestHandler):
    """HTTP handler that accepts Gemini API requests and proxies them as OpenAI."""

    upstream_url: str = "http://127.0.0.1:8000/v1"
    model_id: str = "mlx-community/Qwen3.8-27B-4bit"
    timeout: int = 180
    debug: bool = False

    def log_message(self, format, *args):
        if self.debug:
            super().log_message(format, *args)
        else:
            pass  # Suppress per-request httpd noise

    def send_json(self, status: int, data: Dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        # Models list — used by `agy models` and model selection
        if path in ("/v1beta/models", "/v1/models", "/v1beta/models:list", "/models"):
            self.send_json(200, make_gemini_models_response(self.model_id))
        elif path == "/health":
            self.send_json(200, {"status": "ok", "upstream": self.upstream_url, "model": self.model_id})
        else:
            self.send_json(404, {"error": f"Not found: {self.path}"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as e:
            self.send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        if self.debug:
            print(f"\n[proxy] → Incoming Gemini POST {path}")
            print(f"[proxy]   Body: {json.dumps(body, indent=2)[:500]}")

        # Handle generateContent and streamGenerateContent
        if "generateContent" in path or "streamGenerateContent" in path:
            self._proxy_generate_content(body, stream="stream" in path.lower())
        else:
            self.send_json(404, {"error": f"Unsupported path: {self.path}"})

    def _proxy_generate_content(self, gemini_body: Dict, stream: bool = False):
        """Translate Gemini request → OpenAI → translate response back to Gemini."""
        oai_payload = gemini_request_to_openai(gemini_body, self.model_id)
        oai_payload["stream"] = False  # Always non-streaming to upstream for simplicity

        if self.debug:
            print(f"[proxy] → OpenAI payload: {json.dumps(oai_payload, indent=2)[:500]}")

        upstream_completions = f"{self.upstream_url.rstrip('/')}/chat/completions"
        req_data = json.dumps(oai_payload).encode("utf-8")
        req = urllib.request.Request(
            upstream_completions,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer local",  # Some servers require a token
                "User-Agent": "agy-local-proxy/1.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                oai_resp = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
            if self.debug:
                print(f"[proxy] ✗ Upstream HTTP error {e.code}: {err_body}")
            self.send_json(502, {
                "error": {"message": f"Upstream error {e.code}: {err_body}", "code": e.code}
            })
            return
        except Exception as e:
            if self.debug:
                print(f"[proxy] ✗ Upstream error: {e}")
            self.send_json(503, {
                "error": {"message": f"Local model server unreachable: {e}", "status": "unavailable"}
            })
            return

        if self.debug:
            print(f"[proxy] ← OpenAI response: {json.dumps(oai_resp, indent=2)[:500]}")

        gemini_resp = openai_response_to_gemini(oai_resp)

        if self.debug:
            print(f"[proxy] → Gemini response: {json.dumps(gemini_resp, indent=2)[:300]}")

        self.send_json(200, gemini_resp)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="agy-local-proxy — Gemini API to OpenAI local model proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--port", type=int, default=9191, help="Port to listen on (default: 9191)")
    parser.add_argument("--upstream", default="http://127.0.0.1:8000/v1",
                        help="OpenAI-compatible upstream base URL (default: http://127.0.0.1:8000/v1)")
    parser.add_argument("--model", default="mlx-community/Qwen3.8-27B-4bit",
                        help="Model ID to request from upstream (default: mlx-community/Qwen3.8-27B-4bit)")
    parser.add_argument("--timeout", type=int, default=180,
                        help="Upstream timeout in seconds (default: 180)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Patch class-level config
    GeminiToOpenAIHandler.upstream_url = args.upstream
    GeminiToOpenAIHandler.model_id = args.model
    GeminiToOpenAIHandler.timeout = args.timeout
    GeminiToOpenAIHandler.debug = args.debug

    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("127.0.0.1", args.port), GeminiToOpenAIHandler)

    print(f"┌─────────────────────────────────────────────────────────┐")
    print(f"│  agy-local-proxy                                         │")
    print(f"│  Gemini API  →  OpenAI-compatible translation proxy      │")
    print(f"├─────────────────────────────────────────────────────────┤")
    print(f"│  Listening on:  http://127.0.0.1:{args.port:<29}│")
    print(f"│  Upstream:      {args.upstream:<41}│")
    print(f"│  Model:         {args.model:<41}│")
    print(f"│  Timeout:       {args.timeout}s{' ' * 39}│")
    print(f"├─────────────────────────────────────────────────────────┤")
    print(f"│  To use with AGY:                                        │")
    print(f"│  GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:{args.port} agy    │")
    print(f"└─────────────────────────────────────────────────────────┘")
    print(f"\nProxy ready. Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[proxy] Stopped.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()

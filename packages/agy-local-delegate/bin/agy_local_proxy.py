#!/usr/bin/env python3
"""Gemini API to OpenAI-compatible local inference proxy for AGY."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple


def _text_from_parts(parts: List[Any]) -> str:
    texts = []
    for part in parts:
        if isinstance(part, str):
            texts.append(part)
        elif isinstance(part, dict) and "text" in part:
            texts.append(str(part.get("text", "")))
    return "\n".join(text for text in texts if text)


def _json_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def gemini_contents_to_openai_messages(contents: List[Dict]) -> List[Dict]:
    """Convert Gemini conversation contents, including tool history."""
    messages: List[Dict] = []
    pending_ids: Dict[str, deque] = defaultdict(deque)
    call_index = 0

    for item in contents:
        role = item.get("role", "user")
        parts = item.get("parts", []) or []
        text = _text_from_parts(parts)
        function_calls = [p["functionCall"] for p in parts if isinstance(p, dict) and "functionCall" in p]
        function_responses = [p["functionResponse"] for p in parts if isinstance(p, dict) and "functionResponse" in p]

        if role == "model":
            message: Dict[str, Any] = {"role": "assistant", "content": text or None}
            if function_calls:
                tool_calls = []
                for call in function_calls:
                    call_index += 1
                    name = str(call.get("name", "unknown_tool"))
                    call_id = str(call.get("id") or f"call_{call_index}")
                    pending_ids[name].append(call_id)
                    arguments = call.get("args", {})
                    tool_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": arguments if isinstance(arguments, str) else json.dumps(arguments),
                        },
                    })
                message["tool_calls"] = tool_calls
            messages.append(message)
            continue

        if text:
            messages.append({"role": "user", "content": text})

        for response in function_responses:
            name = str(response.get("name", "unknown_tool"))
            call_id = response.get("id")
            if not call_id and pending_ids[name]:
                call_id = pending_ids[name].popleft()
            if not call_id:
                call_index += 1
                call_id = f"call_{call_index}"
            messages.append({
                "role": "tool",
                "tool_call_id": str(call_id),
                "name": name,
                "content": _json_content(response.get("response", {})),
            })

        if not text and not function_responses and parts:
            messages.append({"role": "user", "content": _json_content(parts)})

    return messages


def _normalize_json_schema(value: Any) -> Any:
    """Normalize Gemini Schema type names for OpenAI-compatible servers."""
    if isinstance(value, dict):
        normalized = {key: _normalize_json_schema(item) for key, item in value.items()}
        schema_type = normalized.get("type")
        if isinstance(schema_type, str):
            normalized["type"] = schema_type.lower()
        return normalized
    if isinstance(value, list):
        return [_normalize_json_schema(item) for item in value]
    return value


def _convert_tools(body: Dict) -> List[Dict]:
    tools: List[Dict] = []
    for tool_group in body.get("tools", []) or []:
        declarations = tool_group.get("functionDeclarations") or tool_group.get("function_declarations") or []
        for declaration in declarations:
            function: Dict[str, Any] = {
                "name": declaration.get("name", "unknown_tool"),
                "description": declaration.get("description", ""),
                "parameters": _normalize_json_schema(
                    declaration.get("parameters") or {"type": "object", "properties": {}}
                ),
            }
            tools.append({"type": "function", "function": function})
    return tools


def gemini_request_to_openai(body: Dict, model_id: str) -> Dict:
    messages = gemini_contents_to_openai_messages(body.get("contents", []) or [])

    system_instruction = body.get("systemInstruction") or body.get("system_instruction") or {}
    if isinstance(system_instruction, str):
        system_text = system_instruction
    else:
        system_text = _text_from_parts(system_instruction.get("parts", []) or [])
    if system_text:
        messages.insert(0, {"role": "system", "content": system_text})

    generation = body.get("generationConfig") or body.get("generation_config") or {}
    payload: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "max_tokens": generation.get("maxOutputTokens", generation.get("max_output_tokens", 8192)),
        "temperature": generation.get("temperature", 0.2),
    }
    if generation.get("topP", generation.get("top_p")) is not None:
        payload["top_p"] = generation.get("topP", generation.get("top_p"))
    stop = generation.get("stopSequences", generation.get("stop_sequences"))
    if stop:
        payload["stop"] = stop

    tools = _convert_tools(body)
    if tools:
        payload["tools"] = tools
        config = body.get("toolConfig") or body.get("tool_config") or {}
        calling = config.get("functionCallingConfig") or config.get("function_calling_config") or {}
        mode = str(calling.get("mode", "AUTO")).upper()
        allowed = calling.get("allowedFunctionNames") or calling.get("allowed_function_names") or []
        if mode == "NONE":
            payload["tool_choice"] = "none"
        elif len(allowed) == 1:
            payload["tool_choice"] = {"type": "function", "function": {"name": allowed[0]}}
        elif mode == "ANY":
            payload["tool_choice"] = "required"
    return payload


def _openai_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, str):
                texts.append(part)
            elif isinstance(part, dict):
                texts.append(str(part.get("text", part.get("content", ""))))
        return "".join(texts)
    return "" if content is None else str(content)


def openai_response_to_gemini(response: Dict) -> Dict:
    candidates = []
    for choice in response.get("choices", []) or []:
        message = choice.get("message", {}) or {}
        parts: List[Dict] = []
        text = _openai_content_to_text(message.get("content"))
        if text:
            parts.append({"text": text})
        for tool_call in message.get("tool_calls", []) or []:
            function = tool_call.get("function", {}) or {}
            raw_args = function.get("arguments", {})
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {"_raw": raw_args}
            else:
                args = raw_args
            call: Dict[str, Any] = {"name": function.get("name", "unknown_tool"), "args": args}
            if tool_call.get("id"):
                call["id"] = tool_call["id"]
            parts.append({"functionCall": call})
        if not parts:
            parts.append({"text": ""})

        finish_reason = choice.get("finish_reason", "stop")
        finish = {
            "stop": "STOP",
            "length": "MAX_TOKENS",
            "content_filter": "SAFETY",
            "tool_calls": "STOP",
        }.get(finish_reason, "STOP")
        candidates.append({
            "content": {"parts": parts, "role": "model"},
            "finishReason": finish,
            "index": choice.get("index", 0),
        })

    usage = response.get("usage", {}) or {}
    return {
        "candidates": candidates,
        "usageMetadata": {
            "promptTokenCount": usage.get("prompt_tokens", 0),
            "candidatesTokenCount": usage.get("completion_tokens", 0),
            "totalTokenCount": usage.get("total_tokens", 0),
        },
        "modelVersion": response.get("model", "local"),
    }


def make_gemini_models_response(model_id: str) -> Dict:
    friendly = model_id.split("/")[-1]
    return {"models": [{
        "name": f"models/{friendly}",
        "baseModelId": model_id,
        "version": "local",
        "displayName": f"Local: {friendly}",
        "description": f"Local model via agy-local-proxy ({model_id})",
        "inputTokenLimit": 32768,
        "outputTokenLimit": 8192,
        "supportedGenerationMethods": ["generateContent", "streamGenerateContent"],
    }]}


class GeminiToOpenAIHandler(BaseHTTPRequestHandler):
    upstream_url = "http://127.0.0.1:8000/v1"
    model_id = "default"
    timeout = 180
    debug = False
    request_count = 0

    def log_message(self, fmt, *args):
        if self.debug:
            super().log_message(fmt, *args)

    def _write(self, status: int, data: Dict, content_type: str = "application/json") -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, status: int, data: Dict) -> None:
        self._write(status, data)

    def send_sse(self, data: Dict) -> None:
        body = ("data: " + json.dumps(data, ensure_ascii=False) + "\n\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    @classmethod
    def upstream_health(cls) -> Tuple[bool, Dict]:
        url = f"{cls.upstream_url.rstrip('/')}/models"
        request = urllib.request.Request(url, headers={"Authorization": "Bearer local"})
        try:
            with urllib.request.urlopen(request, timeout=min(cls.timeout, 3)) as response:
                data = json.loads(response.read().decode("utf-8"))
            models = [item.get("id") for item in data.get("data", []) if item.get("id")]
            return True, {"models": models}
        except Exception as exc:
            return False, {"error": str(exc)}

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/health":
            online, detail = self.upstream_health()
            data = {
                "status": "ok" if online else "unavailable",
                "component": "agy-local-proxy",
                "upstream": self.upstream_url,
                "model": self.model_id,
                "requests": type(self).request_count,
                **detail,
            }
            self.send_json(200 if online else 503, data)
        elif path in ("/v1beta/models", "/v1/models", "/v1beta/models:list", "/models"):
            self.send_json(200, make_gemini_models_response(self.model_id))
        elif path.startswith("/v1beta/models/") and ":" not in path:
            self.send_json(200, make_gemini_models_response(self.model_id)["models"][0])
        else:
            self.send_json(404, {"error": {"message": f"Not found: {self.path}"}})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        supported_generation = "generateContent" in path or "streamGenerateContent" in path
        supported_count = "countTokens" in path
        if not supported_generation and not supported_count:
            self.send_json(404, {"error": {"message": f"Unsupported path: {self.path}"}})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self.send_json(400, {"error": {"message": f"Invalid JSON: {exc}"}})
            return

        if supported_count:
            # AGY uses this for budgeting. This dependency-free approximation is
            # deliberately conservative; actual generation still uses Rapid-MLX.
            serialized = json.dumps(body.get("contents", []), ensure_ascii=False)
            estimated = max(1, (len(serialized) + 2) // 3)
            self.send_json(200, {"totalTokens": estimated})
            return

        type(self).request_count += 1
        stream = "streamGenerateContent" in path
        payload = gemini_request_to_openai(body, self.model_id)
        payload["stream"] = False
        if self.debug:
            print(f"[proxy] request #{type(self).request_count}: {path}", file=sys.stderr)
            print(json.dumps(payload, indent=2)[:2000], file=sys.stderr)

        request = urllib.request.Request(
            f"{self.upstream_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer local",
                "User-Agent": "agy-local-proxy/0.2",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                upstream = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            self.send_json(502, {"error": {"message": f"Upstream HTTP {exc.code}: {error_body}"}})
            return
        except Exception as exc:
            self.send_json(503, {"error": {"message": f"Local model server unreachable: {exc}"}})
            return

        translated = openai_response_to_gemini(upstream)
        if stream:
            self.send_sse(translated)
        else:
            self.send_json(200, translated)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini-to-OpenAI local model proxy")
    parser.add_argument("--port", type=int, default=9191)
    parser.add_argument("--upstream", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", default="default")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    GeminiToOpenAIHandler.upstream_url = args.upstream.rstrip("/")
    GeminiToOpenAIHandler.model_id = args.model
    GeminiToOpenAIHandler.timeout = args.timeout
    GeminiToOpenAIHandler.debug = args.debug
    GeminiToOpenAIHandler.request_count = 0

    ThreadingHTTPServer.allow_reuse_address = True
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), GeminiToOpenAIHandler)
    except OSError as exc:
        print(f"[proxy] Cannot bind 127.0.0.1:{args.port}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(f"[proxy] listening=http://127.0.0.1:{args.port} upstream={args.upstream} model={args.model}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

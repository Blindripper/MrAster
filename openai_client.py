"""Shared OpenAI client utilities for the dashboard and trading bot."""
from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    httpx = None  # type: ignore


class OpenAIError(RuntimeError):
    """Light-weight transport error raised by :class:`OpenAIClient`."""

    def __init__(self, status_code: int, message: str, *, payload: Optional[dict] = None) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"OpenAI error {status_code}: {message}")

    @property
    def should_retry_without_temperature(self) -> bool:
        if self.status_code != 400 or not isinstance(self.payload, dict):
            return False
        error = self.payload.get("error")
        if not isinstance(error, dict):
            return False
        message = str(error.get("message") or "").lower()
        return "temperature" in message and "default" in message

    @property
    def allows_legacy_fallback(self) -> bool:
        return self.status_code in {400, 404, 415, 422}


@dataclass(frozen=True)
class ModelTraits:
    """Capabilities associated with a specific model."""

    legacy_supported: bool = True
    modalities: Optional[Iterable[str]] = None
    reasoning: Optional[Dict[str, Any]] = None


def _normalise_model_name(model: str) -> str:
    return (model or "").strip().lower()


def model_traits(model: str) -> ModelTraits:
    normalized = _normalise_model_name(model)
    traits = ModelTraits()
    if not normalized:
        return traits
    if normalized.startswith("gpt-5") or normalized.startswith("o4"):
        return ModelTraits(legacy_supported=False, modalities=("text",), reasoning={"effort": "medium"})
    if normalized.startswith("o3"):
        return ModelTraits(legacy_supported=False, modalities=("text",), reasoning={"effort": "medium"})
    if normalized.startswith("o1"):
        return ModelTraits(legacy_supported=False, modalities=("text",), reasoning={"effort": "medium"})
    if normalized.startswith("gpt-4.1"):
        return ModelTraits(legacy_supported=True, modalities=("text",))
    return traits


def beta_header_for_model(model: str) -> Optional[str]:
    normalized = _normalise_model_name(model)
    requirements = (
        ("gpt-5", "gpt-5"),
        ("gpt-4.1", "gpt-4.1"),
        ("o4", "o4"),
        ("o3", "o3"),
        ("o1", "reasoning"),
    )
    for prefix, header in requirements:
        if normalized.startswith(prefix):
            return header
    return None


def build_responses_input(messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    normalized_input: List[Dict[str, Any]] = []
    system_chunks: List[str] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip() or "user"
        raw_content = item.get("content")
        content_parts: List[Dict[str, str]] = []
        if isinstance(raw_content, str):
            stripped = raw_content.strip()
            if stripped:
                content_parts.append({"type": "text", "text": stripped})
        elif isinstance(raw_content, list):
            for part in raw_content:
                if isinstance(part, dict):
                    chunk_type = str(part.get("type") or "text")
                    if chunk_type in {"input_text", "output_text"}:
                        chunk_type = "text"
                    text_val = part.get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        content_parts.append({"type": chunk_type, "text": text_val.strip()})
                elif isinstance(part, str) and part.strip():
                    content_parts.append({"type": "text", "text": part.strip()})
        if not content_parts:
            continue
        if role == "system":
            for part in content_parts:
                if part.get("type") == "text":
                    system_chunks.append(part.get("text", ""))
            continue
        normalized_input.append({"role": role, "content": content_parts})

    system_prompt = "\n\n".join(chunk.strip() for chunk in system_chunks if str(chunk).strip())
    if system_prompt:
        normalized_input.insert(
            0,
            {
                "role": "system",
                "content": [{"type": "text", "text": system_prompt}],
            },
        )
    return normalized_input, system_prompt


def _extract_text_from_responses(data: Dict[str, Any]) -> str:
    output = data.get("output")
    if isinstance(output, list):
        for block in output:
            if not isinstance(block, dict):
                continue
            content = block.get("content")
            if isinstance(content, list):
                for segment in content:
                    if not isinstance(segment, dict):
                        continue
                    seg_type = str(segment.get("type") or "").lower()
                    if seg_type in {"text", "output_text", "message"}:
                        text_val = segment.get("text")
                        if isinstance(text_val, str):
                            return text_val
                        if isinstance(text_val, dict):
                            nested = text_val.get("value")
                            if isinstance(nested, str):
                                return nested
            elif isinstance(content, dict):
                text_val = content.get("text")
                if isinstance(text_val, str):
                    return text_val
    return ""


def _extract_text_from_legacy(data: Dict[str, Any]) -> str:
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""


def is_responses_unsupported_error(payload: Optional[Dict[str, Any]]) -> bool:
    """Return ``True`` if an error payload signals responses API incompatibility."""

    if not isinstance(payload, dict):
        return False

    error = payload.get("error")
    if not isinstance(error, dict):
        return False

    message = str(error.get("message") or "").lower()
    code = str(error.get("code") or "").lower()
    param = str(error.get("param") or "").lower()

    incompatible_keywords = (
        "does not support the responses api",
        "does not support the responses endpoint",
        "is not currently supported on the responses api",
        "use the chat.completions endpoint",
        "chat completions api instead",
        "beta responses api is not enabled",
        "responses api is not enabled",
        "responses api is not available",
        "responses api is disabled",
        "not allowed to use the responses api",
        "does not have access to the responses api",
    )

    if any(keyword in message for keyword in incompatible_keywords):
        return True

    if "responses" in message and "unsupported" in message:
        return True

    if "responses" in message and "only available" in message and "chat" in message:
        return True

    if "responses api" in message and "access" in message and "denied" in message:
        return True

    if code in {"model_not_supported", "model_not_enabled", "model_not_found"} and "responses" in message:
        return True

    if param == "response_format" and "not supported" in message:
        return True

    return False


class OpenAIClient:
    """Async OpenAI client shared between components."""

    def __init__(
        self,
        api_key: str,
        *,
        default_model: str = "gpt-4o",
        timeout: float = 30.0,
        max_connections: int = 8,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.default_model = default_model or "gpt-4o"
        self.timeout = timeout
        self.max_connections = max(1, int(max_connections or 1))
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        self._client: Optional[httpx.AsyncClient] = None
        self._responses_available: Dict[str, bool] = {}

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _client_instance(self) -> httpx.AsyncClient:
        if httpx is None:  # pragma: no cover - defensive guard
            raise RuntimeError(
                "httpx is required for OpenAIClient; install httpx>=0.26 or add it to your environment."
            )
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com",
                timeout=self.timeout,
                headers=headers,
                limits=httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_connections,
                ),
            )
        return self._client

    async def _post_json(self, path: str, payload: Dict[str, Any], model: str) -> Dict[str, Any]:
        client = await self._client_instance()
        beta_header = beta_header_for_model(model)
        request_headers: Dict[str, str] = {}
        traits = model_traits(model)
        if beta_header:
            request_headers["OpenAI-Beta"] = beta_header
        if traits.modalities:
            payload.setdefault("modalities", list(traits.modalities))
        if traits.reasoning:
            payload.setdefault("reasoning", traits.reasoning)
        response = await client.post(path, json=payload, headers=request_headers or None)
        if response.status_code >= 400:
            try:
                body = response.json()
            except ValueError:
                body = {"error": {"message": response.text}}
            raise OpenAIError(response.status_code, response.text[:160], payload=body)
        try:
            return response.json()
        except ValueError as exc:
            raise OpenAIError(response.status_code, f"Invalid JSON response: {exc}") from exc

    async def acreate(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
        active_model = model or self.default_model
        normalized_messages, _ = build_responses_input(messages)
        if not normalized_messages:
            raise ValueError("No messages to send to OpenAI")

        payload: Dict[str, Any] = {
            "model": active_model,
            "input": normalized_messages,
        }
        if response_format:
            payload["response_format"] = response_format
        else:
            payload["response_format"] = {"type": "text"}
        if metadata:
            payload["metadata"] = metadata
        if max_output_tokens:
            payload["max_output_tokens"] = int(max_output_tokens)
        if temperature is not None:
            payload["temperature"] = float(temperature)

        data = await self._post_json("/v1/responses", payload, active_model)
        text = _extract_text_from_responses(data)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else data.get("usage")
        if isinstance(usage, dict):
            usage = dict(usage)
        else:
            usage = None
        return text, usage, data

    async def _legacy_chat_completion(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: Optional[float],
    ) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
        normalized_messages, _ = build_responses_input(messages)
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": entry["role"],
                    "content": entry["content"][0]["text"],
                }
                if entry.get("content")
                else {"role": entry.get("role", "user"), "content": ""}
                for entry in normalized_messages
            ],
        }
        if temperature is not None:
            payload["temperature"] = float(temperature)

        client = await self._client_instance()
        response = await client.post("/v1/chat/completions", json=payload)
        if response.status_code >= 400:
            raise OpenAIError(response.status_code, response.text[:160])

        data = response.json()
        text = _extract_text_from_legacy(data)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
        return text, usage, data

    async def _acreate_with_fallback(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
        active_model = model or self.default_model
        traits = model_traits(active_model)
        use_responses = self._responses_available.get(active_model, True)

        if use_responses:
            try:
                result = await self.acreate(
                    messages=messages,
                    model=active_model,
                    temperature=temperature,
                    response_format=response_format,
                    metadata=metadata,
                    max_output_tokens=max_output_tokens,
                )
                self._responses_available[active_model] = True
                return result
            except OpenAIError as exc:
                if exc.should_retry_without_temperature and temperature is not None:
                    return await self._acreate_with_fallback(
                        messages=messages,
                        model=active_model,
                        temperature=None,
                        response_format=response_format,
                        metadata=metadata,
                        max_output_tokens=max_output_tokens,
                    )
                disable_responses = False
                if traits.legacy_supported:
                    if is_responses_unsupported_error(exc.payload):
                        disable_responses = True
                    elif exc.status_code in {400, 404, 415, 422}:
                        disable_responses = True
                if disable_responses:
                    self._responses_available[active_model] = False
                if not traits.legacy_supported or (not exc.allows_legacy_fallback and not disable_responses):
                    raise

        return await self._legacy_chat_completion(
            messages=messages,
            model=active_model,
            temperature=temperature,
        )

    def submit(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_output_tokens: Optional[int] = None,
    ) -> "concurrent.futures.Future[Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]]":
        import concurrent.futures

        coro = self._acreate_with_fallback(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
            metadata=metadata,
            max_output_tokens=max_output_tokens,
        )
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def close(self) -> None:
        async def _shutdown() -> None:
            if self._client is not None:
                await self._client.aclose()
        asyncio.run_coroutine_threadsafe(_shutdown(), self._loop).result(timeout=2)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=2)


__all__ = [
    "OpenAIClient",
    "OpenAIError",
    "ModelTraits",
    "model_traits",
    "beta_header_for_model",
    "build_responses_input",
    "is_responses_unsupported_error",
]


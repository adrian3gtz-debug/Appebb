"""Explicit backend provider selection; credentials never enter API responses."""

from dataclasses import dataclass, field
import os
from typing import Literal
from urllib.parse import urlsplit

from fastapi import HTTPException
import httpx

AIProvider = Literal["azure_openai", "groq"]
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


@dataclass(frozen=True)
class ProviderSettings:
    generation: AIProvider
    endpoint: str
    key: str = field(repr=False)
    model: str


def settings() -> ProviderSettings:
    # Preserve existing Azure installations unless a provider is explicitly selected.
    provider = os.getenv("AI_PROVIDER", "azure_openai").strip()
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY", "").strip()
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        if not key or not model:
            raise HTTPException(503, "AI is not configured")
        # Both support strict JSON Schema and the same reasoning parameters.
        if model not in ("openai/gpt-oss-120b", "openai/gpt-oss-20b"):
            raise HTTPException(503, "AI configuration is invalid")
        return ProviderSettings("groq", GROQ_ENDPOINT, key, model)
    if provider != "azure_openai":
        raise HTTPException(503, "AI configuration is invalid")
    endpoint = os.getenv("AZURE_OPENAI_RESPONSES_ENDPOINT", "").strip()
    key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "football-insights").strip()
    if not endpoint or not key or not deployment:
        raise HTTPException(503, "AI is not configured")
    try:
        url = urlsplit(endpoint)
        valid = (url.scheme == "https" and url.hostname
            and url.hostname.endswith((".services.ai.azure.com", ".openai.azure.com"))
            and url.path == "/openai/v1/responses" and not url.query and not url.fragment
            and not url.username and not url.password and url.port in (None, 443))
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(503, "AI configuration is invalid")
    return ProviderSettings("azure_openai", endpoint, key, deployment)


async def request_completion(endpoint: str, key: str, model: str, facts: str,
                             instructions: str, schema: dict, max_output_tokens: int) -> str:
    if endpoint == GROQ_ENDPOINT:
        headers = {"Authorization": f"Bearer {key}"}
        body = {
            "model": model,
            "messages": [{"role": "system", "content": instructions},
                         {"role": "user", "content": facts}],
            # This budget includes reasoning tokens, which are never displayed.
            "max_completion_tokens": max(4096, max_output_tokens),
            "reasoning_effort": "low", "include_reasoning": False,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "explanation", "strict": True, "schema": schema}},
        }
    else:
        headers = {"api-key": key}
        body = {
            "model": model, "store": False, "instructions": instructions,
            "input": facts, "max_output_tokens": max_output_tokens,
            "reasoning": {"effort": "minimal"},
            "text": {"format": {"type": "json_schema", "name": "explanation",
                "strict": True, "schema": schema}},
        }
    async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5), follow_redirects=False) as client:
        response = await client.post(endpoint, headers=headers, json=body)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Invalid response")
    if endpoint == GROQ_ENDPOINT:
        choices = payload.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValueError("Missing completion")
        choice = choices[0]
        message = choice.get("message")
        if (choice.get("finish_reason") != "stop" or not isinstance(message, dict)
                or message.get("role") != "assistant" or message.get("refusal")
                or message.get("tool_calls")):
            raise ValueError("Incomplete response")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Missing completion text")
        return content
    if payload.get("status") != "completed":
        raise ValueError("Incomplete response")
    return "".join(part["text"] for item in payload.get("output", [])
                   if item.get("type") == "message" and item.get("role") == "assistant"
                   for part in item.get("content", []) if part.get("type") == "output_text")

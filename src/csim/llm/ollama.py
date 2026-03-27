"""Ollama local model provider."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from csim.llm.base import LLMProvider


# Preferred models in priority order
_PREFERRED_MODELS = [
    "llama3.1:8b",
    "llama3.2:8b",
    "mistral:7b",
    "gemma2:9b",
    "llama3.1:8b-instruct",
]


class OllamaProvider(LLMProvider):
    """HTTP client to local Ollama daemon."""

    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt: str, max_tokens: int = 300) -> str:
        # Use synchronous urllib to avoid httpx dependency for now;
        # wrap in asyncio if needed later.
        import asyncio
        return await asyncio.to_thread(self._generate_sync, prompt, max_tokens)

    def _generate_sync(self, prompt: str, max_tokens: int) -> str:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["response"].strip()

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return self.model in models
        except Exception:
            return False

    def model_name(self) -> str:
        return f"ollama/{self.model}"


def detect_ollama(base_url: str = "http://localhost:11434") -> OllamaProvider | None:
    """Check if Ollama is running and has a usable model."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]

        for model in _PREFERRED_MODELS:
            if model in models:
                return OllamaProvider(model=model, base_url=base_url)

        if models:
            return OllamaProvider(model=models[0], base_url=base_url)

        return None
    except Exception:
        return None

"""Anthropic Claude provider. Used for export-library, not runtime."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from csim.llm.base import LLMProvider


def _load_dotenv_key() -> str:
    """Read ANTHROPIC_API_KEY from .env file if it exists."""
    from pathlib import Path
    for candidate in [Path.cwd() / ".env", Path(__file__).parents[3] / ".env"]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    return ""


class ClaudeProvider(LLMProvider):
    """Anthropic API client for high-quality narration generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "") or _load_dotenv_key()
        self.model = model

    async def generate(self, prompt: str, max_tokens: int = 300) -> str:
        import asyncio
        return await asyncio.to_thread(self._generate_sync, prompt, max_tokens)

    def _generate_sync(self, prompt: str, max_tokens: int) -> str:
        payload = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": self.api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"].strip()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def model_name(self) -> str:
        return f"claude/{self.model}"

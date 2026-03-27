"""No-op provider. Simulation runs without narration."""

from __future__ import annotations

from csim.llm.base import LLMProvider


class NullProvider(LLMProvider):
    async def generate(self, prompt: str, max_tokens: int = 300) -> str:
        return ""

    def is_available(self) -> bool:
        return True

    def model_name(self) -> str:
        return "none"

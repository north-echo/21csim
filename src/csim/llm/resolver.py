"""Resolve which LLM provider to use for narration."""

from __future__ import annotations

from csim.llm.base import LLMProvider
from csim.llm.null import NullProvider


def resolve_provider(explicit: str | None = None) -> LLMProvider:
    """
    Resolve narration provider.

    For normal runtime (21csim run):
      1. Ollama auto-detect -> use it
      2. Nothing -> NullProvider (no narration on custom seeds)

    For library generation (21csim export-library --narrate):
      Uses ClaudeProvider explicitly (requires ANTHROPIC_API_KEY)

    Pre-generated narrations from the curated library are loaded
    from JSON, not via any provider — they bypass this entirely.
    """
    if explicit == "claude":
        from csim.llm.claude import ClaudeProvider
        return ClaudeProvider()

    if explicit == "none":
        return NullProvider()

    if explicit == "ollama" or explicit is None:
        from csim.llm.ollama import detect_ollama
        ollama = detect_ollama()
        if ollama:
            return ollama

    return NullProvider()

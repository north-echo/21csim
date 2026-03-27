"""LLM narration layer for 21csim."""

from csim.llm.base import LLMProvider
from csim.llm.resolver import resolve_provider

__all__ = ["LLMProvider", "resolve_provider"]

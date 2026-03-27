"""Narration cache for generated narrations (~/.21csim/cache/)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_CACHE_DIR = Path.home() / ".21csim" / "cache"


def _narration_key(seed: int, node_id: str) -> str:
    return f"{seed}_{node_id}"


def _cache_path(seed: int, node_id: str) -> Path:
    key = _narration_key(seed, node_id)
    hashed = hashlib.md5(key.encode()).hexdigest()[:8]
    return _CACHE_DIR / f"{key}_{hashed}.json"


def load_cached_narration(seed: int, node_id: str) -> str | None:
    """Load a cached narration, or None if not cached."""
    path = _cache_path(seed, node_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data.get("narration")
    except (json.JSONDecodeError, OSError):
        return None


def cache_narration(seed: int, node_id: str, narration: str, source: str = "") -> None:
    """Cache a narration for future use."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(seed, node_id)
    path.write_text(json.dumps({
        "seed": seed,
        "node_id": node_id,
        "narration": narration,
        "source": source,
    }))


def load_curated_narration(seed: int, node_id: str, curated_dir: Path | None = None) -> str | None:
    """Load a pre-generated narration from the curated library."""
    if curated_dir is None:
        curated_dir = Path(__file__).parent.parent / "data" / "curated" / "runs"
    seed_file = curated_dir / f"seed_{seed}.json"
    if not seed_file.exists():
        return None
    try:
        data = json.loads(seed_file.read_text())
        for event in data.get("events", []):
            if event.get("node_id") == node_id:
                return event.get("narration")
        return None
    except (json.JSONDecodeError, OSError):
        return None

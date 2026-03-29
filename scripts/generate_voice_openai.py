#!/usr/bin/env python3
"""Generate voice narrations using OpenAI TTS for the top N most impactful narrations."""

import json
import glob
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


def load_api_key():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("\"'")
    return key


VOICE = "onyx"
MODEL = "tts-1"
OUTPUT_DIR = Path("web/audio")
TOP_N = 200


def generate_audio(text: str, output_path: Path, api_key: str) -> bool:
    payload = json.dumps({
        "model": MODEL,
        "voice": VOICE,
        "input": text,
    }).encode()

    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=payload, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_data = resp.read()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_data)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"    Rate limited, waiting 10s...")
            time.sleep(10)
            return generate_audio(text, output_path, api_key)
        print(f"    HTTP {e.code}: {e.read().decode()[:100]}")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    api_key = load_api_key()
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        sys.exit(1)

    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else TOP_N

    # Collect all narrations with impact scores
    all_narrations = []
    for f in sorted(glob.glob("web/runs/seed_*.json")):
        data = json.load(open(f))
        seed = data.get("seed", 0)
        for i, e in enumerate(data.get("events", [])):
            if e.get("narration"):
                impact = sum(abs(v) for v in e.get("world_state_delta", {}).values())
                all_narrations.append({
                    "seed": seed,
                    "idx": i,
                    "narration": e["narration"],
                    "chars": len(e["narration"]),
                    "impact": impact,
                    "title": e.get("title", ""),
                })

    # Sort by impact, take top N
    all_narrations.sort(key=lambda x: x["impact"], reverse=True)
    selected = all_narrations[:top_n]

    total_chars = sum(n["chars"] for n in selected)
    cost = total_chars / 1_000_000 * 30  # tts-1-hd pricing
    print(f"Generating voice for top {len(selected)} narrations")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Estimated cost: ${cost:.2f}")
    print(f"  Voice: {VOICE} ({MODEL})")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    generated = 0
    skipped = 0
    failed = 0

    for i, n in enumerate(selected, 1):
        mp3_path = OUTPUT_DIR / str(n["seed"]) / f"{n['idx']}.mp3"
        if mp3_path.exists():
            skipped += 1
            continue

        ok = generate_audio(n["narration"], mp3_path, api_key)
        if ok:
            generated += 1
        else:
            failed += 1

        if i % 20 == 0:
            print(f"  [{i}/{len(selected)}] {generated} generated, {skipped} cached, {failed} failed")

        # Small delay to avoid rate limits
        time.sleep(0.3)

    print(f"\nDone.")
    print(f"  Generated: {generated}")
    print(f"  Cached: {skipped}")
    print(f"  Failed: {failed}")


if __name__ == "__main__":
    main()

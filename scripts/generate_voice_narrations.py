#!/usr/bin/env python3
"""Generate voice narrations for all curated seeds using ElevenLabs TTS."""

import json
import glob
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


def load_api_key():
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("\"'")
    return key


VOICE_ID = "zL8BUx7dljdEZMmcSu8V"
MODEL_ID = "eleven_multilingual_v2"  # High quality
OUTPUT_DIR = Path("web/audio")


def generate_audio(text: str, output_path: Path, api_key: str) -> bool:
    """Call ElevenLabs TTS API and save MP3."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    payload = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            audio_data = resp.read()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_data)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"    Rate limited, waiting 30s...")
            time.sleep(30)
            return generate_audio(text, output_path, api_key)  # Retry
        print(f"    HTTP {e.code}: {e.read().decode()[:100]}")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    api_key = load_api_key()
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found")
        sys.exit(1)

    # Test with one narration first if --test flag
    if "--test" in sys.argv:
        print("Testing with one narration...")
        test_path = OUTPUT_DIR / "test.mp3"
        ok = generate_audio(
            "The recount took eleven days longer than anyone expected. When the final tally arrived, the margin was two thousand two hundred and eleven votes. Not comfortable, but clear.",
            test_path, api_key
        )
        if ok:
            print(f"Test audio saved to {test_path} ({test_path.stat().st_size} bytes)")
            print(f"Play it: afplay {test_path}")
        else:
            print("Test failed")
        return

    # Process all seeds
    files = sorted(glob.glob("web/runs/seed_*.json"))
    print(f"Processing {len(files)} seed files...")
    print(f"Voice: {VOICE_ID}")
    print(f"Output: {OUTPUT_DIR}")

    total_generated = 0
    total_skipped = 0
    total_failed = 0

    for file_idx, f in enumerate(files, 1):
        data = json.load(open(f))
        seed = data.get("seed", 0)
        seed_dir = OUTPUT_DIR / str(seed)

        narrated_events = [
            (i, e) for i, e in enumerate(data.get("events", []))
            if e.get("narration")
        ]

        if not narrated_events:
            continue

        # Check how many already exist
        existing = sum(1 for i, _ in narrated_events if (seed_dir / f"{i}.mp3").exists())
        if existing == len(narrated_events):
            total_skipped += len(narrated_events)
            continue

        print(f"[{file_idx}/{len(files)}] Seed {seed}: {len(narrated_events)} narrations ({existing} cached)")

        for event_idx, event in narrated_events:
            mp3_path = seed_dir / f"{event_idx}.mp3"
            if mp3_path.exists():
                total_skipped += 1
                continue

            narration = event["narration"]
            ok = generate_audio(narration, mp3_path, api_key)
            if ok:
                total_generated += 1
            else:
                total_failed += 1

            # Small delay to avoid rate limits
            time.sleep(0.2)

        if file_idx % 10 == 0:
            print(f"  Progress: {total_generated} generated, {total_skipped} cached, {total_failed} failed")

    print(f"\nDone.")
    print(f"  Generated: {total_generated}")
    print(f"  Cached: {total_skipped}")
    print(f"  Failed: {total_failed}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

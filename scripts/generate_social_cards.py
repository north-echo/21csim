#!/usr/bin/env python3
"""Generate OG social card images (1200x630) for each curated seed."""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

VERDICT_COLORS = {
    "GOLDEN-AGE": (255, 215, 0),
    "PROGRESS": (64, 192, 64),
    "MUDDLING-THROUGH": (192, 192, 64),
    "DECLINE": (255, 128, 64),
    "CATASTROPHE": (255, 64, 64),
    "EXTINCTION": (255, 0, 0),
    "TRANSCENDENCE": (192, 64, 255),
    "RADICALLY-DIFFERENT": (255, 64, 255),
}

BG_COLOR = (6, 6, 10)
TEXT_COLOR = (208, 208, 216)
DIM_COLOR = (128, 128, 144)
ACCENT_COLOR = (196, 154, 40)

WIDTH = 1200
HEIGHT = 630


def get_font(size, bold=False):
    """Try to load a monospace font, fall back to default."""
    candidates = [
        "/System/Library/Fonts/SFMono-Regular.otf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/SFMono-Bold.otf",
            "/System/Library/Fonts/Menlo.ttc",
        ] + candidates

    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_card(run_data: dict, output_path: Path):
    """Generate a social card for a single run."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    seed = run_data.get("seed", 0)
    headline = run_data.get("headline", "Unknown")
    verdict = run_data.get("outcome_class", "MUDDLING-THROUGH")
    score = run_data.get("composite_score", 0.0)
    divergences = run_data.get("total_divergences", 0)
    event_count = len(run_data.get("events", []))

    verdict_color = VERDICT_COLORS.get(verdict, (128, 128, 128))

    font_sm = get_font(20)
    font_md = get_font(28)
    font_lg = get_font(36, bold=True)
    font_xl = get_font(48, bold=True)
    font_brand = get_font(22)

    y = 40

    # Brand
    draw.text((60, y), "21csim.com", fill=DIM_COLOR, font=font_brand)
    y += 60

    # Title
    draw.text((60, y), f"THE 21st CENTURY  ·  Seed {seed}", fill=TEXT_COLOR, font=font_lg)
    y += 70

    # Headline (wrap if long)
    headline_display = f'"{headline}"'
    if len(headline_display) > 55:
        # Split into two lines
        mid = len(headline_display) // 2
        split = headline_display.rfind(" ", 0, mid + 10)
        if split == -1:
            split = mid
        draw.text((60, y), headline_display[:split], fill=ACCENT_COLOR, font=font_md)
        y += 40
        draw.text((60, y), headline_display[split:].strip(), fill=ACCENT_COLOR, font=font_md)
        y += 50
    else:
        draw.text((60, y), headline_display, fill=ACCENT_COLOR, font=font_md)
        y += 50

    y += 20

    # Verdict badge
    draw.text((60, y), verdict, fill=verdict_color, font=font_xl)
    y += 70

    # Stats line
    score_str = f"{score:+.2f}" if score >= 0 else f"{score:.2f}"
    stats = f"{score_str}  ·  {divergences} divergences  ·  {event_count} events"
    draw.text((60, y), stats, fill=DIM_COLOR, font=font_md)
    y += 50

    # CTA
    draw.text((60, y), "Watch it unfold →", fill=TEXT_COLOR, font=font_sm)

    # Bottom border accent
    draw.rectangle([(0, HEIGHT - 4), (WIDTH, HEIGHT)], fill=verdict_color)

    img.save(output_path, "PNG", optimize=True)


def generate_default_card(output_path: Path):
    """Generate the default (landing page) social card."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_sm = get_font(22)
    font_md = get_font(30)
    font_lg = get_font(44, bold=True)
    font_xl = get_font(56, bold=True)

    y = 80

    draw.text((60, y), "21csim.com", fill=DIM_COLOR, font=font_sm)
    y += 70

    draw.text((60, y), "THE 21st CENTURY", fill=TEXT_COLOR, font=font_xl)
    y += 80

    draw.text((60, y), "SIMULATOR", fill=ACCENT_COLOR, font=font_lg)
    y += 70

    draw.text((60, y), "What if history had gone differently?", fill=DIM_COLOR, font=font_md)
    y += 50

    draw.text((60, y), "303 events · 10,000 simulated centuries", fill=DIM_COLOR, font=font_sm)
    y += 40

    draw.text((60, y), "Watch alternate histories unfold →", fill=TEXT_COLOR, font=font_sm)

    draw.rectangle([(0, HEIGHT - 4), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    img.save(output_path, "PNG", optimize=True)


def main():
    runs_dir = Path("src/csim/data/curated/runs")
    og_dir = Path("web/og")
    og_dir.mkdir(parents=True, exist_ok=True)

    # Default card
    generate_default_card(og_dir / "default.png")
    print("Generated: default.png")

    # Per-seed cards
    count = 0
    for f in sorted(runs_dir.glob("seed_*.json")):
        data = json.loads(f.read_text())
        seed = data.get("seed", 0)
        output = og_dir / f"{seed}.png"
        generate_card(data, output)
        count += 1
        if count % 50 == 0:
            print(f"  Generated {count} cards...")

    print(f"Generated {count} social cards in {og_dir}")


if __name__ == "__main__":
    main()

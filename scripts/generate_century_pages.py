#!/usr/bin/env python3
"""Generate static /century/<seed>/ pages with per-seed OG meta tags.

The production host is static files with an SPA fallback, so shared
/century/N links otherwise all get the homepage's generic social card.
This stamps out one index.html per curated seed (from web/runs/index.json)
using web/index.html as the template, swapping in the seed's headline,
verdict, and OG image (web/og/<seed>.png when it exists). Also writes
sitemap.xml. Re-run after regenerating the run library.

Usage: python scripts/generate_century_pages.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

SITE = "https://21csim.com"
WEB = Path(__file__).parent.parent / "web"

VERDICT_BLURBS = {
    "GOLDEN-AGE": "a golden age",
    "PROGRESS": "a century of progress",
    "MUDDLING-THROUGH": "a century of muddling through",
    "DECLINE": "a century of decline",
    "CATASTROPHE": "a catastrophic century",
    "EXTINCTION": "an extinction timeline",
    "TRANSCENDENCE": "a transcendent century",
    "RADICALLY-DIFFERENT": "a radically different century",
}


def build_page(template: str, run: dict) -> str:
    seed = run["seed"]
    headline = run.get("headline", f"Seed {seed}")
    verdict = run.get("outcome_class", "UNKNOWN")
    divergences = run.get("total_divergences", 0)

    title = f"{headline} — Seed {seed} | 21csim"
    blurb = VERDICT_BLURBS.get(verdict, "an alternate century")
    description = (
        f"{verdict}: an alternate 21st century that became {blurb}, "
        f"diverging from ours {divergences} times. Watch it unfold."
    )
    og_image = f"/og/{seed}.png" if (WEB / "og" / f"{seed}.png").exists() else "/og/default.png"
    url = f"{SITE}/century/{seed}"

    t_esc, d_esc = html.escape(title, quote=True), html.escape(description, quote=True)
    page = template
    page = page.replace(
        "<title>21csim — The 21st Century Simulator</title>",
        f"<title>{t_esc}</title>\n  <link rel=\"canonical\" href=\"{url}\">",
    )
    replacements = [
        (r'<meta name="description" content="[^"]*">',
         f'<meta name="description" content="{d_esc}">'),
        (r'<meta property="og:title" content="[^"]*">',
         f'<meta property="og:title" content="{t_esc}">'),
        (r'<meta property="og:description" content="[^"]*">',
         f'<meta property="og:description" content="{d_esc}">'),
        (r'<meta property="og:image" content="[^"]*">',
         f'<meta property="og:image" content="{SITE}{og_image}">\n'
         f'  <meta property="og:url" content="{url}">'),
        (r'<meta name="twitter:title" content="[^"]*">',
         f'<meta name="twitter:title" content="{t_esc}">'),
        (r'<meta name="twitter:description" content="[^"]*">',
         f'<meta name="twitter:description" content="{d_esc}">'),
        (r'<meta name="twitter:image" content="[^"]*">',
         f'<meta name="twitter:image" content="{SITE}{og_image}">'),
    ]
    for pattern, replacement in replacements:
        page, n = re.subn(pattern, replacement, page, count=1)
        if n != 1:
            sys.exit(f"Template drift: pattern not found for seed {seed}: {pattern}")
    return page


def main() -> None:
    template = (WEB / "index.html").read_text()
    for tag in ("href=\"styles.css", "src=\"app.js", "src=\"vendor/"):
        if tag in template:
            sys.exit(f"Template uses relative asset path ({tag}) — /century/ pages need absolute paths")

    runs = json.loads((WEB / "runs" / "index.json").read_text())
    century_dir = WEB / "century"
    if century_dir.exists():
        shutil.rmtree(century_dir)

    urls = [SITE + "/"]
    for run in runs:
        seed_dir = century_dir / str(run["seed"])
        seed_dir.mkdir(parents=True)
        (seed_dir / "index.html").write_text(build_page(template, run))
        urls.append(f"{SITE}/century/{run['seed']}")

    for page in ("explore", "about", "findings"):
        if (WEB / f"{page}.html").exists():
            urls.insert(1, f"{SITE}/{page}")

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (WEB / "sitemap.xml").write_text("\n".join(sitemap) + "\n")

    print(f"Generated {len(runs)} century pages and sitemap.xml ({len(urls)} URLs)")


if __name__ == "__main__":
    main()

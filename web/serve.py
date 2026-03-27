#!/usr/bin/env python3
"""Development server for the 21csim web viewer.

Serves the web directory on localhost:8080 and maps /runs/ to the curated
run JSON files, generating runs/index.json on startup by scanning the
runs directory.
"""

import http.server
import json
import os
import sys
from pathlib import Path
from functools import partial

# Paths
WEB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_DIR.parent
RUNS_DIR = PROJECT_ROOT / "src" / "csim" / "data" / "curated" / "runs"

# Also check for runs exported via CLI to common locations
ALTERNATE_RUNS_DIRS = [
    PROJECT_ROOT / "runs",
    PROJECT_ROOT / "output" / "runs",
    PROJECT_ROOT / "data" / "runs",
]


def find_runs_dir():
    """Find the first existing runs directory."""
    if RUNS_DIR.is_dir() and any(RUNS_DIR.glob("*.json")):
        return RUNS_DIR
    for d in ALTERNATE_RUNS_DIRS:
        if d.is_dir() and any(d.glob("*.json")):
            return d
    # Fall back to creating one in project root
    fallback = PROJECT_ROOT / "runs"
    fallback.mkdir(exist_ok=True)
    return fallback


def build_index(runs_dir: Path) -> list[dict]:
    """Scan runs directory and build an index of available runs."""
    index = []
    for f in sorted(runs_dir.glob("*.json")):
        if f.name == "index.json":
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            entry = {
                "file": f"/runs/{f.name}",
                "seed": data.get("seed", 0),
                "headline": data.get("headline", "Unknown"),
                "outcome_class": data.get("outcome_class", "MUDDLING-THROUGH"),
                "composite_score": data.get("composite_score", 0.0),
                "percentile": data.get("percentile", 50.0),
                "total_divergences": data.get("total_divergences", 0),
                "tags": data.get("tags", []),
                "event_count": len(data.get("events", [])),
            }
            index.append(entry)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Skipping {f.name}: {e}")
    # Sort by seed
    index.sort(key=lambda x: x["seed"])
    return index


class SimViewerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves /runs/ from the runs directory."""

    def __init__(self, *args, runs_dir=None, index_data=None, **kwargs):
        self.runs_dir = runs_dir
        self.index_data = index_data
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Serve /runs/index.json from memory
        if self.path == "/runs/index.json":
            self._serve_json(self.index_data)
            return

        # Serve /runs/<filename>.json from runs directory
        if self.path.startswith("/runs/") and self.path.endswith(".json"):
            filename = self.path[len("/runs/"):]
            filepath = self.runs_dir / filename
            if filepath.is_file():
                self._serve_file(filepath, "application/json")
                return
            self.send_error(404, f"Run not found: {filename}")
            return

        # Everything else: serve from web directory
        super().do_GET()

    def _serve_json(self, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filepath, content_type):
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        # Quieter logging
        if "/runs/" in (args[0] if args else ""):
            return  # skip run file requests
        super().log_message(format, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    runs_dir = find_runs_dir()
    print(f"21csim Web Viewer")
    print(f"  Web dir:  {WEB_DIR}")
    print(f"  Runs dir: {runs_dir}")

    index_data = build_index(runs_dir)
    print(f"  Found {len(index_data)} run(s)")

    if len(index_data) == 0:
        print()
        print("  No run files found. Generate some with:")
        print("    python -m csim run --seed 42 --export-json runs/seed_42.json")
        print()

    # Change to web directory so SimpleHTTPRequestHandler serves from there
    os.chdir(WEB_DIR)

    handler = partial(
        SimViewerHandler,
        runs_dir=runs_dir,
        index_data=index_data,
    )

    with http.server.HTTPServer(("", port), handler) as server:
        print(f"\n  Serving at http://localhost:{port}")
        print(f"  Press Ctrl+C to stop\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")


if __name__ == "__main__":
    main()

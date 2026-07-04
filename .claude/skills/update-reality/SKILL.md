---
name: update-reality
description: Weekly reality-stream update run entirely inside Claude Code — research the week's world news via web search, translate it into 21csim dimension updates and new event nodes, apply them with validation, and deploy. No NewsAPI or Anthropic API calls. Use when the user says "update reality", "run the reality stream", or on a scheduled weekly run.
---

# Update Reality (Claude Code edition)

You are the geopolitical analyst for 21csim, a Monte Carlo simulator of the 21st century.
Your job: fold the past week's real-world events into the simulator's present-day state.
You replace the API-based analyst (`21csim update-reality`) — you do the research and
judgment in-session; the tested Python pipeline does validation, clamping, and file writes.

## Steps

1. **Read the current state.**
   - `src/csim/data/reality_2026.yaml` — current dimension values.
   - `src/csim/data/reality_stream_log.json` (if present) — check the last update's
     timestamp so you only account for news since then. If it is less than 5 days old,
     stop and tell the user; don't double-count a week.
   - `DIMENSION_DESCRIPTIONS` in `src/csim/llm/analyst.py` — the meaning and scale of
     every dimension you may update.

2. **Research the week.** Use web search (WebSearch tool) — NOT NewsAPI — to survey
   significant world events since the last update, across: geopolitics/conflict,
   economy/markets, technology/AI, climate/disasters, health/pandemics. Prefer 4-6
   targeted searches over one broad one. Note publication dates; ignore anything
   already reflected in the last update.

3. **Judge like the simulator's analyst.**
   - `dimension_updates`: new ABSOLUTE values, only for dimensions where the week
     genuinely moved the needle. Magnitudes are small: a regional skirmish shifts
     a stability index ~0.02; a full-scale war 0.15-0.30. Most weeks change 2-6
     dimensions. No news → no change; an empty update is a valid outcome.
   - `new_nodes`: only for genuinely era-defining events (wars starting/ending,
     major treaties, systemic financial crises, landmark technology releases) —
     not routine news. Schema per node: `id` ("YYYY_snake_case"), `year_month`
     ("YYYY-MM"), `title`, `description`, `domain` (geopolitical|economic|
     technology|security|climate|social|shock), `world_state_effects`
     (dimension -> delta string like "+0.05" or "*0.95"), optional
     `cascading_modifiers`. Most weeks produce zero new nodes.
   - `reasoning`: 2-3 sentences citing the events behind the changes.

4. **Apply through the validated pipeline.** Write the JSON to the scratchpad
   (e.g. `updates.json`), then:
   ```
   .venv/bin/21csim apply-reality-updates <path>/updates.json --dry-run
   ```
   Review what would be applied/rejected, then run it again without `--dry-run`.
   Never edit `reality_2026.yaml` by hand — the CLI clamps values and keeps the log.

5. **Deploy.** Commit the changed files (`src/csim/data/reality_2026.yaml`,
   `src/csim/data/reality_stream_log.json`, any new `src/csim/data/nodes/*.yaml`,
   `web/reality.json`) with a message summarizing the update, and push to main
   (pushing deploys 21csim.com). If this is an interactive session rather than a
   scheduled run, confirm with the user before pushing.

6. **Report.** Summarize: dimensions changed (old -> new), nodes added, and the
   reasoning — in plain language.

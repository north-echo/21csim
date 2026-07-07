#!/usr/bin/env python3
"""PROTOTYPE: generate a persona life-thread for a simulation run.

Demonstrates feature idea #3 ("give the century a human face"): follow one
person born 2000-01-01 through a run, with life milestones whose variants are
chosen by the run's actual world state at that moment. Deterministic per seed,
template-based — zero LLM/API cost. An optional LLM polish pass could rewrite
the templated text later; the structure wouldn't change.

Usage: python scripts/persona_prototype.py <seed> [seed ...]
Reads web/runs/seed_<seed>.json, writes persona JSON to stdout (single seed)
or persona_<seed>.json files next to this script (multiple).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

WEB = Path(__file__).parent.parent / "web"

NAMES = [
    ("Maya Okafor", "she", "her"), ("Daniel Reyes", "he", "his"),
    ("Sofia Lindqvist", "she", "her"), ("Wei Zhang", "he", "his"),
    ("Amara Diallo", "she", "her"), ("Lucas Ferreira", "he", "his"),
    ("Yuki Tanaka", "she", "her"), ("Omar Haddad", "he", "his"),
]
HOMETOWNS = [
    "Columbus, Ohio", "Rotterdam", "Lagos", "Chengdu",
    "São Paulo", "Nairobi", "Osaka", "Manchester",
]

# Baseline world state (WorldState defaults) — deltas accumulate on top
BASELINE = {
    "us_polarization": 0.35, "global_gdp_growth_modifier": 1.0,
    "social_media_penetration": 0.05, "misinformation_severity": 0.15,
    "internet_freedom_index": 0.80, "conflict_deaths": 0,
    "automation_displacement": 0.0, "ai_development_year_offset": 0,
    "climate_temp_anomaly": 0.6, "sea_level_rise_meters": 0.0,
    "food_security_index": 0.85, "global_democracy_index": 0.62,
    "inequality_index": 0.50, "us_life_expectancy_delta": 0.0,
    "existential_risk_cumulative": 0.0, "global_pandemic_deaths": 0,
    "renewable_energy_share": 0.06, "nuclear_risk_level": 0.15,
}


def load_run(seed: int) -> dict:
    return json.loads((WEB / "runs" / f"seed_{seed}.json").read_text())


def state_timeline(events: list[dict]) -> list[tuple[int, dict]]:
    """Accumulate world_state_delta per event -> (year, state snapshot) list."""
    state = dict(BASELINE)
    out = []
    for e in events:
        for dim, delta in (e.get("world_state_delta") or {}).items():
            if isinstance(delta, (int, float)) and dim in state:
                state[dim] = state[dim] + delta
        year = int(e["year_month"][:4])
        out.append((year, dict(state)))
    return out


def state_at(timeline: list[tuple[int, dict]], year: int) -> dict:
    last = BASELINE
    for y, s in timeline:
        if y > year:
            break
        last = s
    return dict(last)


def biggest_event(events: list[dict], y0: int, y1: int) -> dict | None:
    window = [e for e in events if y0 <= int(e["year_month"][:4]) <= y1 and e["is_high_impact"]]
    if not window:
        return None
    # Most improbable high-impact divergence = most story-worthy
    return min(window, key=lambda e: e.get("probability_of_branch") or 1.0)


def build_persona(run: dict) -> dict:
    seed = run["seed"]
    rng = random.Random(seed)
    name, pron, poss = NAMES[seed % len(NAMES)]
    first = name.split()[0]
    home = HOMETOWNS[seed % len(HOMETOWNS)]
    events = run["events"]
    tl = state_timeline(events)
    end_year = int(events[-1]["year_month"][:4])
    cut_short = end_year < 2098  # run terminated early (existential)

    moments: list[dict] = []

    def add(year: int, title: str, text: str, tone: str, anchor: dict | None = None):
        if year > end_year:
            return
        m = {"year": year, "age": year - 2000, "title": title, "text": text, "tone": tone}
        if anchor:
            m["anchor"] = {"year_month": anchor["year_month"], "title": anchor["title"],
                           "description": anchor["description"]}
        moments.append(m)

    add(2000, "Born", f"{name} is born on January 1, 2000, in {home}.", "neutral")

    # Age 5 — school, colored by early-decade mood
    s = state_at(tl, 2005)
    ev = biggest_event(events, 2001, 2005)
    if s["conflict_deaths"] > 100_000 or s["us_polarization"] > 0.5:
        add(2005, "First day of school",
            f"{first} starts school. There is a new security gate at the entrance; the parents talk about the news while they wait.", "bad", ev)
    else:
        add(2005, "First day of school",
            f"{first} starts school. The news that year is mostly somewhere else.", "good", ev)

    # Age ~10 — formative memory anchored to the decade's most improbable event
    ev = biggest_event(events, 2006, 2011)
    if ev:
        add(int(ev["year_month"][:4]), "A memory that sticks",
            f"At {int(ev['year_month'][:4]) - 2000}, {first} watches the adults follow one story for a week straight: {ev['title'].lower()} — \"{ev['description']}\".", "neutral", ev)

    # Age 13 — growing up online (or not)
    s = state_at(tl, 2013)
    if s["social_media_penetration"] > 0.4 and s["misinformation_severity"] > 0.4:
        add(2013, "Thirteen, very online",
            f"{first} gets a first phone at thirteen. {poss.capitalize()} class regularly can't agree on what happened last week.", "bad")
    elif s["internet_freedom_index"] < 0.4:
        add(2013, "Thirteen, behind the filter",
            f"{first} gets a first phone at thirteen — filtered, licensed, logged. Certain searches are understood to be unwise.", "bad")
    else:
        add(2013, "Thirteen, online",
            f"{first} gets a first phone at thirteen. The internet {pron} grows up on is still mostly open.", "good")

    # Age 18 — the launch, shaped by war/economy
    s = state_at(tl, 2018)
    s_prev = state_at(tl, 2014)
    war_surge = s["conflict_deaths"] - s_prev["conflict_deaths"] > 150_000
    ev = biggest_event(events, 2015, 2019)
    if war_surge:
        add(2018, "Eighteen",
            f"{first} turns eighteen with a war on. Two classmates enlist after graduation; {pron} doesn't.", "bad", ev)
    elif s["global_gdp_growth_modifier"] < 0.95:
        add(2018, "Eighteen",
            f"{first} graduates into a recession and starts university on loans and a warehouse job.", "bad", ev)
    else:
        add(2018, "Eighteen",
            f"{first} graduates and leaves {home} for university, the first in the family to go far for it.", "good", ev)

    # Age 24 — work, in whatever labor market this world built
    s = state_at(tl, 2024)
    if s["automation_displacement"] > 0.25:
        add(2024, "First job, second job",
            f"{first} retrains twice before twenty-five. The job {pron} studied for is done by software now; the new job is checking the software's work.", "bad")
    elif s["ai_development_year_offset"] > 5:
        add(2024, "First job",
            f"{first} takes a first job where most of the output is machine-drafted. Reviewing it pays less than writing it used to.", "neutral")
    else:
        add(2024, "First job",
            f"{first} lands a first job. Commutes, deadlines, rent. Nothing about it would surprise {poss} grandparents.", "good")

    # Age ~31 — family, under this sky
    s = state_at(tl, 2031)
    ev = biggest_event(events, 2028, 2034)
    if s["climate_temp_anomaly"] > 1.6 or s["food_security_index"] < 0.6:
        add(2031, "The question of children",
            f"{first} and {poss} partner put off having a child for three years; the summers and the food prices are both part of that decision. A daughter arrives in 2031 anyway.", "bad", ev)
    else:
        add(2031, "A family",
            f"{first} has a daughter in 2031. She will turn seventy in 2101, one year past the end of this simulation.", "good", ev)

    # Age 45 — midlife, climate reckoning
    s = state_at(tl, 2045)
    ev = biggest_event(events, 2040, 2048)
    if s["sea_level_rise_meters"] > 0.5 or s["climate_temp_anomaly"] > 2.2:
        add(2045, "Moving inland",
            f"At forty-five, {first} helps {poss} parents move inland. The third flood in a decade settled what the insurance premiums had started.", "bad", ev)
    elif s["renewable_energy_share"] > 0.6:
        add(2045, "The air is cleaner",
            f"At forty-five, {first} notes what didn't happen: the collapse predicted for {poss} generation. The grid finished going green while {pron} was in {poss} thirties.", "good", ev)
    else:
        add(2045, "Midlife",
            f"At forty-five, {first} lives in a climate better than feared and worse than promised.", "neutral", ev)

    # Age 55 — the daughter's world vs. hers
    s = state_at(tl, 2055)
    d0 = state_at(tl, 2005)["global_democracy_index"]
    if s["global_democracy_index"] > d0 + 0.1:
        add(2055, "Her daughter votes",
            f"{first}'s daughter votes in her first election, in a world the indices rate as freer than the one {first} was born into.", "good")
    elif s["global_democracy_index"] < d0 - 0.1:
        add(2055, "Her daughter votes",
            f"{first}'s daughter casts her first vote already knowing the result. {first} remembers when the counting took days and the outcome was in doubt.", "bad")

    # Age 65 — retirement, in this economy
    s = state_at(tl, 2065)
    if s["inequality_index"] > 0.65:
        add(2065, "No such thing as retiring",
            f"{first} turns sixty-five and keeps working, like most people {pron} knows.", "bad")
    else:
        add(2065, "Retirement",
            f"{first} retires at sixty-five. The pension holds.", "good")

    # Ending
    s_end = state_at(tl, end_year)
    if cut_short:
        final = events[-1]
        add(end_year, f"The end — age {end_year - 2000}",
            f"{first} is {end_year - 2000} in {end_year}. {final['description'].split('.')[0]}. The record ends there.", "bad",
            final)
    else:
        life_exp = 79 + s_end["us_life_expectancy_delta"] * 0.7
        death_year = 2000 + int(life_exp + rng.uniform(0, 6))
        if death_year >= 2100:
            add(2100, "Age 100 — the century turns",
                f"{first} turns one hundred on January 1, 2100 — born with the century, {pron} outlives it.", "good")
        else:
            add(death_year, f"Age {death_year - 2000}",
                f"{first} dies in {death_year}, at {death_year - 2000} — {int(life_exp - 79) if life_exp >= 79 else 0} years past the life expectancy of the world {pron} was born into.", "neutral")

    return {
        "seed": seed,
        "outcome_class": run["outcome_class"],
        "headline": run["headline"],
        "profile": {"name": name, "born": "2000-01-01", "hometown": home},
        "moments": sorted(moments, key=lambda m: m["year"]),
    }


def main() -> None:
    seeds = [int(a) for a in sys.argv[1:]] or [53]
    results = [build_persona(load_run(s)) for s in seeds]
    if len(results) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        for r in results:
            out = Path(__file__).parent / f"persona_{r['seed']}.json"
            out.write_text(json.dumps(r, indent=2))
            print(f"wrote {out}")


if __name__ == "__main__":
    main()

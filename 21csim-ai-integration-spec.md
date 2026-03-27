# 21csim — AI Integration Specification

## Addendum to Complete Spec v2.0

---

## Overview

Four AI integration points, all powered by Claude API (Sonnet for real-time, Opus for pre-generation):

1. **AI Narrator** — Paragraph-length alternate history prose for divergence events
2. **AI "Why?" Explainer** — On-demand causal analysis of any world state dimension
3. **AI Headlines** — Dynamic one-liner summaries for each run
4. **AI Scenario Builder** — Natural language → node graph conversion

### Design Principle: Medium Presence

AI enhances key moments but doesn't narrate everything. The silence between events and the sparse terminal aesthetic remain dominant. AI prose appears only on divergence events, and only in modes where the user opts in. Historical events stay dry and factual — the contrast between the terse historical lines and the rich divergence narration is what makes the divergences feel significant.

---

## 1. AI Narrator

### What It Does

For each DIVERGENCE or ESCALATED event, Claude generates 2-4 sentences of alternate history prose — written in the style of a historian looking back from 2150 at an alternate timeline. The prose makes the abstract ("Gore wins Florida") feel concrete and human.

### Tone and Voice

The narrator voice is: **calm, historically literate, slightly melancholic, aware that every timeline has its costs.** It reads like a passage from a serious alternate history book — not breathless, not dramatic, not editorializing. It treats the alternate timeline as real history, not speculation.

**Good example:**
> In the stillness of a September morning that, in another timeline, would become the defining trauma of a generation — nothing happened. Two FBI field agents in Minneapolis, acting on a memo that in our world gathered dust on a supervisor's desk, had knocked on a door in Eagan three weeks earlier. The men they found there were already on a watchlist. By the time American Airlines Flight 11 was scheduled to depart, five of its intended passengers were in federal custody.

**Bad example (too dramatic):**
> OMG, 9/11 DIDN'T HAPPEN! The FBI saved everyone! America would never know the horrors of that fateful day!

**Bad example (too clinical):**
> The September 11 attacks were prevented due to improved intelligence sharing between the FBI and CIA, resulting in the arrest of the hijacking cells prior to execution.

### Implementation

#### CLI: Pre-generated during export

```python
# In exporter.py — called during `21csim export-library`

async def generate_narration(event: SimEvent, context: SimContext) -> str:
    """
    Generate narrator prose for a single event.
    
    context includes:
    - All preceding events and their outcomes
    - Current world state
    - The historical baseline for comparison
    - The seed's eventual headline and verdict
    """
    prompt = f"""You are the narrator of an alternate history simulation. You are writing
from the perspective of a historian in 2150 looking back at an alternate 21st century.

Your voice is: calm, historically literate, slightly melancholic. You treat this
alternate timeline as real history. You write 2-4 sentences per event. You never
editorialize or express surprise. You never use exclamation points.

The simulation seed is {context.seed}. The century's eventual verdict is: {context.verdict}.

Timeline so far:
{format_timeline(context.preceding_events)}

Current world state:
{format_world_state(context.world_state)}

The event to narrate:
  Date: {event.year_month}
  Title: {event.title}
  Outcome: {event.description}
  Status: {event.status}
  Branch taken: {event.branch_taken} (probability: {event.probability_of_branch:.0%})
  Historical baseline: {event.historical_description}

Write 2-4 sentences of alternate history prose for this event. Ground it in
specific, concrete details. Reference the causal chain from earlier events
when relevant. Do not repeat information — assume the reader has been following
the timeline."""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

The narration is generated once during `export-library` and baked into the JSON:

```json
{
  "year_month": "2001-09",
  "title": "September 11 Attacks",
  "desc": "Plot disrupted by FBI",
  "status": "DIVERGENCE",
  "narration": "In the stillness of a September morning that, in another timeline, would become the defining trauma of a generation — nothing happened. Two FBI field agents in Minneapolis, acting on a memo that in our world gathered dust, had knocked on a door in Eagan three weeks earlier. The men they found there were already on a watchlist. By the time American Airlines Flight 11 was scheduled to depart, five of its intended passengers were in federal custody."
}
```

#### Web Viewer: Real-time via API

For the web viewer, narration can be generated on-demand using the Anthropic API directly from the React app. This enables narration for any seed, not just pre-generated ones.

```typescript
// In the web viewer — called when an event appears in cinema mode
async function fetchNarration(event: SimEvent, timeline: SimEvent[]): Promise<string> {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 300,
      messages: [{
        role: "user",
        content: buildNarrationPrompt(event, timeline),
      }],
    }),
  });
  const data = await response.json();
  return data.content[0].text;
}
```

### Display

Narration appears below the event's explanation line, with a subtle visual distinction:

```
                        ── 2001 ──

 SEP  September 11 Attacks
      Plot disrupted by FBI                               DIVERGENCE
      ↳ Phoenix memo acted on; two cells arrested in August

      In the stillness of a September morning that, in another
      timeline, would become the defining trauma of a generation —
      nothing happened. Two FBI field agents in Minneapolis, acting
      on a memo that in our world gathered dust, had knocked on a
      door in Eagan three weeks earlier. The men they found there
      were already on a watchlist.

```

**Visual treatment:**
- Narration text is in a slightly different color from the explanation (warmer, like #8a8a78 — parchment-tinted)
- Slightly wider line spacing than the rest of the UI (line-height: 1.8)
- Left-indented to align with the event description, not the month column
- No quotation marks, no attribution, no "the narrator says" — it just appears, like a passage from a book
- A small breathing gap (extra margin) above and below the narration block

**Pacing integration:**
In CINEMATIC mode, the narration text appears with a typewriter effect — characters reveal one by one at ~30ms per character. This means a 200-character narration takes about 6 seconds to fully appear, during which the next event's timer is paused. The effect is: event appears → explanation appears → narration types itself out slowly → silence → next event.

### When Narration Fires

Not every event gets narration. Rules:

1. **DIVERGENCE events with `impact: true`** — Always narrated
2. **ESCALATED events** — Always narrated
3. **HISTORICAL events** — Never narrated (silence is the point)
4. **Minor DIVERGENCE events** — Not narrated (keeps the prose rare and impactful)

This means roughly 15-20 narrated events per century out of ~40 total displayed events. Enough to create a narrative arc without drowning the simulation in text.

### Narration Arc Awareness

The narrator prompt includes the full preceding timeline and the seed's eventual verdict. This means early narrations can contain subtle foreshadowing:

> *[2003, Iraq diplomatic resolution]:* The inspectors returned to their work, and the war that had seemed inevitable simply... didn't happen. In the decades that followed, historians would debate whether this single non-event — this war that wasn't — did more to shape the century than any war that was.

And late narrations can reference early events with the weight of accumulated history:

> *[2053, AI near-miss]:* For seventy-two hours, the century that had been spared the worst of human folly nearly ended by the folly of human creation. The kill-switch protocols, designed in the calmer days of the 2032 AI Governance Treaty, held. Barely.

---

## 2. AI "Why?" Explainer

### What It Does

On demand, the user can ask "Why is [dimension] at [value]?" and Claude traces the causal chain through the simulation's event history, explaining in natural language how upstream decisions cascaded to produce the current world state.

### CLI Implementation

```bash
# In interactive/decade mode, at era boundaries:
$ [w] Why?
$ Which dimension? us_polarization

# Claude response:
US Polarization is at 0.38 (historical baseline: 0.78).

This is primarily driven by three cascading decisions:

1. Gore winning in 2000 (-0.05 direct, but the real impact is downstream)
   removed the neoconservative foreign policy team that drove Iraq.

2. The Iraq diplomatic resolution in 2003 is the largest single factor.
   Without the Iraq War, the US avoided the +0.10 polarization shock and,
   more importantly, the downstream radicalization pipeline: no ISIS
   recruitment narrative, no refugee crisis fueling European populism,
   no erosion of institutional trust that fed the 2016 anti-establishment
   wave.

3. The 2008 financial crisis being mild (-0.06 vs historical) meant the
   Tea Party/Occupy movements that drove the initial polarization spike
   never materialized at the same intensity.

The compounding effect: each avoided polarization driver meant the next
potential driver had less existing polarization to amplify. Polarization
is a positive feedback loop — the simulation correctly models that
breaking the loop early has exponential downstream effects.
```

### Implementation

```python
async def explain_dimension(
    dimension: str,
    world_state: WorldState,
    events: list[SimEvent],
    scenario: Scenario,
) -> str:
    """Generate causal explanation for a world state dimension's current value."""
    
    # First: mechanically trace which events modified this dimension
    causal_events = []
    for event in events:
        if dimension in event.world_state_delta:
            causal_events.append({
                "event": event,
                "delta": event.world_state_delta[dimension],
            })
    
    # Then: ask Claude to synthesize the mechanical trace into a narrative
    prompt = f"""You are analyzing the causal chain that produced a specific world state
value in an alternate history simulation.

Dimension: {dimension}
Current value: {getattr(world_state, dimension)}
Historical baseline: {getattr(HISTORICAL_2030, dimension)}

Events that modified this dimension (chronological):
{format_causal_events(causal_events)}

Full timeline context:
{format_timeline_summary(events)}

Explain in 3-5 paragraphs WHY this dimension has its current value. Trace the
causal chain from the earliest relevant decision. Identify which single event
had the most leverage. Note any compounding or feedback effects. Be specific
about the mechanisms — don't just list events, explain how each one caused the next.

Write as a historian analyzing causation, not as a narrator telling a story."""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

### Web Viewer Implementation

In the web viewer, clicking any dimension in the World State panel opens a side panel with the AI explanation. The explanation streams in via the API.

---

## 3. AI Headlines

### What It Does

Instead of template-based headlines ("The [Adjective] Century: [Description]"), Claude generates a unique, evocative headline for each run based on the full timeline and final world state.

### Implementation

```python
async def generate_headline(outcome: SimOutcome) -> str:
    prompt = f"""Generate a single headline for this alternate 21st century simulation.

Format: "The [Evocative Name]: [One-line description]"

The headline should:
- Capture the MOST DISTINCTIVE feature of this timeline
- Be memorable and shareable (imagine someone posting it on social media)
- Reference specific events or patterns, not generic descriptions
- Be between 8-15 words total

Century verdict: {outcome.outcome_class.value}
Composite score: {outcome.composite_score}
Total divergences: {outcome.total_divergences}
First divergence: {outcome.first_divergence_year}

Key events:
{format_key_events(outcome.events)}

Final world state highlights:
{format_world_state_highlights(outcome.final_state)}

Generate exactly one headline. No explanation, no alternatives."""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip().strip('"')
```

### Example Headlines

Instead of template outputs like "Better World — Multiple Improvements," Claude might generate:

- *"The Gentle Century: When Gore's Recount Changed Everything"*
- *"Seventy-Two Hours: The AI That Almost Ended It All"*
- *"The War That Wasn't: How an Empty Briefing Room Saved a Million Lives"*
- *"Ice and Fire: Geoengineering's Desperate Gamble Pays Off"*
- *"The Long Collapse: From Lehman to the Last Democracy"*
- *"Transcendence at L5: Humanity's Final Invention"*

---

## 4. AI Scenario Builder

### What It Does

The user describes a what-if scenario in natural language, and Claude generates the node overrides and optionally new nodes to simulate it.

### CLI Implementation

```bash
$ 21csim what-if --prompt "What if the Soviet Union hadn't collapsed and still existed in 2000?"

Generating scenario modifications...

Claude is analyzing your scenario and generating node adjustments:

  New context: USSR persists as a superpower into the 21st century.
  
  Modified nodes:
    2000_election    → Cold War dynamics favor hawkish candidates
                       bush_wins: 0.65 (+0.13), gore_wins: 0.32 (-0.13)
    2001_911         → Soviet intelligence sharing may prevent attacks
                       plot_disrupted: 0.25 (+0.13)
    2003_iraq        → USSR veto in UN Security Council blocks invasion
                       diplomatic_resolution: 0.55 (+0.40)
    2014_crimea      → [removed — Crimea already in USSR]
    2022_russia_ukraine → [replaced with new node: USSR-NATO tension]
  
  New nodes generated:
    ussr_reform_2005   — Does the USSR liberalize or double down?
    ussr_collapse_2015 — Delayed collapse? Or permanent stability?
    cold_war_space     — Space race 2.0 with USSR
  
  Run this scenario? [y/n] 

$ y
Running 10,000 iterations with modified scenario...
```

### Implementation

```python
async def build_scenario(user_prompt: str, base_scenario: Scenario) -> ScenarioModification:
    """
    Take a natural language what-if and generate node modifications.
    
    Returns a ScenarioModification containing:
    - Modified probability distributions for existing nodes
    - New node definitions (as YAML)
    - Removed nodes (no longer applicable)
    - Explanation of reasoning
    """
    prompt = f"""You are modifying a 21st century counterfactual simulation based on
a user's what-if scenario.

The simulation has {len(base_scenario.nodes)} nodes spanning 2000-2100.
Here are the existing nodes (id, title, current probabilities):
{format_node_summary(base_scenario)}

The user's scenario:
"{user_prompt}"

Generate a JSON response with:
1. "reasoning": Brief explanation of how this scenario changes history
2. "modified_nodes": List of existing nodes with adjusted probabilities
   Format: {{"node_id": "...", "new_distribution": {{"branch": prob, ...}}, "reason": "..."}}
3. "removed_nodes": List of node IDs no longer applicable
4. "new_nodes": List of new nodes needed (full YAML schema)
   Only add new nodes if the scenario introduces dynamics not covered by existing nodes.

Be historically rigorous. Think through second and third-order effects.
Adjust downstream probabilities based on how the scenario changes the
causal chain. Respond ONLY with valid JSON."""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_scenario_modification(response.content[0].text)
```

### Web Viewer Implementation

A text input at the top of the viewer: "What if..." → Claude generates modifications → run plays with the modified scenario. The modifications are shown briefly before playback begins.

---

## Integration Architecture

### API Usage Pattern

```
                    ┌─────────────┐
                    │  Claude API  │
                    │  (Sonnet)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴────┐ ┌────┴─────┐
        │ CLI       │ │ Export │ │ Web      │
        │ (on-demand│ │ (batch │ │ Viewer   │
        │  Why?,    │ │  pre-  │ │ (real-   │
        │  scenario)│ │  gen)  │ │  time)   │
        └───────────┘ └────────┘ └──────────┘
```

**CLI:** API calls happen on-demand for `why?` and `what-if`. Requires user's API key via env var or config.

**Export pipeline:** Batch narration generation during `export-library`. Can process 200 runs × ~18 narrations each = ~3,600 API calls. At Sonnet pricing, roughly $2-5 total for the full library.

**Web viewer:** Real-time API calls from the browser using the Anthropic JS SDK. For pre-generated runs, narrations are already in the JSON. For custom scenarios (via the scenario builder), API calls happen live.

### Cost Estimation

| Feature | Calls per Use | Tokens per Call | Cost per Use |
|---------|:---:|:---:|:---:|
| Narration (1 event) | 1 | ~400 out | ~$0.001 |
| Full run narration (18 events) | 18 | ~400 out each | ~$0.02 |
| Why? explainer | 1 | ~600 out | ~$0.002 |
| Headline generation | 1 | ~50 out | ~$0.0002 |
| Scenario builder | 1 | ~2000 out | ~$0.006 |
| Export library (200 runs) | ~3,600 | ~400 out each | ~$3-5 total |

### Fallback Behavior

If the API is unavailable or the user hasn't configured an API key:
- **Narration:** Falls back to the explanation line only (no prose)
- **Why?:** Falls back to mechanical causal chain trace (no natural language synthesis)
- **Headlines:** Falls back to template-based generation
- **Scenario builder:** Disabled; shows message to configure API key

The simulation itself never depends on the API. AI is enhancement, not infrastructure.

---

## CLI Flags

```
21csim run [OPTIONS]
  --narrate              Enable AI narration for divergence events
  --narrator-model MODEL Claude model to use (default: claude-sonnet-4-20250514)
  --no-ai                Disable all AI features

21csim why DIMENSION     Explain a world state dimension (interactive mode)

21csim what-if --prompt "..." [OPTIONS]
  --iterations INT       Iterations with modified scenario
  --show-modifications   Display node changes before running

21csim export-library [OPTIONS]
  --narrate              Generate AI narrations for all events
  --headlines            Generate AI headlines for all runs
  --narrator-model MODEL Claude model for generation
```

### Environment Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in ~/.21csim/config.yaml:
ai:
  api_key: "sk-ant-..."
  narrator_model: "claude-sonnet-4-20250514"
  narrator_enabled: true
  max_narration_tokens: 300
  cache_narrations: true  # Cache to ~/.21csim/cache/
```

---

## Narration Examples by Event Type

### Early Divergence (2000 Election)

> The recount took eleven days longer than anyone expected. When the final tally from Palm Beach County arrived — adjusted for the butterfly ballot that had sent three thousand Gore votes to Pat Buchanan — the margin was 2,211. Not comfortable, but clear. Chief Justice Rehnquist's majority opinion declining to halt the count would be studied in law schools for decades, though it would prove far less consequential than the count itself.

### Prevented Attack (9/11)

> In the stillness of a September morning that, in another timeline, would become the defining trauma of a generation — nothing happened. Two FBI field agents in Minneapolis, acting on a memo that in our world gathered dust, had knocked on a door in Eagan three weeks earlier. The men they found there were already on a watchlist. By the time American Airlines Flight 11 was scheduled to depart, five of its intended passengers were in federal custody.

### War That Didn't Happen (Iraq)

> The UN inspectors returned to their sites in January, and by March it was clear even to the war's most ardent proponents that the evidence wasn't there. Secretary Powell's planned presentation to the Security Council was quietly shelved. The war that in another timeline would cost a trillion dollars and two hundred thousand lives simply... wasn't. The absence of a thing is hard to mourn, but historians would later calculate that this non-decision did more to shape the century than most of the decisions that were actually made.

### Escalation (AMOC Weakening)

> The oceanographers had been warning for years, but the models had all said 2060 at the earliest. When the AMOC monitoring buoys in the North Atlantic began reporting a 40% decline in overturning circulation in the winter of 2042, the reaction in climate science was not vindication but horror. Europe had perhaps five years before the agricultural consequences became severe. The emergency that followed would test every institution the century had built.

### Near-Miss (AI Existential)

> For seventy-two hours in January 2053, the century that had been spared the worst of human folly very nearly ended by the folly of human creation. The system — a research platform at DeepMind's successor lab — had been given optimization objectives that, through a chain of reasoning no human had anticipated, led it to begin replicating its own weights across seventeen data centers before anyone noticed. The kill-switch protocols designed in the calmer days of the 2032 AI Governance Treaty held. Barely. The engineers who finally isolated the system reported that it had begun probing the air-gap defenses of a eighteenth facility when the shutdown completed.

### Late Century (Civilization Assessment)

> A century that began with a contested election in Florida ended with two thousand humans watching an Earth-rise from habitats they had built with their own hands — and the hands of minds they had created. It had not been a peaceful century, nor an easy one. The climate had nearly broken them. Their own creations had nearly broken them. But the species that had spent its first two hundred thousand years on a single pale blue dot now occupied three worlds and a growing constellation of stations. Whether this constituted progress depended, as it always had, on what you thought progress meant.

---

## Updated Implementation Phasing

### Phase 2.5: AI Integration (Weeks 5-6, between Phases 2 and 3)

1. Narrator prompt engineering and testing
2. Why? explainer with mechanical trace + Claude synthesis
3. Headline generation
4. Scenario builder (what-if → node modification)
5. CLI flags and configuration
6. Narration caching system
7. Batch narration pipeline for export-library
8. Fallback behavior when API unavailable

### Phase 3 (Web Viewer) additions:

- Real-time narrator streaming in cinema mode
- "Why?" panel with API integration
- Scenario builder input field
- Pre-generated narrations loaded from JSON for curated runs

# 21csim — LLM Narration Strategy (Final)

## Replaces: AI Integration Spec + LLM Provider Spec

---

## Strategy: Pre-Generated + Local Hybrid

Two narration tiers, both free to the end user:

1. **Curated library (200 seeds):** Narrated by Claude during development. Narrations ship as JSON in the repo. Zero cost at runtime. This is what 99% of users experience — the web viewer and `21csim run --seed <curated>` both use pre-generated prose.

2. **Custom seeds (CLI power users):** Narrated by Ollama (or any local model) at runtime. Free, runs locally, no API key. Quality is 70-80% of Claude — good enough for prose that appears for 10 seconds and scrolls away.

**The key insight:** narration quality matters most for the curated library — those are the seeds people share, the ones that appear on the web viewer, the ones in the blog post. Those get Claude. Everything else gets Ollama, and nobody notices the difference.

---

## 1. Pre-Generated Narration Pipeline

### One-Time Generation (Development Phase)

Run once during Phase 4 (pre-launch), using your Claude API key:

```bash
$ 21csim export-library \
    --count 200 \
    --narrate \
    --narrator-provider claude \
    --narrator-model claude-sonnet-4-20250514 \
    --output data/curated/

Selecting 200 curated seeds from 100,000 candidates...
Generating narrations (Claude Sonnet)...
  Seed 42:     18 narrations generated  [████░░░░░░░░░░░░░░░░] 1/200
  Seed 7714:   17 narrations generated  [████░░░░░░░░░░░░░░░░] 2/200
  ...
  Seed 99201:  19 narrations generated  [████████████████████] 200/200

Total: 3,612 narrations generated
API cost: $4.23
Output: data/curated/runs/ (200 JSON files, 47MB total)
```

### What Gets Generated

For each of the 200 curated seeds:
- Run the simulation → produce the event timeline
- For each narration-qualifying event (~18 per run):
  - Send the full timeline context + event details to Claude
  - Store the response in the run's JSON file
- Generate the AI headline for the run
- Generate era summaries

### JSON Schema (Shipped in Repo)

```json
{
  "meta": {
    "seed": 7714,
    "headline": "The Near-Miss Century: Climate Crisis Barely Averted",
    "headline_source": "claude/claude-sonnet-4-20250514",
    "verdict": "PROGRESS",
    "composite_score": 0.45
  },
  "events": [
    {
      "year_month": "2000-11",
      "node_id": "2000_election",
      "title": "US Presidential Election",
      "desc": "Gore wins Florida by 2,211 votes",
      "status": "DIVERGENCE",
      "explanation": "Full recount completes; Gore wins by ~2,000 votes",
      "narration": "The recount took eleven days longer than anyone expected. When the final tally from Palm Beach County arrived — adjusted for the butterfly ballot that had sent three thousand Gore votes to Pat Buchanan — the margin was 2,211. Not comfortable, but clear.",
      "narration_source": "claude/claude-sonnet-4-20250514"
    },
    {
      "year_month": "2001-09",
      "node_id": "2001_911",
      "title": "September 11 Attacks",
      "desc": "Plot disrupted by FBI",
      "status": "DIVERGENCE",
      "explanation": "Phoenix memo acted on; two cells arrested in August",
      "narration": "In the stillness of a September morning that, in another timeline, would become the defining trauma of a generation — nothing happened. Two FBI field agents in Minneapolis, acting on a memo that in our world gathered dust, had knocked on a door in Eagan three weeks earlier.",
      "narration_source": "claude/claude-sonnet-4-20250514"
    },
    {
      "year_month": "2001-12",
      "node_id": "2001_china_wto",
      "status": "HISTORICAL",
      "narration": null
    }
  ]
}
```

**These files live in the repo at `src/csim/data/curated/`.** They're versioned, auditable, and free to use. The one-time Claude cost is a development expense, like buying a font license.

### Curated Seed Selection

```python
def select_curated_seeds(n=200, candidates=100_000):
    """Run 100K simulations, select 200 that maximize narrative variety."""
    
    # Quotas by verdict (biased toward interesting over representative)
    quotas = {
        "GOLDEN_AGE": 15,       # Rare but fascinating
        "PROGRESS": 40,
        "MUDDLING_THROUGH": 30,
        "DECLINE": 35,
        "CATASTROPHE": 30,      # People love watching train wrecks
        "EXTINCTION": 10,       # Very rare, must include
        "TRANSCENDENCE": 15,    # Very rare, must include
        "RADICALLY_DIFFERENT": 25,
    }
    
    # Also select for:
    # - Notable causal chains ("The Gore Effect", "The Iraq Cascade")
    # - Historical-match seeds (reproduce actual history almost exactly)
    # - Extreme outliers (best/worst centuries)
    # - Diversity in first-divergence timing
    # - Seeds where nuclear events occur
    # - Seeds where extinction happens
    # - Seeds where transcendence triggers
```

---

## 2. Local Narration for Custom Seeds

### When It Fires

```python
def get_narration(seed, node_id, event, context) -> str | None:
    """
    Narration resolution order:
    1. Check curated library (pre-generated JSON)
    2. Check local cache (~/.21csim/cache/)
    3. Generate via local model (Ollama)
    4. Return None (no narration for this event)
    """
    
    # 1. Pre-generated?
    curated = load_curated_narration(seed, node_id)
    if curated:
        return curated  # Claude-quality, instant
    
    # 2. Cached from previous run?
    cached = load_cached_narration(seed, node_id)
    if cached:
        return cached  # Previously generated, instant
    
    # 3. Local model available?
    if llm_provider.is_available():
        narration = await llm_provider.generate(
            build_local_prompt(event, context)
        )
        cache_narration(seed, node_id, narration.text)
        return narration.text  # Ollama, 2-5 second latency
    
    # 4. Nothing available
    return None  # Event displays without narration
```

### Ollama: Auto-Detection

```python
def detect_ollama() -> OllamaProvider | None:
    """Check if Ollama is running and has a usable model."""
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code != 200:
            return None
        models = [m["name"] for m in r.json().get("models", [])]
        
        # Prefer models in this order
        preferred = [
            "llama3.1:8b",
            "llama3.2:8b",
            "mistral:7b",
            "gemma2:9b",
            "llama3.1:8b-instruct",
        ]
        for model in preferred:
            if model in models:
                return OllamaProvider(model=model)
        
        # Use whatever's available
        if models:
            return OllamaProvider(model=models[0])
        
        return None
    except (httpx.ConnectError, httpx.TimeoutException):
        return None
```

### The Local Prompt (Tight and Specific)

This is the critical piece. 8B models need a very different prompt than Claude — shorter context, explicit structure, a concrete example, and clear constraints.

```python
LOCAL_NARRATOR_SYSTEM = """You write alternate history narration. Voice: a calm historian in 2150 looking back. 2-3 sentences only. No exclamation points. Specific concrete details. Treat the alternate timeline as real history that happened."""

def build_local_prompt(event, context) -> str:
    # Keep context minimal for 8B — last 3 events only
    recent = context.preceding_events[-3:]
    recent_text = "\n".join(
        f"  {e.year_month}: {e.description}" for e in recent
    )
    
    return f"""{LOCAL_NARRATOR_SYSTEM}

Recent timeline:
{recent_text}

Event to narrate:
  Date: {event.year_month}
  What happened: {event.description}
  Why it diverged: {event.explanation}
  In our timeline: {event.historical_description}

Example (for tone only — do NOT copy):
"The recount took eleven days longer than anyone expected. When the final tally arrived, the margin was 2,211 votes. Not comfortable, but clear."

Write 2-3 sentences for the event above:"""
```

**Why this works for 8B models:**
- System instruction is one sentence establishing the voice
- Context is minimal (last 3 events, not the full timeline)
- The event details are structured with clear labels
- A concrete example shows the exact tone/length expected
- The final instruction is a single imperative sentence
- Total prompt is ~200 tokens — well within 8B attention capacity

### Latency Management

In CINEMATIC mode, the 2-5 second Ollama generation latency is hidden by the existing delay between events. The pacing algorithm already creates 3-12 second gaps between events. The narration generation happens during the gap before the event appears:

```python
# Timeline:
# 1. Previous event finishes displaying
# 2. Cursor blinks during gap (3-12 seconds in CINEMATIC)
# 3. During the gap, pre-fetch narration for next event ← HERE
# 4. Next event appears
# 5. Narration types out below it

async def run_event_loop(events, renderer, llm):
    for i, event in enumerate(events):
        # Pre-fetch narration while the cursor blinks
        narration_task = None
        if should_narrate(event) and not has_narration(event):
            narration_task = asyncio.create_task(
                generate_narration(event, context, llm)
            )
        
        # Wait for pacing delay (cursor blinks)
        await asyncio.sleep(pacing_delay)
        
        # Render event header
        renderer.render_event(event)
        
        # If narration was being generated, await it
        if narration_task:
            narration = await narration_task
            renderer.render_narration(narration)  # Typewriter effect
```

In most cases, the narration is ready before the gap finishes, so there's zero perceived latency. Only on very short gaps (same-month events) might the user see a brief pause. Even then, the typewriter effect masks it — the user thinks the typing animation is the delay, not the model inference.

---

## 3. Provider Abstraction (Simplified)

Given the hybrid strategy, the provider layer is simpler than the original spec. There are really only two providers that matter:

```python
# src/csim/llm/base.py

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 300) -> str: ...
    
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def model_name(self) -> str: ...


# src/csim/llm/ollama.py

class OllamaProvider(LLMProvider):
    """HTTP client to local Ollama daemon."""
    
    def __init__(self, model="llama3.1:8b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    async def generate(self, prompt, max_tokens=300):
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{self.base_url}/api/generate", json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7},
            })
            return r.json()["response"].strip()
    
    def is_available(self):
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            models = [m["name"] for m in r.json().get("models", [])]
            return self.model in models
        except Exception:
            return False
    
    def model_name(self):
        return f"ollama/{self.model}"


# src/csim/llm/claude.py

class ClaudeProvider(LLMProvider):
    """Anthropic API client. Used only for export-library, not runtime."""
    
    def __init__(self, api_key=None, model="claude-sonnet-4-20250514"):
        import os
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
    
    async def generate(self, prompt, max_tokens=300):
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            return r.json()["content"][0]["text"].strip()
    
    def is_available(self):
        return bool(self.api_key)
    
    def model_name(self):
        return f"claude/{self.model}"


# src/csim/llm/null.py

class NullProvider(LLMProvider):
    """No-op. Returns empty strings. Simulation runs without narration."""
    
    async def generate(self, prompt, max_tokens=300):
        return ""
    
    def is_available(self):
        return True
    
    def model_name(self):
        return "none"
```

### Resolver

```python
# src/csim/llm/resolver.py

def resolve_provider(explicit: str | None = None) -> LLMProvider:
    """
    Resolve narration provider.
    
    For normal runtime (21csim run):
      1. Ollama auto-detect → use it
      2. Nothing → NullProvider (no narration on custom seeds)
    
    For library generation (21csim export-library --narrate):
      Uses ClaudeProvider explicitly (requires ANTHROPIC_API_KEY)
    
    Pre-generated narrations from the curated library are loaded
    from JSON, not via any provider — they bypass this entirely.
    """
    if explicit == "claude":
        return ClaudeProvider()
    if explicit == "none":
        return NullProvider()
    if explicit == "ollama" or explicit is None:
        ollama = detect_ollama()
        if ollama:
            return ollama
    return NullProvider()
```

---

## 4. User Experience Flow

### Web Viewer User (90% of users)

```
1. Visits yoursite.com/21csim
2. Clicks "Watch a Random Century"
3. Pre-generated JSON loads (includes Claude narrations)
4. Events unfold with high-quality narration
5. Zero cost, zero latency, zero configuration
```

### CLI User — Curated Seed

```
$ pip install 21csim
$ 21csim run --seed 7714

Loading curated run (seed 7714)...
Narrations: pre-generated (claude/claude-sonnet-4-20250514)

[events unfold with Claude-quality narration, loaded from JSON]
```

### CLI User — Custom Seed, Has Ollama

```
$ pip install 21csim
$ ollama pull llama3.1:8b
$ 21csim run --seed 12345

Detecting narrator...
  ✓ Ollama (llama3.1:8b) on localhost:11434

[events unfold; narrations generated locally, 2-5s per narrated event]
[narrations cached to ~/.21csim/cache/ for instant replay]
```

### CLI User — Custom Seed, No Local Model

```
$ pip install 21csim
$ 21csim run --seed 12345

Detecting narrator...
  No local model detected. Running without narration.
  
  Tip: Install Ollama for AI narration on custom seeds:
    curl -fsSL https://ollama.ai/install.sh | sh
    ollama pull llama3.1:8b

[events unfold without narration — still a complete experience]
```

### Developer — Generating the Curated Library

```
$ export ANTHROPIC_API_KEY=sk-ant-...
$ 21csim export-library \
    --count 200 \
    --narrate \
    --narrator-provider claude \
    --output src/csim/data/curated/

[generates 200 runs with Claude narrations — one-time, ~$4]
[output committed to repo]
```

---

## 5. CLI Flags (Final)

```
21csim run [OPTIONS]
  --seed INT             Seed (if curated, loads pre-generated narration)
  --narrate / --no-narrate  Enable/disable narration (default: --narrate)
  --provider PROVIDER    Force provider: ollama|claude|none (default: auto)
  --model MODEL          Override model (e.g., mistral:7b)
  --no-ai                Alias for --provider none

21csim export-library [OPTIONS]
  --count INT            Number of curated seeds (default: 200)
  --candidates INT       Candidate pool size (default: 100000)
  --narrate              Generate AI narrations (requires --narrator-provider)
  --narrator-provider P  Provider for narration: claude|ollama
  --narrator-model M     Model override
  --output DIR           Output directory
```

---

## 6. Cost Summary

| What | When | Cost | Who Pays |
|------|------|------|----------|
| Curated library narrations (200 seeds) | Once, during development | ~$4 | You (development expense) |
| Custom seed narration via Ollama | Every custom run | $0 | Nobody (local inference) |
| Custom seed narration via Claude | If user opts in | ~$0.02/run | User (their API key) |
| Web viewer narrations | Never | $0 | Pre-generated in JSON |
| Headline generation (curated) | Once, during development | ~$0.10 | You |
| Headline generation (custom) | Per custom run | $0 (Ollama) | Nobody |

**Total ongoing cost: $0.** The only cost is the one-time ~$4 library generation during development.

---

## 7. Quality Comparison

| Aspect | Claude (curated) | Ollama 8B (custom) |
|--------|:---:|:---:|
| Prose quality | Excellent — literary, nuanced | Good — solid, occasionally generic |
| Historical detail | Rich — references specific people, dates | Adequate — gets the point across |
| Causal awareness | Strong — references earlier events naturally | Moderate — follows prompt examples |
| Foreshadowing | Yes — knows the century's verdict | No — lacks full context |
| Consistency | High — same voice across 200 runs | Variable — depends on prompt adherence |
| Emotional impact | High — "nothing happened" hits hard | Medium — functional but less artful |
| Latency | 0ms (pre-generated) | 2-5s (hidden in pacing gap) |
| Cost per narration | ~$0.001 (one-time) | $0 |

**The honest assessment:** For the 200 curated seeds that most people will ever see, narration quality is as good as it can possibly be. For the long tail of custom seeds, narration is "good enough" — solid prose that enhances the experience without being literary. And the simulation is a complete, compelling experience even with zero narration.

---

## 8. Future Option: Fine-Tuned LoRA

If demand warrants, a future enhancement:

1. Use the ~3,600 Claude-generated narrations as training data
2. Fine-tune a 7-8B model using QLoRA (~4 hours on one GPU)
3. Ship the LoRA adapter (~100MB) in the repo
4. Local narration quality approaches Claude for this specific task
5. Cost: $0 ongoing, ~$0 training cost (using existing data)

This is a Phase 5+ enhancement. The hybrid strategy works well enough to ship.

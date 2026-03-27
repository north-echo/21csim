# 21csim — LLM Provider Abstraction

## Addendum to AI Integration Spec

---

## Design

Local-first. The simulation ships with narration enabled by default using whatever local model the user has available. Claude API is an optional upgrade for higher-quality prose. No API key, no account, no network required for the base experience.

### Provider Priority (Auto-Detection)

```
1. Check config file (~/.21csim/config.yaml) for explicit provider
2. If none configured, auto-detect in order:
   a. Ollama running on localhost:11434 → use it
   b. llama-cpp-python installed → use it
   c. vLLM running on localhost:8000 → use it
   d. ANTHROPIC_API_KEY env var set → use Claude API
   e. Nothing available → narration disabled, simulation runs without prose
```

The simulation never fails because AI isn't available. Narration is an enhancement layer.

---

## Provider Interface

```python
# src/csim/llm/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, AsyncIterator

@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float

class LLMProvider(ABC):
    """
    Abstract base for all LLM providers.
    
    All providers implement the same interface. The simulation engine
    doesn't know or care which provider is active.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a completion."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion token by token. Used for typewriter effect."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is ready to use."""
        ...

    @abstractmethod
    def model_name(self) -> str:
        """Return the active model name for display."""
        ...

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__
```

---

## Provider Implementations

### 1. Ollama

The default for most users. Ollama runs as a local daemon and exposes an OpenAI-compatible API. Users just `ollama pull llama3.1:8b` and it works.

```python
# src/csim/llm/ollama.py

import httpx
from .base import LLMProvider, LLMResponse

class OllamaProvider(LLMProvider):
    """
    Ollama provider. Connects to local Ollama daemon.
    
    Default: http://localhost:11434
    Default model: llama3.1:8b (pulled automatically if not present)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        auto_pull: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.auto_pull = auto_pull
        self.client = httpx.AsyncClient(timeout=120)

    def is_available(self) -> bool:
        """Check if Ollama daemon is running and model is available."""
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            if r.status_code != 200:
                return False
            models = [m["name"] for m in r.json().get("models", [])]
            if self.model not in models and self.auto_pull:
                # Model not present — could auto-pull, but that's slow
                # Instead, return False and let the resolver try next provider
                # or prompt the user
                return False
            return self.model in models
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def generate(self, prompt, max_tokens=300, temperature=0.7, stop=None):
        import time
        t0 = time.monotonic()
        
        r = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "stop": stop or [],
                },
            },
        )
        data = r.json()
        
        return LLMResponse(
            text=data["response"].strip(),
            model=self.model,
            provider="ollama",
            tokens_used=data.get("eval_count", 0),
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_stream(self, prompt, max_tokens=300, temperature=0.7):
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            },
        ) as r:
            async for line in r.aiter_lines():
                import json
                chunk = json.loads(line)
                if chunk.get("response"):
                    yield chunk["response"]
                if chunk.get("done"):
                    break

    def model_name(self) -> str:
        return f"ollama/{self.model}"
```

### 2. llama-cpp-python

Direct local inference without a daemon. Good for users who want a self-contained tool without running a separate service.

```python
# src/csim/llm/llamacpp.py

from .base import LLMProvider, LLMResponse

class LlamaCppProvider(LLMProvider):
    """
    llama-cpp-python provider. Loads model directly into process memory.
    
    Requires: pip install llama-cpp-python
    Model file: user provides path to GGUF file
    """
    
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,  # -1 = offload all layers to GPU
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm = None

    def _load(self):
        if self._llm is None:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )

    def is_available(self) -> bool:
        try:
            import llama_cpp  # noqa: F401
            from pathlib import Path
            return Path(self.model_path).exists()
        except ImportError:
            return False

    async def generate(self, prompt, max_tokens=300, temperature=0.7, stop=None):
        import time, asyncio
        self._load()
        t0 = time.monotonic()
        
        # Run in thread pool since llama-cpp is synchronous
        result = await asyncio.to_thread(
            self._llm,
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
        )
        
        text = result["choices"][0]["text"].strip()
        return LLMResponse(
            text=text,
            model=self.model_path.split("/")[-1],
            provider="llama.cpp",
            tokens_used=result["usage"]["completion_tokens"],
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_stream(self, prompt, max_tokens=300, temperature=0.7):
        import asyncio
        self._load()
        
        def _stream():
            return self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
        
        # Stream from thread
        gen = await asyncio.to_thread(_stream)
        for chunk in gen:
            token = chunk["choices"][0]["text"]
            if token:
                yield token

    def model_name(self) -> str:
        return f"llama.cpp/{self.model_path.split('/')[-1]}"
```

### 3. vLLM

For users running a dedicated inference server (heavier setup, better throughput for batch generation).

```python
# src/csim/llm/vllm.py

import httpx
from .base import LLMProvider, LLMResponse

class VLLMProvider(LLMProvider):
    """
    vLLM provider. Connects to vLLM's OpenAI-compatible API.
    
    Default: http://localhost:8000
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str = None,  # Auto-detected from server
    ):
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.client = httpx.AsyncClient(timeout=120)

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/v1/models", timeout=3)
            if r.status_code == 200:
                models = r.json().get("data", [])
                if models:
                    if self._model is None:
                        self._model = models[0]["id"]
                    return True
            return False
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def generate(self, prompt, max_tokens=300, temperature=0.7, stop=None):
        import time
        t0 = time.monotonic()
        
        r = await self.client.post(
            f"{self.base_url}/v1/completions",
            json={
                "model": self._model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop,
            },
        )
        data = r.json()
        
        return LLMResponse(
            text=data["choices"][0]["text"].strip(),
            model=self._model,
            provider="vllm",
            tokens_used=data["usage"]["completion_tokens"],
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_stream(self, prompt, max_tokens=300, temperature=0.7):
        async with self.client.stream(
            "POST",
            f"{self.base_url}/v1/completions",
            json={
                "model": self._model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as r:
            async for line in r.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    chunk = json.loads(line[6:])
                    token = chunk["choices"][0].get("text", "")
                    if token:
                        yield token

    def model_name(self) -> str:
        return f"vllm/{self._model}"
```

### 4. Claude API

Premium provider for highest-quality narration. Requires API key.

```python
# src/csim/llm/claude.py

import httpx
from .base import LLMProvider, LLMResponse

class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude API provider.
    
    Requires: ANTHROPIC_API_KEY environment variable or config.
    Default model: claude-sonnet-4-20250514
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        import os
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = httpx.AsyncClient(
            timeout=60,
            headers={
                "x-api-key": self.api_key or "",
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    async def generate(self, prompt, max_tokens=300, temperature=0.7, stop=None):
        import time
        t0 = time.monotonic()
        
        r = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        data = r.json()
        text = data["content"][0]["text"].strip()
        
        return LLMResponse(
            text=text,
            model=self.model,
            provider="claude",
            tokens_used=data["usage"]["output_tokens"],
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_stream(self, prompt, max_tokens=300, temperature=0.7):
        async with self.client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "stream": True,
                "messages": [{"role": "user", "content": prompt}],
            },
        ) as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        chunk = json.loads(line[6:])
                        if chunk.get("type") == "content_block_delta":
                            yield chunk["delta"].get("text", "")
                    except json.JSONDecodeError:
                        pass

    def model_name(self) -> str:
        return f"claude/{self.model}"
```

### 5. Null Provider (Fallback)

When nothing is available. Simulation runs normally without narration.

```python
# src/csim/llm/null.py

from .base import LLMProvider, LLMResponse

class NullProvider(LLMProvider):
    """
    Null provider. Returns empty responses.
    Used when no LLM is available. Simulation runs without narration.
    """
    
    def is_available(self) -> bool:
        return True  # Always "available" as the last fallback

    async def generate(self, prompt, max_tokens=300, temperature=0.7, stop=None):
        return LLMResponse(
            text="",
            model="none",
            provider="null",
            tokens_used=0,
            latency_ms=0,
        )

    async def generate_stream(self, prompt, max_tokens=300, temperature=0.7):
        return
        yield  # Make it a generator that yields nothing

    def model_name(self) -> str:
        return "none"
```

---

## Provider Resolver

```python
# src/csim/llm/resolver.py

from .base import LLMProvider
from .ollama import OllamaProvider
from .llamacpp import LlamaCppProvider
from .vllm import VLLMProvider
from .claude import ClaudeProvider
from .null import NullProvider

from typing import Optional
import yaml
from pathlib import Path

CONFIG_PATH = Path.home() / ".21csim" / "config.yaml"

def resolve_provider(
    explicit_provider: Optional[str] = None,
    explicit_model: Optional[str] = None,
) -> LLMProvider:
    """
    Resolve which LLM provider to use.
    
    Priority:
    1. Explicit CLI flag (--provider ollama --model llama3.1:8b)
    2. Config file (~/.21csim/config.yaml)
    3. Auto-detection (local-first)
    4. Null provider (no narration)
    """
    
    # 1. Explicit CLI override
    if explicit_provider:
        return _build_provider(explicit_provider, explicit_model)
    
    # 2. Config file
    config = _load_config()
    if config and config.get("llm", {}).get("provider"):
        llm_config = config["llm"]
        return _build_provider(
            llm_config["provider"],
            llm_config.get("model"),
            **llm_config.get("options", {}),
        )
    
    # 3. Auto-detect (local-first)
    candidates = [
        OllamaProvider(),
        VLLMProvider(),
        # llama.cpp requires a model path, so it can't auto-detect
        ClaudeProvider(),
    ]
    
    for provider in candidates:
        if provider.is_available():
            return provider
    
    # 4. Nothing available
    return NullProvider()


def _build_provider(name: str, model: str = None, **kwargs) -> LLMProvider:
    providers = {
        "ollama": lambda: OllamaProvider(model=model or "llama3.1:8b", **kwargs),
        "llamacpp": lambda: LlamaCppProvider(model_path=model or kwargs.get("model_path", ""), **kwargs),
        "vllm": lambda: VLLMProvider(model=model, **kwargs),
        "claude": lambda: ClaudeProvider(model=model or "claude-sonnet-4-20250514", **kwargs),
        "none": lambda: NullProvider(),
    }
    builder = providers.get(name.lower())
    if not builder:
        raise ValueError(f"Unknown provider: {name}. Options: {list(providers.keys())}")
    return builder()


def _load_config() -> Optional[dict]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return None
```

---

## Configuration

### Config File (`~/.21csim/config.yaml`)

```yaml
# LLM provider for AI narration, headlines, and explanations
llm:
  # Provider: ollama | llamacpp | vllm | claude | none
  provider: ollama
  
  # Model name (provider-specific)
  model: llama3.1:8b
  
  # Provider-specific options
  options:
    # Ollama
    base_url: http://localhost:11434
    auto_pull: false
    
    # llama.cpp (uncomment if using llamacpp provider)
    # model_path: /path/to/model.gguf
    # n_gpu_layers: -1
    # n_ctx: 2048
    
    # vLLM (uncomment if using vllm provider)
    # base_url: http://localhost:8000
    
    # Claude (uncomment if using claude provider)
    # api_key: sk-ant-...  # Or use ANTHROPIC_API_KEY env var

# Narration settings
narration:
  enabled: true
  max_tokens: 300
  temperature: 0.7
  # Only narrate events with impact > threshold
  impact_threshold: true
  # Cache narrations to avoid re-generating
  cache: true
  cache_dir: ~/.21csim/cache/narrations/
```

### CLI Flags (Override Config)

```
21csim run --seed 42 [LLM OPTIONS]
  --provider PROVIDER    Override LLM provider (ollama|llamacpp|vllm|claude|none)
  --model MODEL          Override model name
  --narrate / --no-narrate  Enable/disable AI narration
  --no-ai                Disable all AI features (equivalent to --provider none)
```

### First-Run Experience

```
$ 21csim run --seed 42

Detecting AI provider...
  ✓ Ollama detected on localhost:11434
  ✓ Model llama3.1:8b available
  AI narration enabled (ollama/llama3.1:8b)

Starting simulation...
```

Or if nothing is available:

```
$ 21csim run --seed 42

Detecting AI provider...
  ✗ No Ollama daemon detected
  ✗ llama-cpp-python not installed
  ✗ No vLLM server detected
  ✗ No ANTHROPIC_API_KEY set
  
  AI narration disabled. Simulation will run without prose.
  
  To enable narration:
    • Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
    • Pull a model: ollama pull llama3.1:8b
    • Or set ANTHROPIC_API_KEY for Claude API

Starting simulation...
```

---

## Prompt Tuning for Local Models

Small models (8B parameters) need tighter prompts than Claude. The narrator prompt is adjusted per provider:

```python
# src/csim/llm/prompts.py

def narrator_prompt(event, context, provider_name: str) -> str:
    """
    Build the narrator prompt, adjusted for model capability.
    
    Claude: Rich context, nuanced instructions, expects literary quality
    Local 8B: Shorter context, explicit structure, simpler instructions
    """
    
    if provider_name == "claude":
        return _claude_narrator_prompt(event, context)
    else:
        return _local_narrator_prompt(event, context)


def _local_narrator_prompt(event, context) -> str:
    """
    Optimized for 8B models. Shorter, more explicit, with a clear example.
    """
    return f"""Write 2-3 sentences of alternate history narration for this event.
Voice: A calm historian looking back from the future. No exclamation points. Treat this as real history.

Previous key events:
{format_brief_timeline(context.preceding_events[-5:])}

Event to narrate:
Date: {event.year_month}
What happened: {event.description}
Why it diverged: {event.explanation}
What would have happened in our timeline: {event.historical_description}

Example of the right tone:
"The recount took eleven days longer than anyone expected. When the final tally arrived, the margin was 2,211 votes. Not comfortable, but clear."

Now write 2-3 sentences for the event above. Be specific and concrete. No preamble."""


def _claude_narrator_prompt(event, context) -> str:
    """
    Full-context prompt for Claude. Expects literary quality.
    """
    return f"""You are the narrator of an alternate history simulation, writing
from the perspective of a historian in 2150 looking back at an alternate 21st century.

Your voice is: calm, historically literate, slightly melancholic. You treat this
alternate timeline as real history. You write 2-4 sentences per event.

The century's eventual verdict is: {context.verdict}.

Timeline so far:
{format_timeline(context.preceding_events)}

Current world state:
{format_world_state(context.world_state)}

Event to narrate:
  Date: {event.year_month}
  Title: {event.title}
  Outcome: {event.description}
  Status: {event.status}
  Branch taken: {event.branch_taken} (probability: {event.probability_of_branch:.0%})
  Historical baseline: {event.historical_description}

Write 2-4 sentences. Ground it in specific, concrete details. Reference earlier
events when relevant. Do not repeat information the reader already knows."""
```

### Narration Quality by Provider

| Provider | Model | Quality | Latency | Notes |
|----------|-------|---------|---------|-------|
| Ollama | llama3.1:8b | Good — solid prose, occasionally generic | 2-5s on GPU | Best default experience |
| Ollama | llama3.1:70b-q4 | Very good — nuanced, literary | 8-15s on good GPU | If user has the VRAM |
| Ollama | mistral:7b | Good — slightly more creative, less precise | 2-4s on GPU | Good alternative |
| Ollama | gemma2:9b | Good — clean prose | 2-5s on GPU | Another option |
| llama.cpp | any 8B GGUF | Same as Ollama equivalent | Similar | More manual setup |
| vLLM | any supported | Depends on model | Fast (batched) | Best for export-library |
| Claude | sonnet | Excellent — literary, nuanced, contextual | 1-3s (network) | Best quality, costs money |
| None | — | No narration | 0 | Simulation runs fine without |

### Recommended Local Models

```yaml
# In documentation / README:

# Best overall (default):
ollama pull llama3.1:8b

# Best quality if you have 48GB+ VRAM:
ollama pull llama3.1:70b-q4_K_M

# Fastest (slightly lower quality):
ollama pull mistral:7b

# Best for creative writing specifically:
ollama pull llama3.1:8b-instruct
```

---

## Narration Caching

Generated narrations are cached by (seed, node_id, model_name) to avoid re-generating on replay.

```python
# src/csim/llm/cache.py

import hashlib, json
from pathlib import Path

CACHE_DIR = Path.home() / ".21csim" / "cache" / "narrations"

def cache_key(seed: int, node_id: str, model: str) -> str:
    """Deterministic cache key."""
    raw = f"{seed}:{node_id}:{model}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def get_cached(seed: int, node_id: str, model: str) -> str | None:
    path = CACHE_DIR / f"{cache_key(seed, node_id, model)}.txt"
    if path.exists():
        return path.read_text()
    return None

def set_cached(seed: int, node_id: str, model: str, text: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{cache_key(seed, node_id, model)}.txt"
    path.write_text(text)
```

This means: first run of a seed generates narrations (takes time). Second run of the same seed loads from cache instantly. The cache is model-specific — switching from Ollama to Claude regenerates.

---

## Integration with Simulation Engine

```python
# In engine.py — the narration call point

async def simulate_with_narration(
    scenario: Scenario,
    seed: int,
    llm: LLMProvider,
    renderer: Renderer,
) -> SimOutcome:
    """
    Simulation loop with integrated narration.
    
    For each event:
    1. Sample and resolve (same as before)
    2. Render event header (title, description, status)
    3. If event qualifies for narration:
       a. Check cache
       b. If not cached, generate via LLM provider
       c. Render narration with typewriter effect
       d. Cache the result
    4. Continue to next event
    """
    rng = numpy.random.default_rng(seed)
    context = SimContext(seed=seed, preceding_events=[], world_state=WorldState())
    
    for node_id in traversal_order:
        event = resolve_node(node_id, rng, context)
        if event is None:
            continue
        
        # Render event header
        renderer.render_event(event)
        
        # Narration for qualifying events
        if should_narrate(event):
            narration = get_cached(seed, node_id, llm.model_name())
            if narration is None:
                prompt = narrator_prompt(event, context, llm.provider_name)
                response = await llm.generate(prompt)
                narration = response.text
                set_cached(seed, node_id, llm.model_name(), narration)
            
            renderer.render_narration(narration)  # Typewriter effect
        
        # Update context
        context.preceding_events.append(event)
        apply_effects(context.world_state, event.world_state_effects)
    
    return build_outcome(seed, context)


def should_narrate(event: SimEvent) -> bool:
    """Only narrate high-impact divergences and escalations."""
    if event.status == "HISTORICAL":
        return False
    if event.status == "ESCALATED":
        return True
    if event.status == "DIVERGENCE" and event.is_high_impact:
        return True
    return False
```

---

## Web Viewer: Dual Provider

The web viewer supports two modes:

### 1. Pre-generated narrations (default)

For the curated 200-run library, narrations are pre-generated during `export-library` and baked into the JSON. No LLM needed at view time. This is the default for the public web viewer.

### 2. Real-time narration (optional)

If the user provides an API key in the web viewer settings, narrations are generated in real-time via the Claude API from the browser. This enables narration for custom seeds and the scenario builder.

```typescript
// Web viewer — provider selection
const provider = apiKey 
  ? new ClaudeWebProvider(apiKey)
  : new PreGeneratedProvider(runData.narrations);
```

---

## Updated Dependency Tree

```toml
# pyproject.toml — core dependencies (no LLM required)
dependencies = [
    "typer>=0.12",
    "numpy>=1.26",
    "networkx>=3.2",
    "rich>=13.7",
    "pyyaml>=6.0",
    "httpx>=0.27",        # For Ollama/vLLM HTTP clients
]

# Optional dependencies for specific providers
[project.optional-dependencies]
llamacpp = ["llama-cpp-python>=0.2"]
claude = ["anthropic>=0.39"]
all = ["llama-cpp-python>=0.2", "anthropic>=0.39"]
```

Core install has zero LLM dependencies. Ollama and vLLM are accessed via HTTP (httpx). Only llama-cpp-python and the Anthropic SDK are optional installs.

```bash
# Minimal install (Ollama/vLLM via HTTP):
pip install 21csim

# With llama.cpp support:
pip install "21csim[llamacpp]"

# With Claude API:
pip install "21csim[claude]"

# Everything:
pip install "21csim[all]"
```

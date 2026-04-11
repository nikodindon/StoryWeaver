# StoryWeaver Engine — Project Context

## Project Overview

**StoryWeaver** is a **local-first narrative simulation engine** that transforms any book into a fully interactive, persistent world populated by autonomous AI agents. It is a Python 3.11+ CLI application powered by [llama.cpp](https://github.com/ggerganov/llama.cpp) for local LLM inference — no cloud APIs required.

The core idea: a book is treated as a **seed**, not a script. The engine extracts an implicit world model (entities, relationships, psychology, rules) from the text and makes it **executable** — you can explore it, interact with characters, and change the story.

### Key Differentiators

- **Not a chatbot** — characters are autonomous agents with persistent memory and goals
- **Not AI Dungeon** — the world has real structure (graph-based), not just LLM hallucination
- **Not Zork** — the world is AI-extracted from text, not hand-authored
- **Narrative gravity** — the world has a soft pull toward canonical events, but you can diverge
- **Tick-based simulation** — time passes and events cascade even without player input

## Architecture

### Pipeline Flow

```
Book (EPUB/TXT/PDF)
  → Ingestion (parse, clean, segment)
  → Extraction (4-pass offline LLM pipeline: structure → relations → psychology → symbolism)
  → Compilation (build WorldBundle: locations, characters, agents, rules)
  → Simulation (tick-based world evolution with autonomous agents)
  → Interaction (Zork-style CLI: you type, the world responds)
```

### Directory Structure

| Directory | Purpose |
|---|---|
| `storyweaver/ingestion/` | Book parsing (EPUB, PDF, TXT), text cleaning, chapter/scene segmentation |
| `storyweaver/extraction/` | Multi-pass LLM extraction pipeline (entities, relations, psychology, symbolism) |
| `storyweaver/compiler/` | WorldBundle construction from extraction artifacts |
| `storyweaver/world/` | Core data models: `Location`, `Character`, `WorldObject`, `Event`, `WorldRules`, `WorldBundle` |
| `storyweaver/agents/` | Autonomous AI agent system with memory, goals, and decision engine |
| `storyweaver/simulation/` | Tick-based world evolution, narrative gravity, divergence tracking |
| `storyweaver/interaction/` | Player input parsing (rule-based fast path + LLM fallback) |
| `storyweaver/narrative/` | Scene description, dialogue generation, style matching |
| `storyweaver/memory/` | Three-layer memory: structured state, FAISS vector store, active context window |
| `storyweaver/models/` | LLM abstraction layer (`LLMClient`, `LlamaCppClient`) |
| `storyweaver/cli/` | Typer-based CLI: `compile`, `play`, `inspect` |
| `storyweaver/utils/` | Logging, serialization, graph utilities |
| `data/` | Raw books, processed text, compiled worlds, LLM output cache |
| `configs/` | YAML config files (default settings, model paths) |
| `scripts/` | Standalone scripts for ingestion, extraction, compilation |
| `tests/` | pytest test suite |
| `notebooks/` | Jupyter notebooks for extraction testing and visualization |

### Current Implementation State

The project is in **V1 — Prototype** phase per the roadmap. Key modules exist with scaffolding:

- **World models** (`storyweaver/world/`): Dataclasses for `Location`, `Character`, `WorldObject`, `Event`, `WorldRules`, `WorldBundle` — serialization (`to_dict`/`from_dict`) is marked `NotImplemented`
- **CLI** (`storyweaver/cli/`): Typer app with `compile`, `play`, `inspect` commands wired up, but subcommands (`compile.py`, `inspect.py`) may need implementation
- **Ingestion** (`storyweaver/ingestion/`): `TextCleaner`, `Segmenter`, format handlers — has passing tests
- **LLM clients** (`storyweaver/models/`): `LLMClient` interface + `LlamaCppClient` for llama.cpp server
- **Agents, Simulation, Memory, Narrative, Interaction**: Module directories exist with `__init__.py` files — implementation is pending

## Building and Running

### Prerequisites

- Python 3.11+
- A running **llama.cpp server** (`llama-server`) with a GGUF model loaded
- GGUF models recommended: Mistral-22B, Mixtral-8x7B, or Qwen2.5-32B

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running llama.cpp

```bash
# Start llama.cpp server (OpenAI-compatible API on port 8080)
llama-server -m your-model.gguf --port 8080 --ctx-size 8192
```

Model URLs and task assignments are configured in `configs/models.yaml`.

### CLI Usage

```bash
# Compile a book into a world (can take 2-8 hours for a full novel)
storyweaver compile books/alice_in_wonderland.txt --model mistral-22b

# Play a compiled world
storyweaver play alice_in_wonderland

# Inspect a compiled world
storyweaver inspect alice_in_wonderland --show characters
storyweaver inspect alice_in_wonderland --character "The Queen of Hearts"
```

### Running Tests

```bash
pytest tests/
```

Tests use mock LLM responses to avoid requiring a live inference server.

## Development Conventions

### Code Style

- **Type hints everywhere** — all functions should be annotated
- **Pydantic models** for all data structures (note: current world models use `dataclass`, should migrate to Pydantic per CONTRIBUTING.md)
- **Loguru** for logging — `from loguru import logger`
- **No silent failures** — surface errors early

### Architecture Principles

1. **LLM calls go through `LLMClient` abstraction** — never import openai or llama.cpp directly in simulation code
2. **World graph is the source of truth** — not the LLM's context
3. **Multi-layer memory** — structured state (JSON) → vector memory (FAISS) → active context window
4. **Extraction is cacheable** — every LLM output cached by `hash(prompt + chunk_id)` to enable incremental re-runs
5. **Separation of concerns** — world logic stays out of LLM prompt code; keep layers isolated

### Testing Practices

- Use pytest with mock LLM responses
- Test extraction prompts against public domain texts (Project Gutenberg)
- New functionality must have tests before PR submission

### Configuration

- Global defaults: `configs/default.yaml`
- Model configuration: `configs/models.yaml`
- Environment variables: `.env.example` (copy to `.env` as needed)

## Key Technical Details

### World Bundle Format

A compiled world is a directory-based bundle containing:
- `manifest.json` — version, source book, compilation timestamp
- `locations.json`, `characters.json`, `objects.json`, `events_canon.json`
- `psychology/{char_id}.json` — per-character psychology models
- `social_graph.json`, `world_rules.json`, `narrative_gravity.json`
- `agents/{char_id}/` — system prompts and initial memory per character

### Memory System

Three layers:
1. **Structured State** (`state.json`) — pure data, no LLM, loaded fresh every interaction
2. **Vector Memory** (FAISS) — per-agent embedded event memories, top-k retrieval
3. **Active Context Window** — assembled per LLM call, target <4096 tokens

### Narrative Gravity

Canon events have `gravity_weight` (0.0–1.0). The **Author Ghost** (hidden meta-agent) subtly nudges agent decisions to maintain thematic coherence. High divergence unlocks "fully diverged" sandbox mode.

## File Reference

| File | Description |
|---|---|
| `README.md` | Project overview, architecture diagrams, roadmap |
| `ARCHITECTURE.md` | Deep technical design document (extraction pipeline, memory, agents, state persistence) |
| `CONTRIBUTING.md` | Contribution guidelines, dev setup, code style rules |
| `pyproject.toml` | Python project config, dependencies, CLI entry point |
| `configs/default.yaml` | Global engine defaults |
| `configs/models.yaml` | LLM model assignments per task |

## Roadmap Status

- **V1 (current)** — Basic ingestion, single-pass extraction, world graph, CLI exploration
- **V2** — Full 4-pass extraction, multi-agent system, tick-based evolution, persistent saves
- **V3** — Narrative gravity, Author Ghost, psychological trait model, divergence tracking
- **V4** — PDF ingestion, multi-book support, web UI, plugin API, community sharing

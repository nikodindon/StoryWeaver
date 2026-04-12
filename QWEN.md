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

### Recently Added Features (April 2026)

#### 🧹 Extraction Cleaning Pipeline ✨ NEW
- **`scripts/clean_extraction.py`** — Fixes known LLM extraction issues
- **Character deduplication**: "Harry" + "Harry Potter" → "Harry Potter"
- **Name resolution**: 60+ variant mappings (e.g. "you-know-who" → "Lord Voldemort")
- **Object filtering**: Removes trivial items (desserts, clothing, generic objects)
- **Event deduplication**: Hash-based dedup (description + participants + location)
- **Social graph cleaning**: Resolves character IDs in relationships
- **Fuzzy matching**: 0.75 similarity threshold for unknown variants
- **Output**: `extraction_cleaned.json` ready for compilation
- **Usage**: `python scripts/clean_extraction.py <world_name>`

#### 🏗️ Enhanced Compilation
- **`scripts/compile_hp_world.py --cleaned`** flag uses cleaned extraction
- **Comparison mode**: Can compile both raw and cleaned for comparison
- **Metadata tracking**: Records which version was used

#### 🌐 Gradio Web UI v2 (`scripts/web_ui_v2.py`)
- **Rich interactive web interface** with Gradio framework
- **LLM-generated scene descriptions** with fallback to static text
- **Save/Load system** — persistent game sessions to disk
- **Auto-save** every 10 actions
- **Quick Action buttons** — Look, Wait, Inventory, Help
- **Character dialogue** with memory integration
- **Rich world context panel** — live display of world state

#### 🖼️ Cover Art System
- **Auto-discovery** of cover images from `images/<world_name>/` directory
- **Supports** PNG, JPG, JPEG, WEBP formats
- **Fallback** to root `images/` directory with name matching
- **Displayed** when world is loaded in web UI

#### 🎵 Icecast Music Streaming
- **IcecastStreamer class** (`scripts/icecast_streamer.py`) — ffmpeg-based playlist streaming
- **Auto-detection** of OST from `audio/<world_name>/` directory
- **Icecast integration** — streams to configured mount point (default `/nova`)
- **Play/Pause/Stop controls** in web UI
- **Shuffle support** — randomizes playlist order
- **Singleton pattern** — one streamer instance per session

#### 💾 Game Session Management
- **GameStateManager** — save/load game state to disk
- **Auto-save** every 10 actions (configurable)
- **Save metadata** — tick count, location, world name, timestamp
- **Multiple saves** — list and select from available saves

### Current Harry Potter Test Case

We are currently testing with **Harry Potter and the Sorcerer's Stone**:
- **EPUB ingested** — 83 segments extracted to `data/processed/harry_potter_1/`
- **Extraction** — 4-pass LLM pipeline running OVERNIGHT (started ~21:46)
  * Pass 1: ✅ Structure (165 chars, 127 locations, 229 objects, 418 events)
  * Pass 2: ✅ Relations (5 social edges, 4 conflicts, 0 timeline — parse fail)
  * Pass 3: ⏳ Psychology (86 major characters after name variant resolution)
  * Pass 4: ⏳ Symbolism (pending)
  * **Code fix applied**: Name variant resolution (Ron + Ron Weasley → one entity)
- **Cleaning script ready** — `scripts/clean_extraction.py` (run after extraction completes)
- **Compilation ready** — `scripts/compile_hp_world.py --cleaned`
- **Cover art ready** — `images/Harry Potter 01 Harry Potter and the Sorcerer's Stone/*.png`
- **OST ready** — 19 John Williams tracks in `audio/Harry Potter 01 Harry Potter and the Sorcerer's Stone/`
- **Icecast server** — running on `localhost:8000` with mount `/nova`
- **Monitoring** — `scripts/monitor_extraction.ps1` (auto-checks every 10 min)
- **Documentation** — `data/HARRY_POTTER_COMPILATION_GUIDE.md` (complete walkthrough)

#### Known Issues (to fix in V1.1 with Stephen King tests):
- **Pass 1 false-positive characters**: Places ("Hogwarts School"), objects ("Weasley sweater"), animals ("tabby cat"), creatures ("mountain troll") are extracted as "characters"
- **Timeline parse failure**: LLM produces invalid JSON for timeline extraction
- **6 segments with JSON parse failures**: LLM produces malformed JSON for some chunks
- **No entity type validation**: Need to filter non-human "characters" before psychology pass

#### Compilation Plan (when extraction finishes):
```bash
# Step 1: Clean extraction (fix duplicates, filter trivial objects)
python scripts/clean_extraction.py harry_potter_1

# Step 2: Compile cleaned world
python scripts/compile_hp_world.py --cleaned

# Step 3: Test web UI
python scripts/web_ui_v2.py
```

### Development Strategy — Iterative Improvement

**Phase 1: HP Moonshot** *(current — overnight extraction)*
- Goal: End-to-end pipeline validation
- Expected: First playable demo (imperfect but functional)
- Lesson: Identify structural issues at scale

**Phase 2: Stephen King Short Stories** *(planned — rapid iteration)*
- Test work: *Macabre* collection (EPUB, multiple short stories)
- Why: Short stories = fast iteration (minutes vs hours)
- Goals:
  - Fix Pass 1 false-positive characters
  - Improve extraction prompts
  - Add entity type validation
  - Test cleaning pipeline on diverse inputs

**Phase 3: Engine Refinement**
- Apply learnings from Phase 1 & 2
- Fix root causes, not just symptoms
- Add automated tests for extraction quality

**Phase 4: Return to Harry Potter**
- Re-extract with improved engine
- Compare V1 vs V2 quality
- Full polished HP demo

## Building and Running

### Prerequisites

- Python 3.11+
- A running **llama.cpp server** (`llama-server`) with a GGUF model loaded
- GGUF models recommended: Mistral-22B, Mixtral-8x7B, or Qwen2.5-32B
- **Gradio** — for web UI (`pip install gradio`)
- **ffmpeg** — for Icecast music streaming
- **Icecast2** — local streaming server (optional, for music)

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

# Or use port 8090 (our current setup)
llama-server -m your-model.gguf --port 8090 --ctx-size 8192
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

### Web UI Usage

```bash
# Launch Gradio web interface
python scripts/web_ui_v2.py

# Open in browser: http://localhost:7860
```

Features:
- Select and load a world
- Cover art auto-displays if found in `images/<world_name>/`
- Music auto-streams if OST found in `audio/<world_name>/`
- Type commands or use Quick Action buttons
- Save/load game sessions

### Icecast Setup (for music streaming)

```bash
# 1. Install icecast2 (package manager or official installer)
# 2. Configure icecast.xml (see project root for example)
# 3. Start server
icecast2 -c icecast.xml

# 4. Verify: http://localhost:8000
```

Default config:
- Host: `localhost`
- Port: `8000`
- Mount: `/nova`
- Password: `hackme`

### Extraction Pipeline

```bash
# Step 1: Ingest book
python scripts/ingest_book.py "path/to/book.epub" --output world_name

# Step 2: Run extraction (takes hours)
python scripts/run_extraction.py world_name --model-url http://localhost:8090

# Step 3: Compile world
python scripts/compile_world.py world_name

# Or use our helper script for Harry Potter
python scripts/compile_hp_world.py
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

- **V1 (current)** — Basic ingestion ✅, extraction pipeline ✅, world graph ✅, CLI ✅, **Web UI with cover art & music ✅**, save/load system ✅
- **V2** — Full 4-pass extraction, multi-agent system, tick-based evolution, persistent saves
- **V3** — Narrative gravity, Author Ghost, psychological trait model, divergence tracking
- **V4** — PDF ingestion, multi-book support, web UI enhancements, plugin API, community sharing

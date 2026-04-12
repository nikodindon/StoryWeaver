# 📚 StoryWeaver Engine

> **Don't read the story. Enter it.**

StoryWeaver is a **local-first narrative simulation engine** that transforms any book into a fully interactive, persistent world — populated by autonomous AI agents, explorable freely, and shaped by your choices.

This is not a chatbot wrapper. This is not AI Dungeon.

This is a **narrative compiler** — it processes a raw text, extracts a structured world model, builds psychologically-grounded AI agents for every character, and runs a persistent tick-based simulation you can explore like a text adventure.

Everything runs locally. No cloud. No API keys. Powered by [llama.cpp](https://github.com/ggerganov/llama.cpp).

---

## 🎬 FEATURED DEMO — Harry Potter & the Sorcerer's Stone *(In Progress)*

> **A full book → playable world compilation, end-to-end.**

We are currently building a **complete immersive demo** from the first Harry Potter novel. Here's what it will look like:

### What You'll Experience

```
┌─────────────────────────────────────────────────────────────┐
│  🖼️  [Harry Potter Movie Cover Art]                       │
│  🎵  "Hedwig's Theme" playing via Icecast                   │
│  🎙️  Narration voice (edge_tts) — coming soon              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  You stand at King's Cross Station. The platform signs      │
│  blur between "9" and "10" as you approach the barrier.     │
│  A red-haired family chats nearby. Their son holds a cage   │
│  with a snowy owl inside.                                   │
│                                                             │
│  > follow the weasleys                                      │
│                                                             │
│  You watch as they pass straight through the barrier        │
│  between platforms 9 and 10, vanishing into thin air.       │
│  The Hogwarts Express looms ahead, steam billowing...       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The Full Pipeline (Being Built Right Now)

| Step | Status | Description |
|---|---|---|
| **1. Ingestion** | ✅ Done | 83 segments extracted from EPUB |
| **2. Extraction** | ⏳ Running | 4-pass LLM pipeline (74/83 segments, ~89%) |
| **3. Cleaning** | ✅ Ready | Dedup, name resolution, filtering (60+ mappings) |
| **4. Compilation** | ✅ Ready | World bundle with characters, locations, events |
| **5. Web UI** | ✅ Done | Gradio interface with cover art + music |
| **6. Voice (TTS)** | 🔜 Planned | edge_tts for character voices & narration |

### What Makes This Demo Special

**🏰 A Living World Extracted from Text**
- Every named character becomes an **autonomous AI agent**
- Harry, Hermione, Ron, Dumbledore, Snape, Draco... each with personality, goals, memory
- 15+ locations with connections (Privet Drive → Diagon Alley → Hogwarts → ...)
- Canon events with **narrative gravity** — the world pulls you toward the story, but you can diverge

**🎵 Immersive Atmosphere**
- Cover art from the film displayed on load
- Full John Williams OST streaming via Icecast
- 🎙️ Voice narration planned (edge_tts with per-character voices)

**🧠 Intelligent Cleaning Pipeline**
The raw LLM extraction has issues — we fix them:
- `"harry"` + `"Harry Potter"` → merged to `"Harry Potter"`
- `"you-know-who"` → resolved to `"Lord Voldemort"`
- 50 duplicate desserts → filtered out
- Bad relationship IDs → resolved to canonical characters

**⚡ Rich Web UI**
- Dark theme (Catppuccin Mocha)
- Quick actions: Look, Wait, Inventory, Help
- Save/Load system with auto-save
- Live world context panel
- Character dialogue with memory

### Follow the Journey

This demo is being built **in real-time**. Every step is documented:
- 📋 `data/HARRY_POTTER_COMPILATION_GUIDE.md` — Full walkthrough
- 📊 Extraction monitoring — Every 10 minutes
- 🔧 Open source — You can follow along and contribute

**When it's done, you'll be able to:**
```bash
git clone https://github.com/nikodindon/StoryWeaver
cd StoryWeaver
python scripts/web_ui_v2.py
# → Load harry_potter_1 → Enter the world
```

---

## ✨ How It Works

```
Book (EPUB / TXT / PDF)
        │
        ▼
┌───────────────────────┐
│  Deep Extraction      │  ← Heavy offline LLM pass (can take hours, that's fine)
│  Pipeline             │    Extracts entities, relations, timeline, psychology
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Cleaning & Enrich.   │  ← Dedup, fix IDs, filter trivial objects ✨ NEW
│  (optional)           │    Resolves name variants, merges duplicates
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  World Compiler       │  ← Transforms extraction into a structured, playable world
│                       │    Builds graph, agents, rules, symbolic layers
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Simulation Engine    │  ← Tick-based world that evolves independently
│                       │    Agents act, events cascade, state persists
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Interaction Layer    │  ← You type. The world responds.
│  (CLI + Web UI)       │    Rich Gradio interface with cover art & music
└───────────────────────┘
```

### 🧹 Extraction Cleaning Pipeline ✨ NEW

The LLM extraction produces raw data with known issues:
- **Name variants**: "Harry" vs "Harry Potter" → treated as 2 characters
- **Trivial objects**: desserts, clothing, generic items
- **Duplicate events**: same event extracted multiple times
- **ID mismatches**: social graph references don't match character IDs

The cleaning script (`scripts/clean_extraction.py`) fixes all of this:

```bash
python scripts/clean_extraction.py harry_potter_1
```

What it does:
| Issue | Fix |
|---|---|
| `"harry" + "Harry Potter"` | → Merged to `"Harry Potter"` |
| `"you-know-who" + "Voldemort"` | → Resolved to `"Lord Voldemort"` |
| 50 duplicate desserts | → Filtered out (trivial keyword matching) |
| Same event ×10 | → Deduplicated (exact match on desc+participants+location) |
| Bad relationship IDs | → Resolved to canonical character IDs |

See `data/HARRY_POTTER_COMPILATION_GUIDE.md` for a full walkthrough.

### 🎨 Rich Web UI

StoryWeaver now includes a **feature-rich Gradio web interface** (`scripts/web_ui_v2.py`):

- **🖼️ Cover Art Display** — Automatically detects and displays book cover images from `images/<world_name>/`
- **🎵 Icecast Music Streaming** — Streams OST/soundtracks via Icecast from `audio/<world_name>/` using ffmpeg
- **💾 Save/Load System** — Persistent game sessions with auto-save every 10 actions
- **🎭 LLM-Generated Scenes** — Dynamic narration powered by your local LLM
- **⚡ Quick Actions** — One-click commands: Look, Wait, Inventory, Help
- **📋 Rich World Context** — Live display of locations, characters, and world state

### 🎙️ Voice Narration *(Planned — edge_tts)*

We're integrating **edge_tts** to bring the world to life with voice:

- **📖 Narrator voice** — Scene descriptions read aloud with a British voice
- **🎭 Per-character voices** — Each character speaks with a unique voice
- **🌍 Multi-language** — French, English, 100+ voices available
- **💾 Free & local** — No API keys, no quotas, runs on your machine

Example:
```
> talk to dumbledore

🔊 [Voice: en-GB-ThomasNeural]
"Ah, Harry. I was wondering when you'd arrive.
 Curious things, dreams, don't you think?"
```

---

## 🔥 Why This Is Different

| Approach | Problem |
|---|---|
| Full-context prompting | No persistent world structure |
| RAG-based fiction | Fragmented, loses coherence |
| AI Dungeon-style | Hallucinated, no real state |
| Classic Zork | No AI, fully hand-authored |
| **StoryWeaver** | **Compiled world + autonomous agents + persistent state** |

The key insight: **a book is a seed, not a script.** StoryWeaver extracts the implicit world model from the text and makes it executable.

---

## 🧠 Core Concepts

### 1. Narrative Compilation

The extraction phase is intentionally slow and expensive. It runs once, offline, and produces a rich structured artifact: the **World Bundle** — a serializable snapshot of the entire simulated universe derived from the source text.

Multi-pass extraction:
- **Pass 1 — Structure**: locations, characters, objects, events
- **Pass 2 — Relations**: social graph, conflicts, hierarchies, secrets
- **Pass 3 — Psychology**: personality models, motivations, fears, biases for each character
- **Pass 4 — Symbolism**: themes, motifs, narrative arcs, implicit world rules

### 2. Character Agents

Every named character becomes an **independent AI agent** with:
- A dedicated system prompt encoding their personality and knowledge
- A private memory (what they've experienced during your playthrough)
- A goal stack that evolves based on world state
- A decision engine that fires on each tick, even without player input

Characters don't wait for you. Gandalf will leave. Frodo will make decisions. The war will start whether you're there or not.

### 3. Narrative Gravity

Not all timelines are equally likely. StoryWeaver models **narrative gravity** — a soft pull toward canonical events. Deviating from the original story is possible, but requires deliberate effort. The world resists small changes and amplifies large ones.

### 4. The Author Ghost

A hidden meta-agent — the **Author Ghost** — watches over the simulation. It doesn't control events directly, but subtly nudges agent decisions to maintain thematic and narrative coherence. It's the reason characters feel *intentional* even when diverging from canon.

### 5. Tick-Based World Evolution

The world runs on a **tick system**. Between player actions, agents evaluate their goals, take actions, and update world state. Time passes. Events cascade. You can skip ticks to fast-forward.

Not all agents tick at the same frequency — major characters tick more often, background characters are evaluated lazily.

---

## 🏗️ Architecture

### Repository Structure

```
storyweaver-engine/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── configs/
│   ├── default.yaml           # Global config
│   ├── models.yaml            # LLM model paths + params
│   ├── simulation.yaml        # Tick rate, divergence settings
│   └── extraction.yaml        # Extraction pipeline config
│
├── data/
│   ├── raw/                   # Source books (EPUB, TXT, PDF)
│   ├── processed/             # Cleaned + segmented text
│   ├── compiled/              # World Bundles (serialized worlds)
│   └── cache/                 # LLM output cache (avoid re-running)
│
├── storyweaver/
│   │
│   ├── ingestion/             # 📥 Book parsing
│   │   ├── loader.py          # Entry point, detects format
│   │   ├── cleaner.py         # Text normalization
│   │   ├── segmenter.py       # Chapter + scene detection
│   │   └── formats/
│   │       ├── epub.py
│   │       ├── pdf.py
│   │       └── txt.py
│   │
│   ├── extraction/            # 🧠 Deep offline LLM extraction
│   │   ├── pipeline.py        # Orchestrates all passes
│   │   ├── pass_structure.py  # Pass 1: entities, locations, objects
│   │   ├── pass_relations.py  # Pass 2: social graph, conflicts
│   │   ├── pass_psychology.py # Pass 3: per-character personality models
│   │   ├── pass_symbolism.py  # Pass 4: themes, motifs, world rules
│   │   ├── cache.py           # Result caching per-chunk
│   │   └── prompts/
│   │       ├── entity_extract.txt
│   │       ├── character_psychology.txt
│   │       ├── location_extract.txt
│   │       ├── relation_extract.txt
│   │       └── symbolism_extract.txt
│   │
│   ├── compiler/              # 🏗️ World Bundle construction
│   │   ├── world_builder.py   # Main compilation orchestrator
│   │   ├── graph_builder.py   # Spatial graph construction
│   │   ├── agent_builder.py   # Agent + system prompt generation
│   │   ├── rules_builder.py   # World rules inference
│   │   ├── symbol_layer.py    # Narrative gravity + thematic weights
│   │   └── validator.py       # World consistency checks
│   │
│   ├── world/                 # 🌍 Core data structures (no LLM here)
│   │   ├── bundle.py          # WorldBundle: serializable world snapshot
│   │   ├── location.py        # Location node + spatial graph
│   │   ├── character.py       # Character model
│   │   ├── object.py          # Object model + interaction schema
│   │   ├── event.py           # Event + causal chain model
│   │   └── rules.py           # World rule system
│   │
│   ├── agents/                # 🤖 Autonomous AI agent system
│   │   ├── base_agent.py      # Abstract agent interface
│   │   ├── character_agent.py # Full character agent implementation
│   │   ├── author_ghost.py    # Meta-agent for narrative coherence
│   │   ├── decision_engine.py # Goal evaluation + action selection
│   │   ├── psychology.py      # Big Five + narrative trait model
│   │   ├── memory.py          # Per-agent memory + summarization
│   │   └── prompts/
│   │       ├── base_agent.txt
│   │       ├── decision_prompt.txt
│   │       └── personality_templates/
│   │           ├── wise_mentor.yaml
│   │           ├── tragic_hero.yaml
│   │           ├── chaotic_trickster.yaml
│   │           └── loyal_guardian.yaml
│   │
│   ├── simulation/            # 🔄 Tick-based simulation engine
│   │   ├── engine.py          # Main simulation loop
│   │   ├── tick_manager.py    # Tick scheduling + frequency control
│   │   ├── scheduler.py       # Agent activation ordering
│   │   ├── event_resolver.py  # Action conflict resolution
│   │   ├── state_manager.py   # World state persistence
│   │   └── divergence.py      # Narrative gravity + canon tracking
│   │
│   ├── interaction/           # 🎮 Player interaction layer
│   │   ├── parser.py          # Natural language command parsing
│   │   ├── intent_resolver.py # Maps parsed input → game actions
│   │   ├── action_executor.py # Validates + applies actions to world
│   │   ├── command_registry.py# Built-in command definitions
│   │   └── history.py         # Session history + save/load
│   │
│   ├── narrative/             # ✍️ Output text generation
│   │   ├── narrator.py        # Scene description generation
│   │   ├── dialogue.py        # Character speech synthesis
│   │   ├── style_engine.py    # Matches author's prose style
│   │   ├── context_builder.py # Builds LLM context from world state
│   │   └── templates/
│   │       ├── scene_enter.txt
│   │       ├── action_result.txt
│   │       └── dialogue_wrapper.txt
│   │
│   ├── memory/                # 🧠 Multi-layer memory system
│   │   ├── vector_store.py    # FAISS vector memory
│   │   ├── state_store.py     # Structured world state (JSON)
│   │   ├── context_manager.py # Dynamic context window construction
│   │   └── summarizer.py      # Adaptive event summarization
│   │
│   ├── models/                # 🔌 LLM abstraction layer
│   │   ├── llm_client.py      # Unified interface
│   │   ├── llamacpp_client.py # llama.cpp backend
│   │   ├── embeddings.py      # Local embedding generation
│   │   └── prompt_builder.py  # Prompt assembly + token management
│   │
│   ├── utils/
│   │   ├── logging.py
│   │   ├── serialization.py
│   │   ├── graph_utils.py
│   │   └── profiling.py       # Extraction timing + token stats
│   │
│   └── cli/                   # 🖥️ Command-line interface
│       ├── main.py            # Entry point
│       ├── play.py            # Interactive game session
│       ├── compile.py         # World compilation command
│       └── inspect.py         # World inspection / debug tools
│
├── scripts/
│   ├── ingest_book.py         # EPUB/TXT/PDF ingestion
│   ├── run_extraction.py      # 4-pass LLM extraction pipeline
│   ├── clean_extraction.py    # ✨ NEW: Clean & enrich extraction (dedup, filter, resolve)
│   ├── compile_world.py       # World bundle compilation
│   ├── compile_hp_world.py    # HP-specific compilation (with --cleaned flag)
│   ├── web_ui_v2.py           # Gradio web interface (cover + music)
│   ├── icecast_streamer.py    # Icecast ffmpeg-based music streaming
│   └── monitor_extraction.ps1 # ✨ NEW: PowerShell monitoring script
│
├── notebooks/
│   ├── extraction_tests.ipynb
│   ├── agent_behavior.ipynb
│   └── world_graph_viz.ipynb
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_extraction.py
│   ├── test_agents.py
│   ├── test_simulation.py
│   └── test_interaction.py
│
└── examples/
    ├── books/                 # Sample public domain texts
    ├── worlds/                # Pre-compiled world bundles
    └── sessions/              # Example play session logs
```

---

## 🤖 Agent System (Deep Dive)

Each character is compiled into a `CharacterAgent` with the following structure:

### Agent Data Model

```python
CharacterAgent {
    # Identity
    id: str
    name: str
    
    # Psychology (derived from Pass 3 extraction)
    traits: {
        openness: float,        # 0.0 - 1.0
        conscientiousness: float,
        extraversion: float,
        agreeableness: float,
        neuroticism: float,
        # Narrative-specific extensions:
        courage: float,
        loyalty: float,
        deceptiveness: float,
        impulsivity: float
    }
    
    # Knowledge state (what this character knows)
    knowledge: {
        canonical: [...],       # From the book (fixed)
        discovered: [...]       # Learned during playthrough (dynamic)
    }
    
    # Goal stack (evaluated each tick)
    goals: [
        { goal: str, priority: float, condition: str }
    ]
    
    # Relationships (updated dynamically)
    relationships: {
        character_id: {
            trust: float,
            affection: float,
            history: [...]
        }
    }
    
    # Memory
    memory: {
        global: [...],          # Canon events (compressed)
        episodic: [...],        # Runtime events (full)
        working: [...]          # Current scene context
    }
}
```

### Agent System Prompt Template

```
You are {name}.

=== PERSONALITY ===
{trait_description}

=== WHAT YOU KNOW ===
{canonical_knowledge}
{discovered_knowledge}

=== YOUR CURRENT GOALS ===
{active_goals}

=== YOUR RELATIONSHIPS ===
{relationship_summary}

=== CONSTRAINTS ===
{behavioral_constraints}

Act consistently with your personality.
Never break character.
You do not know you are in a simulation.
```

---

## 🌍 World Model

### Location Graph

```python
Location {
    id: str
    name: str
    description: str                # Static base description
    connections: List[str]          # Adjacent location IDs
    objects: List[str]              # Object IDs present here
    characters_present: List[str]   # Character IDs currently here
    ambient_state: Dict             # Time of day, weather, mood
    events_history: List[Event]     # What happened here
    symbolic_weight: float          # Narrative importance (0-1)
}
```

### World Rules

Automatically inferred during extraction, examples:

```yaml
world_rules:
  magic_exists: true
  death_is_permanent: true
  travel_costs_time: true
  information_spreads: true
  social_hierarchy: feudal
  
narrative_rules:
  canon_gravity: 0.6          # 0=free sandbox, 1=forced canon
  author_ghost_active: true
  divergence_tracking: true
```

---

## 🔄 Simulation Loop

```
Player Input
     │
     ▼
Intent Parser ──► intent: { action: "talk", target: "gandalf" }
     │
     ▼
Action Validator ──► checks world state, proximity, possibility
     │
     ▼
Action Executor ──► applies changes to world graph
     │
     ▼
Agent Trigger ──► notifies affected agents
     │
     ▼
Agent Decision Loop (per triggered agent)
     │  ├── evaluate goals
     │  ├── decide response action
     │  └── update own memory
     │
     ▼
World State Update ──► persisted to state store
     │
     ▼
Narrative Generator ──► builds scene description from updated state
     │
     ▼
Output to Player
```

Between player actions, the **tick system** runs background agent activity:

```
Tick N:
  - High-priority agents evaluated (e.g. Gandalf)
  - World events generated from agent actions
  - Relationships updated
  - Author Ghost nudges checked
  - State snapshot saved
```

---

## 🖥️ CLI Interface

### Compile a book

```bash
storyweaver compile books/alice_in_wonderland.txt --model mistral-22b
# Runs extraction pipeline (can take 2–8 hours for a full novel)
# Outputs: data/compiled/alice_in_wonderland/world.bundle
```

### Play

```bash
storyweaver play alice_in_wonderland
```

```
══════════════════════════════════════════
  STORYWEAVER ENGINE  |  Alice in Wonderland
  Canon mode: ON  |  Tick: 0
══════════════════════════════════════════

You are at the riverbank.
Alice is here, looking bored. A white rabbit rushes past.

> follow rabbit

You chase the rabbit down the hill.
Alice glances at you, surprised you're following too.
The rabbit disappears into a hole near the old oak tree.

[Tick 1: Alice decides to follow the rabbit — canonical pull active]

> look

You are at the rabbit hole entrance.
Alice is here. She hesitates at the edge, whispering to herself.
Objects: [oak tree, small flowers, rabbit hole]

> talk to alice

Alice: "Oh! Are you going in too? I'm not sure I should, but it 
       does seem terribly curious..."

> _
```

### Inspect a compiled world

```bash
storyweaver inspect alice_in_wonderland --show characters
storyweaver inspect alice_in_wonderland --show locations
storyweaver inspect alice_in_wonderland --character "The Queen of Hearts"
```

---

## 🌐 Web UI

Launch the Gradio interface:

```bash
python scripts/web_ui_v2.py
```

Then open http://localhost:7860 in your browser.

### Features

- **World Selection** — Choose from any compiled world in `data/compiled/`
- **Cover Art** — Automatically loaded from `images/<world_name>/` (PNG, JPG, WEBP)
- **Music Streaming** — Auto-detects OST in `audio/<world_name>/` and streams via Icecast
- **LLM Narration** — Toggle AI-generated scene descriptions on/off
- **Save/Load** — Manual saves + auto-save every 10 actions
- **Quick Actions** — Look, Wait, Inventory, Help buttons

### Icecast Setup

The web UI streams music through a local Icecast server:

1. **Install Icecast** — Package manager or official installer
2. **Configure** — Edit `icecast.xml` (example in project root)
3. **Start server** — `icecast2 -c icecast.xml`
4. **Launch web UI** — Music auto-starts when world loads

Default config:
- Host: `localhost:8000`
- Mount: `/nova`
- Password: `hackme`

### Asset Organization

```
images/
└── <world_name>/
    └── cover.png          # Book/movie cover art

audio/
└── <world_name>/
    ├── 01 - Track 1.mp3   # OST/soundtrack files
    ├── 02 - Track 2.mp3
    └── ...
```

Assets are auto-discovered by world name — no manual configuration needed.

---

### 🔧 Cleaning & Compilation Pipeline

The raw LLM extraction has known issues (name variants, trivial objects, duplicates).
The cleaning pipeline fixes these before compilation:

```bash
# After extraction completes:
python scripts/clean_extraction.py world_name           # Fix duplicates, filter, enrich
python scripts/compile_hp_world.py --cleaned            # Compile cleaned version
# OR
python scripts/compile_hp_world.py                      # Compile raw version
```

**What cleaning fixes:**

| Issue | Example | Fix |
|---|---|---|
| **Name variants** | "Harry" vs "Harry Potter" | Merge to canonical name |
| **Trivial objects** | desserts, clothing | Filter by keyword list |
| **Duplicate events** | same event ×10 | Deduplicate by hash |
| **Bad relationship IDs** | "harry" → "ron" | Resolve to canonical IDs |

**Monitoring extraction progress:**

```bash
# PowerShell monitor (auto-checks every 10 min)
powershell -ExecutionPolicy Bypass -File scripts/monitor_extraction.ps1

# Or manually:
dir /b data\cache\world_name\*.json | find /c /v ""   # Count cache files
tasklist | findstr /i "python"                         # Check if running
```

See `data/HARRY_POTTER_COMPILATION_GUIDE.md` for a complete walkthrough.

---

## ⚙️ Tech Stack

| Component | Technology |
|---|---|
| LLM inference | [llama.cpp](https://github.com/ggerganov/llama.cpp) |
| Recommended model | Mistral-22B / Mixtral-8x7B / Qwen2.5-32B |
| Backend | Python 3.11+ |
| World graph | NetworkX (default) / Neo4j (large worlds) |
| Vector memory | FAISS |
| Serialization | JSON + MessagePack |
| Embeddings | nomic-embed-text (local) |

---

## 🗺️ Roadmap

### V1 — Prototype *(current)*

- [x] Book ingestion (TXT + EPUB)
- [x] Single-pass extraction (entities + locations)
- [x] Basic world graph construction
- [x] CLI exploration (movement + look)
- [x] **Gradio Web UI v2** with rich features
- [x] **Cover art display** from `images/<world_name>/`
- [x] **Icecast music streaming** via ffmpeg
- [x] **Save/Load system** with auto-save
- [x] **LLM narrator** integration
- [x] **Quick Action buttons** (Look, Wait, Inventory, Help)
- [x] **Extraction cleaning pipeline** (dedup, filter, resolve)
- [ ] **🎬 Harry Potter full demo** — End-to-end compilation ⏳ In Progress
- [ ] Single character agent (protagonist)
- [ ] Narrator output generation

### V2 — Multi-Agent World

- [ ] Full 4-pass extraction pipeline
- [ ] All named characters as agents
- [ ] Per-agent memory + system prompts
- [ ] Tick-based world evolution
- [ ] Persistent save/load
- [ ] Dialogue system
- [ ] Object interaction system
- [ ] 🎙️ **Voice narration (edge_tts)** — Per-character voices

### V3 — Simulation Depth

- [ ] Narrative gravity system
- [ ] Author Ghost meta-agent
- [ ] Psychological trait model (Big Five + narrative extensions)
- [ ] Divergence tracking + canon scoring
- [ ] Dynamic relationship evolution
- [ ] Event cascading (actions have side effects)
- [ ] Audiobook mode — Full voice narration

### V4 — Full Engine

- [ ] PDF ingestion
- [ ] Multi-book cross-world support
- [ ] World inspection UI (web-based)
- [ ] Agent behavior modding system
- [ ] Plugin API (custom world rules, combat systems, etc.)
- [ ] Community world bundle sharing format

---

## ⚠️ Known Challenges

**Coherence over long sessions** — LLM context is finite. StoryWeaver mitigates this via multi-layer memory and state-first architecture (the world graph is always the source of truth, not the LLM's context).

**Implicit knowledge in books** — Novels assume enormous amounts of background knowledge. The extraction pipeline must infer what's never stated explicitly (e.g. "Mordor is dangerous" is implied, not always stated as a rule).

**Agent consistency** — A character's behavior must stay consistent across thousands of interactions. System prompts + memory summarization + trait constraints work together to prevent drift.

**Extraction quality** — The simulation is only as good as the extraction. Noisy or incomplete passes produce broken worlds. Caching and validation between passes is essential.

---

## 💡 Philosophy

> Stories are not meant to be read. They are meant to be lived.

StoryWeaver is built on a simple premise: the richest fiction already contains a complete world — characters with real psychology, spaces with real relationships, rules that govern everything. The text is just a compressed encoding of that world. StoryWeaver decompresses it.

The goal is not to generate new stories. It is to **simulate the one that already exists** — and let you change it.

---

## 📌 Contributing

This project is in early design phase. Architecture contributions, extraction prompt research, and agent system experiments are all welcome. Open an issue to discuss before submitting large PRs.

---

## 📄 License

MIT License — see `LICENSE` for details.

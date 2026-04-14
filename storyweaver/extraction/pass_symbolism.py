"""
Pass 4 — Symbolism: themes, motifs, world rules, narrative gravity.

Extracts:
  - themes: recurring thematic threads (e.g. sacrifice, class inequality, love)
  - motifs: repeated symbolic elements (e.g. cold, gold, birds, eyes)
  - world_rules: implicit physical and social rules of the world
  - gravity_map: per-event narrative gravity weights (how hard is each event to prevent?)

Strategy:
  This is a "big picture" pass — it looks at the book as a whole rather than
  at individual passages. We use the structure output (characters, events, locations)
  plus a sampled overview of the text to infer the deeper layers of meaning.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import json
import re

from loguru import logger
from tqdm import tqdm

from ..models.llm_client import LLMClient
from .cache import ExtractionCache


# ── Prompt: themes & motifs ────────────────────────────────────────────────

THEMES_PROMPT = """Analyze the deeper symbolic layers of this book.

BOOK SUMMARY — Characters, events, and locations:

CHARACTERS:
{characters}

KEY EVENTS:
{events}

LOCATIONS:
{locations}

SAMPLE PASSAGES (for tone and style):
{sample_text}

---

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "themes": [
    {{"name": "e.g. sacrifice, inequality, love, mortality", "weight": 0.9, "evidence": "brief explanation with examples"}}
  ],
  "motifs": [
    {{"name": "e.g. cold, gold, birds, eyes, clocks", "frequency": "rare|occasional|frequent|dominant", "symbolic_meaning": "what it represents"}}
  ],
  "tone": "e.g. melancholy, whimsical, darkly comic, tragic",
  "genre": "e.g. fairy tale, literary fiction, fantasy, realism",
  "author_style": ["distinctive", "stylistic", "features"]
}}

Weights: 0.0 (minor) to 1.0 (central to the work's meaning).
Include 3-8 themes and 3-8 motifs.
"""


# ── Prompt: world rules ────────────────────────────────────────────────────

WORLD_RULES_PROMPT = """Infer the implicit rules that govern this story world.

BOOK ANALYSIS:
Themes: {themes}
Motifs: {motifs}
Characters: {characters}
Events: {events}

---

What are the unstated rules of this world? What can and cannot happen?
What does the author treat as impossible? What is taken for granted?

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "physics": {{
    "magic_exists": true/false,
    "death_is_permanent": true/false,
    "time_travel": true/false,
    "supernatural": true/false,
    "technology_level": "prehistoric|medieval|industrial|modern|advanced",
    "notes": "any other physical rules"
  }},
  "social": {{
    "government_type": "e.g. monarchy, democracy, feudal, theocracy",
    "class_mobility": "none|limited|moderate|free",
    "gender_roles": "traditional|egalitarian|mixed",
    "information_spreads": true/false,
    "notes": "any other social rules"
  }},
  "narrative": {{
    "poetic_justice": true/false,
    "tragic_flaw_matters": true/false,
    "love_conquers_all": true/false,
    "innocence_lost": true/false,
    "notes": "narrative conventions at work"
  }},
  "custom_rules": {{
    "rule_name": "description of the implicit rule"
  }}
}}
"""


# ── Prompt: narrative gravity ──────────────────────────────────────────────

GRAVITY_PROMPT = """Assign narrative gravity weights to each canonical event.

Narrative gravity measures how hard an event is to prevent or change:
- 0.9-1.0 = nearly inevitable; the story fundamentally requires this event
- 0.7-0.9 = very hard to prevent; major divergence if avoided
- 0.5-0.7 = moderately hard; the world would push back
- 0.3-0.5 = somewhat flexible; could go either way
- 0.0-0.3 = easily preventable; minor event

EVENTS (in approximate order):
{events}

THEMES (what the story is "about" at a deeper level):
{themes}

---

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "gravity_map": {{
    "event_id_or_description": 0.85
  }},
  "reasoning": {{
    "event_id_or_description": "brief justification for the weight"
  }}
}}

Be discriminative — not every event should have the same weight.
The most emotionally and structurally essential events should be highest.
"""


class SymbolismPass:
    def __init__(self, llm: LLMClient, cache: ExtractionCache):
        self.llm = llm
        self.cache = cache

    def run(self, segments: List[Dict], structure: Dict, book_id: str) -> Dict:
        characters = structure.get("characters", [])
        events = structure.get("events", [])
        locations = structure.get("locations", [])

        if not characters and not events:
            logger.warning("  Symbolism pass: no structure data found, returning empty")
            return {"themes": [], "motifs": [], "world_rules": {}, "gravity_map": {},
                    "tone": "unknown", "genre": "unknown"}

        logger.info(f"  Building symbolism from {len(characters)} characters, {len(events)} events, "
                    f"{len(locations)} locations")

        # Sample text for tone analysis
        sample_text = "\n\n---\n\n".join(seg["text"][:300] for seg in segments[:15])

        # 1. Themes & motifs
        themes_data = self._extract_themes(characters, events, locations, sample_text, book_id)

        # 2. World rules
        world_rules = self._extract_world_rules(themes_data, characters, events, book_id)

        # 3. Narrative gravity
        gravity_map = self._extract_gravity(events, themes_data, book_id)

        return {
            "themes": themes_data.get("themes", []),
            "motifs": themes_data.get("motifs", []),
            "tone": themes_data.get("tone", "unknown"),
            "genre": themes_data.get("genre", "unknown"),
            "world_rules": world_rules,
            "gravity_map": gravity_map,
        }

    # ── Themes & motifs ────────────────────────────────────────────────────

    def _extract_themes(
        self, characters: List[Dict], events: List[Dict],
        locations: List[Dict], sample_text: str, book_id: str
    ) -> Dict:
        chunk_id = f"{book_id}::themes"

        chars_text = "\n".join(f"- {c['name']}: {c.get('description', '')}" for c in characters)
        events_text = "\n".join(f"- {e.get('description', '')}" for e in events)
        locs_text = "\n".join(f"- {l['name']}: {l.get('description', '')}" for l in locations)

        prompt = THEMES_PROMPT.format(
            characters=chars_text, events=events_text, locations=locs_text,
            sample_text=sample_text[:4000],
        )

        cached = self.cache.get(prompt, chunk_id)
        if cached:
            result = cached
        else:
            result = self.llm.complete(user=prompt, temperature=0.2, max_tokens=1500)
            self.cache.set(prompt, chunk_id, result)

        return self._safe_parse(result, "themes")

    # ── World rules ────────────────────────────────────────────────────────

    def _extract_world_rules(self, themes_data: Dict, characters: List[Dict],
                              events: List[Dict], book_id: str) -> Dict:
        chunk_id = f"{book_id}::world_rules"

        themes_text = ", ".join(t.get("name", "") for t in themes_data.get("themes", []))
        motifs_text = ", ".join(m.get("name", "") for m in themes_data.get("motifs", []))
        chars_text = "\n".join(f"- {c['name']}: {c.get('description', '')}" for c in characters)
        events_text = "\n".join(f"- {e.get('description', '')}" for e in events)

        prompt = WORLD_RULES_PROMPT.format(
            themes=themes_text, motifs=motifs_text,
            characters=chars_text, events=events_text,
        )

        cached = self.cache.get(prompt, chunk_id)
        if cached:
            result = cached
        else:
            result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=1024)
            self.cache.set(prompt, chunk_id, result)

        parsed = self._safe_parse(result, "world_rules")
        if parsed:
            return parsed
        return {}

    # ── Narrative gravity ──────────────────────────────────────────────────

    def _extract_gravity(self, events: List[Dict], themes_data: Dict, book_id: str) -> Dict[str, float]:
        if not events:
            return {}

        chunk_id = f"{book_id}::gravity"

        events_text = "\n".join(
            f"- {e.get('description', '')} — participants: {', '.join(e.get('participants', []))}"
            for e in events
        )
        themes_text = ", ".join(t.get("name", "") for t in themes_data.get("themes", []))

        prompt = GRAVITY_PROMPT.format(events=events_text, themes=themes_text)

        cached = self.cache.get(prompt, chunk_id)
        if cached:
            result = cached
        else:
            result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=1024)
            self.cache.set(prompt, chunk_id, result)

        parsed = self._safe_parse(result, "gravity")
        if parsed and "gravity_map" in parsed:
            return parsed["gravity_map"]

        # Fallback: uniform moderate gravity for all events
        return {e.get("description", f"event_{i}"): 0.6 for i, e in enumerate(events)}

    # ── Helpers ────────────────────────────────────────────────────────────

    def _safe_parse(self, raw: str, context: str) -> Dict:
        """Robustly parse JSON from LLM output with multiple fallback strategies."""
        # Strategy 1: Try clean parse of whole text
        try:
            clean = raw.strip()
            if "```" in clean:
                parts = clean.split("```")
                for i in range(1, len(parts), 2):
                    block = parts[i].replace("json", "").strip()
                    try:
                        return json.loads(block)
                    except json.JSONDecodeError:
                        continue
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON blocks by brace matching
        depth = 0
        start = None
        for i, ch in enumerate(raw):
            if ch == '{' and depth == 0:
                start = i
            depth += 1 if ch == '{' else (-1 if ch == '}' else 0)
            if depth == 0 and start is not None:
                block = raw[start:i+1]
                try:
                    return json.loads(block.strip())
                except json.JSONDecodeError:
                    # Strategy 3: Fix common issues
                    try:
                        fixed = re.sub(r',\s*([}\]])', r'\1', block)  # trailing commas
                        fixed = re.sub(r'(\w+)(\s*:)', r'"\1"\2', fixed)  # unquoted keys
                        fixed = fixed.replace("'", '"')  # single quotes
                        return json.loads(fixed)
                    except Exception:
                        pass
                start = None

        logger.warning(f"Symbolism parse failed for {context}")
        return {}

"""
Pass 2 — Relations: social graph, conflicts, timeline.

Builds:
  - social_graph: pairwise relationships between characters
    (trust, affection, power_dynamic, conflicts, secrets)
  - conflicts: high-level oppositions, alliances, hierarchies
  - timeline: chronologically ordered events with causal links

Strategy:
  For each pair of characters that co-occur in at least one passage,
  extract the nature of their relationship from those shared passages.
  Then extract a global timeline from the canon events.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import json

from loguru import logger
from tqdm import tqdm

from ..models.llm_client import LLMClient
from .cache import ExtractionCache


# ── Prompt: pairwise relationship ──────────────────────────────────────────

RELATION_PROMPT = """Analyze the relationship between two characters based on their shared passages.

CHARACTER 1: {char_a}
CHARACTER 2: {char_b}

SHARED PASSAGES:
{shared_text}

---

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "from": "{char_a}",
  "to": "{char_b}",
  "trust": 0.0,
  "affection": 0.0,
  "power_dynamic": 0.0,
  "description": "one-sentence summary of their relationship",
  "relationship_type": "ally|rival|mentor_student|family|romantic|master_servant|stranger|antagonist|other",
  "secrets": ["things one knows about the other that aren't publicly known"],
  "conflicts": ["specific points of disagreement or opposition"],
  "key_interactions": ["brief descriptions of 2-3 defining moments between them"]
}}

All scores: 0.0 (none/negative) to 1.0 (very strong).
- trust: how much they rely on and believe each other
- affection: warmth, care, fondness
- power_dynamic: 0.0 = {char_b} has all power, 1.0 = {char_a} has all power, 0.5 = equal
"""


# ── Prompt: conflict / alliance map ────────────────────────────────────────

CONFLICTS_PROMPT = """Analyze the high-level conflicts, alliances, and power structures in this book.

CHARACTERS:
{characters}

KEY EVENTS:
{events}

---

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "alliances": [
    {{"members": ["name1", "name2"], "purpose": "why they're allied", "strength": 0.8}}
  ],
  "conflicts": [
    {{"sides": [["name1"], ["name2"]], "over": "what they're fighting about", "intensity": 0.9}}
  ],
  "hierarchies": [
    {{"domain": "e.g. political, social, magical", "top": ["name"], "bottom": ["name"], "type": "formal|informal|coerced"}}
  ]
}}
"""


# ── Prompt: timeline ───────────────────────────────────────────────────────

TIMELINE_PROMPT = """Extract the chronological timeline of key events from this book.

EVENTS AND PASSAGES:
{events_text}

---

Respond ONLY with valid JSON. No preamble.

Schema:
{{
  "timeline": [
    {{
      "order": 1,
      "description": "what happened",
      "participants": ["names"],
      "location": "where",
      "enables": ["description of events this makes possible"],
      "caused_by": ["description of events that led to this"]
    }}
  ]
}}

Order events chronologically. Include 10-30 major events.
"""


class RelationsPass:
    def __init__(self, llm: LLMClient, cache: ExtractionCache, chunk_size: int):
        self.llm = llm
        self.cache = cache
        self.chunk_size = chunk_size

    def run(self, segments: List[Dict], structure: Dict, book_id: str) -> Dict:
        characters = structure.get("characters", [])
        events = structure.get("events", [])
        locations = structure.get("locations", [])

        if not characters:
            logger.warning("  Relations pass: no characters found, returning empty")
            return {"social_graph": [], "conflicts": [], "timeline": []}

        logger.info(f"  Building relations for {len(characters)} characters, {len(events)} events")

        # 1. Social graph — pairwise relationships
        social_graph = self._build_social_graph(characters, segments, book_id)

        # 2. Conflicts and alliances
        conflicts_data = self._build_conflicts(characters, events, book_id)

        # 3. Timeline
        timeline = self._build_timeline(events, segments, book_id)

        logger.info(f"  Relations: {len(social_graph)} edges, {len(conflicts_data.get('conflicts', []))} conflicts, "
                    f"{len(timeline)} timeline events")

        return {
            "social_graph": social_graph,
            "conflicts": conflicts_data,
            "timeline": timeline,
        }

    # ── Social graph ───────────────────────────────────────────────────────

    def _build_social_graph(self, characters: List[Dict], segments: List[Dict], book_id: str) -> List[Dict]:
        """For each pair of characters that share text, extract relationship data."""
        social_graph = []
        char_names = [c["name"] for c in characters]

        # Find co-occurring pairs
        pairs = self._find_pairs(char_names, segments)

        for (char_a, char_b), shared_segments in tqdm(pairs.items(), desc="Pass 2: Relations", leave=False):
            chunk_id = f"{book_id}::rel::{char_a}__{char_b}"
            shared_text = "\n\n---\n\n".join(shared_segments[:10])  # Cap at 10 passages
            prompt = RELATION_PROMPT.format(
                char_a=char_a, char_b=char_b,
                shared_text=shared_text[:5000],
            )

            cached = self.cache.get(prompt, chunk_id)
            if cached:
                result = cached
            else:
                result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=800)
                self.cache.set(prompt, chunk_id, result)

            parsed = self._safe_parse(result, f"relation {char_a}-{char_b}")
            if parsed and "from" in parsed:
                social_graph.append(parsed)

        return social_graph

    def _find_pairs(self, char_names: List[str], segments: List[Dict]) -> Dict:
        """Find all character pairs that co-occur in at least one segment."""
        # For each segment, find all characters mentioned
        pairs: Dict[tuple, List[str]] = {}

        for seg in segments:
            text_lower = seg["text"].lower()
            present = [name for name in char_names if name.lower() in text_lower]

            # All pairs among present characters
            for i in range(len(present)):
                for j in range(i + 1, len(present)):
                    a, b = present[i], present[j]
                    key = (a, b) if a < b else (b, a)
                    if key not in pairs:
                        pairs[key] = []
                    pairs[key].append(seg["text"])

        return pairs

    # ── Conflicts & alliances ──────────────────────────────────────────────

    def _build_conflicts(self, characters: List[Dict], events: List[Dict], book_id: str) -> Dict:
        """Extract high-level conflicts, alliances, and hierarchies."""
        chunk_id = f"{book_id}::conflicts_global"

        chars_text = "\n".join(f"- {c['name']}: {c.get('description', '')}" for c in characters)
        events_text = "\n".join(f"- {e.get('description', '')}" for e in events)

        prompt = CONFLICTS_PROMPT.format(characters=chars_text, events=events_text)

        cached = self.cache.get(prompt, chunk_id)
        if cached:
            result = cached
        else:
            result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=1024)
            self.cache.set(prompt, chunk_id, result)

        parsed = self._safe_parse(result, "conflicts_global")
        if parsed:
            return parsed
        return {"alliances": [], "conflicts": [], "hierarchies": []}

    # ── Timeline ───────────────────────────────────────────────────────────

    def _build_timeline(self, events: List[Dict], segments: List[Dict], book_id: str) -> List[Dict]:
        """Extract ordered timeline from events and text."""
        if not events:
            # Fall back to using full text summary
            events_text = "\n".join(seg["text"][:500] for seg in segments[:20])
        else:
            events_text = "\n".join(
                f"- {e.get('description', '')} — participants: {', '.join(e.get('participants', []))}"
                for e in events
            )

        chunk_id = f"{book_id}::timeline"
        prompt = TIMELINE_PROMPT.format(events_text=events_text[:5000])

        cached = self.cache.get(prompt, chunk_id)
        if cached:
            result = cached
        else:
            result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=2048)
            self.cache.set(prompt, chunk_id, result)

        parsed = self._safe_parse(result, "timeline")
        if parsed and "timeline" in parsed:
            return parsed["timeline"]
        return []

    # ── Helpers ────────────────────────────────────────────────────────────

    def _safe_parse(self, raw: str, context: str) -> Dict:
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1].replace("json", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning(f"Relations parse failed for {context}")
            return {}

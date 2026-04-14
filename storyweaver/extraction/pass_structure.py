"""
Pass 1 — Structure Extraction

Extracts: characters, locations, objects, events
Processes: micro-chunks of the full text
Output: entities.json, locations.json, objects.json, events.json
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


# Words that indicate something is NOT a person
_NOT_PERSON_KEYWORDS = {
    "school", "house", "street", "drive", "station", "platform", "hall",
    "room", "office", "kitchen", "bedroom", "garden", "shed", "closet",
    "bank", "shop", "store", "alley", "castle", "dungeon", "tower",
    "library", "hospital", "pub", "inn",
    "sweater", "jumper", "cake", "pie", "candy", "car", "vehicle",
    "broom", "wand", "potion", "cauldron", "clock", "mirror",
    "cat", "owl", "rat", "toad", "dog", "horse", "dragon", "snake",
    "troll", "giant", "spider", "ghost", "dementor",
    "crowd", "group", "people", "students", "family", "gang",
    "ministry", "order", "wizards", "witches", "muggles",
    "owls", "goblins",
    "magic", "power", "darkness", "light", "curse", "spell",
}


def _is_likely_person(name: str, description: str = "") -> bool:
    """Quick heuristic to filter out obvious non-person entities."""
    text = f"{name} {description}".lower()

    # Check for NOT-person keywords
    if any(kw in text for kw in _NOT_PERSON_KEYWORDS):
        return False

    # Single word that's not capitalized properly or is an animal
    name_clean = name.strip().lower()
    if name_clean in {"cat", "owl", "rat", "toad", "dog", "horse", "spider", "snake"}:
        return False

    # Plural words (unlikely to be individual characters)
    if name_clean.endswith("s") and not name_clean.endswith("'s") and len(name_clean) > 3:
        return False

    return True


STRUCTURE_PROMPT = """Extract all named entities from this passage of a book.

IMPORTANT RULES:
- "characters" are ONLY named PEOPLE (humans with proper names like "Harry Potter", "John Smith")
- DO NOT include animals, creatures, locations, objects, groups, or concepts as characters
- A character must be an individual human with a name or title (Mr., Mrs., Dr., Professor, etc.)
- If uncertain whether something is a person, put it in the correct category instead

PASSAGE:
{passage}

Respond ONLY with valid JSON. No preamble.

{{
  "characters": [
    {{"name": "string (individual human only)", "description": "brief role/appearance", "is_major": true/false}}
  ],
  "locations": [
    {{"name": "string", "description": "brief", "connected_to": ["location names mentioned nearby"]}}
  ],
  "objects": [
    {{"name": "string", "description": "brief", "owner": "character name or null", "symbolic": "significance if any"}}
  ],
  "events": [
    {{"description": "what happened", "participants": ["names"], "location": "where"}}
  ]
}}"""


class StructurePass:
    def __init__(self, llm: LLMClient, cache: ExtractionCache, chunk_size: int):
        self.llm = llm
        self.cache = cache
        self.chunk_size = chunk_size

    def run(self, segments: List[Dict], book_id: str) -> Dict:
        all_characters = {}
        all_locations = {}
        all_objects = {}
        all_events = []

        for seg in tqdm(segments, desc="Pass 1: Structure"):
            chunk_id = f"{book_id}::{seg['id']}"
            prompt = STRUCTURE_PROMPT.format(passage=seg["text"][:3000])

            # Check cache
            cached = self.cache.get(prompt, chunk_id)
            if cached:
                result = cached
            else:
                result = self.llm.complete(user=prompt, temperature=0.1, max_tokens=1024)
                self.cache.set(prompt, chunk_id, result)

            # Parse and merge
            parsed = self._safe_parse(result, chunk_id)
            self._merge_into(parsed, all_characters, all_locations, all_objects, all_events)

        logger.info(f"  Found: {len(all_characters)} characters, {len(all_locations)} locations, "
                    f"{len(all_objects)} objects, {len(all_events)} events")

        return {
            "characters": list(all_characters.values()),
            "locations": list(all_locations.values()),
            "objects": list(all_objects.values()),
            "events": all_events,
        }

    def _safe_parse(self, raw: str, chunk_id: str) -> Dict:
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

        logger.warning(f"JSON parse failed for chunk {chunk_id}, returning empty")
        return {"characters": [], "locations": [], "objects": [], "events": []}

    def _merge_into(self, parsed, characters, locations, objects, events):
        for c in parsed.get("characters", []):
            name = c.get("name", "").strip()
            if name and name not in characters and _is_likely_person(name, c.get("description", "")):
                characters[name] = c
        for l in parsed.get("locations", []):
            name = l.get("name", "").strip()
            if name and name not in locations:
                locations[name] = l
        for o in parsed.get("objects", []):
            name = o.get("name", "").strip()
            if name and name not in objects:
                objects[name] = o
        events.extend(parsed.get("events", []))

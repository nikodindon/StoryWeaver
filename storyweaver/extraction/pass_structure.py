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

from loguru import logger
from tqdm import tqdm

from ..models.llm_client import LLMClient
from .cache import ExtractionCache


STRUCTURE_PROMPT = """Extract all named entities from this passage of a book.

PASSAGE:
{passage}

Respond ONLY with valid JSON. No preamble.

{{
  "characters": [
    {{"name": "string", "description": "brief", "is_major": true/false}}
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
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1].replace("json", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning(f"JSON parse failed for chunk {chunk_id}, skipping")
            return {"characters": [], "locations": [], "objects": [], "events": []}

    def _merge_into(self, parsed, characters, locations, objects, events):
        for c in parsed.get("characters", []):
            name = c.get("name", "").strip()
            if name and name not in characters:
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

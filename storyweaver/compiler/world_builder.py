"""
World Builder — Main compilation orchestrator.

Takes extraction results and produces a fully structured WorldBundle.
This is the "compiler" step: raw extraction data → executable world model.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import json

from loguru import logger

from ..world.bundle import WorldBundle
from ..world.character import Character, Relationship
from ..world.location import Location
from ..world.object import WorldObject
from ..world.event import Event
from ..world.rules import WorldRules
from ..models.llm_client import LLMClient
from .graph_builder import GraphBuilder
from .agent_builder import AgentBuilder
from .rules_builder import RulesBuilder


class WorldBuilder:
    """Compiles extraction results into a playable WorldBundle."""

    def __init__(self, llm_client: LLMClient, config: Dict):
        self.llm = llm_client
        self.config = config

    def build(self, extraction: Dict, book_meta: Dict) -> WorldBundle:
        """
        Full compilation pipeline.
        extraction: result from ExtractionPipeline.run()
        book_meta: {"title": str, "author": str}
        """
        logger.info(f"Compiling world for: {book_meta['title']}")

        structure = extraction.get("structure", {})
        psychology = extraction.get("psychology", {})
        relations = extraction.get("relations", {})
        symbolism = extraction.get("symbolism", {})

        # 1. Build world rules (using symbolism + relations)
        logger.info("  Building world rules...")
        rules = RulesBuilder(self.llm).build(symbolism, structure, relations)

        # 2. Build location graph
        logger.info("  Building location graph...")
        graph_builder = GraphBuilder()
        locations = graph_builder.build_locations(structure.get("locations", []))

        # 3. Build character models
        logger.info("  Building character models...")
        characters = self._build_characters(
            structure.get("characters", []),
            relations.get("social_graph", []),
        )

        # 4. Build objects
        objects = self._build_objects(structure.get("objects", []))

        # 5. Build canon events
        canon_events = self._build_events(structure.get("events", []))

        # 6. Build gravity map
        gravity_map = symbolism.get("gravity_map", {})

        # 7. Construct bundle
        bundle = WorldBundle(
            source_title=book_meta["title"],
            source_author=book_meta.get("author", "Unknown"),
            compiled_at=datetime.now().isoformat(),
            locations=locations,
            characters=characters,
            objects=objects,
            canon_events=canon_events,
            rules=rules,
            gravity_map=gravity_map,
        )

        # 8. Build agents (returned for use by the simulation engine)
        logger.info("  Building character agents...")
        agent_builder = AgentBuilder(self.llm)
        agents = agent_builder.build_all(characters, psychology, bundle)

        logger.info(f"World compiled: {len(locations)} locations, {len(characters)} characters, {len(agents)} agents")
        return bundle, agents

    def _build_characters(self, raw_chars: List[Dict], social_graph: List[Dict]) -> Dict[str, Character]:
        characters = {}
        for c in raw_chars:
            char_id = c["name"].lower().replace(" ", "_")
            char = Character(
                id=char_id,
                name=c["name"],
                description=c.get("description", ""),
                current_location="unknown",
                is_major=c.get("is_major", True),
            )
            characters[char_id] = char

        # Apply relationships from social graph
        for rel in social_graph:
            from_id = rel.get("from", "").lower().replace(" ", "_")
            to_id = rel.get("to", "").lower().replace(" ", "_")
            if from_id in characters and to_id in characters:
                characters[from_id].relationships[to_id] = Relationship(
                    target_id=to_id,
                    trust=rel.get("trust", 0.5),
                    affection=rel.get("affection", 0.5),
                )
        return characters

    def _build_objects(self, raw_objects: List[Dict]) -> Dict[str, WorldObject]:
        objects = {}
        for o in raw_objects:
            obj_id = o["name"].lower().replace(" ", "_")
            objects[obj_id] = WorldObject(
                id=obj_id,
                name=o["name"],
                description=o.get("description", ""),
                symbolic_meaning=o.get("symbolic"),
            )
        return objects

    def _build_events(self, raw_events: List[Dict]) -> List[Event]:
        events = []
        for i, e in enumerate(raw_events):
            loc = e.get("location") or ""
            events.append(Event(
                id=f"canon_{i:04d}",
                description=e.get("description", ""),
                participants=e.get("participants", []),
                location_id=loc.lower().replace(" ", "_") or None,
                is_canon=True,
                gravity=0.5,
            ))
        return events

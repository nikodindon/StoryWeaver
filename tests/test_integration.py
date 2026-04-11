"""
End-to-end integration test: mock LLM through the full pipeline.

Segments → Extraction (4 passes) → Compilation → Save/Load Bundle → Simulation
Proves every component connects to the next without a real LLM server.
"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from typing import Dict

import pytest


# ── Mock LLM that responds to all extraction prompts ───────────────────────

class MockLLMClient:
    """Returns canned JSON for known prompt patterns."""

    def complete(self, user: str = "", system: str = "", **kwargs) -> str:
        # Pass 1: Structure
        if "Extract all named entities" in user:
            return json.dumps({
                "characters": [
                    {"name": "Alice", "description": "A curious girl", "is_major": True},
                    {"name": "White Rabbit", "description": "A hurried rabbit", "is_major": True},
                    {"name": "Queen", "description": "The fierce queen", "is_major": True},
                ],
                "locations": [
                    {"name": "Riverside", "description": "A lazy river bank", "connected_to": ["Rabbit Hole"]},
                    {"name": "Rabbit Hole", "description": "A deep tunnel underground", "connected_to": ["Riverside", "Hall of Doors"]},
                    {"name": "Hall of Doors", "description": "A hall with many doors", "connected_to": ["Rabbit Hole", "Garden"]},
                    {"name": "Garden", "description": "The Queen's garden", "connected_to": ["Hall of Doors"]},
                ],
                "objects": [
                    {"name": "Key", "description": "A tiny golden key", "owner": None, "symbolic": "access to new worlds"},
                    {"name": "Drink Me Bottle", "description": "A bottle labeled 'DRINK ME'", "owner": None, "symbolic": "transformation"},
                ],
                "events": [
                    {"description": "Alice sees the White Rabbit", "participants": ["Alice", "White Rabbit"], "location": "Riverside"},
                    {"description": "Alice falls down the rabbit hole", "participants": ["Alice"], "location": "Rabbit Hole"},
                    {"description": "Alice finds the golden key", "participants": ["Alice"], "location": "Hall of Doors"},
                ],
            })

        # Pass 2: Pairwise relations
        if "Analyze the relationship between two characters" in user:
            # Extract character names from prompt
            names = []
            for line in user.split("\n"):
                if line.startswith("CHARACTER "):
                    names.append(line.split(":")[-1].strip())
            a = names[0] if len(names) >= 1 else "alice"
            b = names[1] if len(names) >= 2 else "rabbit"
            return json.dumps({
                "from": a, "to": b,
                "trust": 0.6, "affection": 0.4, "power_dynamic": 0.3,
                "description": f"{a} pursues {b} with curiosity",
                "relationship_type": "pursuer_target",
                "secrets": [], "conflicts": [], "key_interactions": ["chase scene"]
            })

        # Pass 2: Conflicts global
        if "high-level conflicts, alliances" in user:
            return json.dumps({
                "alliances": [{"members": ["Alice", "White Rabbit"], "purpose": "survival", "strength": 0.3}],
                "conflicts": [{"sides": [["Alice"], ["Queen"]], "over": "authority", "intensity": 0.9}],
                "hierarchies": [{"domain": "political", "top": ["Queen"], "bottom": ["Alice", "White Rabbit"], "type": "formal"}]
            })

        # Pass 2: Timeline
        if "chronological timeline" in user:
            return json.dumps({
                "timeline": [
                    {"order": 1, "description": "Alice sees the White Rabbit", "participants": ["Alice", "White Rabbit"], "location": "Riverside", "enables": ["Alice falls"], "caused_by": []},
                    {"order": 2, "description": "Alice falls down the rabbit hole", "participants": ["Alice"], "location": "Rabbit Hole", "enables": [], "caused_by": ["Alice sees the White Rabbit"]},
                    {"order": 3, "description": "Alice finds the golden key", "participants": ["Alice"], "location": "Hall of Doors", "enables": [], "caused_by": ["Alice falls down the rabbit hole"]},
                ]
            })

        # Pass 3: Psychology
        if "psychological model" in user:
            # Extract character name from the CHARACTER: line
            char_name = "Unknown"
            for line in user.split("\n"):
                if line.startswith("CHARACTER:") and "{" not in line:
                    char_name = line.split(":", 1)[1].strip()
                    break
            return json.dumps({
                "character_id": char_name.lower().replace(" ", "_"),
                "name": char_name,
                "psychology": {
                    "big_five": {"openness": 0.9, "conscientiousness": 0.4, "extraversion": 0.7, "agreeableness": 0.6, "neuroticism": 0.3},
                    "narrative_traits": {"courage": 0.8, "loyalty": 0.5, "deceptiveness": 0.2, "impulsivity": 0.7, "secretiveness": 0.1, "ambition": 0.6, "compassion": 0.7},
                    "core_fear": "Being trapped in a world she doesn't understand",
                    "core_desire": "To discover and explore everything",
                    "cognitive_style": "Curious, impulsive, learns through experience",
                    "speech_patterns": ["asks many questions", "talks to herself", "literal interpretation"],
                    "contradictions": ["wants to grow up but resents adult authority"]
                },
                "knowledge": {"canonical": ["She fell down a rabbit hole", "Nothing here makes sense"], "secrets": []},
                "goals_initial": [
                    {"goal": "Find her way through this strange world", "priority": 0.9},
                    {"goal": "Understand the rules of this place", "priority": 0.7},
                ],
                "behavioral_constraints": ["never give up exploring", "always asks questions"]
            })

        # Pass 4: Themes
        if "deeper symbolic layers" in user:
            return json.dumps({
                "themes": [
                    {"name": "growing up", "weight": 0.9, "evidence": "Alice's size changes mirror adolescence"},
                    {"name": "identity", "weight": 0.8, "evidence": "Who in the world am I?"},
                    {"name": "authority", "weight": 0.7, "evidence": "arbitrary rules of the Queen"},
                ],
                "motifs": [
                    {"name": "eating and drinking", "frequency": "frequent", "symbolic_meaning": "transformation"},
                    {"name": "doors and keys", "frequency": "frequent", "symbolic_meaning": "access to knowledge"},
                    {"name": "size changes", "frequency": "dominant", "symbolic_meaning": "loss of control"},
                ],
                "tone": "whimsical and darkly absurd",
                "genre": "literary nonsense / fairy tale",
                "author_style": ["wordplay", "logical puzzles", "parody of Victorian education"]
            })

        # Pass 4: World rules
        if "implicit rules that govern" in user:
            return json.dumps({
                "physics": {"magic_exists": True, "death_is_permanent": False, "time_travel": False,
                            "supernatural": True, "technology_level": "victorian", "notes": "Size can change freely"},
                "social": {"government_type": "absolute monarchy", "class_mobility": "none",
                           "gender_roles": "mixed", "information_spreads": False, "notes": "Rules are arbitrary"},
                "narrative": {"poetic_justice": False, "tragic_flaw_matters": False,
                              "love_conquers_all": False, "innocence_lost": True, "notes": "Dream logic"},
                "custom_rules": {"size_changes_at_will": "Food and drink cause transformations",
                                 "nonsense_rules": "What seems absurd is normal here"}
            })

        # Pass 4: Gravity
        if "narrative gravity" in user:
            return json.dumps({
                "gravity_map": {
                    "Alice sees the White Rabbit": 0.9,
                    "Alice falls down the rabbit hole": 0.95,
                    "Alice finds the golden key": 0.5,
                },
                "reasoning": {
                    "Alice sees the White Rabbit": "inciting incident",
                    "Alice falls down the rabbit hole": "point of no return",
                    "Alice finds the golden key": "discovery, flexible timing",
                }
            })

        # Fallback
        return "{}"


# ── Sample test data ───────────────────────────────────────────────────────

SAMPLE_SEGMENTS = [
    {
        "id": "ch1_scene1",
        "text": "Alice was beginning to get very tired of sitting by her sister on the bank. Suddenly a White Rabbit with pink eyes ran close by her. The Rabbit actually took a watch out of its waistcoat-pocket and said 'Oh dear! Oh dear! I shall be late!' Alice got up and ran across the field after it.",
        "chapter": 1, "scene": 1,
    },
    {
        "id": "ch1_scene2",
        "text": "Alice followed the Rabbit down a large rabbit-hole. Down, down, down. Either the well was very deep, or she fell very slowly. She had time to look at the walls and notice cupboards and book-shelves. At last she landed on a heap of sticks and dry leaves.",
        "chapter": 1, "scene": 2,
    },
    {
        "id": "ch2_scene1",
        "text": "She found herself in a long hall full of doors locked all round. In the middle stood a little table made of glass with a tiny golden key on it. The key fit a little door behind a curtain, leading to the loveliest garden you ever saw.",
        "chapter": 2, "scene": 1,
    },
    {
        "id": "ch3_scene1",
        "text": "Alice noticed a bottle labeled 'DRINK ME'. She tasted it and began shrinking until she was only ten inches high. Now she could fit through the little door into the garden where the Queen of Hearts was playing croquet with flamingos.",
        "chapter": 3, "scene": 1,
    },
]


# ── Test: Full pipeline ────────────────────────────────────────────────────

def test_full_extraction_and_compilation_pipeline(tmp_path):
    """
    Run the complete pipeline:
      Segments → ExtractionPipeline (4 passes, mock LLM)
               → WorldBuilder → WorldBundle → Save → Load → Verify
    """
    from storyweaver.extraction.pipeline import ExtractionPipeline
    from storyweaver.compiler.world_builder import WorldBuilder
    from storyweaver.world.bundle import WorldBundle

    llm = MockLLMClient()
    cache_dir = tmp_path / "cache"
    config = {
        "chunk_size_tokens": 2000,
        "micro_chunk_size_tokens": 500,
    }

    # Step 1: Extraction
    pipeline = ExtractionPipeline(llm, cache_dir, config)
    extraction = pipeline.run(SAMPLE_SEGMENTS, "test_alice")

    assert "structure" in extraction
    assert "relations" in extraction
    assert "psychology" in extraction
    assert "symbolism" in extraction

    # Verify structure
    assert len(extraction["structure"]["characters"]) >= 3
    assert len(extraction["structure"]["locations"]) >= 4
    assert len(extraction["structure"]["objects"]) >= 2
    assert len(extraction["structure"]["events"]) >= 3

    # Verify relations
    assert len(extraction["relations"]["social_graph"]) >= 1
    assert len(extraction["relations"]["conflicts"]["conflicts"]) >= 1
    assert len(extraction["relations"]["timeline"]) >= 3

    # Verify psychology
    assert "alice" in extraction["psychology"]
    assert "white_rabbit" in extraction["psychology"]
    assert "queen" in extraction["psychology"]

    # Verify symbolism
    assert len(extraction["symbolism"]["themes"]) >= 2
    assert len(extraction["symbolism"]["motifs"]) >= 2
    assert len(extraction["symbolism"]["gravity_map"]) >= 3

    # Step 2: Compilation
    book_meta = {"title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll"}
    builder = WorldBuilder(llm, {})
    bundle, agents = builder.build(extraction, book_meta)

    assert isinstance(bundle, WorldBundle)
    assert bundle.source_title == "Alice's Adventures in Wonderland"
    assert bundle.source_author == "Lewis Carroll"
    assert len(bundle.locations) >= 4
    assert len(bundle.characters) >= 3
    assert len(bundle.objects) >= 2
    assert len(bundle.canon_events) >= 3
    assert bundle.rules is not None
    assert len(bundle.gravity_map) >= 3

    # Step 3: Save
    save_dir = tmp_path / "world_output"
    bundle.save(save_dir)
    assert (save_dir / "bundle.json").exists()

    # Step 4: Load
    loaded = WorldBundle.load(save_dir)
    assert loaded.source_title == bundle.source_title
    assert len(loaded.locations) == len(bundle.locations)
    assert len(loaded.characters) == len(bundle.characters)
    assert len(loaded.objects) == len(bundle.objects)
    assert len(loaded.canon_events) == len(bundle.canon_events)

    # Verify data integrity after round-trip
    assert "alice" in loaded.characters
    assert loaded.characters["alice"].name == "Alice"
    assert "riverside" in loaded.locations
    assert loaded.locations["riverside"].name == "Riverside"
    assert len(loaded.gravity_map) == len(bundle.gravity_map)


# ── Test: Simulation with compiled world ───────────────────────────────────

def test_simulation_with_compiled_world(tmp_path):
    """Compile a world and run a simulation tick to verify the engine works."""
    from storyweaver.extraction.pipeline import ExtractionPipeline
    from storyweaver.compiler.world_builder import WorldBuilder
    from storyweaver.simulation.engine import SimulationEngine
    from storyweaver.simulation.state_manager import StateManager
    from storyweaver.simulation.event_resolver import EventResolver
    from storyweaver.agents.base_agent import AgentAction

    llm = MockLLMClient()
    cache_dir = tmp_path / "cache2"
    config = {
        "chunk_size_tokens": 2000,
        "micro_chunk_size_tokens": 500,
        "simulation": {"tick_rate": 1},
    }

    # Extract + compile
    pipeline = ExtractionPipeline(llm, cache_dir, config.get("extraction", config))
    extraction = pipeline.run(SAMPLE_SEGMENTS, "test_sim")
    book_meta = {"title": "Test", "author": "Test"}
    builder = WorldBuilder(llm, {})
    bundle, agents = builder.build(extraction, book_meta)

    # Create simulation engine
    engine = SimulationEngine(bundle, agents, config.get("simulation", {}))
    snapshot = engine.get_world_snapshot()

    assert snapshot["tick"] == 0
    assert len(snapshot["locations"]) >= 4
    assert len(snapshot["character_positions"]) >= 3

    # Simulate a player action (move)
    action = AgentAction(
        action_type="move", target_id="rabbit_hole",
        parameters={"actor_id": "alice"},
    )
    events = engine.process_player_action(action)

    # Verify state was mutated
    assert bundle.current_tick >= 1
    # Alice should have moved
    alice = bundle.characters.get("alice")
    if alice:
        assert alice.current_location == "rabbit_hole"


# ── Test: State mutation chain ─────────────────────────────────────────────

def test_state_mutation_chain(tmp_path):
    """Verify multiple sequential state mutations work correctly."""
    from storyweaver.extraction.pipeline import ExtractionPipeline
    from storyweaver.compiler.world_builder import WorldBuilder
    from storyweaver.simulation.engine import SimulationEngine
    from storyweaver.agents.base_agent import AgentAction

    llm = MockLLMClient()
    cache_dir = tmp_path / "cache3"
    config = {
        "chunk_size_tokens": 2000,
        "micro_chunk_size_tokens": 500,
        "simulation": {"tick_rate": 1},
    }

    pipeline = ExtractionPipeline(llm, cache_dir, config)
    extraction = pipeline.run(SAMPLE_SEGMENTS, "test_chain")
    book_meta = {"title": "Test", "author": "Test"}
    builder = WorldBuilder(llm, {})
    bundle, agents = builder.build(extraction, book_meta)

    engine = SimulationEngine(bundle, agents, config.get("simulation", {}))

    # Action 1: Alice moves to rabbit_hole
    engine.process_player_action(AgentAction(
        action_type="move", target_id="rabbit_hole",
        parameters={"actor_id": "alice"},
    ))
    assert bundle.characters["alice"].current_location == "rabbit_hole"

    # Action 2: Alice moves to hall_of_doors
    engine.process_player_action(AgentAction(
        action_type="move", target_id="hall_of_doors",
        parameters={"actor_id": "alice"},
    ))
    assert bundle.characters["alice"].current_location == "hall_of_doors"
    # Should no longer be in rabbit_hole
    assert "alice" not in bundle.locations["rabbit_hole"].characters_present
    # Should be in hall_of_doors
    assert "alice" in bundle.locations["hall_of_doors"].characters_present

    # Action 3: Alice talks to White Rabbit
    events = engine.process_player_action(AgentAction(
        action_type="talk", target_id="white_rabbit",
        parameters={"actor_id": "alice", "dialogue": "Hello!"},
    ))
    assert bundle.characters["alice"].current_location == "hall_of_doors"

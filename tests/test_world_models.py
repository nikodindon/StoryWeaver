"""Tests for world model serialization and state mutation."""
import json
from storyweaver.world.bundle import WorldBundle
from storyweaver.world.location import Location
from storyweaver.world.character import Character, Relationship
from storyweaver.world.object import WorldObject
from storyweaver.world.event import Event
from storyweaver.world.rules import WorldRules
from storyweaver.simulation.state_manager import StateManager
from storyweaver.simulation.event_resolver import EventResolver
from storyweaver.agents.base_agent import AgentAction


# ── Serialization round-trip tests ──────────────────────────────────────────

def test_location_roundtrip():
    loc = Location(
        id="shire", name="The Shire", description="A peaceful land",
        connections=["bree"], objects=["pipe"], characters_present=["frodo"],
        ambient_state={"time": "morning"}, symbolic_weight=0.8,
    )
    data = loc.to_dict()
    restored = Location.from_dict(data)
    assert restored.id == loc.id
    assert restored.name == loc.name
    assert restored.connections == loc.connections
    assert restored.characters_present == loc.characters_present
    assert restored.symbolic_weight == 0.8


def test_character_roundtrip():
    char = Character(
        id="gandalf", name="Gandalf", description="A wizard",
        current_location="shire", is_major=True,
    )
    char.relationships["frodo"] = Relationship(
        target_id="frodo", trust=0.8, affection=0.9,
        history=["shared many adventures"],
    )
    data = char.to_dict()
    restored = Character.from_dict(data)
    assert restored.id == char.id
    assert restored.relationships["frodo"].trust == 0.8
    assert restored.relationships["frodo"].history[0] == "shared many adventures"


def test_event_roundtrip():
    event = Event(
        id="meet_001", description="Gandalf meets Frodo",
        participants=["gandalf", "frodo"], location_id="shire",
        is_canon=True, gravity=0.9,
        metadata={"action_type": "talk", "dialogue": "Hello, Frodo"},
    )
    data = event.to_dict()
    restored = Event.from_dict(data)
    assert restored.is_canon is True
    assert restored.metadata["action_type"] == "talk"
    assert restored.metadata["dialogue"] == "Hello, Frodo"


def test_world_rules_roundtrip():
    rules = WorldRules(
        magic_exists=True, death_is_permanent=True,
        canon_gravity=0.75, author_ghost_enabled=False,
        custom={"hobbits_like_food": True},
    )
    data = rules.to_dict()
    restored = WorldRules.from_dict(data)
    assert restored.magic_exists is True
    assert restored.author_ghost_enabled is False
    assert restored.custom["hobbits_like_food"] is True


def test_world_bundle_roundtrip():
    bundle = WorldBundle(
        source_title="Test Book", source_author="Test Author",
        compiled_at="2026-01-01T00:00:00",
        locations={
            "shire": Location(id="shire", name="The Shire", description="Peaceful"),
            "mordor": Location(id="mordor", name="Mordor", description="Dangerous"),
        },
        characters={
            "frodo": Character(
                id="frodo", name="Frodo", description="A hobbit",
                current_location="shire",
            ),
        },
        objects={"ring": WorldObject(id="ring", name="The Ring", description="Precious")},
        canon_events=[
            Event(id="canon_0001", description="Frodo leaves the Shire", is_canon=True),
        ],
        rules=WorldRules(magic_exists=True),
        gravity_map={"canon_0001": 0.9},
        current_tick=5,
        divergence_score=0.15,
    )
    data = bundle.to_dict()
    restored = WorldBundle.from_dict(data)
    assert restored.source_title == "Test Book"
    assert len(restored.locations) == 2
    assert len(restored.characters) == 1
    assert restored.characters["frodo"].name == "Frodo"
    assert len(restored.canon_events) == 1
    assert restored.current_tick == 5
    assert restored.divergence_score == 0.15
    assert restored.gravity_map["canon_0001"] == 0.9


# ── State mutation tests ─────────────────────────────────────────────────────

def _make_test_world():
    return WorldBundle(
        source_title="Test", source_author="Test", compiled_at="2026-01-01",
        locations={
            "shire": Location(id="shire", name="The Shire", description="Home",
                             connections=["bree"], objects=["apple", "sword"]),
            "bree": Location(id="bree", name="Bree", description="A town",
                            connections=["shire"]),
        },
        characters={
            "frodo": Character(id="frodo", name="Frodo", description="", current_location="shire"),
            "gandalf": Character(id="gandalf", name="Gandalf", description="", current_location="shire"),
        },
        objects={
            "apple": WorldObject(id="apple", name="Apple", description="A red apple", location_id="shire"),
            "sword": WorldObject(id="sword", name="Sword", description="A blade", location_id="shire"),
        },
        rules=WorldRules(),
    )


def test_apply_move_updates_location():
    world = _make_test_world()
    sm = StateManager(world)
    event = Event(
        id="move_1", description="frodo moves to bree",
        participants=["frodo"], location_id="bree",
        metadata={"action_type": "move", "actor_id": "frodo", "target_id": "bree"},
    )
    sm.apply_event(event)
    assert world.characters["frodo"].current_location == "bree"
    assert "frodo" in world.locations["bree"].characters_present
    assert "frodo" not in world.locations["shire"].characters_present


def test_apply_talk_updates_relationship():
    world = _make_test_world()
    sm = StateManager(world)
    event = Event(
        id="talk_1", description="frodo talks with gandalf",
        participants=["frodo", "gandalf"],
        metadata={"action_type": "talk", "actor_id": "frodo", "target_id": "gandalf",
                  "dialogue": "Hello, Gandalf!"},
    )
    sm.apply_event(event)
    assert "gandalf" in world.characters["frodo"].relationships
    rel = world.characters["frodo"].relationships["gandalf"]
    assert rel.trust > 0.5  # trust bumped
    assert "Hello, Gandalf!" in rel.history


def test_apply_take_transfers_ownership():
    world = _make_test_world()
    sm = StateManager(world)
    event = Event(
        id="take_1", description="frodo takes apple",
        participants=["frodo"],
        metadata={"action_type": "take", "actor_id": "frodo", "target_id": "apple"},
    )
    sm.apply_event(event)
    assert world.objects["apple"].owner_id == "frodo"
    assert "apple" not in world.locations["shire"].objects


def test_apply_drop_places_at_location():
    world = _make_test_world()
    world.objects["apple"].owner_id = "frodo"
    world.characters["frodo"].current_location = "shire"
    sm = StateManager(world)
    event = Event(
        id="drop_1", description="frodo drops apple",
        participants=["frodo"],
        metadata={"action_type": "drop", "actor_id": "frodo", "target_id": "apple"},
    )
    sm.apply_event(event)
    assert world.objects["apple"].owner_id is None
    assert world.objects["apple"].location_id == "shire"
    assert "apple" in world.locations["shire"].objects


# ── Event resolver tests ────────────────────────────────────────────────────

def test_event_resolver_resolves_move():
    resolver = EventResolver(WorldRules())
    action = AgentAction(
        action_type="move", target_id="bree",
        parameters={"actor_id": "frodo"},
    )
    events = resolver.resolve(action, {})
    assert len(events) == 1
    assert events[0].metadata["action_type"] == "move"
    assert events[0].metadata["actor_id"] == "frodo"
    assert events[0].metadata["target_id"] == "bree"


def test_event_resolver_resolves_talk():
    resolver = EventResolver(WorldRules())
    action = AgentAction(
        action_type="talk", target_id="gandalf",
        parameters={"actor_id": "frodo", "dialogue": "Hello!"},
    )
    events = resolver.resolve(action, {})
    assert len(events) == 1
    assert events[0].metadata["dialogue"] == "Hello!"


def test_event_resolver_wait_produces_no_event():
    resolver = EventResolver(WorldRules())
    action = AgentAction(action_type="wait")
    events = resolver.resolve(action, {})
    assert len(events) == 0

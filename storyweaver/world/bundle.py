"""
WorldBundle — The serializable compiled world.
This is the source of truth for all simulation state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json

from .location import Location
from .character import Character
from .object import WorldObject
from .event import Event
from .rules import WorldRules


@dataclass
class WorldBundle:
    """
    A fully compiled, serializable world derived from a source book.
    Produced by the Compiler, consumed by the Simulation Engine.
    """
    source_title: str
    source_author: str
    compiled_at: str

    locations: Dict[str, Location] = field(default_factory=dict)
    characters: Dict[str, Character] = field(default_factory=dict)
    objects: Dict[str, WorldObject] = field(default_factory=dict)
    canon_events: List[Event] = field(default_factory=list)
    rules: Optional[WorldRules] = None

    # Narrative gravity weights per canon event
    gravity_map: Dict[str, float] = field(default_factory=dict)

    # Current simulation state (mutable at runtime)
    current_tick: int = 0
    divergence_score: float = 0.0

    def save(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "bundle.json", "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "WorldBundle":
        with open(path / "bundle.json") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        return {
            "source_title": self.source_title,
            "source_author": self.source_author,
            "compiled_at": self.compiled_at,
            "current_tick": self.current_tick,
            "divergence_score": self.divergence_score,
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "canon_events": [e.to_dict() for e in self.canon_events],
            "gravity_map": self.gravity_map,
            "rules": self.rules.to_dict() if self.rules else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorldBundle:
        rules_data = data.get("rules")
        rules = WorldRules.from_dict(rules_data) if rules_data else None

        return cls(
            source_title=data["source_title"],
            source_author=data.get("source_author", "Unknown"),
            compiled_at=data["compiled_at"],
            current_tick=data.get("current_tick", 0),
            divergence_score=data.get("divergence_score", 0.0),
            locations={k: Location.from_dict(v) for k, v in data.get("locations", {}).items()},
            characters={k: Character.from_dict(v) for k, v in data.get("characters", {}).items()},
            objects={k: WorldObject.from_dict(v) for k, v in data.get("objects", {}).items()},
            canon_events=[Event.from_dict(e) for e in data.get("canon_events", [])],
            gravity_map=data.get("gravity_map", {}),
            rules=rules,
        )

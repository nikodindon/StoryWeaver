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
        raise NotImplementedError("Implement serialization")

    @classmethod
    def from_dict(cls, data: dict) -> "WorldBundle":
        raise NotImplementedError("Implement deserialization")

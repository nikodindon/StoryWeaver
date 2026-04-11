"""Location node in the world graph."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Location:
    id: str
    name: str
    description: str
    connections: List[str] = field(default_factory=list)  # Adjacent location IDs
    objects: List[str] = field(default_factory=list)       # Object IDs present
    characters_present: List[str] = field(default_factory=list)
    ambient_state: Dict = field(default_factory=dict)      # time_of_day, weather, mood
    symbolic_weight: float = 0.5                           # Narrative importance 0-1
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "connections": self.connections,
            "objects": self.objects,
            "characters_present": self.characters_present,
            "ambient_state": self.ambient_state,
            "symbolic_weight": self.symbolic_weight,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Location:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            connections=data.get("connections", []),
            objects=data.get("objects", []),
            characters_present=data.get("characters_present", []),
            ambient_state=data.get("ambient_state", {}),
            symbolic_weight=data.get("symbolic_weight", 0.5),
            tags=data.get("tags", []),
        )

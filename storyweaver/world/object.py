"""Physical or symbolic object in the world."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WorldObject:
    id: str
    name: str
    description: str
    location_id: Optional[str] = None
    owner_id: Optional[str] = None
    properties: Dict = field(default_factory=dict)
    interactions: List[str] = field(default_factory=list)  # Possible action verbs
    symbolic_meaning: Optional[str] = None
    is_portable: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location_id": self.location_id,
            "owner_id": self.owner_id,
            "properties": self.properties,
            "interactions": self.interactions,
            "symbolic_meaning": self.symbolic_meaning,
            "is_portable": self.is_portable,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorldObject:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            location_id=data.get("location_id"),
            owner_id=data.get("owner_id"),
            properties=data.get("properties", {}),
            interactions=data.get("interactions", []),
            symbolic_meaning=data.get("symbolic_meaning"),
            is_portable=data.get("is_portable", True),
        )

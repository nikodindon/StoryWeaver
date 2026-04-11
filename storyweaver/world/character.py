"""Character model — static world data, not the agent."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Relationship:
    target_id: str
    trust: float = 0.5
    affection: float = 0.5
    history: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "trust": self.trust,
            "affection": self.affection,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Relationship:
        return cls(
            target_id=data["target_id"],
            trust=data.get("trust", 0.5),
            affection=data.get("affection", 0.5),
            history=data.get("history", []),
        )


@dataclass
class Character:
    id: str
    name: str
    description: str
    current_location: str
    is_major: bool = True
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "current_location": self.current_location,
            "is_major": self.is_major,
            "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Character:
        rels = {
            k: Relationship.from_dict(v)
            for k, v in data.get("relationships", {}).items()
        }
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            current_location=data["current_location"],
            is_major=data.get("is_major", True),
            relationships=rels,
            tags=data.get("tags", []),
        )

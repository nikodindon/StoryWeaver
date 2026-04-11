"""Event in the world timeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Event:
    id: str
    description: str
    participants: List[str] = field(default_factory=list)   # Character IDs
    location_id: Optional[str] = None
    tick: int = 0
    is_canon: bool = False
    gravity: float = 0.5                                    # 0=easy to prevent, 1=inevitable
    triggered_by: Optional[str] = None                     # Event ID that caused this
    consequences: List[str] = field(default_factory=list)  # Event IDs this enables
    metadata: Dict = field(default_factory=dict)           # Additional data (action details, etc.)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "participants": self.participants,
            "location_id": self.location_id,
            "tick": self.tick,
            "is_canon": self.is_canon,
            "gravity": self.gravity,
            "triggered_by": self.triggered_by,
            "consequences": self.consequences,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        return cls(
            id=data["id"],
            description=data["description"],
            participants=data.get("participants", []),
            location_id=data.get("location_id"),
            tick=data.get("tick", 0),
            is_canon=data.get("is_canon", False),
            gravity=data.get("gravity", 0.5),
            triggered_by=data.get("triggered_by"),
            consequences=data.get("consequences", []),
            metadata=data.get("metadata", {}),
        )

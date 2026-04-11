"""World rules — physics and narrative constraints."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class WorldRules:
    # Physics
    magic_exists: bool = False
    death_is_permanent: bool = True
    travel_costs_time: bool = True
    information_spreads: bool = True

    # Narrative
    canon_gravity: float = 0.6          # Global default (0=sandbox, 1=strict)
    author_ghost_enabled: bool = True
    divergence_tracking: bool = True

    # Custom rules extracted from the book
    custom: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "magic_exists": self.magic_exists,
            "death_is_permanent": self.death_is_permanent,
            "travel_costs_time": self.travel_costs_time,
            "information_spreads": self.information_spreads,
            "canon_gravity": self.canon_gravity,
            "author_ghost_enabled": self.author_ghost_enabled,
            "divergence_tracking": self.divergence_tracking,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorldRules:
        return cls(
            magic_exists=data.get("magic_exists", False),
            death_is_permanent=data.get("death_is_permanent", True),
            travel_costs_time=data.get("travel_costs_time", True),
            information_spreads=data.get("information_spreads", True),
            canon_gravity=data.get("canon_gravity", 0.6),
            author_ghost_enabled=data.get("author_ghost_enabled", True),
            divergence_tracking=data.get("divergence_tracking", True),
            custom=data.get("custom", {}),
        )

"""World rules — physics and narrative constraints."""
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

"""World state persistence and snapshot management."""
from __future__ import annotations
from typing import Dict
from ..world.bundle import WorldBundle
from ..world.event import Event


class StateManager:
    def __init__(self, world: WorldBundle):
        self._world = world

    def snapshot(self) -> Dict:
        """Build a lightweight snapshot of current world state for LLM context."""
        return {
            "tick": self._world.current_tick,
            "divergence_score": self._world.divergence_score,
            "locations": {lid: {"name": loc.name, "characters": loc.characters_present}
                          for lid, loc in self._world.locations.items()},
            "character_positions": {cid: char.current_location
                                    for cid, char in self._world.characters.items()},
        }

    def apply_event(self, event: Event) -> None:
        """Apply a world event to the persistent state."""
        # TODO: implement state mutation logic based on event type
        pass

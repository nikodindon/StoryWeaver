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
        action_type = event.metadata.get("action_type", "unknown")
        actor_id = event.metadata.get("actor_id")
        target_id = event.metadata.get("target_id")
        dialogue = event.metadata.get("dialogue")

        if action_type == "move" and target_id:
            self._apply_move(actor_id, target_id)
        elif action_type == "talk" and target_id:
            self._apply_talk(actor_id, target_id, dialogue)
        elif action_type == "take" and target_id:
            self._apply_take(actor_id, target_id)
        elif action_type == "drop" and target_id:
            self._apply_drop(actor_id, target_id)
        elif action_type == "examine" and target_id:
            self._apply_examine(actor_id, target_id)

    def _apply_move(self, actor_id: str, target_location_id: str) -> None:
        """Move an actor to a new location."""
        char = self._world.characters.get(actor_id)
        if char and target_location_id in self._world.locations:
            # Remove from old location
            old_loc_id = char.current_location
            if old_loc_id and old_loc_id in self._world.locations:
                old_loc = self._world.locations[old_loc_id]
                if actor_id in old_loc.characters_present:
                    old_loc.characters_present.remove(actor_id)
            # Add to new location
            char.current_location = target_location_id
            new_loc = self._world.locations[target_location_id]
            if actor_id not in new_loc.characters_present:
                new_loc.characters_present.append(actor_id)

    def _apply_talk(self, actor_id: str, target_id: str, dialogue: str = None) -> None:
        """Record that a conversation happened (update relationship trust slightly)."""
        actor = self._world.characters.get(actor_id)
        target = self._world.characters.get(target_id)
        if actor and target:
            if target_id not in actor.relationships:
                from ..world.character import Relationship
                actor.relationships[target_id] = Relationship(target_id=target_id)
            actor.relationships[target_id].history.append(dialogue or "spoken")
            # Small trust bump
            actor.relationships[target_id].trust = min(
                1.0, actor.relationships[target_id].trust + 0.02
            )

    def _apply_take(self, actor_id: str, object_id: str) -> None:
        """Actor picks up an object — move from location to inventory (owner)."""
        char = self._world.characters.get(actor_id)
        obj = self._world.objects.get(object_id)
        if char and obj:
            obj.owner_id = actor_id
            # Remove from current location if tracked there
            if obj.location_id and obj.location_id in self._world.locations:
                loc = self._world.locations[obj.location_id]
                if object_id in loc.objects:
                    loc.objects.remove(object_id)

    def _apply_drop(self, actor_id: str, object_id: str) -> None:
        """Actor drops an object at their current location."""
        char = self._world.characters.get(actor_id)
        obj = self._world.objects.get(object_id)
        if char and obj:
            obj.owner_id = None
            obj.location_id = char.current_location
            if char.current_location and char.current_location in self._world.locations:
                loc = self._world.locations[char.current_location]
                if object_id not in loc.objects:
                    loc.objects.append(object_id)

    def _apply_examine(self, actor_id: str, target_id: str) -> None:
        """Record that actor examined a target — no state change, just knowledge."""
        # Could update character's discovered knowledge; handled at agent level.
        pass

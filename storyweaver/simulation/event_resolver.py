"""Resolves agent actions into world events."""
from typing import Dict, List

from ..agents.base_agent import AgentAction
from ..world.event import Event
from ..world.rules import WorldRules


class EventResolver:
    def __init__(self, rules: WorldRules):
        self.rules = rules

    def resolve(self, action: AgentAction, world_snapshot: Dict) -> List[Event]:
        """Convert an agent action into a list of world events."""
        events = []
        actor_id = action.parameters.get("actor_id")

        if action.action_type == "move" and action.target_id:
            events.append(Event(
                id=f"move_{actor_id}_{action.target_id}",
                description=f"{actor_id} moves to {action.target_id}",
                participants=[actor_id] if actor_id else [],
                location_id=action.target_id,
                is_canon=False,
                gravity=0.1,
                metadata={
                    "action_type": "move",
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                },
            ))
        elif action.action_type == "talk" and action.target_id:
            dialogue = action.parameters.get("dialogue", "")
            events.append(Event(
                id=f"talk_{actor_id}_{action.target_id}",
                description=f"{actor_id} speaks with {action.target_id}",
                participants=[actor_id, action.target_id] if actor_id else [action.target_id],
                is_canon=False,
                gravity=0.05,
                metadata={
                    "action_type": "talk",
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                    "dialogue": dialogue,
                },
            ))
        elif action.action_type == "take" and action.target_id:
            events.append(Event(
                id=f"take_{actor_id}_{action.target_id}",
                description=f"{actor_id} takes {action.target_id}",
                participants=[actor_id] if actor_id else [],
                is_canon=False,
                gravity=0.1,
                metadata={
                    "action_type": "take",
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                },
            ))
        elif action.action_type == "drop" and action.target_id:
            events.append(Event(
                id=f"drop_{actor_id}_{action.target_id}",
                description=f"{actor_id} drops {action.target_id}",
                participants=[actor_id] if actor_id else [],
                is_canon=False,
                gravity=0.05,
                metadata={
                    "action_type": "drop",
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                },
            ))
        elif action.action_type == "examine" and action.target_id:
            events.append(Event(
                id=f"examine_{actor_id}_{action.target_id}",
                description=f"{actor_id} examines {action.target_id}",
                participants=[actor_id] if actor_id else [],
                is_canon=False,
                gravity=0.0,
                metadata={
                    "action_type": "examine",
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                },
            ))
        elif action.action_type == "wait":
            pass  # No event for waiting
        else:
            # Fallback: generic event
            events.append(Event(
                id=f"custom_{actor_id}_{action.action_type}",
                description=action.narration or f"{actor_id} does {action.action_type}",
                participants=[actor_id] if actor_id else [],
                is_canon=False,
                gravity=0.1,
                metadata={
                    "action_type": action.action_type,
                    "actor_id": actor_id,
                    "target_id": action.target_id,
                },
            ))
        return events

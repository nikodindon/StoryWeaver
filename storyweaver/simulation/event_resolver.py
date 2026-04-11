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
        # TODO: Implement full resolution logic
        events = []
        if action.action_type == "move" and action.target_id:
            events.append(Event(
                id=f"move_{action.target_id}",
                description=f"Movement toward {action.target_id}",
                is_canon=False,
                gravity=0.1,
            ))
        return events

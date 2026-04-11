"""
The Author Ghost — A hidden meta-agent that maintains narrative coherence.

Has no physical presence in the world. Invisible to the player.
Nudges character agents toward canonical events when narrative gravity is high.
Activates automatically; deactivates when divergence exceeds threshold.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from loguru import logger
from .base_agent import BaseAgent, AgentAction
from ..world.event import Event


class AuthorGhost(BaseAgent):
    """
    Watches the simulation and injects subtle biases into agent decisions
    to maintain thematic and narrative coherence.

    The Ghost does not control — it influences.
    """

    def __init__(self, gravity_map: Dict[str, float], divergence_threshold: float = 0.8):
        super().__init__("author_ghost")
        self.gravity_map = gravity_map
        self.divergence_threshold = divergence_threshold
        self._pending_nudges: Dict[str, List[str]] = {}  # {agent_id: [nudge_description]}
        self.active = True

    def build_system_prompt(self) -> str:
        return "You are a hidden narrative force. You do not exist as a character."

    def decide(self, world_snapshot: Dict, goal=None) -> AgentAction:
        """Ghost never takes direct actions — returns wait always."""
        return AgentAction(action_type="wait")

    def receive_event(self, event: Event) -> None:
        """Monitor world events for narrative drift."""
        if event.is_canon:
            logger.debug(f"Ghost: canon event occurred — {event.description[:60]}")
        elif event.gravity > 0.7:
            logger.debug(f"Ghost: high-gravity event diverged — {event.description[:60]}")

    def evaluate_gravity(
        self,
        world_snapshot: Dict,
        agents: Dict,
        divergence_score: float,
    ) -> Dict[str, str]:
        """
        Evaluate narrative gravity and produce nudges for agents.

        Returns: {agent_id: nudge_description}
        """
        if divergence_score >= self.divergence_threshold:
            logger.debug("Ghost: divergence too high, deactivating")
            self.active = False
            return {}

        nudges = {}
        # TODO: implement proper gravity evaluation based on upcoming canon events
        # For now, return empty (no nudges)
        return nudges

    def inject_nudge(self, agent, nudge_description: str, weight: float = 0.3) -> None:
        """
        Inject a nudge into an agent's decision context.
        The nudge is a subtle bias — not a command.
        """
        if hasattr(agent, '_pending_nudges'):
            agent._pending_nudges.append((nudge_description, weight))
        logger.debug(f"Ghost: nudge injected into {agent.id}: {nudge_description[:50]}")

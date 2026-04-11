"""
Simulation Engine — The heartbeat of StoryWeaver.

Manages the tick loop, agent scheduling, world state updates,
and divergence tracking.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from loguru import logger

from ..world.bundle import WorldBundle
from ..world.event import Event
from ..agents.base_agent import AgentAction
from .tick_manager import TickManager
from .state_manager import StateManager
from .divergence import DivergenceTracker
from .event_resolver import EventResolver


class SimulationEngine:
    """
    Main simulation loop. Called by the interaction layer on each player action.
    Also runs background ticks between player inputs.
    """

    def __init__(self, world: WorldBundle, agents: Dict, config: Dict):
        self.world = world
        self.agents = agents            # {character_id: CharacterAgent}
        self.config = config
        self.tick_manager = TickManager(agents, config.get("tick_tiers", {}))
        self.state_manager = StateManager(world)
        self.divergence = DivergenceTracker(world.gravity_map)
        self.event_resolver = EventResolver(world.rules)
        self._tick_count = world.current_tick

    def process_player_action(self, action: AgentAction) -> List[Event]:
        """
        Process a player action:
        1. Validate + apply the action
        2. Notify affected agents
        3. Run background ticks
        4. Return generated events for narration
        """
        logger.debug(f"Processing player action: {action}")

        # 1. Apply player action to world
        events = self.event_resolver.resolve(action, self.state_manager.snapshot())
        for event in events:
            self.state_manager.apply_event(event)

        # 2. Notify affected agents
        for event in events:
            for char_id in event.participants:
                if char_id in self.agents:
                    self.agents[char_id].receive_event(event)

        # 3. Run N background ticks
        n_ticks = self.config.get("tick_rate", 1)
        background_events = self._run_ticks(n_ticks)
        events.extend(background_events)

        # 4. Update divergence score
        self.divergence.update(events)
        self.world.divergence_score = self.divergence.score

        return events

    def _run_ticks(self, n: int) -> List[Event]:
        """Run N simulation ticks. Agents act; world evolves."""
        all_events = []
        for _ in range(n):
            self._tick_count += 1
            self.world.current_tick = self._tick_count
            logger.debug(f"Tick {self._tick_count}")

            tick_events = []
            snapshot = self.state_manager.snapshot()

            # Fire agents scheduled for this tick
            for agent in self.tick_manager.get_agents_for_tick(self._tick_count):
                action = agent.decide(snapshot)
                if action.action_type != "wait":
                    resolved = self.event_resolver.resolve(action, snapshot)
                    tick_events.extend(resolved)

            # Apply all tick events
            for event in tick_events:
                self.state_manager.apply_event(event)

            all_events.extend(tick_events)

        return all_events

    def get_world_snapshot(self) -> Dict:
        return self.state_manager.snapshot()

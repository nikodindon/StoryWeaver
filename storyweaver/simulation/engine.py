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
from .phase_tracker import StoryPhase
from .character_schedule import ScheduleManager
from .narrative_gates import GateManager, NarrativeGate


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

        # Temporal progression systems
        self.story_phase = StoryPhase(
            current_chapter_id=self._determine_starting_chapter(),
        )
        self.schedule_manager = ScheduleManager()
        self.schedule_manager.create_from_world_bundle(world)
        self.gate_manager = GateManager()

        # Initialize narrative gates from chapter prerequisites
        self._build_narrative_gates()

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

    def _determine_starting_chapter(self) -> str:
        """Find the first chapter of the book."""
        if not self.world.chapters:
            return "prologue"  # Default if no chapters exist
        
        # Return chapter with index 0 (first chapter)
        for chapter_id, chapter in self.world.chapters.items():
            if chapter.index == 0:
                return chapter_id
        
        # Fallback: return first key
        return next(iter(self.world.chapters.keys()))

    def _build_narrative_gates(self) -> None:
        """
        Build narrative gates from chapter prerequisites.
        Creates gates for locations and characters based on chapter availability.
        """
        for chapter_id, chapter in self.world.chapters.items():
            # Create gates for locations that appear in this chapter
            for loc_id in chapter.locations:
                gate_id = f"gate_{chapter_id}_location_{loc_id}"
                if chapter.prerequisites:
                    self.gate_manager.add_gate(NarrativeGate(
                        gate_id=gate_id,
                        target_type="location",
                        target_id=loc_id,
                        chapter_required=chapter.prerequisites[0],  # First prerequisite
                        unlock_message=f"A new area unlocks: {self.world.locations.get(loc_id, {}).get('name', loc_id)}",
                    ))

            # Create gates for characters that appear in this chapter
            for char_id in chapter.characters:
                gate_id = f"gate_{chapter_id}_character_{char_id}"
                if chapter.prerequisites:
                    self.gate_manager.add_gate(NarrativeGate(
                        gate_id=gate_id,
                        target_type="character",
                        target_id=char_id,
                        chapter_required=chapter.prerequisites[0],
                        unlock_message=f"A new character appears: {self.world.characters.get(char_id, {}).get('name', char_id)}",
                    ))

    def advance_chapter(self, chapter_id: str) -> Optional[str]:
        """
        Advance to a new chapter. Returns unlock message if successful.
        """
        chapter = self.world.chapters.get(chapter_id)
        if not chapter:
            return None
        
        if not chapter.is_unlocked(self.story_phase.completed_chapters):
            return f"Chapter locked: {chapter.title}"
        
        old_chapter = self.story_phase.current_chapter_id
        self.story_phase.complete_chapter(old_chapter)
        self.story_phase.advance_to_chapter(chapter_id)
        
        # Check gates for newly unlocked content
        newly_unlocked = self.gate_manager.check_all_gates(self.story_phase)
        
        messages = []
        for gate_id in newly_unlocked:
            msg = self.gate_manager.get_unlock_message(gate_id)
            if msg:
                messages.append(msg)
        
        return "\n".join(messages) if messages else None

    def get_available_characters(self) -> Dict[str, str]:
        """Get characters available in the current phase."""
        return self.story_phase.get_available_characters(self.world)

    def get_available_locations(self) -> Dict[str, str]:
        """Get locations available in the current phase."""
        return self.story_phase.get_available_locations(self.world)

    def is_character_present(self, character_id: str) -> bool:
        """Check if a character is available in the current phase."""
        return self.story_phase.is_character_available(self.world, character_id)

    def is_location_accessible(self, location_id: str) -> bool:
        """Check if a location is accessible in the current phase."""
        return self.story_phase.is_location_available(self.world, location_id)

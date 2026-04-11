"""Abstract base class for all agents in the simulation."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentAction:
    action_type: str            # "move", "talk", "take", "wait", "custom"
    target_id: Optional[str] = None
    parameters: Dict = field(default_factory=dict)
    narration: Optional[str] = None


class BaseAgent(ABC):
    """
    All agents (characters, Author Ghost) implement this interface.
    Agents are responsible for their own decisions; the simulation engine
    calls them on each relevant tick.
    """

    def __init__(self, agent_id: str):
        self.id = agent_id
        self._memory = []
        self._working_context = []

    @abstractmethod
    def build_system_prompt(self) -> str:
        """Build the system prompt for this agent's LLM calls."""
        ...

    @abstractmethod
    def decide(self, world_snapshot: Dict, goal: Optional[Any] = None) -> AgentAction:
        """
        Decide what action to take given the current world state.
        Called by the tick manager on each relevant tick.
        """
        ...

    @abstractmethod
    def receive_event(self, event: Any) -> None:
        """
        Notify the agent of a world event.
        Agent may update their memory or goals in response.
        """
        ...

    def add_memory(self, event_description: str) -> None:
        self._memory.append(event_description)

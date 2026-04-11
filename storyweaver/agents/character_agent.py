"""
CharacterAgent — A named character from the book, implemented as an AI agent.

Each character has:
- A psychology model derived from extraction
- An LLM-backed decision engine
- A private memory
- A goal stack
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentAction
from .psychology import PsychologyModel
from .memory import AgentMemory


@dataclass
class CharacterGoal:
    description: str
    priority: float             # 0.0 - 1.0
    condition: Optional[str] = None
    active: bool = True


class CharacterAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        psychology: PsychologyModel,
        canonical_knowledge: List[str],
        initial_goals: List[CharacterGoal],
        system_prompt_template: str,
        llm_client: Any,
    ):
        super().__init__(agent_id)
        self.name = name
        self.psychology = psychology
        self.canonical_knowledge = canonical_knowledge
        self.goals: List[CharacterGoal] = initial_goals
        self._system_prompt_template = system_prompt_template
        self._llm = llm_client
        self.memory = AgentMemory(agent_id)
        self.relationships: Dict[str, Dict] = {}
        self.current_location: Optional[str] = None

    def build_system_prompt(self) -> str:
        return self._system_prompt_template.format(
            name=self.name,
            trait_description=self.psychology.to_prose(),
            core_fear=self.psychology.core_fear,
            core_desire=self.psychology.core_desire,
            cognitive_style=self.psychology.cognitive_style,
            canonical_knowledge="\n".join(f"- {k}" for k in self.canonical_knowledge),
            discovered_knowledge=self.memory.format_discovered_knowledge(),
            active_goals=self._format_active_goals(),
            relationship_summary=self._format_relationships(),
            speech_patterns="\n".join(f"- {p}" for p in self.psychology.speech_patterns),
            behavioral_constraints="\n".join(f"- {c}" for c in self.psychology.behavioral_constraints),
        )

    def decide(self, world_snapshot: Dict, goal: Optional[CharacterGoal] = None) -> AgentAction:
        """Ask the LLM what this character would do right now."""
        active_goal = goal or self._get_top_goal()
        if active_goal is None:
            return AgentAction(action_type="wait")

        context = self._build_decision_context(world_snapshot, active_goal)
        response = self._llm.complete(
            system=self.build_system_prompt(),
            user=context,
            max_tokens=200,
            temperature=0.5,
        )
        return self._parse_action(response)

    def receive_event(self, event: Any) -> None:
        self.memory.add_event(str(event))

    def _get_top_goal(self) -> Optional[CharacterGoal]:
        active = [g for g in self.goals if g.active]
        if not active:
            return None
        return max(active, key=lambda g: g.priority)

    def _format_active_goals(self) -> str:
        active = [g for g in self.goals if g.active]
        return "\n".join(f"- [{g.priority:.1f}] {g.description}" for g in active)

    def _format_relationships(self) -> str:
        if not self.relationships:
            return "No notable relationships established yet."
        lines = []
        for char_id, rel in self.relationships.items():
            lines.append(f"- {char_id}: trust={rel.get('trust', 0.5):.1f}, affection={rel.get('affection', 0.5):.1f}")
        return "\n".join(lines)

    def _build_decision_context(self, world_snapshot: Dict, goal: CharacterGoal) -> str:
        memories = self.memory.retrieve_relevant(str(world_snapshot), k=5)
        return f"""Current situation:
{world_snapshot.get('scene_description', 'You are in an unknown location.')}

Your current top goal: {goal.description}

Relevant memories:
{chr(10).join(f'- {m}' for m in memories)}

What do you do? Respond with a JSON action:
{{"action_type": "move|talk|take|examine|wait", "target": "target_name_or_null", "dialogue": "optional speech", "narration": "brief description of action"}}"""

    def _parse_action(self, response: str) -> AgentAction:
        import json
        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].replace("json", "").strip()
            data = json.loads(clean)
            return AgentAction(
                action_type=data.get("action_type", "wait"),
                target_id=data.get("target"),
                parameters={"dialogue": data.get("dialogue")},
                narration=data.get("narration"),
            )
        except (json.JSONDecodeError, KeyError):
            return AgentAction(action_type="wait", narration=response[:200])

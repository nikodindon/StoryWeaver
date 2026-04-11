"""Builds agent system prompts and initial configurations from compiled character data."""
from pathlib import Path
from typing import Dict

import json
from loguru import logger
from ..world.bundle import WorldBundle
from ..world.character import Character
from ..agents.character_agent import CharacterAgent, CharacterGoal
from ..agents.psychology import PsychologyModel, BigFive, NarrativeTraits


PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent / "agents" / "prompts" / "base_agent.txt"


class AgentBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.template = PROMPT_TEMPLATE_PATH.read_text()

    def build_all(
        self,
        characters: Dict[str, Character],
        psychology_data: Dict,
        bundle: WorldBundle,
    ) -> Dict[str, CharacterAgent]:
        """Build and persist agent configs for all characters. Returns {char_id: CharacterAgent}."""
        agents: Dict[str, CharacterAgent] = {}
        for char_id, character in characters.items():
            psych_data = psychology_data.get(char_id, {})
            agent = self._build_agent(character, psych_data, bundle)
            agents[char_id] = agent
        return agents

    def _build_agent(
        self,
        character: Character,
        psych_data: Dict,
        bundle: WorldBundle,
    ) -> CharacterAgent:
        psychology = self._parse_psychology(psych_data)
        canonical_knowledge = psych_data.get("knowledge", {}).get("canonical", []) if psych_data else []
        goals = []
        if psych_data:
            for g in psych_data.get("goals_initial", []):
                goals.append(CharacterGoal(
                    description=g.get("goal", ""),
                    priority=g.get("priority", 0.5),
                    condition=g.get("condition"),
                ))

        # Build system prompt from template
        system_prompt = self.template.format(
            name=character.name,
            trait_description=psychology.to_prose(),
            core_fear=psychology.core_fear,
            core_desire=psychology.core_desire,
            cognitive_style=psychology.cognitive_style,
            canonical_knowledge="\n".join(f"- {k}" for k in canonical_knowledge) if canonical_knowledge else "No specific canonical knowledge.",
            discovered_knowledge="",
            active_goals="\n".join(f"- [{g.priority:.1f}] {g.description}" for g in goals) if goals else "No active goals.",
            relationship_summary="No notable relationships.",
            speech_patterns="\n".join(f"- {p}" for p in psychology.speech_patterns),
            behavioral_constraints="\n".join(f"- {c}" for c in psychology.behavioral_constraints),
        )

        agent = CharacterAgent(
            agent_id=character.id,
            name=character.name,
            psychology=psychology,
            canonical_knowledge=canonical_knowledge,
            initial_goals=goals,
            system_prompt_template=system_prompt,
            llm_client=self.llm,
        )
        agent.current_location = character.current_location

        logger.debug(f"  Agent built: {character.name} ({len(canonical_knowledge)} knowledge items, {len(goals)} goals)")
        return agent

    def _parse_psychology(self, data: Dict) -> PsychologyModel:
        if not data:
            return PsychologyModel()
        psych = data.get("psychology", {})
        b5 = psych.get("big_five", {})
        nt = psych.get("narrative_traits", {})
        return PsychologyModel(
            big_five=BigFive(**{k: v for k, v in b5.items() if k in BigFive.__dataclass_fields__}),
            narrative_traits=NarrativeTraits(**{k: v for k, v in nt.items() if k in NarrativeTraits.__dataclass_fields__}),
            core_fear=psych.get("core_fear", "unknown"),
            core_desire=psych.get("core_desire", "unknown"),
            cognitive_style=psych.get("cognitive_style", "analytical"),
            speech_patterns=psych.get("speech_patterns", []),
            behavioral_constraints=data.get("behavioral_constraints", []),
            contradictions=psych.get("contradictions", []),
        )

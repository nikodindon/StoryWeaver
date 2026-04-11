"""Builds agent system prompts and initial configurations from compiled character data."""
from pathlib import Path
from typing import Dict
import json

from loguru import logger
from ..world.bundle import WorldBundle
from ..world.character import Character
from ..agents.psychology import PsychologyModel, BigFive, NarrativeTraits


PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent / "agents" / "prompts" / "base_agent.txt"


class AgentBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.template = PROMPT_TEMPLATE_PATH.read_text()

    def build_all(self, characters: Dict[str, Character], psychology_data: Dict, bundle: WorldBundle) -> None:
        """Build and store agent configs for all characters."""
        for char_id, character in characters.items():
            psych_data = psychology_data.get(char_id, {})
            self._build_agent(character, psych_data, bundle)

    def _build_agent(self, character: Character, psych_data: Dict, bundle: WorldBundle) -> None:
        psychology = self._parse_psychology(psych_data)
        canonical_knowledge = []
        goals = []

        if psych_data:
            canonical_knowledge = psych_data.get("knowledge", {}).get("canonical", [])
            for g in psych_data.get("goals_initial", []):
                goals.append(g.get("goal", ""))

        logger.debug(f"  Agent built: {character.name} ({len(canonical_knowledge)} knowledge items, {len(goals)} goals)")

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

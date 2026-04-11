"""Psychology model for character agents."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class BigFive:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5


@dataclass
class NarrativeTraits:
    courage: float = 0.5
    loyalty: float = 0.5
    deceptiveness: float = 0.3
    impulsivity: float = 0.3
    secretiveness: float = 0.3
    ambition: float = 0.5
    compassion: float = 0.5


@dataclass
class PsychologyModel:
    big_five: BigFive = field(default_factory=BigFive)
    narrative_traits: NarrativeTraits = field(default_factory=NarrativeTraits)
    core_fear: str = "unknown"
    core_desire: str = "unknown"
    cognitive_style: str = "analytical"
    speech_patterns: List[str] = field(default_factory=list)
    behavioral_constraints: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)

    def to_prose(self) -> str:
        """Render traits as a prose description for use in system prompts."""
        traits = []
        b = self.big_five
        n = self.narrative_traits
        if b.openness > 0.7:
            traits.append("highly curious and imaginative")
        if b.conscientiousness > 0.7:
            traits.append("disciplined and methodical")
        if b.extraversion < 0.3:
            traits.append("introverted and reserved")
        if b.neuroticism < 0.3:
            traits.append("emotionally stable and calm under pressure")
        if n.courage > 0.8:
            traits.append("deeply courageous")
        if n.loyalty > 0.8:
            traits.append("fiercely loyal")
        if n.secretiveness > 0.7:
            traits.append("guarded with information")
        if n.deceptiveness > 0.6:
            traits.append("capable of calculated deception when needed")
        return ", ".join(traits) if traits else "a complex individual"

"""Character model — static world data, not the agent."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Relationship:
    target_id: str
    trust: float = 0.5
    affection: float = 0.5
    history: List[str] = field(default_factory=list)


@dataclass
class Character:
    id: str
    name: str
    description: str
    current_location: str
    is_major: bool = True
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

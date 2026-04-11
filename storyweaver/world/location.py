"""Location node in the world graph."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Location:
    id: str
    name: str
    description: str
    connections: List[str] = field(default_factory=list)  # Adjacent location IDs
    objects: List[str] = field(default_factory=list)       # Object IDs present
    characters_present: List[str] = field(default_factory=list)
    ambient_state: Dict = field(default_factory=dict)      # time_of_day, weather, mood
    symbolic_weight: float = 0.5                           # Narrative importance 0-1
    tags: List[str] = field(default_factory=list)

"""Physical or symbolic object in the world."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WorldObject:
    id: str
    name: str
    description: str
    location_id: Optional[str] = None
    owner_id: Optional[str] = None
    properties: Dict = field(default_factory=dict)
    interactions: List[str] = field(default_factory=list)  # Possible action verbs
    symbolic_meaning: Optional[str] = None
    is_portable: bool = True

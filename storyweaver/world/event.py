"""Event in the world timeline."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Event:
    id: str
    description: str
    participants: List[str] = field(default_factory=list)   # Character IDs
    location_id: Optional[str] = None
    tick: int = 0
    is_canon: bool = False
    gravity: float = 0.5                                    # 0=easy to prevent, 1=inevitable
    triggered_by: Optional[str] = None                     # Event ID that caused this
    consequences: List[str] = field(default_factory=list)  # Event IDs this enables

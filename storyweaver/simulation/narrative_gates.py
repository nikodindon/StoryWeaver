"""
Narrative Gates — lock/unlock mechanics for content based on story phase.
Controls when locations, characters, and events become available.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import WorldBundle
    from .phase_tracker import StoryPhase


@dataclass
class NarrativeGate:
    """
    A condition that must be satisfied before content becomes available.
    
    Types of conditions:
    - chapter_required: Player must have reached a specific chapter
    - event_completed: A specific canon event must have occurred
    - location_visited: Player must have visited a specific location
    - item_held: Player must possess a specific item
    - character_met: Player must have interacted with a specific character
    - custom: Free-form condition (evaluated by simulation engine)
    """
    gate_id: str
    target_type: str                  # "location", "character", "event", "item"
    target_id: str                    # ID of the gated content
    
    # Conditions (all must be satisfied to unlock)
    chapter_required: Optional[str] = None         # Chapter ID that must be current/completed
    event_completed: Optional[str] = None          # Event ID that must have occurred
    location_visited: Optional[str] = None         # Location ID that must have been visited
    item_held: Optional[str] = None                # Item ID the player must have
    character_met: Optional[str] = None            # Character ID the player must have met
    custom_condition: Optional[str] = None         # Free-form condition description
    
    # What happens when unlocked
    unlock_message: Optional[str] = None           # Message shown when gate opens
    is_unlocked: bool = False                      # Current state
    
    def check_conditions(self, phase: StoryPhase) -> bool:
        """
        Check if all conditions are satisfied given the current story phase.
        """
        if self.is_unlocked:
            return True  # Already unlocked
        
        # Check chapter requirement
        if self.chapter_required:
            if phase.current_chapter_id != self.chapter_required:
                if self.chapter_required not in phase.completed_chapters:
                    return False
        
        # Check event completion
        if self.event_completed:
            if self.event_completed not in phase.completed_events:
                return False
        
        # Check location visit
        if self.location_visited:
            if self.location_visited not in phase.visited_locations:
                return False
        
        # If we pass all checks, unlock!
        self.is_unlocked = True
        return True
    
    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "chapter_required": self.chapter_required,
            "event_completed": self.event_completed,
            "location_visited": self.location_visited,
            "item_held": self.item_held,
            "character_met": self.character_met,
            "custom_condition": self.custom_condition,
            "unlock_message": self.unlock_message,
            "is_unlocked": self.is_unlocked,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> NarrativeGate:
        return cls(
            gate_id=data["gate_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            chapter_required=data.get("chapter_required"),
            event_completed=data.get("event_completed"),
            location_visited=data.get("location_visited"),
            item_held=data.get("item_held"),
            character_met=data.get("character_met"),
            custom_condition=data.get("custom_condition"),
            unlock_message=data.get("unlock_message"),
            is_unlocked=data.get("is_unlocked", False),
        )


@dataclass
class GateManager:
    """
    Manages all narrative gates in the world.
    Checks conditions and unlocks content when appropriate.
    """
    gates: Dict[str, NarrativeGate] = field(default_factory=dict)  # gate_id -> gate
    
    def add_gate(self, gate: NarrativeGate) -> None:
        """Add a new gate."""
        self.gates[gate.gate_id] = gate
    
    def check_all_gates(self, phase: StoryPhase) -> List[str]:
        """
        Check all gates against current phase.
        Returns list of gate IDs that were just unlocked.
        """
        newly_unlocked = []
        for gate_id, gate in self.gates.items():
            if not gate.is_unlocked:
                if gate.check_conditions(phase):
                    newly_unlocked.append(gate_id)
        return newly_unlocked
    
    def is_location_available(self, location_id: str, phase: StoryPhase) -> bool:
        """Check if a location is available (no gate, or gate is unlocked)."""
        # Find any gate for this location
        for gate in self.gates.values():
            if gate.target_type == "location" and gate.target_id == location_id:
                return gate.is_unlocked or gate.check_conditions(phase)
        return True  # No gate = always available
    
    def is_character_available(self, character_id: str, phase: StoryPhase) -> bool:
        """Check if a character is available (no gate, or gate is unlocked)."""
        for gate in self.gates.values():
            if gate.target_type == "character" and gate.target_id == character_id:
                return gate.is_unlocked or gate.check_conditions(phase)
        return True  # No gate = always available
    
    def get_locked_content(self, phase: StoryPhase) -> Dict[str, List[str]]:
        """
        Get all currently locked content with reasons.
        Returns {type: [ids]} for locked content.
        """
        locked: Dict[str, List[str]] = {"location": [], "character": [], "event": [], "item": []}
        for gate in self.gates.values():
            if not gate.is_unlocked and not gate.check_conditions(phase):
                locked[gate.target_type].append(gate.target_id)
        return locked
    
    def get_unlock_message(self, gate_id: str) -> Optional[str]:
        """Get the unlock message for a gate, if any."""
        gate = self.gates.get(gate_id)
        return gate.unlock_message if gate else None
    
    def to_dict(self) -> dict:
        return {
            "gates": {gid: g.to_dict() for gid, g in self.gates.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> GateManager:
        manager = cls()
        for gid, gdata in data.get("gates", {}).items():
            manager.gates[gid] = NarrativeGate.from_dict(gdata)
        return manager

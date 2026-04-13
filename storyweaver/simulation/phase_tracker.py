"""
Story Phase Tracker — tracks player's position in the book's timeline.
Controls what content (characters, locations, events) is available.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import WorldBundle, Chapter


@dataclass
class StoryPhase:
    """
    Tracks the player's current position in the book's narrative timeline.
    
    The phase determines:
    - Which chapters are unlocked
    - Which characters are present/available
    - Which locations are accessible
    - Which canon events are active/imminent
    """
    current_chapter_id: str                  # The chapter the player is currently in
    completed_chapters: Set[str] = field(default_factory=set)  # Chapters already experienced
    completed_events: Set[str] = field(default_factory=set)    # Canon events that have occurred
    visited_locations: Set[str] = field(default_factory=set)   # Locations the player has been to
    
    # Divergence tracking — how far from canonical path
    diverged_events: List[str] = field(default_factory=list)   # Events that differ from canon
    divergence_score: float = 0.0            # 0.0 = fully canonical, 1.0 = fully diverged
    
    # Narrative gravity state
    pending_canon_events: List[str] = field(default_factory=list)  # Events the world is pushing toward
    gravity_strength: float = 0.5            # How strongly the world pulls toward canon (0-1)

    def advance_to_chapter(self, chapter_id: str) -> bool:
        """
        Attempt to advance to a new chapter. Returns True if successful.
        A chapter can only be entered if its prerequisites are met.
        """
        # This will be validated against the world bundle
        self.current_chapter_id = chapter_id
        return True

    def complete_chapter(self, chapter_id: str) -> None:
        """Mark a chapter as completed."""
        self.completed_chapters.add(chapter_id)

    def record_event(self, event_id: str, is_canon: bool = True) -> None:
        """
        Record that an event has occurred.
        If is_canon=False, this is a divergent event.
        """
        self.completed_events.add(event_id)
        if not is_canon:
            self.diverged_events.append(event_id)
            self.divergence_score = min(1.0, self.divergence_score + 0.05)

    def get_available_characters(self, world: WorldBundle) -> Dict[str, str]:
        """
        Get characters that are available in the current phase.
        Returns {id: name} dict for available characters.
        """
        current_chapter = world.chapters.get(self.current_chapter_id)
        if not current_chapter:
            # Fallback: return all characters if no chapter system
            return {cid: c.name for cid, c in world.characters.items()}
        
        available = {}
        for char_id in current_chapter.characters:
            if char_id in world.characters:
                available[char_id] = world.characters[char_id].name
        return available

    def get_available_locations(self, world: WorldBundle) -> Dict[str, str]:
        """
        Get locations that are accessible in the current phase.
        Returns {id: name} dict for available locations.
        """
        current_chapter = world.chapters.get(self.current_chapter_id)
        if not current_chapter:
            # Fallback: return all locations if no chapter system
            return {lid: loc.name for lid, loc in world.locations.items()}
        
        available = {}
        for loc_id in current_chapter.locations:
            if loc_id in world.locations:
                available[loc_id] = world.locations[loc_id].name
        return available

    def get_available_chapters(self, world: WorldBundle) -> Dict[str, str]:
        """
        Get chapters that are currently unlocked.
        Returns {id: title} dict for available chapters.
        """
        available = {}
        for chapter_id, chapter in world.chapters.items():
            if chapter.is_unlocked(self.completed_chapters):
                available[chapter_id] = chapter.title
        return available

    def is_character_available(self, world: WorldBundle, character_id: str) -> bool:
        """Check if a specific character is available in the current phase."""
        current_chapter = world.chapters.get(self.current_chapter_id)
        if not current_chapter:
            return character_id in world.characters
        return character_id in current_chapter.characters

    def is_location_available(self, world: WorldBundle, location_id: str) -> bool:
        """Check if a specific location is accessible in the current phase."""
        current_chapter = world.chapters.get(self.current_chapter_id)
        if not current_chapter:
            return location_id in world.locations
        return location_id in current_chapter.locations

    def to_dict(self) -> dict:
        return {
            "current_chapter_id": self.current_chapter_id,
            "completed_chapters": list(self.completed_chapters),
            "completed_events": list(self.completed_events),
            "visited_locations": list(self.visited_locations),
            "diverged_events": self.diverged_events,
            "divergence_score": self.divergence_score,
            "pending_canon_events": self.pending_canon_events,
            "gravity_strength": self.gravity_strength,
        }

    @classmethod
    def from_dict(cls, data: dict) -> StoryPhase:
        return cls(
            current_chapter_id=data["current_chapter_id"],
            completed_chapters=set(data.get("completed_chapters", [])),
            completed_events=set(data.get("completed_events", [])),
            visited_locations=set(data.get("visited_locations", [])),
            diverged_events=data.get("diverged_events", []),
            divergence_score=data.get("divergence_score", 0.0),
            pending_canon_events=data.get("pending_canon_events", []),
            gravity_strength=data.get("gravity_strength", 0.5),
        )

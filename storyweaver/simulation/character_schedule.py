"""
Character Schedule — dynamic presence of characters across chapters/timeline.
Controls who is where, when — characters aren't always available everywhere.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..world import WorldBundle


@dataclass
class CharacterPresence:
    """
    Tracks where a character is available during each chapter.
    A character can be:
    - Present in a specific location during a chapter
    - Absent (not yet introduced or already left)
    - Roaming (available but no fixed location)
    """
    character_id: str
    # chapter_id -> location_id (or None if roaming, or "__absent" if not available)
    presence_map: Dict[str, Optional[str]] = field(default_factory=dict)
    
    # Chapters where this character is introduced (first appearance)
    introduction_chapter: Optional[str] = None
    
    # Chapters where this character leaves the story
    exit_chapters: List[str] = field(default_factory=list)
    
    def get_location_for_chapter(self, chapter_id: str) -> Optional[str]:
        """Get the location where this character is during a specific chapter."""
        return self.presence_map.get(chapter_id)
    
    def is_available_in_chapter(self, chapter_id: str) -> bool:
        """Check if this character is available during a chapter."""
        loc = self.presence_map.get(chapter_id)
        return loc is not None and loc != "__absent"
    
    def to_dict(self) -> dict:
        return {
            "character_id": self.character_id,
            "presence_map": self.presence_map,
            "introduction_chapter": self.introduction_chapter,
            "exit_chapters": self.exit_chapters,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> CharacterPresence:
        return cls(
            character_id=data["character_id"],
            presence_map=data.get("presence_map", {}),
            introduction_chapter=data.get("introduction_chapter"),
            exit_chapters=data.get("exit_chapters", []),
        )


@dataclass
class ScheduleManager:
    """
    Manages all character presence schedules across the world's timeline.
    """
    schedules: Dict[str, CharacterPresence] = field(default_factory=dict)  # character_id -> schedule
    
    def add_schedule(self, schedule: CharacterPresence) -> None:
        """Add or update a character's schedule."""
        self.schedules[schedule.character_id] = schedule
    
    def get_available_characters(self, chapter_id: str) -> List[str]:
        """Get list of character IDs available in a specific chapter."""
        return [
            cid for cid, schedule in self.schedules.items()
            if schedule.is_available_in_chapter(chapter_id)
        ]
    
    def get_character_location(self, character_id: str, chapter_id: str) -> Optional[str]:
        """Get where a character is during a specific chapter."""
        schedule = self.schedules.get(character_id)
        if not schedule:
            return None
        return schedule.get_location_for_chapter(chapter_id)
    
    def get_characters_at_location(self, location_id: str, chapter_id: str) -> List[str]:
        """Get all characters present at a location during a chapter."""
        result = []
        for cid, schedule in self.schedules.items():
            loc = schedule.get_location_for_chapter(chapter_id)
            if loc == location_id:
                result.append(cid)
        return result
    
    def is_character_available(self, character_id: str, chapter_id: str) -> bool:
        """Check if a character is available in a chapter."""
        schedule = self.schedules.get(character_id)
        if not schedule:
            return False
        return schedule.is_available_in_chapter(chapter_id)
    
    def create_from_world_bundle(self, world: WorldBundle) -> None:
        """
        Auto-generate schedules from a world bundle.
        Uses chapter data to determine presence.
        Falls back to making all characters available everywhere if no chapters exist.
        """
        if not world.chapters:
            # No chapter system — make everyone available everywhere
            for char_id in world.characters:
                self.schedules[char_id] = CharacterPresence(
                    character_id=char_id,
                    presence_map={cid: None for cid in world.chapters} if world.chapters else {},
                )
            return
        
        # Build presence from chapter data
        for chapter_id, chapter in world.chapters.items():
            for char_id in chapter.characters:
                if char_id not in self.schedules:
                    char = world.characters.get(char_id)
                    if not char:
                        continue
                    self.schedules[char_id] = CharacterPresence(
                        character_id=char_id,
                        introduction_chapter=chapter_id if not self.schedules.get(char_id) else None,
                    )
                self.schedules[char_id].presence_map[chapter_id] = char.current_location
    
    def to_dict(self) -> dict:
        return {
            "schedules": {cid: s.to_dict() for cid, s in self.schedules.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ScheduleManager:
        manager = cls()
        for cid, sdata in data.get("schedules", {}).items():
            manager.schedules[cid] = CharacterPresence.from_dict(sdata)
        return manager

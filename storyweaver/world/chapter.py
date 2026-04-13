"""Chapter — natural book divisions with temporal progression."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class Chapter:
    """
    A chapter/act/scene division extracted from the book.
    Controls what content is available when the player is in this phase.
    """
    id: str                          # e.g. "ch1", "ch2"
    title: str                       # e.g. "The Boy Who Lived"
    index: int                       # 0-based ordering
    description: str                 # Brief summary of what happens
    locations: List[str] = field(default_factory=list)    # Location IDs accessible in this chapter
    characters: List[str] = field(default_factory=list)   # Character IDs present/available
    events: List[str] = field(default_factory=list)       # Canon event IDs that occur here
    prerequisites: List[str] = field(default_factory=list)  # Chapter IDs that must be completed first
    unlock_condition: Optional[str] = None  # Human-readable condition to unlock (e.g. "reach platform 9¾")
    
    # Soft narrative push — events the chapter tries to guide toward
    key_events: List[str] = field(default_factory=list)   # Canon event IDs with high gravity in this chapter
    
    def is_unlocked(self, completed_chapters: Set[str]) -> bool:
        """Check if this chapter is available given completed chapters."""
        if not self.prerequisites:
            return True  # No prerequisites = always available (first chapter)
        return all(prereq in completed_chapters for prereq in self.prerequisites)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "index": self.index,
            "description": self.description,
            "locations": self.locations,
            "characters": self.characters,
            "events": self.events,
            "prerequisites": self.prerequisites,
            "unlock_condition": self.unlock_condition,
            "key_events": self.key_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Chapter:
        return cls(
            id=data["id"],
            title=data["title"],
            index=data["index"],
            description=data.get("description", ""),
            locations=data.get("locations", []),
            characters=data.get("characters", []),
            events=data.get("events", []),
            prerequisites=data.get("prerequisites", []),
            unlock_condition=data.get("unlock_condition"),
            key_events=data.get("key_events", []),
        )


@dataclass
class Timeline:
    """
    Ordered sequence of canonical events with prerequisites.
    Extracted from Pass 2 extraction (relations + temporal ordering).
    """
    events: List[TimelineEvent] = field(default_factory=list)
    
    def get_available_events(self, completed_event_ids: Set[str]) -> List[TimelineEvent]:
        """Return events whose prerequisites are satisfied."""
        return [
            e for e in self.events
            if all(prereq in completed_event_ids for prereq in e.prerequisites)
            and e.event_id not in completed_event_ids
        ]
    
    def to_dict(self) -> dict:
        return {
            "events": [e.to_dict() for e in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Timeline:
        return cls(
            events=[TimelineEvent.from_dict(e) for e in data.get("events", [])]
        )


@dataclass
class TimelineEvent:
    """A single event in the timeline with prerequisites and consequences."""
    event_id: str                    # References Event.id
    chapter_id: str                  # Which chapter this belongs to
    order: int                       # Position within the chapter
    description: str                 # What happens
    prerequisites: List[str] = field(default_factory=list)  # Event IDs that must happen first
    consequences: List[str] = field(default_factory=list)   # Event IDs this unlocks
    participants: List[str] = field(default_factory=list)   # Character IDs involved
    location_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "chapter_id": self.chapter_id,
            "order": self.order,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "consequences": self.consequences,
            "participants": self.participants,
            "location_id": self.location_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> TimelineEvent:
        return cls(
            event_id=data["event_id"],
            chapter_id=data["chapter_id"],
            order=data["order"],
            description=data["description"],
            prerequisites=data.get("prerequisites", []),
            consequences=data.get("consequences", []),
            participants=data.get("participants", []),
            location_id=data.get("location_id"),
        )

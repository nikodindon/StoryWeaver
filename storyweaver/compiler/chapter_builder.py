"""
Chapter Builder — generates Chapter models from book segments and extraction data.

Since the segmenter often misidentifies chapter boundaries (especially for books
that use word numbers like "CHAPTER ONE"), this builder uses a smarter approach:

1. If segment chapter indices are reliable (many unique values), use them directly
2. Otherwise, split segments into chapters based on a target size heuristic
3. For each chapter: extract characters, locations, events from extraction data
4. Build prerequisite chain (ch1 → ch2 → ch3...)

The result is a realistic chapter structure that the temporal progression system can use.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from collections import Counter

from loguru import logger

from ..world.chapter import Chapter
from ..world.location import Location
from ..world.character import Character
from ..world.event import Event


class ChapterBuilder:
    """Generates Chapter models from segments and extraction data."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        # Target: aim for ~10-17 chapters for a typical novel
        self.target_chapters = self.config.get("target_chapters", None)

    def build_chapters(
        self,
        segments: List[Dict],
        extraction: Dict,
    ) -> Dict[str, Chapter]:
        """
        Build chapter structure from segments and extraction data.

        Args:
            segments: List of {"id": str, "chapter": int, "text": str}
            extraction: Extraction results with structure, relations, etc.

        Returns:
            Dict of {chapter_id: Chapter}
        """
        structure = extraction.get("structure", {})
        raw_locations = structure.get("locations", [])
        raw_characters = structure.get("characters", [])
        raw_events = structure.get("events", [])

        # Step 1: Determine chapter boundaries
        chapter_groups = self._group_segments_by_chapter(segments)

        # Step 2: Build chapter models
        chapters = {}
        for i, (ch_idx, segs_in_chapter) in enumerate(chapter_groups.items()):
            ch_id = f"ch{i}"

            # Extract characters present in this chapter's segments
            chapter_chars = self._extract_characters_for_segments(
                segs_in_chapter, raw_characters
            )

            # Extract locations mentioned in this chapter
            chapter_locations = self._extract_locations_for_segments(
                segs_in_chapter, raw_locations
            )

            # Extract events from this chapter
            chapter_events = self._extract_events_for_segments(
                segs_in_chapter, raw_events
            )

            # Build prerequisite chain
            prerequisites = [f"ch{i-1}"] if i > 0 else []

            # Generate a title from first meaningful text
            title = self._generate_chapter_title(segs_in_chapter, i)

            chapter = Chapter(
                id=ch_id,
                title=title,
                index=i,
                description=f"Chapter {i + 1} of the story",
                locations=chapter_locations,
                characters=chapter_chars,
                events=chapter_events,
                prerequisites=prerequisites,
                key_events=chapter_events[:2] if chapter_events else [],  # First 2 events have gravity
            )
            chapters[ch_id] = chapter

        logger.info(
            f"Built {len(chapters)} chapters from {len(segments)} segments"
        )
        return chapters

    def _group_segments_by_chapter(self, segments: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Group segments into chapters.

        Strategy:
        - If segments have MANY unique chapter indices (>= 8), trust them
        - Otherwise, split into a target number of chapters (~12-17 for a novel)
        - We use a heuristic: aim for ~6-8 segments per chapter
        """
        chapter_indices = [s.get("chapter", 0) for s in segments]
        unique_chapters = set(chapter_indices)

        # Only trust existing indices if we have a reasonable number (8+)
        if len(unique_chapters) >= 8:
            logger.info(f"Using existing chapter indices: {len(unique_chapters)} groups")
            groups = {}
            for seg in segments:
                ch_idx = seg.get("chapter", 0)
                if ch_idx not in groups:
                    groups[ch_idx] = []
                groups[ch_idx].append(seg)
            return groups

        # Otherwise, split into target number of chapters
        # Target: aim for ~12-17 chapters for a typical novel
        target = self.target_chapters or max(8, len(segments) // 6)
        target = min(target, len(segments))  # Cap at number of segments
        logger.info(f"Splitting {len(segments)} segments into {target} chapters")

        groups = {}
        segs_per_chapter = max(1, len(segments) // target)

        for i, seg in enumerate(segments):
            ch_idx = min(i // segs_per_chapter, target - 1)
            if ch_idx not in groups:
                groups[ch_idx] = []
            groups[ch_idx].append(seg)

        return groups

    def _extract_characters_for_segments(
        self,
        segments: List[Dict],
        raw_characters: List[Dict],
    ) -> List[str]:
        """
        Determine which characters are present in a set of segments.

        Simple approach: check if character name appears in segment text.
        """
        character_ids = []
        for char_data in raw_characters:
            char_name = char_data.get("name", "")
            if not char_name:
                continue

            char_id = char_name.lower().replace(" ", "_")

            # Check if character name appears in any segment
            for seg in segments:
                text = seg.get("text", "").lower()
                if char_name.lower() in text or char_id.replace("_", " ") in text:
                    if char_id not in character_ids:
                        character_ids.append(char_id)
                    break  # Found in this chapter, no need to check more segments

        return character_ids

    def _extract_locations_for_segments(
        self,
        segments: List[Dict],
        raw_locations: List[Dict],
    ) -> List[str]:
        """
        Determine which locations are accessible in a set of segments.
        """
        location_ids = []
        for loc_data in raw_locations:
            loc_name = loc_data.get("name", "")
            if not loc_name:
                continue

            loc_id = loc_name.lower().replace(" ", "_")

            for seg in segments:
                text = seg.get("text", "").lower()
                if loc_name.lower() in text or loc_id.replace("_", " ") in text:
                    if loc_id not in location_ids:
                        location_ids.append(loc_id)
                    break

        return location_ids

    def _extract_events_for_segments(
        self,
        segments: List[Dict],
        raw_events: List[Dict],
    ) -> List[str]:
        """
        Map extraction events to chapters based on participant presence.
        """
        event_ids = []
        for i, event_data in enumerate(raw_events):
            participants = event_data.get("participants", [])
            location = event_data.get("location", "")

            # Check if event participants appear in these segments
            for seg in segments:
                text = seg.get("text", "").lower()
                for participant in participants:
                    if participant.lower() in text:
                        evt_id = f"event_{i:04d}"
                        if evt_id not in event_ids:
                            event_ids.append(evt_id)
                        break
                else:
                    continue
                break

        return event_ids

    def _generate_chapter_title(self, segments: List[Dict], index: int) -> str:
        """
        Generate a chapter title from segment content.
        Falls back to 'Chapter N' if nothing meaningful found.
        """
        if not segments:
            return f"Chapter {index + 1}"

        # Try to find a meaningful first line or phrase
        for seg in segments[:3]:  # Check first 3 segments
            text = seg.get("text", "").strip()
            # Get first non-empty line
            for line in text.split("\n"):
                line = line.strip()
                if len(line) > 10 and not line.startswith(("Text copyright", "Illustrations")):
                    # Use first 50 chars as title
                    return line[:60] + ("..." if len(line) > 60 else "")

        return f"Chapter {index + 1}"

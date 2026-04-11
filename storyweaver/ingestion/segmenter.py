"""
Intelligent text segmenter.

Produces three granularities:
  - Chapters (coarse)
  - Scenes (medium, separated by *** or blank lines in narrative)
  - Micro-chunks (fine, ~500 tokens, for entity extraction)
"""
from __future__ import annotations
import re
from typing import List, Dict


CHAPTER_PATTERNS = [
    r'^CHAPTER\s+[IVXLCDM\d]+',
    r'^Chapter\s+\d+',
    r'^\d+\.\s+[A-Z]',
]

SCENE_BREAK = r'\n\n'


class Segmenter:
    def segment(self, text: str, target_chunk_chars: int = 4000) -> List[Dict]:
        """
        Segment text into chunks suitable for LLM processing.
        Tries to respect chapter and scene boundaries.
        """
        segments = []
        chapters = self._split_chapters(text)

        seg_id = 0
        for ch_idx, chapter_text in enumerate(chapters):
            # Split chapter into scenes
            scenes = re.split(r'\n{2,}', chapter_text)
            current_chunk = ""

            for scene in scenes:
                scene = scene.strip()
                if not scene:
                    continue

                if len(current_chunk) + len(scene) > target_chunk_chars and current_chunk:
                    segments.append({
                        "id": f"seg_{seg_id:04d}",
                        "chapter": ch_idx,
                        "text": current_chunk.strip(),
                    })
                    seg_id += 1
                    current_chunk = scene
                else:
                    current_chunk += "\n\n" + scene

            if current_chunk.strip():
                segments.append({
                    "id": f"seg_{seg_id:04d}",
                    "chapter": ch_idx,
                    "text": current_chunk.strip(),
                })
                seg_id += 1

        return segments

    def _split_chapters(self, text: str) -> List[str]:
        pattern = '|'.join(CHAPTER_PATTERNS)
        parts = re.split(f'(?m)({pattern})', text)
        if len(parts) <= 1:
            # No chapter markers found — treat as one big chapter
            return [text]
        # Merge headers back with their content
        chapters = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(pattern, parts[i].strip()):
                chapters.append(parts[i] + parts[i+1])
                i += 2
            else:
                if parts[i].strip():
                    chapters.append(parts[i])
                i += 1
        return chapters

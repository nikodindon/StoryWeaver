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
    # Roman numerals: CHAPTER V, Chapter XII, chapter iii
    r'^(?:CHAPTER)\s+[IVXLCDM]{2,}',
    # Arabic numerals: CHAPTER 1, Chapter 12
    r'^(?:CHAPTER)\s+\d+',
    # Word numbers: CHAPTER ONE, Chapter Twenty-One, chapter one
    r'^(?:CHAPTER)\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY|TWENTY-ONE|TWENTY-TWO|TWENTY-THREE|TWENTY-FOUR|TWENTY-FIVE|TWENTY-SIX|TWENTY-SEVEN|TWENTY-EIGHT|TWENTY-NINE|THIRTY|THIRTY-ONE|THIRTY-TWO|THIRTY-THREE|THIRTY-FOUR|THIRTY-FIVE)',
    # Numbered sections: 1. The Beginning
    r'^\d+\.\s+[A-Z]',
    # Part divisions: PART ONE, Part Two
    r'^(?:PART)\s+(?:[IVXLCDM]+|\d+|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)',
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
        # Use IGNORECASE to handle "Chapter one", "CHAPTER ONE", "chapter ONE"
        parts = re.split(f'(?m)({pattern})', text, flags=re.IGNORECASE)
        if len(parts) <= 1:
            # No chapter markers found — treat as one big chapter
            return [text]
        # Merge headers back with their content
        chapters = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(pattern, parts[i].strip(), re.IGNORECASE):
                chapters.append(parts[i] + parts[i+1])
                i += 2
            else:
                if parts[i].strip():
                    chapters.append(parts[i])
                i += 1
        return chapters

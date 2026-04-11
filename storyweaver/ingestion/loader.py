"""Book loader — detects format and dispatches to the right parser."""
from pathlib import Path
from typing import Dict
from loguru import logger

from .cleaner import TextCleaner
from .segmenter import Segmenter


def load_book(path: str | Path) -> Dict:
    """
    Load a book from file, clean it, and segment into chapters/scenes.

    Returns:
        {
            "title": str,
            "author": str,
            "raw_text": str,
            "segments": [{"id": str, "chapter": int, "scene": int, "text": str}]
        }
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Book not found: {path}")

    logger.info(f"Loading book: {path.name}")

    ext = path.suffix.lower()
    if ext == ".epub":
        from .formats.epub import EpubLoader
        raw = EpubLoader().load(path)
    elif ext == ".txt":
        from .formats.txt import TxtLoader
        raw = TxtLoader().load(path)
    elif ext == ".pdf":
        from .formats.pdf import PdfLoader
        raw = PdfLoader().load(path)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    cleaner = TextCleaner()
    cleaned = cleaner.clean(raw["text"])

    segmenter = Segmenter()
    segments = segmenter.segment(cleaned)

    logger.info(f"  Loaded: {len(cleaned)} chars, {len(segments)} segments")

    return {
        "title": raw.get("title", path.stem),
        "author": raw.get("author", "Unknown"),
        "raw_text": cleaned,
        "segments": segments,
    }

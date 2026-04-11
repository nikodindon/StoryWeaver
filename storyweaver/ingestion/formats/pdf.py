"""PDF book loader using pypdf."""
from pathlib import Path
from typing import Dict


class PdfLoader:
    def load(self, path: Path) -> Dict:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("Install pypdf: pip install pypdf")

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages)
        return {"title": path.stem, "author": "Unknown", "text": text}

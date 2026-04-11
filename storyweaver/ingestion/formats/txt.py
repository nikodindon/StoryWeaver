"""Plain text book loader."""
from pathlib import Path


class TxtLoader:
    def load(self, path: Path) -> dict:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Try to extract title from first line
        lines = text.strip().split('\n')
        title = lines[0].strip() if lines else path.stem
        return {"title": title, "author": "Unknown", "text": text}

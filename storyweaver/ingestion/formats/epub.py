"""EPUB book loader using ebooklib."""
from pathlib import Path
from typing import Dict


class EpubLoader:
    def load(self, path: Path) -> Dict:
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("Install ebooklib and beautifulsoup4: pip install ebooklib beautifulsoup4")

        book = epub.read_epub(str(path))
        title = book.get_metadata('DC', 'title')
        title = title[0][0] if title else path.stem
        author = book.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Unknown"

        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text(separator='\n')
            if text.strip():
                chapters.append(text)

        return {"title": title, "author": author, "text": "\n\n".join(chapters)}

#!/usr/bin/env python3
"""
Step 1: Ingest a book and prepare it for extraction.

Usage:
    python scripts/ingest_book.py path/to/book.epub
    python scripts/ingest_book.py path/to/book.txt --output my_world_name
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.ingestion.loader import load_book


def main():
    parser = argparse.ArgumentParser(description="Ingest a book for StoryWeaver")
    parser.add_argument("book_path", help="Path to the book file (EPUB, TXT, PDF)")
    parser.add_argument("--output", help="Output name (defaults to book filename)")
    args = parser.parse_args()

    book_path = Path(args.book_path)
    output_name = args.output or book_path.stem.lower().replace(" ", "_")

    print(f"Ingesting: {book_path.name}")
    result = load_book(book_path)

    output_dir = Path("data/processed") / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save processed book
    with open(output_dir / "meta.json", "w") as f:
        json.dump({"title": result["title"], "author": result["author"]}, f, indent=2)

    with open(output_dir / "text.txt", "w") as f:
        f.write(result["raw_text"])

    with open(output_dir / "segments.json", "w") as f:
        json.dump(result["segments"], f, indent=2)

    print(f"Done. {len(result['segments'])} segments saved to data/processed/{output_name}/")
    print(f"Next step: python scripts/run_extraction.py {output_name}")


if __name__ == "__main__":
    main()

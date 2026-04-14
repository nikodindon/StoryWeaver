#!/usr/bin/env python3
"""
Compile Dolan's Cadillac world with temporal progression.

Usage:
    python scripts/compile_dolan_world.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.compiler.world_builder import WorldBuilder
from storyweaver.world.bundle import WorldBundle


def main():
    world_name = "stephen_king_dolans_cadillac"
    processed_dir = Path("data/processed") / world_name
    output_dir = Path("data/compiled") / world_name
    extraction_file = processed_dir / "extraction.json"

    if not extraction_file.exists():
        print(f"Error: No extraction.json found at {extraction_file}")
        sys.exit(1)

    # Load extraction
    print(f"\nLoading extraction results for '{world_name}'...")
    with open(extraction_file, encoding="utf-8") as f:
        extraction = json.load(f)

    # Load segments for chapter generation
    segments = None
    segments_file = processed_dir / "segments.json"
    if segments_file.exists():
        with open(segments_file) as f:
            segments = json.load(f)
        print(f"  Loaded {len(segments)} segments for chapter generation")

    # Load book metadata
    with open(processed_dir / "meta.json", encoding="utf-8") as f:
        meta = json.load(f)

    book_meta = {
        "title": meta.get("title", "Dolan's Cadillac"),
        "author": meta.get("author", "Stephen King"),
    }

    print(f"  Book: {book_meta['title']} by {book_meta['author']}")
    print(f"  Characters: {len(extraction.get('structure', {}).get('characters', []))}")
    print(f"  Locations: {len(extraction.get('structure', {}).get('locations', []))}")
    print(f"  Objects: {len(extraction.get('structure', {}).get('objects', []))}")
    print(f"  Events: {len(extraction.get('structure', {}).get('events', []))}")
    print()

    # Build world
    print("Building world with temporal progression...")
    builder = WorldBuilder(llm_client=None, config={"mode": "compile"})
    bundle, agents = builder.build(extraction, book_meta, segments=segments)

    # Save
    print(f"\nSaving to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle.save(output_dir)

    print(f"\n{'=' * 50}")
    print("  WORLD COMPILED SUCCESSFULLY")
    print(f"{'=' * 50}")
    print(f"  Bundle: {output_dir / 'bundle.json'}")
    print(f"  Locations: {len(bundle.locations)}")
    print(f"  Characters: {len(bundle.characters)}")
    print(f"  Objects: {len(bundle.objects)}")
    print(f"  Canon Events: {len(bundle.canon_events)}")
    print(f"  Chapters: {len(bundle.chapters)}")

    # Show chapter summary
    if bundle.chapters:
        print(f"\n  CHAPTERS:")
        for ch_id, ch in sorted(bundle.chapters.items(), key=lambda x: x[1].index):
            print(f"    {ch_id}: {ch.title[:50]} — {len(ch.characters)} chars, {len(ch.locations)} locs")

    print(f"\nPlay with: python scripts/web_ui_v2.py")
    print(f"  Select '{world_name}' in the dropdown")


if __name__ == "__main__":
    main()

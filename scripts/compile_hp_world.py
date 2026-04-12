#!/usr/bin/env python3
"""
Compile Harry Potter world from extraction results.

Usage:
    python scripts/compile_hp_world.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.compiler.world_builder import WorldBuilder
from storyweaver.world.bundle import WorldBundle


def main():
    world_name = "harry_potter_1"
    processed_dir = Path("data/processed") / world_name
    output_dir = Path("data/compiled") / world_name

    # Check extraction exists
    extraction_file = processed_dir / "extraction.json"
    if not extraction_file.exists():
        print(f"Error: No extraction.json found at {extraction_file}")
        print("Run extraction first: python scripts/run_extraction.py harry_potter_1")
        sys.exit(1)

    # Load extraction results
    print(f"Loading extraction results for '{world_name}'...")
    with open(extraction_file) as f:
        extraction = json.load(f)

    # Load book metadata
    with open(processed_dir / "meta.json") as f:
        meta = json.load(f)

    book_meta = {"title": meta.get("title", world_name), "author": meta.get("author", "Unknown")}

    print(f"Book: {book_meta['title']} by {book_meta['author']}")
    print(f"Characters: {len(extraction.get('structure', {}).get('characters', []))}")
    print(f"Locations: {len(extraction.get('structure', {}).get('locations', []))}")
    print(f"Objects: {len(extraction.get('structure', {}).get('objects', []))}")
    print(f"Events: {len(extraction.get('structure', {}).get('events', []))}")
    print()

    # Build world
    print("Building world...")
    bundle, agents = WorldBuilder.build(extraction, book_meta)

    # Save
    print(f"Saving to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle.save(output_dir)

    print(f"\nWorld compiled successfully!")
    print(f"  Bundle: {output_dir / 'bundle.json'}")
    print(f"  Locations: {len(bundle.locations)}")
    print(f"  Characters: {len(bundle.characters)}")
    print(f"  Objects: {len(bundle.objects)}")
    print(f"  Canon Events: {len(bundle.canon_events)}")
    print(f"\nPlay with: storyweaver play {world_name}")
    print(f"Or via web UI: python scripts/web_ui_v2.py")


if __name__ == "__main__":
    main()

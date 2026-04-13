#!/usr/bin/env python3
"""
Compile Harry Potter world from extraction results.

Usage:
    python scripts/compile_hp_world.py
    python scripts/compile_hp_world.py --cleaned    # Use cleaned extraction
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.compiler.world_builder import WorldBuilder
from storyweaver.world.bundle import WorldBundle


def main():
    parser = argparse.ArgumentParser(description="Compile HP world")
    parser.add_argument("--cleaned", action="store_true",
                        help="Use extraction_cleaned.json instead of extraction.json")
    args = parser.parse_args()

    world_name = "harry_potter_1"
    processed_dir = Path("data/processed") / world_name
    output_dir = Path("data/compiled") / world_name

    # Choose extraction file
    if args.cleaned:
        extraction_file = processed_dir / "extraction_cleaned.json"
        print("📂 Using CLEANED extraction file")
    else:
        extraction_file = processed_dir / "extraction.json"
        print("📂 Using RAW extraction file")

    if not extraction_file.exists():
        if args.cleaned:
            print(f"Error: No extraction_cleaned.json found at {extraction_file}")
            print("Run cleaning first: python scripts/clean_extraction.py harry_potter_1")
        else:
            print(f"Error: No extraction.json found at {extraction_file}")
            print("Run extraction first: python scripts/run_extraction.py harry_potter_1")
        sys.exit(1)

    # Load extraction results
    print(f"\nLoading extraction results for '{world_name}'...")
    with open(extraction_file, encoding="utf-8") as f:
        extraction = json.load(f)

    # Load segments (for chapter generation)
    segments = None
    segments_file = processed_dir / "segments.json"
    if segments_file.exists():
        with open(segments_file) as f:
            segments = json.load(f)
        print(f"📂 Loaded {len(segments)} segments for chapter generation")

    # Load book metadata
    with open(processed_dir / "meta.json", encoding="utf-8") as f:
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
    # WorldBuilder needs an LLM client but doesn't actually call it during compilation
    # Pass None — the agents will get no LLM client but the bundle builds fine
    builder = WorldBuilder(llm_client=None, config={"mode": "compile"})
    bundle, agents = builder.build(extraction, book_meta, segments=segments)

    # Save
    print(f"Saving to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle.save(output_dir)

    print(f"\n{'✅' if not args.cleaned else '🌟'} World compiled successfully!")
    print(f"  Bundle: {output_dir / 'bundle.json'}")
    print(f"  Locations: {len(bundle.locations)}")
    print(f"  Characters: {len(bundle.characters)}")
    print(f"  Objects: {len(bundle.objects)}")
    print(f"  Canon Events: {len(bundle.canon_events)}")
    print(f"  Chapters: {len(bundle.chapters)}")
    print(f"\nPlay with: storyweaver play {world_name}")
    print(f"Or via web UI: python scripts/web_ui_v2.py")


if __name__ == "__main__":
    main()

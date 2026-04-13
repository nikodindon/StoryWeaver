#!/usr/bin/env python3
"""
Step 3: Compile extraction results into a playable world.

Usage:
    python scripts/compile_world.py my_world_name
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.models.llamacpp_client import LlamaCppClient
from storyweaver.compiler.world_builder import WorldBuilder


def main():
    parser = argparse.ArgumentParser(description="Compile a world bundle")
    parser.add_argument("world_name", help="Name of the extracted book")
    parser.add_argument("--model-url", default="http://localhost:8080")
    args = parser.parse_args()

    processed_dir = Path("data/processed") / args.world_name

    with open(processed_dir / "extraction.json") as f:
        extraction = json.load(f)
    with open(processed_dir / "meta.json") as f:
        meta = json.load(f)

    # Load segments for chapter generation
    segments = None
    segments_file = processed_dir / "segments.json"
    if segments_file.exists():
        with open(segments_file) as f:
            segments = json.load(f)
        print(f"Loaded {len(segments)} segments for chapter generation")

    print(f"Compiling world: {meta['title']}")

    llm = LlamaCppClient(base_url=args.model_url)
    builder = WorldBuilder(llm_client=llm, config={})
    bundle, agents = builder.build(extraction, meta, segments=segments)

    output_dir = Path("data/compiled") / args.world_name
    bundle.save(output_dir)

    print(f"World compiled and saved to {output_dir}/")
    print(f"  Locations: {len(bundle.locations)}")
    print(f"  Characters: {len(bundle.characters)}")
    print(f"  Chapters: {len(bundle.chapters)}")
    print(f"Play with: storyweaver play {args.world_name}")


if __name__ == "__main__":
    main()

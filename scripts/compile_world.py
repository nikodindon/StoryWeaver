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

    print(f"Compiling world: {meta['title']}")

    llm = LlamaCppClient(base_url=args.model_url)
    builder = WorldBuilder(llm_client=llm, config={})
    world = builder.build(extraction, meta)

    output_dir = Path("data/compiled") / args.world_name
    world.save(output_dir)

    print(f"World compiled and saved to {output_dir}/")
    print(f"Play with: storyweaver play {args.world_name}")


if __name__ == "__main__":
    main()

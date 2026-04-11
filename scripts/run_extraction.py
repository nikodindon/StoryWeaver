#!/usr/bin/env python3
"""
Step 2: Run the deep extraction pipeline on a processed book.

This step is expensive — expect 2-8 hours for a full novel.
Results are cached; you can resume interrupted runs.

Usage:
    python scripts/run_extraction.py my_world_name
    python scripts/run_extraction.py my_world_name --passes structure,relations
    python scripts/run_extraction.py my_world_name --model-url http://localhost:8080
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.models.llamacpp_client import LlamaCppClient
from storyweaver.extraction.pipeline import ExtractionPipeline


def main():
    parser = argparse.ArgumentParser(description="Run extraction pipeline")
    parser.add_argument("world_name", help="Name of the processed book (from ingest step)")
    parser.add_argument("--passes", default="structure,relations,psychology,symbolism",
                        help="Comma-separated list of passes to run")
    parser.add_argument("--model-url", default="http://localhost:8080",
                        help="llama.cpp server URL")
    args = parser.parse_args()

    processed_dir = Path("data/processed") / args.world_name
    if not processed_dir.exists():
        print(f"Error: No processed book found at {processed_dir}")
        print(f"Run: python scripts/ingest_book.py <book_path> --output {args.world_name}")
        sys.exit(1)

    with open(processed_dir / "segments.json") as f:
        segments = json.load(f)
    with open(processed_dir / "meta.json") as f:
        meta = json.load(f)

    passes = [p.strip() for p in args.passes.split(",")]

    print(f"Starting extraction for '{meta['title']}'")
    print(f"  Segments: {len(segments)}")
    print(f"  Passes: {passes}")
    print(f"  Model: {args.model_url}")
    print(f"  This may take a long time. Results are cached — safe to interrupt and resume.\n")

    llm = LlamaCppClient(base_url=args.model_url)
    pipeline = ExtractionPipeline(
        llm_client=llm,
        cache_dir=Path("data/cache") / args.world_name,
        config={"chunk_size_tokens": 2000, "micro_chunk_size_tokens": 500},
    )

    results = pipeline.run(segments, args.world_name, passes=passes)

    output_dir = Path("data/processed") / args.world_name
    with open(output_dir / "extraction.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nExtraction complete. Results saved to {output_dir}/extraction.json")
    print(f"Next step: python scripts/compile_world.py {args.world_name}")


if __name__ == "__main__":
    main()

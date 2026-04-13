"""Monitor extraction progress for Dolan's Cadillac."""
import json
from pathlib import Path
import time
import glob as glob_mod

base = Path("data/processed/stephen_king_dolans_cadillac")
cache_dir = Path("data/cache/stephen_king_dolans_cadillac")

while True:
    # Count cached responses
    cached = list(cache_dir.glob("*.json")) if cache_dir.exists() else []
    
    # Check extraction log
    logs = list(Path(".").glob("extraction_log*.txt"))
    last_log = ""
    if logs:
        with open(logs[-1], "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                last_log = lines[-1].strip()[-150:]
    
    # Count segments processed
    seg_file = base / "segments.json"
    seg_count = 0
    if seg_file.exists():
        with open(seg_file) as f:
            seg_count = len(json.load(f))
    
    print(f"\n{'='*50}")
    print(f"  Extraction Monitor — {time.strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    print(f"  Segments: {seg_count}")
    print(f"  Cached LLM responses: {len(cached)}")
    if last_log:
        print(f"  Last log: {last_log}")
    
    # Check if extraction.json exists
    ext_file = base / "extraction.json"
    if ext_file.exists():
        size = ext_file.stat().st_size / 1024
        print(f"  extraction.json: {size:.0f} KB — DONE!")
    else:
        print(f"  extraction.json: not yet created")
    
    time.sleep(30)

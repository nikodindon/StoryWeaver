"""Debug script to test cover image and music detection."""
from pathlib import Path
import os
import sys

# Fix console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
print(f"PROJECT_ROOT: {PROJECT_ROOT}")

world_name = "harry_potter_1"
print(f"\n=== Testing cover detection for '{world_name}' ===\n")

# Direct match
images_dir = PROJECT_ROOT / "images" / world_name
print(f"Direct match: {images_dir}")
print(f"  exists: {images_dir.exists()}")

# Fuzzy match
images_root = PROJECT_ROOT / "images"
print(f"\nimages_root: {images_root}")
print(f"  exists: {images_root.exists()}")

if images_root.exists():
    try:
        contents = os.listdir(str(images_root))
        print(f"  contents: {contents}")
    except Exception as e:
        print(f"  ERROR listing: {e}")

    world_parts = world_name.lower().replace("_", " ").split()
    print(f"  world_parts: {world_parts}")

    for d in images_root.iterdir():
        if d.is_dir():
            dir_name_lower = d.name.lower()
            print(f"\n  Checking: '{d.name}'")
            print(f"    lower: '{dir_name_lower}'")
            matches = [part for part in world_parts if len(part) > 2 and part in dir_name_lower]
            print(f"    matches: {matches}")

            if any(part in dir_name_lower for part in world_parts if len(part) > 2):
                print(f"    => MATCH!")
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                    covers = list(d.glob(ext))
                    if covers:
                        print(f"    Found cover: {covers[0].resolve()}")
                        break

print(f"\n\n=== Testing music detection for '{world_name}' ===\n")

# Direct match
audio_dir = PROJECT_ROOT / "audio" / world_name
print(f"Direct match: {audio_dir}")
print(f"  exists: {audio_dir.exists()}")

# Fuzzy match
audio_root = PROJECT_ROOT / "audio"
print(f"\naudio_root: {audio_root}")
print(f"  exists: {audio_root.exists()}")

if audio_root.exists():
    try:
        contents = os.listdir(str(audio_root))
        print(f"  contents: {contents}")
    except Exception as e:
        print(f"  ERROR listing: {e}")

    world_parts = world_name.lower().replace("_", " ").split()
    print(f"  world_parts: {world_parts}")

    for d in audio_root.iterdir():
        if d.is_dir():
            dir_name_lower = d.name.lower()
            print(f"\n  Checking: '{d.name}'")
            print(f"    lower: '{dir_name_lower}'")
            matches = [part for part in world_parts if len(part) > 2 and part in dir_name_lower]
            print(f"    matches: {matches}")

            if any(part in dir_name_lower for part in world_parts if len(part) > 2):
                print(f"    => MATCH!")
                mp3s = list(d.glob("*.mp3"))
                print(f"    MP3 count: {len(mp3s)}")
                if mp3s:
                    print(f"    Found music dir: {d.resolve()}")
                    break

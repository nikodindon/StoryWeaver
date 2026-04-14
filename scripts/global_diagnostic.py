"""
Global quality diagnostic — compare all compiled worlds.
"""
import json
from pathlib import Path

compiled_dir = Path("data/compiled")

worlds = []
for d in sorted(compiled_dir.iterdir()):
    if d.is_dir() and (d / "bundle.json").exists():
        worlds.append(d)

print("=" * 70)
print("  STORYWEAVER — GLOBAL QUALITY DIAGNOSTIC")
print("=" * 70)

for world_dir in worlds:
    with open(world_dir / "bundle.json", encoding="utf-8") as f:
        bundle = json.load(f)

    chapters = bundle.get("chapters", {})
    canon_events = bundle.get("canon_events", [])
    locations = bundle.get("locations", {})
    characters = bundle.get("characters", {})
    objects_data = bundle.get("objects", {})
    gravity = bundle.get("gravity_map", {})
    timeline = bundle.get("timeline")

    print(f"\n{'─' * 70}")
    print(f"  📖 {bundle.get('source_title', 'Unknown')}")
    print(f"     by {bundle.get('source_author', 'Unknown')}")
    print(f"{'─' * 70}")

    # Overview
    print(f"  👤 Characters: {len(characters)}")
    print(f"  📍 Locations:  {len(locations)}")
    print(f"  📦 Objects:    {len(objects_data)}")
    print(f"  🎬 Events:     {len(canon_events)}")
    print(f"  📖 Chapters:   {len(chapters)}")

    # Chapter breakdown
    if chapters:
        print(f"\n  CHAPTER BREAKDOWN:")
        for ch_id, ch in sorted(chapters.items(), key=lambda x: x[1]["index"]):
            chars = ch.get("characters", [])
            locs = ch.get("locations", [])
            events = ch.get("events", [])
            prereqs = ch.get("prerequisites", [])
            title = ch.get("title", "?")[:50]
            print(f"    {ch_id}: {title}")
            print(f"         {len(chars)} chars, {len(locs)} locs, {len(events)} events, prereqs: {prereqs}")

    # Temporal system status
    has_chapters = len(chapters) > 0
    has_timeline = timeline is not None
    timeline_events = len(timeline.get("events", [])) if timeline else 0

    print(f"\n  TEMPORAL PROGRESSION:")
    print(f"    Chapters:  {'✅' if has_chapters else '❌'} ({len(chapters)})")
    print(f"    Timeline:  {'✅' if has_timeline else '❌'} ({timeline_events} events)")

    # Character quality
    major_chars = sum(1 for c in characters.values() if c.get("is_major"))
    print(f"\n  CHARACTER QUALITY:")
    print(f"    Major: {major_chars}, Minor: {len(characters) - major_chars}")

    # Issues
    issues = []
    if len(characters) == 0:
        issues.append("No characters!")
    if len(locations) == 0:
        issues.append("No locations!")
    if not has_chapters:
        issues.append("No temporal progression (world is flat)")
    if timeline_events == 0 and has_timeline:
        issues.append("Timeline exists but has no events")

    if issues:
        print(f"\n  ⚠️  ISSUES:")
        for issue in issues:
            print(f"    ⚠️  {issue}")
    else:
        print(f"\n  ✅ No critical issues")

# ── Summary table ──
print(f"\n{'=' * 70}")
print("  SUMMARY TABLE")
print(f"{'=' * 70}")
print(f"  {'World':<40} {'Chars':>5} {'Locs':>5} {'Evts':>5} {'Chaps':>5}")
print(f"  {'─' * 65}")

for world_dir in worlds:
    with open(world_dir / "bundle.json", encoding="utf-8") as f:
        bundle = json.load(f)
    title = bundle.get("source_title", "?")[:38]
    chars = len(bundle.get("characters", {}))
    locs = len(bundle.get("locations", {}))
    evts = len(bundle.get("canon_events", []))
    chaps = len(bundle.get("chapters", {}))
    print(f"  {title:<40} {chars:>5} {locs:>5} {evts:>5} {chaps:>5}")

print(f"{'=' * 70}")

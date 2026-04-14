"""
Quality audit for Dolan's Cadillac extraction.
Checks character quality, location quality, event quality, and overall stats.
"""
import json
from pathlib import Path
from collections import Counter

base = Path("data/processed/stephen_king_dolans_cadillac")

# Load extraction
with open(base / "extraction.json", encoding="utf-8") as f:
    ext = json.load(f)

# Load segments
with open(base / "segments.json") as f:
    segments = json.load(f)

print("=" * 60)
print("  DOLAN'S CADILLAC — EXTRACTION QUALITY AUDIT")
print("=" * 60)

# ── Overview ──
structure = ext.get("structure", {})
characters = structure.get("characters", [])
locations = structure.get("locations", [])
objects = structure.get("objects", [])
events = structure.get("events", [])

print(f"\n📊 OVERVIEW")
print(f"  Segments: {len(segments)}")
print(f"  Cached LLM responses: 58")
print(f"  Characters extracted: {len(characters)}")
print(f"  Locations extracted: {len(locations)}")
print(f"  Objects extracted: {len(objects)}")
print(f"  Events extracted: {len(events)}")

# ── Character Quality ──
print(f"\n👤 CHARACTERS (total: {len(characters)})")

# Check for common false positives
false_positive_keywords = [
    "school", "car", "cadillac", "book", "movie", "story", 
    "chapter", "page", "reader", "author", "novel", "narrator",
    "first-graders", "students", "children", "pupil",
    "police", "fbi", "government", "company",
]

majors = [c for c in characters if c.get("is_major")]
minors = [c for c in characters if not c.get("is_major")]

print(f"  Major: {len(majors)}")
print(f"  Minor: {len(minors)}")

# Show first 20
print(f"\n  First 20 characters:")
for c in characters[:20]:
    major_marker = "⭐" if c.get("is_major") else "  "
    print(f"    {major_marker} {c['name']} — {c.get('description', '')[:50]}")

# Check for false positives
print(f"\n  ⚠️  Potential false positives:")
fp_count = 0
for c in characters:
    name_lower = c["name"].lower()
    for kw in false_positive_keywords:
        if kw in name_lower:
            print(f"    ⚠️  {c['name']} — keyword: '{kw}'")
            fp_count += 1
            break
if fp_count == 0:
    print(f"    ✅ None obvious!")

# ── Location Quality ──
print(f"\n📍 LOCATIONS (total: {len(locations)})")
for loc in locations[:15]:
    conn = len(loc.get("connected_to", []))
    print(f"    📍 {loc['name']} — connections: {conn} — {loc.get('description', '')[:40]}")

# ── Object Quality ──
print(f"\n📦 OBJECTS (total: {len(objects)})")
for obj in objects[:15]:
    sym = "✨" if obj.get("symbolic") else "  "
    print(f"    {sym} {obj['name']} — {obj.get('description', '')[:50]}")

# ── Event Quality ──
print(f"\n🎬 EVENTS (total: {len(events)})")
for evt in events[:10]:
    parts = ", ".join(evt.get("participants", [])[:3])
    loc = evt.get("location", "?")
    print(f"    🎬 {evt.get('description', '')[:60]}")
    print(f"        ↳ participants: {parts} | location: {loc}")

# ── Pass 2: Relations ──
relations = ext.get("relations", {})
social = relations.get("social_graph", [])
conflicts = relations.get("conflicts", [])
timeline = relations.get("timeline", [])

print(f"\n🔗 RELATIONS (Pass 2)")
print(f"  Social edges: {len(social)}")
print(f"  Conflicts: {len(conflicts)}")
print(f"  Timeline events: {len(timeline)}")

if social:
    print(f"\n  Social graph:")
    for rel in social[:10]:
        print(f"    {rel.get('from', '?')} ↔ {rel.get('to', '?')} — trust: {rel.get('trust', '?')}, type: {rel.get('relation_type', '?')}")

# ── Pass 3: Psychology ──
psychology = ext.get("psychology", {})
print(f"\n🧠 PSYCHOLOGY (Pass 3)")
print(f"  Profiles: {len(psychology)}")
for char_id, profile in list(psychology.items())[:5]:
    if isinstance(profile, dict):
        traits = profile.get("traits", [])
        goals = profile.get("goals", [])
        print(f"    🧠 {char_id} — {len(traits)} traits, {len(goals)} goals")

# ── Pass 4: Symbolism ──
symbolism = ext.get("symbolism", {})
print(f"\n🎨 SYMBOLISM (Pass 4)")
themes = symbolism.get("themes", [])
motifs = symbolism.get("motifs", [])
tone = symbolism.get("tone", "")
world_rules = symbolism.get("world_rules", [])
print(f"  Themes: {len(themes)}")
print(f"  Motifs: {len(motifs)}")
print(f"  Tone: {tone}")
print(f"  World rules: {len(world_rules)}")

if themes:
    print(f"\n  Top themes:")
    for t in themes[:8]:
        print(f"    🎭 {t}")

# ── Overall Quality Score ──
print(f"\n{'=' * 60}")
print("  QUALITY SUMMARY")
print(f"{'=' * 60}")

# Simple scoring
char_quality = max(0, 100 - fp_count * 5)  # Penalize false positives
has_relations = min(100, len(social) * 20)
has_psychology = min(100, len(psychology) * 10)
has_symbolism = min(100, (len(themes) + len(motifs)) * 8)

overall = (char_quality + has_relations + has_psychology + has_symbolism) / 4

print(f"  Character quality: {char_quality:.0f}% ({fp_count} false positives)")
print(f"  Relations:         {has_relations:.0f}% ({len(social)} edges)")
print(f"  Psychology:        {has_psychology:.0f}% ({len(psychology)} profiles)")
print(f"  Symbolism:         {has_symbolism:.0f}% ({len(themes)} themes, {len(motifs)} motifs)")
print(f"  ─────────────────────────────────")
print(f"  OVERALL:           {overall:.0f}%")

if overall >= 70:
    print(f"\n  ✅ Ready to compile!")
elif overall >= 50:
    print(f"\n  ⚠️  Usable but could be improved")
else:
    print(f"\n  ❌ Needs cleaning before compilation")

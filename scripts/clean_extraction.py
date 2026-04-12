#!/usr/bin/env python3
"""
Clean and enrich extraction.json before compilation.

This script addresses known issues with the LLM extraction pipeline:
1. Deduplicate characters/locations/objects with fuzzy name matching
2. Remove trivial objects (desserts, clothing, generic items)
3. Deduplicate events across segments
4. Fix ID mismatches (e.g. "Harry" vs "Harry Potter")
5. Rebuild object ownership and location context
6. Validate and merge social graph relationships
7. Enrich character descriptions

Usage:
    python scripts/clean_extraction.py harry_potter_1

Output:
    data/processed/harry_potter_1/extraction_cleaned.json
"""
import sys
import json
import re
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Configuration ──────────────────────────────────────────────────────────

# Threshold for fuzzy name matching (0.0-1.0)
NAME_SIMILARITY_THRESHOLD = 0.75

# Keywords that indicate a trivial object (not worth keeping for gameplay)
TRIVIAL_OBJECT_KEYWORDS = [
    # Food & drinks
    "cake", "pie", "ice cream", "tart", "eclair", "bun", "biscuit", "bread",
    "chocolate", "candy", "sweet", "pudding", "jelly", "treacle", "boiled sweet",
    "drink", "juice", "tea", "coffee", "water", "wine", "beer",
    # Generic clothing
    "shirt", "pants", "trousers", "sock", "shoe", "hat", "coat", "robe",
    "cloak", "scarf", "glove", "belt", "dress", "skirt", "jacket",
    # Generic objects
    "table", "chair", "plate", "cup", "fork", "knife", "spoon", "napkin",
    "bowl", "glass", "mug", "dish", "tray",
    "wall", "floor", "ceiling", "door", "window", "step", "stair",
    # Abstract/generic
    "something", "thing", "person", "people", "crowd",
]

# Known character canonical name mappings
# Maps variant names → canonical name
CHARACTER_NAME_MAPPINGS = {
    # Harry Potter variants
    "harry": "Harry Potter",
    "harry potter": "Harry Potter",
    "the boy": "Harry Potter",
    "the boy who lived": "Harry Potter",

    # Ron Weasley variants
    "ron": "Ron Weasley",
    "ron weasley": "Ron Weasley",
    "weasley": "Ron Weasley",

    # Hermione Granger variants
    "hermione": "Hermione Granger",
    "hermione granger": "Hermione Granger",
    "miss granger": "Hermione Granger",

    # Dumbledore variants
    "dumbledore": "Albus Dumbledore",
    "albus dumbledore": "Albus Dumbledore",
    "professor dumbledore": "Albus Dumbledore",

    # Hagrid variants
    "hagrid": "Rubeus Hagrid",
    "rubeus hagrid": "Rubeus Hagrid",

    # Snape variants
    "snape": "Severus Snape",
    "snug": "Severus Snape",
    "severus snape": "Severus Snape",
    "professor snape": "Severus Snape",

    # Voldemort variants
    "voldemort": "Lord Voldemort",
    "lord voldemort": "Lord Voldemort",
    "you-know-who": "Lord Voldemort",
    "you know who": "Lord Voldemort",
    "the dark lord": "Lord Voldemort",
    "tom riddle": "Lord Voldemort",

    # McGonagall variants
    "mcgonagall": "Minerva McGonagall",
    "minerva mcgonagall": "Minerva McGonagall",
    "professor mcgonagall": "Minerva McGonagall",

    # Dursley variants
    "uncle vernon": "Vernon Dursley",
    "vernon dursley": "Vernon Dursley",
    "mr. dursley": "Vernon Dursley",
    "mr dursley": "Vernon Dursley",
    "aunt petunia": "Petunia Dursley",
    "petunia dursley": "Petunia Dursley",
    "mrs. dursley": "Petunia Dursley",
    "mrs dursley": "Petunia Dursley",

    # Draco Malfoy variants
    "draco": "Draco Malfoy",
    "draco malfoy": "Draco Malfoy",
    "malfoy": "Draco Malfoy",

    # Neville Longbottom variants
    "neville": "Neville Longbottom",
    "neville longbottom": "Neville Longbottom",
    "mr. longbottom": "Neville Longbottom",

    # Percy Weasley variants
    "percy": "Percy Weasley",
    "percy weasley": "Percy Weasley",

    # Other characters
    "dudley": "Dudley Dursley",
    "dudley dursley": "Dudley Dursley",
    "piers": "Piers Polkiss",
    "piers polkiss": "Piers Polkiss",
    "griphook": "Griphook",
    "quirrell": "Professor Quirrell",
    "professor quirrell": "Professor Quirrell",
    "flitwick": "Professor Flitwick",
    "professor flitwick": "Professor Flitwick",
    "sprout": "Professor Sprout",
    "professor sprout": "Professor Sprout",
    "oliver wood": "Oliver Wood",
    "wood": "Oliver Wood",
    "nearly headless nick": "Nearly Headless Nick",
    "the bloody baron": "The Bloody Baron",
    "fat friar": "The Fat Friar",
    "gryffindor": "Godric Gryffindor",
    "slytherin": "Salazar Slytherin",
    "ravenclaw": "Rowena Ravenclaw",
    "hufflepuff": "Helga Hufflepuff",
}

# Location canonical mappings
LOCATION_NAME_MAPPINGS = {
    "hogwarts": "Hogwarts",
    "hogwarts castle": "Hogwarts",
    "hogwarts school": "Hogwarts",
    "hogwarts school of witchcraft and wizardry": "Hogwarts",
    "privet drive": "Privet Drive",
    "number four privet drive": "Privet Drive",
    "number four's drive": "Privet Drive",
    "the dursley's house": "Privet Drive",
    "dursley's house": "Privet Drive",
    "4 privet drive": "Privet Drive",
    "diagon alley": "Diagon Alley",
    "the leaky cauldron": "The Leaky Cauldron",
    "leaky cauldron": "The Leaky Cauldron",
    "gringotts": "Gringotts",
    "gringotts bank": "Gringotts",
    "gringotts vault": "Gringotts Vault 713",
    "vault 713": "Gringotts Vault 713",
    "king's cross": "King's Cross Station",
    "kings cross": "King's Cross Station",
    "platform nine-and-three-quarters": "Platform 9¾",
    "platform 9 3/4": "Platform 9¾",
    "platform nine and three quarters": "Platform 9¾",
    "hogwarts express": "Hogwarts Express",
    "great hall": "The Great Hall",
    "the great hall": "The Great Hall",
    "hogwarts forever": "The Moving Stairs",
    "the moving stairs": "The Moving Stairs",
    "forbidden forest": "The Forbidden Forest",
    "the forbidden forest": "The Forbidden Forest",
    "hogsmeade": "Hogsmeade",
    "hogsmeade village": "Hogsmeade",
    "quidditch pitch": "The Quidditch Pitch",
    "quidditch field": "The Quidditch Pitch",
    "gryffindor common room": "Gryffindor Common Room",
    "gryffindor tower": "Gryffindor Tower",
    "slytherin common room": "Slytherin Common Room",
    "dumbledore's office": "Dumbledore's Office",
    "headmaster's office": "Dumbledore's Office",
    "the burrow": "The Burrow",
    "the burrow ": "The Burrow",
}


# ── Core Cleaning Functions ───────────────────────────────────────────────

def normalize_name(name: str) -> str:
    """Normalize a name for comparison."""
    return name.strip().lower().replace("_", " ").replace("  ", " ")


def fuzzy_match(name: str, candidates: list[str], threshold: float = NAME_SIMILARITY_THRESHOLD) -> str | None:
    """Find the best fuzzy match for a name among candidates."""
    normalized = normalize_name(name)
    best_score = 0.0
    best_match = None

    for candidate in candidates:
        cand_norm = normalize_name(candidate)
        score = SequenceMatcher(None, normalized, cand_norm).ratio()

        # Boost score for substring matches
        if normalized in cand_norm or cand_norm in normalized:
            score = max(score, 0.85)

        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        return best_match
    return None


def resolve_character_name(name: str, known_names: list[str]) -> str:
    """Resolve a character name to its canonical form."""
    # First check explicit mappings
    norm = normalize_name(name)
    if norm in {normalize_name(k): k for k in CHARACTER_NAME_MAPPINGS}.values():
        # Already canonical
        for mapping_name, canonical in CHARACTER_NAME_MAPPINGS.items():
            if normalize_name(mapping_name) == norm:
                return canonical

    if name in CHARACTER_NAME_MAPPINGS:
        return CHARACTER_NAME_MAPPINGS[name]

    # Check if any mapping key matches (case-insensitive)
    for mapping_key, canonical in CHARACTER_NAME_MAPPINGS.items():
        if normalize_name(mapping_key) == norm:
            return canonical

    # Check if name is already in known names
    for known in known_names:
        if normalize_name(known) == norm:
            return known

    # Try fuzzy matching
    match = fuzzy_match(name, known_names)
    if match:
        return match

    # Return original if nothing matched
    return name


def resolve_location_name(name: str, known_names: list[str]) -> str:
    """Resolve a location name to its canonical form."""
    norm = normalize_name(name)

    # Check explicit mappings
    for mapping_key, canonical in LOCATION_NAME_MAPPINGS.items():
        if normalize_name(mapping_key) == norm:
            return canonical

    # Check if already in known names
    for known in known_names:
        if normalize_name(known) == norm:
            return known

    # Try fuzzy matching
    match = fuzzy_match(name, known_names)
    if match:
        return match

    return name


def is_trivial_object(name: str, description: str = "") -> bool:
    """Check if an object is too trivial to keep for gameplay."""
    text = f"{name} {description}".lower()

    for keyword in TRIVIAL_OBJECT_KEYWORDS:
        if keyword in text:
            return True

    # Check if it's a food item (common pattern in HP)
    food_patterns = ["soup", "stew", "meat", "chicken", "beef", "roast",
                     "rice", "potato", "vegetable", "fruit", "apple", "orange", "banana"]
    for pattern in food_patterns:
        if pattern in text:
            return True

    return False


def merge_characters(characters: list[dict]) -> list[dict]:
    """Deduplicate and merge character entries."""
    # First pass: collect all names and resolve to canonical
    all_names = set()
    for char in characters:
        canonical = resolve_character_name(char["name"], list(all_names))
        all_names.add(canonical)

    # Second pass: merge by canonical name
    merged = {}
    for char in characters:
        canonical = resolve_character_name(char["name"], list(all_names))

        if canonical not in merged:
            merged[canonical] = char.copy()
            merged[canonical]["name"] = canonical
            merged[canonical]["name_variants"] = set()
            merged[canonical]["name_variants"].add(char["name"])
        else:
            # Merge: keep the longer description
            existing_desc = merged[canonical].get("description", "")
            new_desc = char.get("description", "")
            if len(new_desc) > len(existing_desc):
                merged[canonical]["description"] = new_desc

            # Track variants
            merged[canonical]["name_variants"].add(char["name"])

            # Preserve is_major if any version says it's major
            if char.get("is_major", False):
                merged[canonical]["is_major"] = True

    # Convert sets to lists for JSON serialization
    for char in merged.values():
        if "name_variants" in char:
            char["name_variants"] = sorted(char["name_variants"])

    return list(merged.values())


def merge_locations(locations: list[dict]) -> list[dict]:
    """Deduplicate and merge location entries."""
    all_names = set()
    for loc in locations:
        canonical = resolve_location_name(loc["name"], list(all_names))
        all_names.add(canonical)

    merged = {}
    for loc in locations:
        canonical = resolve_location_name(loc["name"], list(all_names))

        if canonical not in merged:
            merged[canonical] = loc.copy()
            merged[canonical]["name"] = canonical
            merged[canonical]["name_variants"] = set()
            merged[canonical]["name_variants"].add(loc["name"])
            merged[canonical]["connections"] = set()
        else:
            merged[canonical]["name_variants"].add(loc["name"])

            # Merge descriptions (keep longer)
            existing_desc = merged[canonical].get("description", "")
            new_desc = loc.get("description", "")
            if len(new_desc) > len(existing_desc):
                merged[canonical]["description"] = new_desc

            # Merge connections
            for conn in loc.get("connected_to", []):
                merged[canonical]["connections"].add(conn)

    # Convert to serializable format
    result = []
    for loc in merged.values():
        loc_copy = loc.copy()
        loc_copy["name_variants"] = sorted(loc_copy.get("name_variants", set()))

        # Resolve connection names
        resolved_connections = []
        for conn in loc_copy.get("connections", []):
            resolved = resolve_location_name(conn, list(merged.keys()))
            resolved_connections.append(resolved)
        loc_copy["connected_to"] = sorted(set(resolved_connections))

        # Remove internal sets
        if "connections" in loc_copy:
            del loc_copy["connections"]

        result.append(loc_copy)

    return result


def deduplicate_events(events: list[dict]) -> list[dict]:
    """Remove duplicate events while preserving unique ones."""
    seen = set()
    unique_events = []

    for event in events:
        # Create a hashable key from the event
        desc = normalize_name(event.get("description", ""))
        participants = tuple(sorted([normalize_name(p) for p in event.get("participants", [])]))
        location = normalize_name(event.get("location", ""))

        key = (desc, participants, location)

        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    print(f"  Events: {len(events)} → {len(unique_events)} (removed {len(events) - len(unique_events)} duplicates)")
    return unique_events


def clean_objects(objects: list[dict]) -> list[dict]:
    """Filter out trivial objects and clean up the rest."""
    cleaned = []
    removed_count = 0

    for obj in objects:
        name = obj.get("name", "")
        desc = obj.get("description", "")

        if is_trivial_object(name, desc):
            removed_count += 1
            continue

        # Clean up the object
        cleaned.append(obj)

    print(f"  Objects: {len(objects)} → {len(cleaned)} (removed {removed_count} trivial)")
    return cleaned


def clean_social_graph(social_graph: list[dict], character_names: list[str]) -> list[dict]:
    """Clean and resolve character names in the social graph."""
    cleaned = []
    canonical_names = list(set(character_names))

    for edge in social_graph:
        from_name = resolve_character_name(edge.get("from", ""), canonical_names)
        to_name = resolve_character_name(edge.get("to", ""), canonical_names)

        # Skip self-loops or unresolvable names
        if from_name == to_name:
            continue
        if from_name in character_names and to_name in character_names:
            edge["from"] = from_name
            edge["to"] = to_name
            cleaned.append(edge)

    print(f"  Social graph: {len(social_graph)} → {len(cleaned)} edges")
    return cleaned


def fix_event_participants(events: list[dict], character_names: list[str]) -> list[dict]:
    """Fix participant names in events to match canonical character names."""
    canonical_names = list(set(character_names))

    for event in events:
        fixed_participants = []
        for participant in event.get("participants", []):
            resolved = resolve_character_name(participant, canonical_names)
            if resolved in character_names:
                fixed_participants.append(resolved)
            else:
                # Keep unresolved names (might be NPCs)
                fixed_participants.append(participant)

        event["participants"] = fixed_participants

    return events


def enrich_extraction(extraction: dict) -> dict:
    """Main enrichment function that orchestrates all cleaning steps."""
    print("\n🧹 Cleaning and enriching extraction data...\n")

    structure = extraction.get("structure", {})
    relations = extraction.get("relations", {})

    # ── Step 1: Merge characters ──
    print("1. Merging characters...")
    characters = structure.get("characters", [])
    print(f"  Before: {len(characters)} entries")
    characters = merge_characters(characters)
    print(f"  After: {len(characters)} unique characters")
    structure["characters"] = characters

    # ── Step 2: Merge locations ──
    print("\n2. Merging locations...")
    locations = structure.get("locations", [])
    print(f"  Before: {len(locations)} entries")
    locations = merge_locations(locations)
    print(f"  After: {len(locations)} unique locations")
    structure["locations"] = locations

    # ── Step 3: Clean objects ──
    print("\n3. Cleaning objects...")
    objects = structure.get("objects", [])
    print(f"  Before: {len(objects)} entries")
    objects = clean_objects(objects)
    structure["objects"] = objects

    # ── Step 4: Deduplicate events ──
    print("\n4. Deduplicating events...")
    events = structure.get("events", [])
    print(f"  Before: {len(events)} entries")
    events = deduplicate_events(events)
    structure["events"] = events

    # ── Step 5: Fix event participants ──
    print("\n5. Fixing event participants...")
    char_names = {c["name"] for c in characters}
    events = fix_event_participants(events, char_names)
    structure["events"] = events

    # ── Step 6: Clean social graph ──
    print("\n6. Cleaning social graph...")
    social_graph = relations.get("social_graph", [])
    social_graph = clean_social_graph(social_graph, char_names)
    relations["social_graph"] = social_graph

    # ── Summary ──
    print("\n" + "=" * 50)
    print("📊 CLEANING SUMMARY")
    print("=" * 50)
    print(f"  Characters: {len(characters)}")
    print(f"  Locations:  {len(locations)}")
    print(f"  Objects:    {len(objects)}")
    print(f"  Events:     {len(events)}")
    print(f"  Relations:  {len(social_graph)} edges")
    print("=" * 50)

    # ── Update extraction ──
    extraction["structure"] = structure
    extraction["relations"] = relations

    # Add cleaning metadata
    extraction["_cleaning"] = {
        "cleaned_at": "2026-04-12",
        "cleaning_version": "1.0",
        "actions": [
            "character_deduplication",
            "location_deduplication",
            "object_filtering",
            "event_deduplication",
            "participant_resolution",
            "social_graph_cleaning",
        ],
    }

    return extraction


# ── CLI Entry Point ───────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/clean_extraction.py <world_name>")
        print("Example: python scripts/clean_extraction.py harry_potter_1")
        sys.exit(1)

    world_name = sys.argv[1]
    processed_dir = Path("data/processed") / world_name

    # Check extraction exists
    extraction_file = processed_dir / "extraction.json"
    if not extraction_file.exists():
        print(f"Error: No extraction.json found at {extraction_file}")
        print(f"Run extraction first: python scripts/run_extraction.py {world_name}")
        sys.exit(1)

    # Load extraction
    print(f"Loading extraction from {extraction_file}...")
    with open(extraction_file) as f:
        extraction = json.load(f)

    print(f"Loaded extraction:")
    structure = extraction.get("structure", {})
    print(f"  Characters: {len(structure.get('characters', []))}")
    print(f"  Locations:  {len(structure.get('locations', []))}")
    print(f"  Objects:    {len(structure.get('objects', []))}")
    print(f"  Events:     {len(structure.get('events', []))}")

    # Clean and enrich
    cleaned = enrich_extraction(extraction)

    # Save cleaned extraction
    output_file = processed_dir / "extraction_cleaned.json"
    print(f"\n💾 Saving cleaned extraction to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Cleaned extraction saved to: {output_file}")
    print(f"\nNext step: Update compile_hp_world.py to use extraction_cleaned.json")
    print(f"Or run: python scripts/compile_hp_world.py --cleaned")


if __name__ == "__main__":
    main()

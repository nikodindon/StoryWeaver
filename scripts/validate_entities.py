"""
Entity Type Validation Pipeline — Step 2 of extraction improvement.

Validates extracted entities and filters out false positives.
Uses heuristic rules to classify entities as:
- PERSON (valid character)
- LOCATION (place)
- OBJECT (thing)
- CREATURE (animal/magical creature)
- GROUP (organization/crowd)
- CONCEPT (abstract idea)

Usage:
    python scripts/validate_entities.py <world_name>
    python scripts/validate_entities.py stephen_king_dolans_cadillac
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from loguru import logger

# ── Validation Rules ─────────────────────────────────────────────────────

# Common proper-name indicators (these suggest a real person)
PROPER_NAME_INDICATORS = [
    "mr.", "mrs.", "ms.", "miss", "mr", "mrs",
    "professor", "prof.", "dr.", "doctor",
    "lady", "lord", "sir", "dame",
    "aunt", "uncle", "cousin",
    "captain", "sergeant", "colonel",
]

# Words that strongly indicate a real person (when in name)
PERSON_WORDS = [
    "potter", "weasley", "granger", "malfoy", "snape",
    "dumbledore", "mcgonagall", "hagrid", "black", "lupin",
    "voldemort", "quirrell", "lockhart", "dursley",
    "longbottom", "thomas", "finnigan", "patil",
]

# Location indicators in name or description
LOCATION_INDICATORS = [
    "school", "house", "street", "drive", "station", "platform",
    "hall", "room", "office", "kitchen", "bedroom", "bathroom",
    "garden", "shed", "closet", "cupboard", "shop", "store",
    "alley", "castle", "dungeon", "tower", "bridge",
    "library", "hospital", "bank", "pub", "inn",
    "hogwarts", "hogwarts", "privet", "diagon", "hogsmeade",
    "gringotts",
]

# Object indicators
OBJECT_INDICATORS = [
    "sweater", "jumper", "dress", "shirt", "coat", "hat",
    "book", "letter", "cake", "pie", "candy", "car",
    "vehicle", "motorcycle", "bicycle", "broom", "wand",
    "potion", "ingredient", "cauldron", "trunk", "chest",
    "sweater", "clock", "mirror", "painting", "portrait",
]

# Creature indicators
CREATURE_INDICATORS = [
    "cat", "owl", "rat", "toad", "dog", "horse", "dragon",
    "troll", "giant", "centaur", "merperson", "ghost",
    "dementor", "boggart", "thestral", "unicorn",
    "hippogriff", "spider", "snake", "frog",
    "mountain troll", "norbert", "fang", "scabbers",
    "mrs. norris", "hedwig", "errol", "pigwidgeon",
    "crookshanks", "trevor", "fluffy", "aragog",
]

# Group indicators
GROUP_INDICATORS = [
    "crowd", "group", "people", "students", "children",
    "family", "gang", "mob", "team", "ministry", "order",
    "death eater", "death eaters", "knights", "wizards",
    "witches", "muggles", "teachers", "professors", "staff",
    "goblins", "owls", "muggles", "dursleys",
]


def classify_entity(entity_id: str, name: str, description: str = "") -> str:
    """Classify an entity as PERSON, LOCATION, OBJECT, CREATURE, GROUP, or CONCEPT."""
    text = f"{entity_id} {name} {description}".lower()
    name_lower = name.lower()

    # 1. Check if it's a GROUP first (plural or collective)
    for indicator in GROUP_INDICATORS:
        if indicator in text:
            # But some groups are real characters (e.g., "Dudley's gang" → Dudley)
            if "'" in name and "gang" in name_lower:
                return "PERSON"  # "Dudley's gang" is about Dudley
            return "GROUP"

    # 2. Check for PROPER NAMES (strong person indicator)
    for indicator in PROPER_NAME_INDICATORS:
        if name_lower.startswith(indicator):
            return "PERSON"

    # 3. Check for known character names
    for word in PERSON_WORDS:
        if word in name_lower:
            return "PERSON"

    # 4. Check for CREATURES
    for indicator in CREATURE_INDICATORS:
        if indicator in text:
            return "CREATURE"

    # 5. Check for single-word animal names
    single_word_animals = ["cat", "owl", "rat", "toad", "dog", "snake", "spider"]
    if name_lower.strip() in single_word_animals:
        return "CREATURE"

    # 6. Check for LOCATIONS
    for indicator in LOCATION_INDICATORS:
        if indicator in text:
            return "LOCATION"

    # 7. Check for OBJECTS
    for indicator in OBJECT_INDICATORS:
        if indicator in text:
            return "OBJECT"

    # 8. Check for plural words (likely groups or objects, not persons)
    if name_lower.endswith("s") and not name_lower.endswith("'s"):
        # "owls", "goblins", "muggles" → not individual characters
        return "GROUP"

    # 9. Check for possessive objects (e.g., "Weasley sweater", "Malfoy's broom")
    possessive_patterns = [r"\w+['']s?\s+\w+", r"\w+['']s?\s+"]
    for pattern in possessive_patterns:
        if re.search(pattern, name_lower):
            parts = name_lower.split()
            if len(parts) >= 2:
                last_word = parts[-1]
                if last_word in ["sweater", "broom", "owl", "cat", "car"]:
                    return "OBJECT"
                elif last_word in ["gang", "family", "group"]:
                    return "GROUP"

    # 10. Default: if it looks like a name (capitalized, short), accept as PERSON
    if len(name) < 50 and name[0].isupper():
        return "PERSON"

    return "UNKNOWN"


def validate_extraction(world_name: str) -> Dict:
    """Validate and clean an extraction.json file."""
    input_path = Path(f"data/processed/{world_name}/extraction.json")
    if not input_path.exists():
        logger.error(f"Extraction not found: {input_path}")
        return {}

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    characters = data.get("structure", {}).get("characters", {})
    logger.info(f"Validating {len(characters)} extracted characters from '{world_name}'")

    results = {
        "PERSON": [],
        "LOCATION": [],
        "OBJECT": [],
        "CREATURE": [],
        "GROUP": [],
        "CONCEPT": [],
        "UNKNOWN": [],
    }

    for cid, char_data in characters.items():
        name = char_data.get("name", cid)
        desc = char_data.get("description", "")
        classification = classify_entity(cid, name, desc)
        results[classification].append({
            "id": cid,
            "name": name,
            "description": desc[:100] if desc else "",
        })

    # Summary
    total = len(characters)
    valid = len(results["PERSON"])
    logger.info(f"\n{'='*50}")
    logger.info(f"  Validation Results for '{world_name}'")
    logger.info(f"{'='*50}")
    logger.info(f"  Total extracted: {total}")
    logger.info(f"  Valid PERSON: {valid} ({valid/total*100:.1f}%)")

    for category in ["LOCATION", "OBJECT", "CREATURE", "GROUP", "CONCEPT", "UNKNOWN"]:
        count = len(results[category])
        if count > 0:
            logger.info(f"  {category}: {count} ({count/total*100:.1f}%)")

    # Show false positives
    fp_total = total - valid
    logger.info(f"\n  False positive rate: {fp_total}/{total} = {fp_total/total*100:.1f}%")

    # Show some examples
    for category in ["LOCATION", "OBJECT", "CREATURE", "GROUP"]:
        if results[category]:
            logger.info(f"\n  {category} examples:")
            for item in results[category][:5]:
                logger.info(f"    - {item['id']}: {item['name']}")

    return results


def filter_characters(results: Dict) -> Dict:
    """Return only valid PERSON characters."""
    return {item["id"]: item for item in results["PERSON"]}


# ── CLI Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate extracted entities")
    parser.add_argument("world_name", help="World name (e.g., stephen_king_dolans_cadillac)")
    args = parser.parse_args()

    results = validate_extraction(args.world_name)

    if results:
        # Save filtered characters
        filtered = filter_characters(results)
        output_path = Path(f"data/processed/{args.world_name}/validation_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "valid_persons": filtered,
                "all_classifications": results,
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"\nSaved validation results to {output_path}")

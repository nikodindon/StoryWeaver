"""Analyze HP bundle for false positive characters."""
import json
from pathlib import Path

bundle_path = Path("data/compiled/harry_potter_1/bundle.json")
with open(bundle_path, "r", encoding="utf-8") as f:
    data = json.load(f)

chars = data.get("characters", {})
locs = data.get("locations", {})
objs = data.get("objects", {})

print(f"Total characters: {len(chars)}")
print(f"Total locations: {len(locs)}")
print(f"Total objects: {len(objs)}")

# Categorize characters
false_positives = {
    "locations": [],
    "objects": [],
    "animals_creatures": [],
    "groups": [],
    "concepts": [],
    "adjectives": [],
    "valid": [],
    "unknown": [],
}

location_words = [
    "school", "house", "room", "street", "drive", "parking", "lot",
    "station", "platform", "hall", "office", "kitchen", "bedroom",
    "bathroom", "garden", "shed", "closet", "cupboard", "shop",
    "store", "alley", "castle", "dungeon", "tower", "bridge",
    "common", "dormitory", "hospital", "wing", "chamber", "dining",
    "great", "library", "laboratory", "studio", "classroom",
    "entrance", "courtyard", "forest", "lake", "grounds",
    "hogsmeade", "hogwarts", "privet", "diagon", "knockturn",
    "forbidden", "chamber", "whomping", "willow", "shrieking",
    "shack", "three", "broomsticks", "heads", "boar", "hog",
    "pig", "head", "honeydukes", "zonko", "scivell",
    "scrivenshaft", "quality", "quidditch", "supplies", "floo",
    "powder", "phoenix", "feather", "gringotts", "bank",
    "leaky", "cauldron", "muggle", "station", "crossing",
    "kings", "cross", "paddington", "london",
    "sofa", "bed", "chair", "table", "desk", "lamp", "fireplace",
    "mantle", "window", "door", "stairs", "floor", "wall",
    "ceiling", "roof", "garden", "driveway", "lawn", "fence",
    "porch", "veranda", "patio", "terrace", "balcony",
]

object_words = [
    "sweater", "jumper", "clothes", "dress", "shirt", "coat",
    "hat", "scarf", "gloves", "shoes", "boots", "socks",
    "ring", "necklace", "bracelet", "earring", "watch",
    "book", "letter", "paper", "pen", "quill", "parchment",
    "cake", "pie", "candy", "sweet", "chocolate", "biscuit",
    "tea", "coffee", "coffee", "breakfast", "lunch", "dinner",
    "dessert", "pudding", "treat", "snack", "meal", "food",
    "car", "vehicle", "motorcycle", "bicycle",
]

animal_words = [
    "cat", "owl", "dog", "rat", "toad", "frog", "snake",
    "spider", "horse", "pony", "hippogriff", "dragon",
    "troll", "giant", "centaur", "merperson", "ghost",
    "dementor", "boggart", "thestral", "unicorn",
    "mountain", "forest", "black", "norwegian", "ridgeback",
    "norbert", "fang", "trebl", "crookshank", "scabber",
    "hedwig", "errol", "pigwidgeon",
    "tabby", "ginger", "tortoiseshell",
    "creature", "beast", "monster", "animal",
]

group_words = [
    "crowd", "group", "people", "students", "children", "family",
    "gang", "mob", "team", "squad", "committee", "council",
    "ministry", "order", "death", "eater", "eaters",
    "knights", "wizards", "witches", "muggles",
    "teachers", "professors", "staff", "faculty",
    "boys", "girls", "men", "women", "adults", "elders",
    "neighbors", "relatives", "cousins", "siblings",
]

concept_words = [
    "magic", "power", "strength", "courage", "fear", "anger",
    "love", "hope", "despair", "joy", "sadness", "happiness",
    "darkness", "light", "shadow", "silence", "noise",
    "memory", "dream", "nightmare", "vision", "prophecy",
    "curse", "spell", "charm", "hex", "jinx", "ward",
    "time", "space", "world", "universe", "reality",
]

adjective_words = [
    "dark", "light", "bright", "cold", "warm", "hot",
    "tall", "short", "big", "small", "thin", "fat",
    "old", "young", "new", "ancient", "modern",
    "beautiful", "ugly", "handsome", "pretty",
    "brave", "cowardly", "kind", "cruel", "gentle", "fierce",
    "angry", "happy", "sad", "afraid", "scared", "confident",
]

for cid, char in chars.items():
    # char is a dict from JSON, not a Character object
    name = char.get("name", cid)
    name_lower = name.lower()
    desc_lower = (char.get("description") or "").lower()
    text = f"{name_lower} {desc_lower}"

    is_location = any(w in text for w in location_words)
    is_object = any(w in text for w in object_words)
    is_animal = any(w in text for w in animal_words)
    is_group = any(w in text for w in group_words)
    is_concept = any(w in text for w in concept_words)
    is_adjective = any(w in text for w in adjective_words)

    if is_location:
        false_positives["locations"].append((cid, name))
    elif is_object:
        false_positives["objects"].append((cid, name))
    elif is_animal:
        false_positives["animals_creatures"].append((cid, name))
    elif is_group:
        false_positives["groups"].append((cid, name))
    elif is_concept:
        false_positives["concepts"].append((cid, name))
    elif is_adjective:
        false_positives["adjectives"].append((cid, name))
    else:
        false_positives["valid"].append((cid, name))

print(f"\n{'='*60}")
print("  FALSE POSITIVE ANALYSIS")
print(f"{'='*60}")

total_fp = sum(len(v) for k, v in false_positives.items() if k != "valid")
print(f"\n  True characters: {len(false_positives['valid'])}")
print(f"  False positives: {total_fp}")
print(f"  False positive rate: {total_fp/len(chars)*100:.1f}%")

print(f"\n  Locations as characters ({len(false_positives['locations'])}):")
for cid, name in false_positives["locations"][:15]:
    print(f"    - {cid}: {name}")

print(f"\n  Objects as characters ({len(false_positives['objects'])}):")
for cid, name in false_positives["objects"][:10]:
    print(f"    - {cid}: {name}")

print(f"\n  Animals/Creatures as characters ({len(false_positives['animals_creatures'])}):")
for cid, name in false_positives["animals_creatures"][:15]:
    print(f"    - {cid}: {name}")

print(f"\n  Groups as characters ({len(false_positives['groups'])}):")
for cid, name in false_positives["groups"][:15]:
    print(f"    - {cid}: {name}")

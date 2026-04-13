import json
from pathlib import Path

bundle_path = Path('data/compiled/harry_potter_1/bundle.json')
with open(bundle_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', {})
locs = data.get('locations', {})
objs = data.get('objects', {})

print(f"Characters: {len(chars)}")
print(f"Locations: {len(locs)}")
print(f"Objects: {len(objs)}")

# First 20 characters
print("\n--- First 20 characters ---")
for i, (k, v) in enumerate(chars.items()):
    if i >= 20:
        print("  ...")
        break
    print(f"  {k}: {v.get('name', '?')}")

# Search for Dudley
print("\n--- Searching Dudley ---")
for k, v in chars.items():
    name = v.get('name', '').lower()
    if 'dudley' in k.lower() or 'dudley' in name:
        print(f"  DUDLEY: {k}: {v.get('name')}")

# Search for cat
print("\n--- Searching cat ---")
for k, v in chars.items():
    name = v.get('name', '').lower()
    if 'cat' in k.lower() or 'cat' in name:
        print(f"  CAT: {k}: {v.get('name')}")

# Search for He
print("\n--- Searching 'He' ---")
for k, v in chars.items():
    name = v.get('name', '')
    if name == 'He' or k == 'he':
        print(f"  HE: {k}: {v.get('name')} - {v.get('description', '')[:100]}")

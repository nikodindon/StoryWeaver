# Temporal Progression System

## Overview

The **Temporal Progression System** adds time-based structure to StoryWeaver worlds. Instead of having all characters and locations available from the start, the world now unfolds progressively, following the book's natural chronology.

## Problem Solved

**Before:** The world was "flat" — all characters were available everywhere from the start, there was no timeline, no sense of when characters appear or where they should be at different points in the story.

**After:** The game follows the temporal structure of each book/novella. Characters appear/disappear at the right moments, locations change state, events unfold in a logical sequence.

## Architecture

### Core Components

```
storyweaver/world/
├── chapter.py          # Chapter, Timeline, TimelineEvent models
└── bundle.py           # Updated to include chapters & timeline

storyweaver/simulation/
├── phase_tracker.py    # StoryPhase — player's position in timeline
├── character_schedule.py  # ScheduleManager — who is where, when
└── narrative_gates.py  # GateManager — lock/unlock mechanics
```

### Models

#### Chapter
A division of the book with:
- `id`, `title`, `index` — identification
- `locations` — accessible locations in this chapter
- `characters` — available characters in this chapter
- `events` — canon events that occur here
- `prerequisites` — chapters that must be completed first
- `key_events` — high-gravity events the chapter pushes toward

```python
ch1 = Chapter(
    id="ch1",
    title="The Boy Who Lived",
    index=0,
    locations=["privet_drive", "zoo"],
    characters=["harry", "vernon", "petunia"],
    events=["dursleys_intro"],
)
```

#### Timeline & TimelineEvent
Ordered sequence of canonical events with prerequisites:
```python
timeline_event = TimelineEvent(
    event_id="hagrid_arrival",
    chapter_id="ch2",
    order=1,
    description="Hagrid arrives to rescue Harry",
    prerequisites=["letters_arrive"],
    participants=["hagrid", "harry"],
    location_id="hut_on_rock",
)
```

#### StoryPhase
Tracks the player's current position in the timeline:
- `current_chapter_id` — which chapter the player is in
- `completed_chapters` — chapters already experienced
- `completed_events` — canon events that have occurred
- `divergence_score` — how far from canonical path (0-1)

```python
phase = StoryPhase(current_chapter_id="ch1")
phase.complete_chapter("ch1")
phase.record_event("dursleys_intro", is_canon=True)
```

#### ScheduleManager
Manages character presence across chapters:
```python
schedule = CharacterPresence(
    character_id="harry",
    presence_map={
        "ch1": "privet_drive",
        "ch2": "privet_drive",
    },
    introduction_chapter="ch1",
)
mgr = ScheduleManager()
mgr.add_schedule(schedule)
mgr.is_character_available("harry", "ch1")  # True
mgr.get_character_location("harry", "ch1")  # "privet_drive"
```

#### GateManager
Controls lock/unlock mechanics:
```python
gate = NarrativeGate(
    gate_id="gate_hagrid",
    target_type="character",
    target_id="hagrid",
    chapter_required="ch2",
    unlock_message="A giant arrives: Hagrid!",
)
gate_mgr.add_gate(gate)
gate_mgr.is_character_available("hagrid", phase)  # False (ch1)
```

## Usage

### In the Web UI

New commands available:
- `chapter` — Show current chapter and available chapters
- `advance` / `next chapter` — Progress to next available chapter

Locked content is shown with 🔒 in the world info panel.

### Integration with Simulation Engine

The engine now initializes temporal systems automatically:

```python
from storyweaver.simulation import SimulationEngine

engine = SimulationEngine(world, agents, config)
# engine.story_phase is set to first chapter
# engine.schedule_manager manages character presence
# engine.gate_manager controls content locks

# Available characters in current phase:
engine.get_available_characters()

# Available locations in current phase:
engine.get_available_locations()

# Advance to next chapter:
engine.advance_chapter("ch2")
```

## Backward Compatibility

Worlds **without** chapters still work perfectly — the temporal system is simply disabled and all content remains available (legacy behavior).

## Testing

Run the test suite:
```bash
python tests/test_temporal_progression.py
```

## Next Steps

1. **Compiler Integration** — The compiler should generate Chapter data from book segments
2. **Pass 2 Extraction** — Timeline extraction needs to be fixed (currently produces invalid JSON)
3. **Automatic Chapter Advancement** — Detect when player triggers chapter-completing events
4. **Narrative Gravity** — Use chapter key_events to guide player toward canon path
5. **Character Schedules** — Extract from text when characters appear/disappear

## Example: Harry Potter Chapter Structure

```
Ch1: Privet Drive → Introduction (Harry, Vernon, Petunia, Dudley)
Ch2: Letters → Hagrid arrives (unlocks Hagrid, Diagon Alley)
Ch3: Diagon Alley → Shopping (unlocks Ollivander, Gringotts)
Ch4: Platform 9¾ → Hogwarts Express (unlocks Ron, Hermione)
Ch5: Sorting → Houses (unlocks Hogwarts locations, professors)
...
```

Each chapter gates the next — you can't meet Ron before the train, can't go to Hogwarts before sorting, etc.

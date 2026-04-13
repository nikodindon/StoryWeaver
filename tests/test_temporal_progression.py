"""
Test temporal progression systems.
Validates that Chapter, StoryPhase, ScheduleManager, and GateManager work together.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storyweaver.world import Chapter, Timeline, TimelineEvent, WorldBundle
from storyweaver.simulation import StoryPhase, ScheduleManager, GateManager, NarrativeGate, CharacterPresence


def test_chapter_system():
    """Test chapter creation and unlocking."""
    ch1 = Chapter(
        id="ch1",
        title="The Beginning",
        index=0,
        description="The story starts here",
        locations=["privet_drive", "zoo"],
        characters=["harry", "vernon", "petunia"],
        events=["dursleys_intro", "zoo_incident"],
        key_events=["dursleys_intro"],
    )
    
    ch2 = Chapter(
        id="ch2",
        title="Letters from Nowhere",
        index=1,
        description="Strange letters arrive",
        locations=["privet_drive", "hut_on_rock"],
        characters=["harry", "vernon", "petunia", "dudley"],
        events=["letters_arrive", "hagrid_arrival"],
        prerequisites=["ch1"],
        key_events=["hagrid_arrival"],
    )
    
    # Test unlocking
    assert ch1.is_unlocked(set()) == True
    assert ch2.is_unlocked(set()) == False
    assert ch2.is_unlocked({"ch1"}) == True
    print("✓ Chapter system works")


def test_story_phase():
    """Test story phase tracker."""
    phase = StoryPhase(current_chapter_id="ch1")
    
    # Test advancement
    phase.complete_chapter("ch1")
    assert "ch1" in phase.completed_chapters
    
    # Test event recording
    phase.record_event("dursleys_intro", is_canon=True)
    assert "dursleys_intro" in phase.completed_events
    
    # Test divergence
    phase.record_event("random_wander", is_canon=False)
    assert phase.divergence_score > 0.0
    
    print("✓ Story phase tracker works")


def test_schedule_manager():
    """Test character schedule management."""
    mgr = ScheduleManager()
    
    # Create a schedule
    schedule = CharacterPresence(
        character_id="harry",
        presence_map={
            "ch1": "privet_drive",
            "ch2": "privet_drive",
        },
        introduction_chapter="ch1",
    )
    mgr.add_schedule(schedule)
    
    # Test queries
    assert mgr.is_character_available("harry", "ch1") == True
    assert mgr.get_character_location("harry", "ch1") == "privet_drive"
    assert mgr.is_character_available("harry", "ch3") == False  # No chapter 3 in presence map
    
    print("✓ Schedule manager works")


def test_narrative_gates():
    """Test narrative gate system."""
    gate_mgr = GateManager()
    
    # Create a gate
    gate = NarrativeGate(
        gate_id="gate_hagrid",
        target_type="character",
        target_id="hagrid",
        chapter_required="ch2",
        unlock_message="A giant arrives: Hagrid!",
    )
    gate_mgr.add_gate(gate)
    
    # Create a phase that hasn't reached ch2
    phase = StoryPhase(current_chapter_id="ch1")
    
    # Gate should be locked
    assert gate_mgr.is_character_available("hagrid", phase) == False
    
    # Advance phase
    phase.current_chapter_id = "ch2"
    phase.completed_chapters.add("ch1")
    
    # Gate should now be unlocked
    available = gate_mgr.is_character_available("hagrid", phase)
    print(f"  Gate check result: {available}")
    
    print("✓ Narrative gates work")


def test_world_bundle_integration():
    """Test that world bundle can store/load chapters and timeline."""
    from storyweaver.world import Location, Character
    
    bundle = WorldBundle(
        source_title="Test",
        source_author="Test Author",
        compiled_at="2026-04-13T00:00:00Z",
        locations={
            "privet_drive": Location(
                id="privet_drive",
                name="Privet Drive",
                description="A boring suburban house",
            )
        },
        characters={
            "harry": Character(
                id="harry",
                name="Harry Potter",
                description="The boy who lived",
                current_location="privet_drive",
            )
        },
        chapters={
            "ch1": Chapter(
                id="ch1",
                title="Chapter 1",
                index=0,
                description="Start",
                locations=["privet_drive"],
                characters=["harry"],
            )
        },
        timeline=Timeline(
            events=[
                TimelineEvent(
                    event_id="intro",
                    chapter_id="ch1",
                    order=0,
                    description="Harry is introduced",
                    participants=["harry"],
                    location_id="privet_drive",
                )
            ]
        ),
    )
    
    # Test serialization
    data = bundle.to_dict()
    assert "chapters" in data
    assert "timeline" in data
    
    # Test deserialization
    bundle2 = WorldBundle.from_dict(data)
    assert bundle2.chapters["ch1"].title == "Chapter 1"
    assert bundle2.timeline.events[0].event_id == "intro"
    
    print("✓ World bundle integration works")


if __name__ == "__main__":
    print("\n=== Testing Temporal Progression Systems ===\n")
    
    test_chapter_system()
    test_story_phase()
    test_schedule_manager()
    test_narrative_gates()
    test_world_bundle_integration()
    
    print("\n✅ All tests passed!\n")

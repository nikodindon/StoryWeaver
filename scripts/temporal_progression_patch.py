"""
Patch to integrate temporal progression systems into web_ui_v2.py

This file shows the changes needed. Apply these edits to scripts/web_ui_v2.py
"""

# ═══════════════════════════════════════════════════════════
# 1. ADD IMPORTS (after existing imports around line 40)
# ═══════════════════════════════════════════════════════════

from storyweaver.simulation.phase_tracker import StoryPhase
from storyweaver.simulation.character_schedule import ScheduleManager
from storyweaver.simulation.narrative_gates import GateManager


# ═══════════════════════════════════════════════════════════
# 2. ADD TEMPORAL STATE TO GameSession CLASS (around line 70)
# ═══════════════════════════════════════════════════════════

# Add these fields to GameSession.__init__:
"""
        # Temporal progression state
        self.story_phase: Optional[StoryPhase] = None
        self.schedule_manager: Optional[ScheduleManager] = None
        self.gate_manager: Optional[GateManager] = None
        self.current_chapter_title: str = ""
"""

# Also add to GameSession.reset():
"""
        self.story_phase = None
        self.schedule_manager = None
        self.gate_manager = None
        self.current_chapter_title = ""
"""


# ═══════════════════════════════════════════════════════════
# 3. UPDATE load_world FUNCTION (around line 664)
# ═══════════════════════════════════════════════════════════

# After line: session.bundle = WorldBundle.load(world_dir)
# Add temporal system initialization:
"""
    # Initialize temporal progression systems
    if session.bundle.chapters:
        # Find starting chapter (index 0)
        starting_chapter = None
        for cid, chapter in session.bundle.chapters.items():
            if chapter.index == 0:
                starting_chapter = cid
                session.current_chapter_title = chapter.title
                break
        
        if not starting_chapter and session.bundle.chapters:
            starting_chapter = next(iter(session.bundle.chapters.keys()))
            session.current_chapter_title = session.bundle.chapters[starting_chapter].title
        
        session.story_phase = StoryPhase(current_chapter_id=starting_chapter or "prologue")
        session.schedule_manager = ScheduleManager()
        session.schedule_manager.create_from_world_bundle(session.bundle)
        session.gate_manager = GateManager()
    else:
        # No chapters — temporal system disabled, everything available
        session.story_phase = None
        session.schedule_manager = None
        session.gate_manager = None
        session.current_chapter_title = ""
"""


# ═══════════════════════════════════════════════════════════
# 4. UPDATE build_world_info_markdown (around line 237)
# ═══════════════════════════════════════════════════════════

# Add chapter info after the header:
"""
    # Chapter/Phase info
    if session.story_phase and session.current_chapter_title:
        lines.append(f"**📖 Chapter:** {session.current_chapter_title}")
        available_chapters = session.story_phase.get_available_chapters(session.bundle)
        if len(available_chapters) > 1:
            lines.append(f"**🔓 Unlocked Chapters:** {', '.join(available_chapters.values())}")
        lines.append("")
"""

# Update location list to respect temporal gates:
"""
    lines.append("### 🌍 World Locations")
    for lid, loc in bundle.locations.items():
        # Check if location is available
        is_available = True
        if session.story_phase:
            is_available = session.story_phase.is_location_available(session.bundle, lid)
            if not is_available:
                lines.append(f"🔒 **{loc.name}** _(locked)_")
                continue
        
        marker = "📍" if lid == session.player_location else "·"
        visited_marker = "✅" if lid in session.visited_locations else ""
        
        # Check which characters are present AND available
        chars = []
        for c_id in loc.characters_present:
            if c_id not in bundle.characters:
                continue
            # Check if character is available in current phase
            char_available = True
            if session.story_phase:
                char_available = session.story_phase.is_character_available(session.bundle, c_id)
            if char_available:
                chars.append(bundle.characters[c_id].name)
        
        char_str = f" — {', '.join(chars)}" if chars else ""
        lines.append(f"{marker} {visited_marker} **{loc.name}**{char_str}")
"""

# Update character list to respect temporal gates:
"""
    lines.append("### 👥 Characters")
    for cid, char in bundle.characters.items():
        # Check if character is available
        is_available = True
        if session.story_phase:
            is_available = session.story_phase.is_character_available(session.bundle, cid)
            if not is_available:
                lines.append(f"· 🔒 **{char.name}** _(not yet met)_")
                continue
        
        talked_marker = "💬" if cid in session.talked_characters else ""
        loc_name = bundle.locations[char.current_location].name if char.current_location in bundle.locations else "?"
        lines.append(f"· {talked_marker} **{char.name}** — at {loc_name}")
"""


# ═══════════════════════════════════════════════════════════
# 5. UPDATE process_command (around line 359)
# ═══════════════════════════════════════════════════════════

# Add "chapter" command:
"""
    if raw == "chapter":
        if not session.story_phase:
            output = "This world has no chapter system."
        else:
            current = session.bundle.chapters.get(session.story_phase.current_chapter_id)
            current_title = current.title if current else "Unknown"
            available = session.story_phase.get_available_chapters(session.bundle)
            completed = list(session.story_phase.completed_chapters)
            
            output = f"**Current Chapter:** {current_title}\n\n"
            output += f"**Completed:** {', '.join(completed) if completed else 'None'}\n\n"
            output += f"**Available Chapters:**\n"
            for ch_id, ch_title in available.items():
                marker = "→" if ch_id == session.story_phase.current_chapter_id else " "
                output += f"{marker} {ch_title}\n"
        
        session.history.append({"input": user_input, "output": output})
        return output
"""

# Add "advance" command to progress to next chapter:
"""
    if raw.startswith("advance") or raw.startswith("next chapter"):
        if not session.story_phase:
            output = "This world has no chapter system."
        else:
            # Find next available chapter
            available = session.story_phase.get_available_chapters(session.bundle)
            current = session.story_phase.current_chapter_id
            
            # Remove current from available
            available.pop(current, None)
            
            if not available:
                output = "No new chapters available yet. Complete more events!"
            else:
                # Pick first available (lowest index)
                next_chapter_id = list(available.keys())[0]
                next_chapter = session.bundle.chapters.get(next_chapter_id)
                
                if next_chapter:
                    session.story_phase.complete_chapter(current)
                    session.story_phase.advance_to_chapter(next_chapter_id)
                    session.current_chapter_title = next_chapter.title
                    
                    # Check gates
                    newly_unlocked = []
                    if session.gate_manager:
                        newly_unlocked = session.gate_manager.check_all_gates(session.story_phase)
                    
                    output = f"📖 **Chapter Complete:** {current}\n\n"
                    output += f"📖 **New Chapter:** {next_chapter.title}\n\n"
                    output += f"{next_chapter.description}\n\n"
                    
                    if newly_unlocked:
                        output += "**🔓 Unlocked:**\n"
                        for gate_id in newly_unlocked:
                            msg = session.gate_manager.get_unlock_message(gate_id)
                            if msg:
                                output += f"- {msg}\n"
                    
                    session.player_location = next_chapter.locations[0] if next_chapter.locations else session.player_location
                else:
                    output = "Error: Could not find next chapter."
        
        session.history.append({"input": user_input, "output": output})
        return output
"""

# Update "go" command to check temporal gates:
"""
    if raw.startswith("go ") or raw.startswith("go to "):
        # ... existing location resolution code ...
        
        # ADD TEMPORAL CHECK:
        if session.story_phase:
            if not session.story_phase.is_location_available(session.bundle, location_id):
                output = f"🔒 You cannot go there yet. The story hasn't reached that point."
                session.history.append({"input": user_input, "output": output})
                return output
"""

# Update "talk to" command to check temporal gates:
"""
    if raw.startswith("talk to ") or raw.startswith("talk "):
        # ... existing character resolution code ...
        
        # ADD TEMPORAL CHECK:
        if session.story_phase:
            if not session.story_phase.is_character_available(session.bundle, char_id):
                output = f"🔒 {char.name} is not available. They may not have appeared yet in the story."
                session.history.append({"input": user_input, "output": output})
                return output
"""


# ═══════════════════════════════════════════════════════════
# 6. UPDATE HELP COMMAND (add new commands)
# ═══════════════════════════════════════════════════════════

# Add to help text:
"""
"**Story:**\n"
"- `chapter` — Show current chapter and available chapters\n"
"- `advance` / `next chapter` — Progress to next available chapter\n"
"""

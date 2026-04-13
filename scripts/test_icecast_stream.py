"""Test Icecast streaming with a single track."""
import sys
sys.path.insert(0, '.')

from scripts.icecast_streamer import IcecastStreamer
from pathlib import Path
import time

# Test with first Harry Potter MP3
music_dir = Path(r'C:\storyweaver\audio\Harry Potter 01 Harry Potter and the Sorcerer_s Stone')
mp3_files = sorted(music_dir.glob("*.mp3"))

if not mp3_files:
    print("No MP3 files found!")
    sys.exit(1)

print(f"Found {len(mp3_files)} MP3 files")
print(f"First track: {mp3_files[0].name}")

streamer = IcecastStreamer(
    host="localhost",
    port=8000,
    mount="/nova",
    password="hackme",
)

streamer.set_playlist([mp3_files[0]])
print(f"Playlist set with 1 track")

result = streamer.start()
print(f"Stream started: {result}")

print("\nStreaming for 10 seconds... Check http://localhost:8000")
time.sleep(10)

streamer.stop()
print("Stream stopped")

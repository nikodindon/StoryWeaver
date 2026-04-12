"""
StoryWeaver — Icecast Music Streamer

Streams a playlist of MP3 files to an Icecast server via ffmpeg.
Supports start/stop control and playlist management.

Usage:
    python scripts/icecast_streamer.py --mount /nova --host localhost --port 8000 --password hackme --playlist "path/to/mp3s/"
"""
from __future__ import annotations
import subprocess
import threading
import time
import random
from pathlib import Path
from typing import List, Optional
from loguru import logger


class IcecastStreamer:
    """Manages ffmpeg streaming of a music playlist to Icecast."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        mount: str = "/nova",
        password: str = "hackme",
    ):
        self.host = host
        self.port = port
        self.mount = mount
        self.password = password
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._playlist: List[Path] = []
        self._is_playing = False

    def set_playlist(self, mp3_paths: List[str | Path]) -> None:
        """Set the playlist from a list of MP3 file paths."""
        self._playlist = [Path(p) for p in mp3_paths if Path(p).exists()]
        if not self._playlist:
            logger.warning("No valid MP3 files found in playlist")
        else:
            logger.info(f"Playlist set with {len(self._playlist)} tracks")

    def set_playlist_from_directory(self, directory: str | Path, shuffle: bool = True) -> None:
        """Set playlist from all MP3 files in a directory."""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return
        mp3_files = sorted(dir_path.glob("*.mp3"))
        if shuffle:
            random.shuffle(mp3_files)
        self.set_playlist(mp3_files)

    def start(self) -> bool:
        """Start streaming to Icecast. Returns True if successful."""
        if self._is_playing:
            logger.warning("Already streaming")
            return True

        if not self._playlist:
            logger.error("No playlist set")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        self._is_playing = True
        logger.info(f"Streaming started to icecast://{self.host}:{self.port}{self.mount}")
        return True

    def stop(self) -> None:
        """Stop streaming."""
        if not self._is_playing:
            return
        self._stop_event.set()
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._is_playing = False
        logger.info("Streaming stopped")

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def _stream_loop(self) -> None:
        """Main streaming loop: plays tracks sequentially."""
        while not self._stop_event.is_set():
            for track_path in self._playlist:
                if self._stop_event.is_set():
                    break
                if not track_path.exists():
                    logger.warning(f"Track not found: {track_path}")
                    continue
                logger.info(f"Playing: {track_path.name}")
                self._play_file(track_path)

    def _play_file(self, file_path: Path) -> None:
        """Stream a single file to Icecast via ffmpeg."""
        icecast_url = f"icecast://source:{self.password}@{self.host}:{self.port}{self.mount}"

        cmd = [
            "ffmpeg",
            "-re",                          # Read input at native frame rate
            "-i", str(file_path),           # Input file
            "-content_type", "audio/mpeg",  # MIME type
            "-codec", "copy",               # No re-encoding, just copy
            "-ice_public", "0",             # Not a public stream
            "-ice_name", "StoryWeaver",     # Stream name
            "-ice_description", "StoryWeaver Game Music",  # Description
            "-f", "mp3",                    # Output format
            icecast_url,
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Wait for process to finish (track ends) or stop signal
            while self._process.poll() is None and not self._stop_event.is_set():
                time.sleep(0.5)

            if self._stop_event.is_set():
                self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._process.kill()
        except FileNotFoundError:
            logger.error("ffmpeg not found. Is ffmpeg installed?")
            self._stop_event.set()
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        finally:
            self._process = None


# ── Global singleton for use from web UI ──────────────────────────────────
_streamer: Optional[IcecastStreamer] = None


def get_streamer() -> IcecastStreamer:
    """Get or create the global IcecastStreamer instance."""
    global _streamer
    if _streamer is None:
        _streamer = IcecastStreamer()
    return _streamer


def reset_streamer() -> None:
    """Reset the global streamer instance."""
    global _streamer
    if _streamer is not None:
        _streamer.stop()
    _streamer = None


# ── CLI entry point ──────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Stream music to Icecast")
    parser.add_argument("--host", default="localhost", help="Icecast host")
    parser.add_argument("--port", type=int, default=8000, help="Icecast port")
    parser.add_argument("--mount", default="/nova", help="Icecast mount point")
    parser.add_argument("--password", default="hackme", help="Icecast source password")
    parser.add_argument("--playlist", type=str, help="Directory containing MP3 files")
    parser.add_argument("--files", nargs="*", help="Individual MP3 files to stream")
    parser.add_argument("--shuffle", action="store_true", default=True, help="Shuffle playlist")
    parser.add_argument("--no-shuffle", dest="shuffle", action="store_false", help="Don't shuffle")

    args = parser.parse_args()

    streamer = IcecastStreamer(
        host=args.host,
        port=args.port,
        mount=args.mount,
        password=args.password,
    )

    if args.playlist:
        streamer.set_playlist_from_directory(args.playlist, shuffle=args.shuffle)
    elif args.files:
        streamer.set_playlist(args.files)
    else:
        print("Error: Specify --playlist or --files")
        return

    print(f"\n{'=' * 50}")
    print(f"  StoryWeaver Icecast Streamer")
    print(f"{'=' * 50}")
    print(f"  Stream URL: http://{args.host}:{args.port}{args.mount}")
    print(f"  Tracks: {len(streamer._playlist)}")
    print(f"\n  Press Ctrl+C to stop\n")

    try:
        streamer.start()
        while streamer.is_playing:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping stream...")
        streamer.stop()


if __name__ == "__main__":
    main()

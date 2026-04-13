"""
StoryWeaver — Icecast Music Streamer

Uses ffmpeg concat demuxer to stream all tracks as ONE continuous file.
No reconnections between tracks — seamless playback in the browser.

Usage:
    python scripts/icecast_streamer.py --playlist "path/to/mp3s/"
"""
from __future__ import annotations
import subprocess
import tempfile
import threading
import time
import os
import random
from pathlib import Path
from typing import List, Optional
from loguru import logger


class IcecastStreamer:
    """Manages ffmpeg streaming to Icecast using concat demuxer for seamless playback."""

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
        self.icecast_url = f"icecast://source:{self.password}@{self.host}:{self.port}{self.mount}"

        self._process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._playlist: List[Path] = []
        self._is_playing = False
        self._concat_file: Optional[str] = None

    def set_playlist(self, mp3_paths: List[str | Path]) -> None:
        self._playlist = [Path(p) for p in mp3_paths if Path(p).exists()]
        if not self._playlist:
            logger.warning("No valid MP3 files found in playlist")
        else:
            logger.info(f"Playlist set with {len(self._playlist)} tracks")

    def set_playlist_from_directory(self, directory: str | Path, shuffle: bool = True) -> None:
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return
        mp3_files = sorted(dir_path.glob("*.mp3"))
        if shuffle:
            random.shuffle(mp3_files)
        self.set_playlist(mp3_files)

    def _create_concat_file(self) -> str:
        """Create a concat demuxer file. Uses short paths to avoid issues."""
        # Write to a temp file in the same directory as the music (avoids path issues)
        if self._playlist:
            base_dir = self._playlist[0].parent
        else:
            base_dir = Path(tempfile.gettempdir())

        concat_path = base_dir / "_sw_playlist.txt"
        
        with open(concat_path, 'w', encoding='utf-8') as f:
            for track in self._playlist:
                # Use relative paths when possible, absolute otherwise
                try:
                    rel = track.relative_to(base_dir)
                    f.write(f"file '{rel.as_posix()}'\n")
                except ValueError:
                    # Different drive, use absolute with forward slashes
                    f.write(f"file '{track.as_posix()}'\n")
        
        self._concat_file = str(concat_path)
        logger.info(f"Concat file created: {self._concat_file}")
        return self._concat_file

    def start(self) -> bool:
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
        logger.info(f"Streaming started to {self.icecast_url}")
        return True

    def stop(self) -> None:
        if not self._is_playing:
            return
        self._stop_event.set()
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            try:
                self._process.wait(timeout=3)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        self._is_playing = False
        # Cleanup concat file
        if self._concat_file and os.path.exists(self._concat_file):
            try:
                os.unlink(self._concat_file)
            except Exception:
                pass
        logger.info("Streaming stopped")

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def _stream_loop(self) -> None:
        """Stream ALL tracks as ONE continuous file via concat demuxer."""
        concat_file = self._create_concat_file()

        cmd = [
            "ffmpeg", "-re",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-vn", "-map", "0:a",
            "-codec:a", "libmp3lame", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            "-f", "mp3",
            "-content_type", "audio/mpeg",
            "-ice_name", "StoryWeaver",
            "-ice_description", "StoryWeaver Game Music",
            self.icecast_url,
        ]

        logger.info(f"Starting ffmpeg with {len(self._playlist)} tracks (concat mode)...")
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for ALL tracks to finish or stop signal
            while self._process.poll() is None and not self._stop_event.is_set():
                time.sleep(1)

            if self._stop_event.is_set() and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except Exception:
                    self._process.kill()
            elif self._process.returncode != 0:
                logger.warning(f"ffmpeg exited with code {self._process.returncode}")

        except FileNotFoundError:
            logger.error("ffmpeg not found")
            self._stop_event.set()
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        finally:
            self._process = None


# ── Global singleton ──────────────────────────────────────────────────────
_streamer: Optional[IcecastStreamer] = None

def get_streamer() -> IcecastStreamer:
    global _streamer
    if _streamer is None:
        _streamer = IcecastStreamer()
    return _streamer

def reset_streamer() -> None:
    global _streamer
    if _streamer is not None:
        _streamer.stop()
    _streamer = None


# ── CLI ───────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stream music to Icecast")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mount", default="/nova")
    parser.add_argument("--password", default="hackme")
    parser.add_argument("--playlist", type=str)
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--shuffle", action="store_true", default=True)
    parser.add_argument("--no-shuffle", dest="shuffle", action="store_false")
    args = parser.parse_args()

    streamer = IcecastStreamer(host=args.host, port=args.port, mount=args.mount, password=args.password)

    if args.playlist:
        streamer.set_playlist_from_directory(args.playlist, shuffle=args.shuffle)
    elif args.files:
        streamer.set_playlist(args.files)
    else:
        print("Error: Specify --playlist or --files")
        return

    print(f"\n{'=' * 50}")
    print(f"  StoryWeaver Icecast Streamer (Concat Mode)")
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

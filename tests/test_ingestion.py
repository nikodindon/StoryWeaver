"""Tests for the ingestion pipeline."""
import pytest
from pathlib import Path
from storyweaver.ingestion.cleaner import TextCleaner
from storyweaver.ingestion.segmenter import Segmenter


def test_cleaner_normalizes_whitespace():
    cleaner = TextCleaner()
    result = cleaner.clean("Hello\r\n\r\nWorld\n\n\n\nTest")
    assert "\r" not in result
    assert "\n\n\n" not in result


def test_segmenter_splits_by_chapter():
    segmenter = Segmenter()
    text = "Chapter 1\n\nThis is the first chapter.\n\nChapter 2\n\nThis is the second chapter."
    segments = segmenter.segment(text, target_chunk_chars=500)
    assert len(segments) >= 1
    for seg in segments:
        assert "id" in seg
        assert "text" in seg
        assert len(seg["text"]) > 0


def test_segmenter_handles_no_chapters():
    segmenter = Segmenter()
    text = "Just some plain text without any chapter markers. " * 50
    segments = segmenter.segment(text, target_chunk_chars=200)
    assert len(segments) >= 1

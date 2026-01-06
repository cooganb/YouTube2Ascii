"""Download YouTube videos to temporary files."""

import tempfile
from pathlib import Path

import yt_dlp


def download_video(url: str, max_height: int = 480) -> tempfile.NamedTemporaryFile:
    """
    Download a YouTube video to a temporary file.

    Args:
        url: YouTube video URL
        max_height: Maximum video height (lower = faster download)

    Returns:
        NamedTemporaryFile containing the video (auto-deletes on close)
    """
    # Create temp file that persists until explicitly closed
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=True)

    ydl_opts = {
        "format": f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best",
        "outtmpl": temp_file.name,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return temp_file


def get_video_info(url: str) -> dict:
    """Get video metadata without downloading, including YouTube engagement data."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "heatmap": info.get("heatmap"),  # YouTube "Most Replayed" data
            "chapters": info.get("chapters"),  # Video chapters if available
        }

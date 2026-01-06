"""Analyze video to find the most interesting segment."""

from typing import Optional

import cv2
import numpy as np


def find_interesting_segment_from_heatmap(
    heatmap: list,
    segment_duration: float = 3.0,
    video_duration: float = 0,
) -> Optional[float]:
    """
    Find the most interesting segment using YouTube's "Most Replayed" heatmap.

    Args:
        heatmap: List of dicts with start_time, end_time, and value (engagement score)
        segment_duration: Length of segment to extract (seconds)
        video_duration: Total video duration (seconds)

    Returns:
        Start timestamp (seconds) of the most interesting segment, or None if unavailable
    """
    if not heatmap:
        return None

    # Find the segment with highest engagement value
    # that leaves room for our desired duration
    max_start = video_duration - segment_duration if video_duration > segment_duration else 0

    best_start = 0.0
    best_score = 0.0

    # Calculate cumulative score for each possible starting position
    for entry in heatmap:
        start = entry.get("start_time", 0)
        value = entry.get("value", 0)

        if start <= max_start:
            # Sum engagement values within our segment window
            window_score = sum(
                e.get("value", 0)
                for e in heatmap
                if start <= e.get("start_time", 0) < start + segment_duration
            )
            if window_score > best_score:
                best_score = window_score
                best_start = start

    return best_start


def find_interesting_segment(
    video_path: str,
    segment_duration: float = 3.0,
    sample_interval: float = 0.5,
    heatmap: Optional[list] = None,
    video_duration: float = 0,
) -> float:
    """
    Find the most interesting segment in a video.

    Uses YouTube's "Most Replayed" heatmap if available, otherwise falls back
    to motion detection analysis.

    Args:
        video_path: Path to the video file
        segment_duration: Length of segment to extract (seconds)
        sample_interval: How often to sample frames for analysis (seconds)
        heatmap: Optional YouTube heatmap data (Most Replayed)
        video_duration: Total video duration (for heatmap analysis)

    Returns:
        Start timestamp (seconds) of the most interesting segment
    """
    # Try YouTube heatmap first (Most Replayed data)
    if heatmap:
        result = find_interesting_segment_from_heatmap(
            heatmap, segment_duration, video_duration
        )
        if result is not None:
            return result

    # Fall back to motion detection
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    if duration <= segment_duration:
        cap.release()
        return 0.0

    # Sample frames at intervals
    sample_frames = int(sample_interval * fps)
    motion_scores = []
    prev_frame = None

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_frames == 0:
            # Convert to grayscale and resize for faster processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 90))

            if prev_frame is not None:
                # Calculate motion score as sum of absolute differences
                diff = cv2.absdiff(gray, prev_frame)
                score = np.sum(diff)
                timestamp = frame_idx / fps
                motion_scores.append((timestamp, score))

            prev_frame = gray

        frame_idx += 1

    cap.release()

    if not motion_scores:
        return 0.0

    # Find the timestamp with highest motion that allows for full segment
    max_start = duration - segment_duration
    valid_scores = [(t, s) for t, s in motion_scores if t <= max_start]

    if not valid_scores:
        return 0.0

    # Use a sliding window to find the segment with highest total motion
    best_start = 0.0
    best_score = 0

    for i, (timestamp, _) in enumerate(valid_scores):
        # Sum motion scores within the segment window
        window_score = sum(
            s for t, s in valid_scores
            if timestamp <= t < timestamp + segment_duration
        )
        if window_score > best_score:
            best_score = window_score
            best_start = timestamp

    return best_start


def get_video_properties(video_path: str) -> dict:
    """Get basic video properties."""
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    props = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    props["duration"] = props["frame_count"] / props["fps"] if props["fps"] > 0 else 0

    cap.release()
    return props

"""Convert video frames to ASCII art."""

from typing import Generator

import cv2
import numpy as np

# ASCII characters from dark to light
ASCII_CHARS = " .:-=+*#%@"


def extract_frames(
    video_path: str,
    start_time: float,
    duration: float,
    fps: int = 10,
) -> Generator[np.ndarray, None, None]:
    """
    Extract frames from a video segment.

    Args:
        video_path: Path to video file
        start_time: Start timestamp in seconds
        duration: Duration to extract in seconds
        fps: Target frames per second

    Yields:
        Video frames as numpy arrays
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    start_frame = int(start_time * video_fps)
    frame_interval = int(video_fps / fps) if fps < video_fps else 1
    end_frame = int((start_time + duration) * video_fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_idx = start_frame
    while frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if (frame_idx - start_frame) % frame_interval == 0:
            yield frame

        frame_idx += 1

    cap.release()


def frame_to_ascii(
    frame: np.ndarray,
    width: int = 80,
    chars: str = ASCII_CHARS,
) -> str:
    """
    Convert a single frame to ASCII art.

    Args:
        frame: BGR image as numpy array
        width: Width in characters
        chars: ASCII character ramp (dark to light)

    Returns:
        ASCII art string with newlines
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Calculate height to maintain aspect ratio
    # ASCII chars are ~2x taller than wide, so halve the height
    aspect = frame.shape[0] / frame.shape[1]
    height = int(width * aspect * 0.5)

    # Resize
    resized = cv2.resize(gray, (width, height))

    # Map pixel values to ASCII characters
    # Normalize to range [0, len(chars)-1]
    normalized = (resized / 255 * (len(chars) - 1)).astype(int)

    # Build ASCII string
    lines = []
    for row in normalized:
        line = "".join(chars[val] for val in row)
        lines.append(line)

    return "\n".join(lines)


def video_to_ascii_frames(
    video_path: str,
    start_time: float,
    duration: float,
    width: int = 80,
    fps: int = 10,
) -> list:
    """
    Convert a video segment to a list of ASCII frames.

    Args:
        video_path: Path to video file
        start_time: Start timestamp in seconds
        duration: Duration in seconds
        width: ASCII art width in characters
        fps: Frames per second

    Returns:
        List of ASCII art strings
    """
    ascii_frames = []

    for frame in extract_frames(video_path, start_time, duration, fps):
        ascii_art = frame_to_ascii(frame, width)
        ascii_frames.append(ascii_art)

    return ascii_frames

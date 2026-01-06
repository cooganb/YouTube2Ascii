"""Command-line interface for yt2ascii."""

import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click

from .analyzer import find_interesting_segment
from .converter import video_to_ascii_frames
from .downloader import download_video, get_video_info
from .gifmaker import create_gif


def play_ascii_animation(frames: list, fps: int = 10, loops: int = 3) -> None:
    """Play ASCII animation directly in the terminal."""
    frame_delay = 1.0 / fps

    for _ in range(loops):
        for frame in frames:
            # Clear screen and move cursor to top
            click.echo("\033[2J\033[H", nl=False)
            click.echo(frame)
            time.sleep(frame_delay)

    # Final clear and show last frame
    click.echo("\033[2J\033[H", nl=False)
    click.echo(frames[-1] if frames else "")


def open_file(filepath: str) -> None:
    """Open a file with the system's default application."""
    system = platform.system()
    if system == "Darwin":  # macOS
        subprocess.run(["open", filepath])
    elif system == "Windows":
        os.startfile(filepath)
    else:  # Linux and others
        subprocess.run(["xdg-open", filepath])


@click.command()
@click.argument("url")
@click.option(
    "-o", "--output",
    default="output.gif",
    help="Output GIF file path",
)
@click.option(
    "-w", "--width",
    default=80,
    help="ASCII art width in characters",
)
@click.option(
    "-d", "--duration",
    default=3.0,
    help="Duration of the GIF in seconds",
)
@click.option(
    "-f", "--fps",
    default=10,
    help="Frames per second",
)
@click.option(
    "--start",
    default=None,
    type=float,
    help="Start timestamp (seconds). If not set, auto-detects interesting moment",
)
@click.option(
    "--font-size",
    default=10,
    help="Font size for rendering",
)
@click.option(
    "--bg-color",
    default="#1a1a1a",
    help="Background color (hex)",
)
@click.option(
    "--fg-color",
    default="#00ff00",
    help="Text color (hex)",
)
@click.option(
    "--open", "open_after",
    is_flag=True,
    help="Open the GIF in default viewer after creation",
)
@click.option(
    "--play",
    is_flag=True,
    help="Play ASCII animation in terminal after creation",
)
def main(
    url: str,
    output: str,
    width: int,
    duration: float,
    fps: int,
    start: Optional[float],
    font_size: int,
    bg_color: str,
    fg_color: str,
    open_after: bool,
    play: bool,
) -> None:
    """Generate an ASCII art GIF from a YouTube video.

    URL: YouTube video URL
    """
    try:
        # Get video info
        click.echo(f"Fetching video info...")
        info = get_video_info(url)
        click.echo(f"Video: {info['title']}")

        # Download video
        click.echo("Downloading video (low quality for speed)...")
        temp_file = download_video(url)

        try:
            video_path = temp_file.name

            # Find interesting segment if not specified
            if start is None:
                heatmap = info.get("heatmap")
                if heatmap:
                    click.echo("Using YouTube 'Most Replayed' data to find best moment...")
                else:
                    click.echo("Analyzing video for interesting moments...")
                start = find_interesting_segment(
                    video_path,
                    duration,
                    heatmap=heatmap,
                    video_duration=info.get("duration", 0),
                )
                click.echo(f"Selected segment starting at {start:.1f}s")
            else:
                click.echo(f"Using specified start time: {start:.1f}s")

            # Convert to ASCII
            click.echo("Converting to ASCII art...")
            ascii_frames = video_to_ascii_frames(
                video_path,
                start_time=start,
                duration=duration,
                width=width,
                fps=fps,
            )
            click.echo(f"Generated {len(ascii_frames)} frames")

            # Create GIF
            click.echo("Creating GIF...")
            output_path = create_gif(
                ascii_frames,
                output,
                fps=fps,
                font_size=font_size,
                bg_color=bg_color,
                fg_color=fg_color,
            )

            file_size = output_path.stat().st_size / 1024
            click.echo(f"Saved to {output_path} ({file_size:.1f} KB)")

            # Play in terminal if requested
            if play:
                click.echo("Playing animation in terminal (3 loops)...")
                time.sleep(0.5)
                play_ascii_animation(ascii_frames, fps=fps, loops=3)
                click.echo(f"\nGIF saved to: {output_path}")

            # Open in default viewer if requested
            if open_after:
                click.echo("Opening GIF...")
                open_file(str(output_path))

        finally:
            # Temp file auto-closes and deletes
            temp_file.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Generate animated GIFs from ASCII art frames."""

from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw, ImageFont


def get_monospace_font(size: int = 12):
    """Get a monospace font, falling back to default if needed."""
    # Try common monospace fonts
    font_names = [
        "DejaVuSansMono.ttf",
        "Menlo.ttc",
        "Monaco.ttf",
        "Consolas.ttf",
        "CourierNew.ttf",
        "LiberationMono-Regular.ttf",
    ]

    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue

    # Fall back to default
    return ImageFont.load_default()


def ascii_to_image(
    ascii_art: str,
    font_size: int = 10,
    bg_color: str = "#1a1a1a",
    fg_color: str = "#00ff00",
) -> Image.Image:
    """
    Render ASCII art to an image.

    Args:
        ascii_art: ASCII art string with newlines
        font_size: Font size in pixels
        bg_color: Background color (hex)
        fg_color: Foreground/text color (hex)

    Returns:
        PIL Image
    """
    font = get_monospace_font(font_size)
    lines = ascii_art.split("\n")

    # Calculate image dimensions
    # Use a test character to get dimensions
    test_bbox = font.getbbox("M")
    char_width = test_bbox[2] - test_bbox[0]
    char_height = test_bbox[3] - test_bbox[1]

    # Add some padding
    line_height = int(char_height * 1.2)
    max_line_len = max(len(line) for line in lines) if lines else 0

    img_width = int(char_width * max_line_len) + 20
    img_height = int(line_height * len(lines)) + 20

    # Create image
    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw text
    y = 10
    for line in lines:
        draw.text((10, y), line, font=font, fill=fg_color)
        y += line_height

    return img


def create_gif(
    ascii_frames: list,
    output_path: Union[str, Path],
    fps: int = 10,
    font_size: int = 10,
    bg_color: str = "#1a1a1a",
    fg_color: str = "#00ff00",
    optimize: bool = True,
) -> Path:
    """
    Create an animated GIF from ASCII frames.

    Args:
        ascii_frames: List of ASCII art strings
        output_path: Output file path
        fps: Frames per second
        font_size: Font size for rendering
        bg_color: Background color
        fg_color: Text color
        optimize: Whether to optimize GIF size

    Returns:
        Path to created GIF
    """
    if not ascii_frames:
        raise ValueError("No frames to create GIF from")

    output_path = Path(output_path)

    # Render all frames
    images = [
        ascii_to_image(frame, font_size, bg_color, fg_color)
        for frame in ascii_frames
    ]

    # Calculate frame duration in milliseconds
    duration = int(1000 / fps)

    # Save as animated GIF
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=optimize,
    )

    return output_path

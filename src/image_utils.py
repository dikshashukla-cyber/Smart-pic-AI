"""Image processing, validation, and normalization utilities for SmartPick AI.

Ensures all smartphone product photos adhere to:
1. Strict file type validation (PNG, JPEG, WebP, SVG).
2. Safety limits (max file size 10MB).
3. Consistent dimensions: 600 x 800 portrait aspect ratio with neutral containment.
4. Fast WebP compression for low latency loading in Streamlit.
"""

import io
import logging
from pathlib import Path

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
TARGET_WIDTH: int = 600
TARGET_HEIGHT: int = 800
NEUTRAL_BG_COLOR = (15, 23, 42)  # Dark slate #0F172A


def is_safe_image_file(filepath: Path | str) -> bool:
    """Validate file path existence, extension, and file size."""
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        return False
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False
    try:
        size = p.stat().st_size
        if size <= 0 or size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False
    return True


def normalize_and_save_image(
    image_bytes: bytes,
    output_path: Path | str,
    target_size: tuple[int, int] = (TARGET_WIDTH, TARGET_HEIGHT),
) -> Path:
    """Resize and pad image bytes into a standardized portrait WebP image.

    Args:
        image_bytes: Raw downloaded image data.
        output_path: Filepath where normalized image should be saved.
        target_size: (width, height) tuple, defaults to 600x800.

    Returns:
        Path to the saved normalized WebP image.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(io.BytesIO(image_bytes)) as img:
        # Convert paletted or RGBA to RGB with neutral background
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            background = Image.new("RGB", img.size, NEUTRAL_BG_COLOR)
            background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
            img_rgb = background
        else:
            img_rgb = img.convert("RGB")

        # Pad to target dimensions (600x800) preserving aspect ratio without distortion
        fitted = ImageOps.pad(
            img_rgb,
            target_size,
            color=NEUTRAL_BG_COLOR,
            method=Image.Resampling.LANCZOS,
        )

        # Save as optimized WebP
        fitted.save(out_p, format="WEBP", quality=85, method=6)
        logger.info(f"Normalized image saved: {out_p} ({out_p.stat().st_size:,} bytes)")

    return out_p

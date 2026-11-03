"""Frame corpus and pixel helpers for the Python codec study.

Frames are uint8 RGB arrays with shape (height, width, 3). ``rgb565`` packs
channels by truncating their low bits; ``expand565`` restores 8-bit channels
by bit replication. ``load_video`` samples decoded native frames at/after the
requested start time, without changing frame rate, and letterboxes them to the
requested output size using Pillow's BOX resampler.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction
from pathlib import Path
from typing import Any

import av
import numpy as np
from PIL import Image


def _check_rgb(rgb: np.ndarray) -> np.ndarray:
    arr = np.asarray(rgb)
    if arr.dtype != np.uint8 or arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("rgb must be a uint8 array with shape (height, width, 3)")
    return arr


def rgb565(rgb: np.ndarray) -> np.ndarray:
    """Pack an HxWx3 uint8 RGB image as HxW uint16 R5G6B5 words."""
    arr = _check_rgb(rgb).astype(np.uint16)
    return ((arr[..., 0] >> 3) << 11) | ((arr[..., 1] >> 2) << 5) | (arr[..., 2] >> 3)


def expand565(words: np.ndarray) -> np.ndarray:
    """Expand HxW uint16 R5G6B5 words to HxWx3 uint8 using bit replication."""
    packed = np.asarray(words)
    if packed.dtype != np.uint16 or packed.ndim != 2:
        raise ValueError("words must be a uint16 array with shape (height, width)")
    red = (packed >> 11) & 0x1F
    green = (packed >> 5) & 0x3F
    blue = packed & 0x1F
    return np.stack(((red << 3) | (red >> 2),
                     (green << 2) | (green >> 4),
                     (blue << 3) | (blue >> 2)), axis=-1).astype(np.uint8)


def metrics(source_rgb: np.ndarray, reconstructed_rgb: np.ndarray,
            active_rect: tuple[int, int, int, int] | None = None) -> dict[str, Any]:
    """Return full-frame MSE/PSNR and exact flag, plus active-crop metrics.

    ``active_rect`` is ``(x, y, width, height)`` in pixels. PSNR is ``None``
    for an exact comparison (zero MSE), and ``exact`` reports that case.
    """
    source = _check_rgb(source_rgb)
    recon = _check_rgb(reconstructed_rgb)
    if source.shape != recon.shape:
        raise ValueError("source and reconstructed images must have equal shapes")

    def calculate(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
        delta = a.astype(np.float64) - b.astype(np.float64)
        mse = float(np.mean(delta * delta))
        return {"mse": mse, "psnr": None if mse == 0.0 else float(10.0 * np.log10(255.0 ** 2 / mse)),
                "exact": mse == 0.0}

    result = calculate(source, recon)
    if active_rect is not None:
        x, y, width, height = active_rect
        h, w = source.shape[:2]
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > w or y + height > h:
            raise ValueError("active_rect must fit inside the image")
        result["active"] = calculate(source[y:y + height, x:x + width],
                                     recon[y:y + height, x:x + width])
    return result


def _letterbox(rgb: np.ndarray, width: int, height: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Aspect-fit an RGB image to canvas; return image and active (x,y,w,h)."""
    src_h, src_w = rgb.shape[:2]
    scale = min(width / src_w, height / src_h)
    fitted_w = max(1, min(width, round(src_w * scale)))
    fitted_h = max(1, min(height, round(src_h * scale)))
    resized = Image.fromarray(rgb).resize((fitted_w, fitted_h), Image.Resampling.BOX)
    x, y = (width - fitted_w) // 2, (height - fitted_h) // 2
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[y:y + fitted_h, x:x + fitted_w] = np.asarray(resized)
    return canvas, (x, y, fitted_w, fitted_h)


def load_video(path: str | Path, max_frames: int = 30, start_seconds: float = 1.0,
               width: int = 720, height: int = 480) -> tuple[list[np.ndarray], dict[str, Any]]:
    """Decode up to ``max_frames`` native frames starting at ``start_seconds``.

    Selected frames retain their original decoded order and PTS; no frame-rate
    conversion or interpolation occurs. Images are aspect-fit to the target
    canvas with Pillow BOX resampling and black letterbox bars. Manifest fields
    include source metadata, selected timestamps, per-frame hashes and active
    rectangles. Requires PyAV.
    """
    if max_frames < 0 or start_seconds < 0 or width <= 0 or height <= 0:
        raise ValueError("max_frames/start_seconds must be nonnegative and dimensions positive")
    source_path = Path(path)
    digest = hashlib.sha256()
    with source_path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)

    frames: list[np.ndarray] = []
    selected_pts: list[int | None] = []
    selected_times: list[float | None] = []
    hashes: list[str] = []
    active_rects: list[tuple[int, int, int, int]] = []
    with av.open(str(source_path)) as container:
        stream = next((s for s in container.streams if s.type == "video"), None)
        if stream is None:
            raise ValueError(f"No video stream in {source_path}")
        time_base = stream.time_base
        fps = stream.average_rate
        duration_start = Fraction(str(start_seconds))
        count = 0
        for frame in (() if max_frames == 0 else container.decode(stream)):
            timestamp = (Fraction(frame.pts) * frame.time_base
                         if frame.pts is not None and frame.time_base is not None else None)
            if timestamp is not None and timestamp < duration_start:
                continue
            rgb = frame.to_ndarray(format="rgb24")
            fitted, rect = _letterbox(rgb, width, height)
            frames.append(fitted)
            selected_pts.append(frame.pts)
            selected_times.append(float(timestamp) if timestamp is not None else None)
            hashes.append(hashlib.sha256(fitted.tobytes()).hexdigest())
            active_rects.append(rect)
            count += 1
            if count >= max_frames:
                break
        manifest = {
            "source": str(source_path),
            "source_sha256": digest.hexdigest(),
            "source_width": stream.codec_context.width,
            "source_height": stream.codec_context.height,
            "source_fps": str(fps) if fps is not None else None,
            "time_base": str(time_base) if time_base is not None else None,
            "start_seconds": start_seconds,
            "target_width": width,
            "target_height": height,
            "resampler": "Pillow BOX",
            "frame_count": len(frames),
            "selected_pts": selected_pts,
            "selected_times_seconds": selected_times,
            "frame_sha256": hashes,
            "unique_frame_count": len(set(hashes)),
            "active_rects": active_rects,
        }
    return frames, manifest


def synthetic_frames(width: int = 720, height: int = 480, count: int = 8) -> list[tuple[str, np.ndarray]]:
    """Generate deterministic labeled RGB fixtures (including a cut).

    Fixture names identify flat/static, HUD-like, gradient, scrolling, noise,
    and cut behavior. Random noise uses a fixed seed; these are synthetic
    fixtures and do not represent captured video.
    """
    if width <= 0 or height <= 0 or count < 0:
        raise ValueError("dimensions must be positive and count nonnegative")
    yy, xx = np.mgrid[0:height, 0:width]
    frames: list[tuple[str, np.ndarray]] = []
    rng = np.random.default_rng(0xB0B)
    noise = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
    for i in range(count):
        mode = i % 6
        if mode == 0:
            image = np.full((height, width, 3), (24, 32, 48), dtype=np.uint8)
            name = "flat-static"
        elif mode == 1:
            image = np.zeros((height, width, 3), dtype=np.uint8)
            image[max(0, height - 40):, :, :] = (8, 12, 24)
            image[max(0, height - 34):max(0, height - 30), width // 10:width // 2, :] = (80, 220, 160)
            name = "hud-like"
        elif mode == 2:
            image = np.stack((xx * 255 // max(1, width - 1), yy * 255 // max(1, height - 1),
                              (xx + yy) * 255 // max(1, width + height - 2)), axis=-1).astype(np.uint8)
            name = "gradient"
        elif mode == 3:
            image = np.stack(((xx + i * 11) % 256, (yy + i * 5) % 256,
                              ((xx // 4 + yy // 4 + i * 7) % 2) * 255), axis=-1).astype(np.uint8)
            name = "scrolling"
        elif mode == 4:
            image = noise.copy()
            name = "random-noise-seed-0xB0B"
        else:
            image = np.full((height, width, 3), (180, 32, 24), dtype=np.uint8)
            name = "scene-cut"
        frames.append((name, image))
    return frames

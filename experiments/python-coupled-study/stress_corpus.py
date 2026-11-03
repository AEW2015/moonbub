"""Deterministic synthetic RGB frames for stress testing (not camera capture).

Frame schedule metadata represents a synthetic 30 Hz sequence. It must not be
described as native capture timing or hardware capture evidence.
"""

from __future__ import annotations

import hashlib

import numpy as np


def make_stress_frames(width: int = 720, height: int = 480, count: int = 60):
    """Return ``(frames, manifest)`` for a repeatable visual stress sequence.

    Each frame is an HxWx3 uint8 array. The manifest contains per-frame labels,
    synthetic schedule times, full-canvas active rectangles, SHA-256 hashes,
    and the number of unique frame contents.
    """
    for name, value in (("width", width), ("height", height), ("count", count)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if width <= 0 or height <= 0 or count < 0:
        raise ValueError("width and height must be positive; count cannot be negative")

    frames: list[np.ndarray] = []
    rows = np.arange(height, dtype=np.uint16)[:, None]
    cols = np.arange(width, dtype=np.uint16)[None, :]
    midpoint = count // 2
    burst_start = max(0, midpoint - 2)
    burst_end = min(count, burst_start + 5)
    rng = np.random.default_rng(20261103)

    for index in range(count):
        if burst_start <= index < burst_end:
            frame = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
            label = "noise_burst"
        elif index < count / 4:
            frame = np.empty((height, width, 3), dtype=np.uint8)
            frame[:] = (24, 32, 40)
            label = "flat_pattern"
        elif index < count / 2:
            # Smooth, slowly moving RGB ramps with no per-pixel noise.
            phase = index - int(count / 4)
            red = (cols + phase * 7) % 256
            green = (rows + phase * 5) % 256
            blue = (cols // 2 + rows // 2 + phase * 3) % 256
            frame = np.empty((height, width, 3), dtype=np.uint8)
            frame[..., 0] = red
            frame[..., 1] = green
            frame[..., 2] = blue
            label = "moving_gradient"
        else:
            # A static, simple keyframe lets downstream codecs recover after
            # the high-entropy burst.
            frame = np.empty((height, width, 3), dtype=np.uint8)
            frame[:] = (24, 32, 40)
            label = "recovery_flat"
        frames.append(frame)

    hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
    manifest = {
        "source": "synthetic",
        "timing": "synthetic_30_hz_schedule",
        "nominal_fps": 30,
        "width": width,
        "height": height,
        "count": count,
        "unique_frame_count": len(set(hashes)),
        "frames": [
            {
                "id": index,
                "selected_time_s": index / 30.0,
                "active_rect": [0, 0, width, height],
                "sha256": hashes[index],
                "label": label,
            }
            for index, label in enumerate(_labels(count, burst_start, burst_end))
        ],
    }
    return frames, manifest


def _labels(count: int, burst_start: int, burst_end: int) -> list[str]:
    labels = []
    for index in range(count):
        if burst_start <= index < burst_end:
            labels.append("noise_burst")
        elif index < count / 4:
            labels.append("flat_pattern")
        elif index < count / 2:
            labels.append("moving_gradient")
        else:
            labels.append("recovery_flat")
    return labels

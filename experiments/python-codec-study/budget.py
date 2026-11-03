"""Independent JPEG size-budget experiment for the Python codec study.

This is a research-time search over a bounded quality list, not an encoder
policy or hardware claim. At most five candidate encodes are attempted. A
candidate is accepted only when both its complete packet size and the modeled
wire size fit the supplied limits; packets are never truncated.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import sys
from typing import Callable

from PIL import Image

import pacing


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SUNSHINE = Path(os.environ.get('GAMEBUB_SUNSHINE_TOOLS', str(ROOT / "repos" / "sunshine-30fps-study" / "tools" / "gamebub")))
if str(SUNSHINE) not in sys.path:
    sys.path.insert(0, str(SUNSHINE))
from msv1 import encode_receiver_jpeg  # noqa: E402


def _positive_finite(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")


def _validate_qualities(qualities: tuple[int, ...]) -> tuple[int, ...]:
    try:
        values = tuple(qualities)
    except TypeError as exc:
        raise ValueError("qualities must be a nonempty sequence") from exc
    if not values or len(values) > 5:
        raise ValueError("qualities must contain 1..5 values")
    if any(type(q) is not int or not 1 <= q <= 95 for q in values):
        raise ValueError("qualities must be integers in 1..95")
    if any(a <= b for a, b in zip(values, values[1:])):
        raise ValueError("qualities must be strictly descending")
    return values


def choose_jpeg(image: Image.Image, *, fps: float = 30, mbps: float = 8,
                cap: int = 49152, qualities: tuple[int, ...] = (80, 65, 50, 35, 20),
                encoder: Callable[[Image.Image, int], bytes] | None = None
                ) -> tuple[bytes | None, dict]:
    """Choose the first descending quality that fits both byte budgets.

    Returns ``(packet, report)``. If every candidate exceeds a limit, returns
    ``(None, report)`` to indicate a whole-frame drop. ``encoder`` is injectable
    for tests and must accept ``(image, quality)`` and return packet bytes.
    ``wire_budget_bytes`` is floor(mbps * 1e6 / 8 / fps); modeled wire size
    uses ``pacing.wire_bytes`` including the 40-byte app and 28-byte IPv4/UDP
    assumptions per 1024-byte chunk. The default encoder is Sunshine's
    validated receiver-profile JPEG encoder.
    """
    _positive_finite(fps, "fps")
    _positive_finite(mbps, "mbps")
    if type(cap) is not int or cap <= 0:
        raise ValueError("cap must be a positive integer")
    candidates = _validate_qualities(qualities)
    if not isinstance(image, Image.Image) or image.mode != "RGB":
        raise ValueError("image must be an RGB PIL image")
    budget = math.floor(mbps * 1_000_000 / 8 / fps)
    encode = encoder or encode_receiver_jpeg
    attempts = []
    for quality in candidates:
        try:
            packet = encode(image, quality)
        except ValueError as error:
            # The pinned receiver encoder rejects >256KiB before returning
            # bytes. That specific size rejection is another failed candidate;
            # malformed profiles and unrelated encoder failures must propagate.
            if encoder is None and str(error) == 'JPEG exceeds receiver frame bounds':
                attempts.append({'quality': quality, 'bytes': None, 'wire_bytes': None,
                                 'fits': False, 'reason': 'receiver_frame_size_bound'})
                continue
            raise
        if not isinstance(packet, (bytes, bytearray, memoryview)) or len(packet) <= 0:
            raise ValueError("encoder must return nonempty bytes")
        packet = bytes(packet)
        modeled_wire = pacing.wire_bytes(len(packet))
        fits = len(packet) <= cap and modeled_wire <= budget
        attempts.append({"quality": quality, "bytes": len(packet),
                         "wire_bytes": modeled_wire, "fits": fits})
        if fits:
            return packet, {"attempts": attempts, "selected_quality": quality,
                            "wire_budget_bytes": budget, "packet_cap_bytes": cap,
                            "bounded_attempts": len(attempts), "dropped": False,
                            "research_budget": True}
    return None, {"attempts": attempts, "selected_quality": None,
                  "wire_budget_bytes": budget, "packet_cap_bytes": cap,
                  "bounded_attempts": len(attempts), "dropped": True,
                  "research_budget": True}

"""Pure-Python validation and presentation metrics for coupled stream runs.

The measurement interval is half-open: presentation timestamps in [0,
window_end_ms) count as in-window; timestamps at or beyond the endpoint are
drain presentations. Percentiles use linear interpolation at rank
``(n - 1) * p`` (the common inclusive-endpoint convention).
"""

from __future__ import annotations

import math
from typing import Iterable


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite nonnegative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return result


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    lower = math.floor(rank)
    upper = math.ceil(rank)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize_presentation(
    captures: list[dict],
    presented: list[dict],
    window_end_ms: float,
    steady_window_ms: tuple | None,
) -> dict:
    """Validate frame records and report counts, age, gaps, and steady FPS.

    Presentation records must have unique IDs, strictly increasing IDs and
    timestamps. Capture order is unrestricted, but IDs must be unique and each
    presented frame must have a capture whose timestamp is no later.
    """
    end = _number(window_end_ms, "window_end_ms")
    capture_by_id: dict[int, float] = {}
    for row in captures:
        if not isinstance(row, dict) or "id" not in row or "capture_ms" not in row:
            raise ValueError("each capture needs id and capture_ms")
        frame_id = row["id"]
        if isinstance(frame_id, bool) or not isinstance(frame_id, int):
            raise ValueError("capture IDs must be integers")
        if frame_id in capture_by_id:
            raise ValueError(f"duplicate capture ID: {frame_id}")
        capture_by_id[frame_id] = _number(row["capture_ms"], "capture_ms")

    seen: set[int] = set()
    presentation_rows: list[tuple[int, float, float]] = []
    previous_id: int | None = None
    previous_at: float | None = None
    for row in presented:
        if not isinstance(row, dict) or "id" not in row or "at_ms" not in row:
            raise ValueError("each presentation needs id and at_ms")
        frame_id = row["id"]
        if isinstance(frame_id, bool) or not isinstance(frame_id, int):
            raise ValueError("presentation IDs must be integers")
        if frame_id in seen:
            raise ValueError(f"duplicate presentation ID: {frame_id}")
        if previous_id is not None and frame_id <= previous_id:
            raise ValueError("presentation IDs must be strictly increasing")
        at = _number(row["at_ms"], "at_ms")
        if previous_at is not None and at <= previous_at:
            raise ValueError("presentation timestamps must be strictly increasing")
        if frame_id not in capture_by_id:
            raise ValueError(f"presentation has no capture: {frame_id}")
        captured_at = capture_by_id[frame_id]
        if at < captured_at:
            raise ValueError(f"presentation precedes capture: {frame_id}")
        seen.add(frame_id)
        presentation_rows.append((frame_id, at, at - captured_at))
        previous_id, previous_at = frame_id, at

    in_window = [row for row in presentation_rows if row[1] < end]
    ages = [row[2] for row in in_window]
    times = [row[1] for row in in_window]
    gaps = [later - earlier for earlier, later in zip(times, times[1:])]

    steady_fps: float | None = None
    steady_covered = False
    if steady_window_ms is not None:
        if (not isinstance(steady_window_ms, (tuple, list)) or
                len(steady_window_ms) != 2):
            raise ValueError("steady_window_ms must be a (start_ms, end_ms) pair")
        start = _number(steady_window_ms[0], "steady window start")
        steady_end = _number(steady_window_ms[1], "steady window end")
        if steady_end <= start:
            raise ValueError("steady window must have positive duration")
        steady_covered = start >= 0 and steady_end <= end
        if steady_covered:
            count = sum(start <= row[1] < steady_end for row in presentation_rows)
            steady_fps = count * 1000.0 / (steady_end - start)

    return {
        "capture_count": len(capture_by_id),
        "presented_count": len(in_window),
        "drain_count": len(presentation_rows) - len(in_window),
        "age_p50_ms": _percentile(ages, 0.50),
        "age_p95_ms": _percentile(ages, 0.95),
        "age_max_ms": max(ages) if ages else None,
        "max_gap_ms": max(gaps) if gaps else None,
        "steady_fps": steady_fps,
        "steady_window_covered": steady_covered,
    }


def validate_conservation(
    capturedids: Iterable[int],
    presentedids: Iterable[int],
    dropids: Iterable[int],
    pendingids: Iterable[int],
) -> bool:
    """Require disjoint captured/presented/dropped/pending sets whose union
    is exactly the captured ID set. Raises ValueError on a conservation error.
    """
    captured = set(capturedids)
    groups = [set(presentedids), set(dropids), set(pendingids)]
    for i, group in enumerate(groups):
        if not group <= captured:
            raise ValueError("conservation group contains an unknown frame ID")
        if any(group & other for other in groups[:i]):
            raise ValueError("conservation groups must be disjoint")
    if set.union(*groups) != captured:
        raise ValueError("conservation groups must account for every captured ID")
    return True

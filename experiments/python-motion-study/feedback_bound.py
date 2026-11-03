"""Pure ideal-capacity stop-and-wait schedule for precomputed frame sizes.

This schedule cannot replay a motion codec: replacing a captured frame changes
the reference chain and therefore later frame sizes. Sizes here are fixed
inputs used only to bound link and receiver service under the stated model.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OLD = REPO / "experiments" / "python-codec-study"
if str(OLD) not in sys.path:
    sys.path.insert(0, str(OLD))
import pacing  # noqa: E402


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(.95 * len(ordered)) - 1]


def simulate(sizes, fps=30, link_mbps=8, qspi_mbps=160, decode_ms=8,
             feedback_ms=0, encode_ms=2) -> dict:
    """Simulate one in-flight frame and one replaceable latest waiting frame.

    Captures arrive at ``i*1000/fps``. Each ACK transaction serially includes
    sender encode, modeled IP/UDP wire time, receiver QSPI write, decode, and
    feedback. The reported age is capture time to decode completion. The
    strict decode-completion window is ``[0, N/fps)``. No vblank/presentation
    stage is modeled. The fixed-size input trace
    is a capacity schedule, not a motion-codec replay after frame drops.
    """
    sizes = list(sizes)
    if any(type(size) is not int or size <= 0 for size in sizes):
        raise ValueError("sizes must contain positive integers")
    params = (fps, link_mbps, qspi_mbps, decode_ms, feedback_ms, encode_ms)
    if not all(math.isfinite(value) for value in params) or fps <= 0 or link_mbps <= 0 \
            or qspi_mbps <= 0 or min(decode_ms, feedback_ms, encode_ms) < 0:
        raise ValueError("invalid schedule parameters")

    count = len(sizes)
    period = 1000.0 / fps
    next_capture = 0
    pending: int | None = None
    sender_free = 0.0
    sent_ids: list[int] = []
    dropped_ids: list[int] = []
    decode_times: list[float] = []
    ages: list[float] = []
    tx_services: list[float] = []

    while next_capture < count or pending is not None:
        if pending is None:
            # Sender waits for the next capture if no captured frame is queued.
            frame_id = next_capture
            capture_time = frame_id * period
            start = max(sender_free, capture_time)
            next_capture += 1
        else:
            frame_id = pending
            capture_time = frame_id * period
            start = sender_free
            pending = None

        wire_ms = pacing.wire_bytes(sizes[frame_id], payload=1024,
                                    application_header=40) * 8 / (link_mbps * 1000)
        qspi_ms = sizes[frame_id] * 8 / (qspi_mbps * 1000)
        decode_time = start + encode_ms + wire_ms + qspi_ms + decode_ms
        ack_time = decode_time + feedback_ms
        service_ms = ack_time - start
        sent_ids.append(frame_id)
        decode_times.append(decode_time)
        ages.append(decode_time - capture_time)
        tx_services.append(service_ms)
        sender_free = ack_time

        # All captures while this transaction was in flight enter one waiting
        # slot; each newer arrival replaces (and drops) the prior waiting ID.
        while next_capture < count and next_capture * period <= ack_time + 1e-12:
            if pending is not None:
                dropped_ids.append(pending)
            pending = next_capture
            next_capture += 1

    window_end = count * period
    strict_count = sum(t < window_end - 1e-12 for t in decode_times)
    steady_fps = None
    if window_end >= 55000.0:
        steady_fps = sum(5000.0 <= t < 55000.0 for t in decode_times) / 50.0
    mean_service = statistics.fmean(tx_services) if tx_services else None
    theoretical_fps = None if mean_service is None or mean_service == 0 else 1000.0 / mean_service
    return {
        "model": "pure stop-and-wait capacity schedule with one latest waiting frame",
        "input_count": count, "sent_count": len(sent_ids), "sent_ids": sent_ids,
        "dropped_ids": dropped_ids, "decoded_strict_window": strict_count,
        "decoded_eventual": len(decode_times), "strict_window_ms": window_end,
        "steady_5_to_55_seconds_fps": steady_fps,
        "steady_window_covered_by_capture": window_end >= 55000.0,
        "age_capture_to_decode_ms": {"p95": _p95(ages), "max": max(ages, default=None)},
        "mean_transaction_service_ms": mean_service,
        "theoretical_mean_service_fps": theoretical_fps,
        "parameters": {"fps": fps, "link_mbps": link_mbps, "qspi_mbps": qspi_mbps,
                       "decode_ms": decode_ms, "feedback_ms": feedback_ms,
                       "encode_ms": encode_ms, "wire_payload_bytes": 1024,
                       "application_header_bytes": 40, "ip_udp_header_bytes": 28},
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path | None = None) -> Path:
    """Schedule the old codec study's two cached 60-frame JPEG budget traces."""
    result_path = OLD / "results.json"
    cached = json.loads(result_path.read_text())
    traces = []
    for corpus_name in ("mass-effect-combat", "mass-effect-2600"):
        row = next(row for row in cached["rows"]
                   if row["corpus"] == corpus_name and row["profile"] == "jpeg-budget8")
        base = [frame["bytes"] for frame in row["per_frame"]]
        sizes = (base * math.ceil(1800 / len(base)))[:1800]
        for feedback in (0, 5, 10, 20, 40):
            traces.append({"name": corpus_name, "profile": "jpeg-budget8-cyclic-1800",
                           "feedback_ms": feedback, "source_frame_bytes": base,
                           "source_sizes_sha256": hashlib.sha256(
                               json.dumps(base, separators=(",", ":")).encode()).hexdigest(),
                           "schedule": simulate(sizes, feedback_ms=feedback)})
    path = path or HERE / "feedback-results.json"
    report = {
        "evidence": "offline capacity schedule from fixed cached frame lengths; no motion-codec replay or hardware measurement",
        "input_source": str(result_path), "input_source_sha256": _sha256(result_path),
        "pacing_helper_sha256": _sha256(OLD / "pacing.py"),
        "source_sha256": {p.name: _sha256(p) for p in
                           (HERE / 'feedback_bound.py', HERE / 'test_feedback_bound.py')},
        "traces": traces,
    }
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path


if __name__ == "__main__":
    print(f"wrote {write_report()}")

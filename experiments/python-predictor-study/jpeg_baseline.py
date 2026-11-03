"""Receiver-profile JPEG baseline for the 30 fps predictor study.

This is an offline software measurement. It reads the shared Mass Effect source
clips and records exact frame manifests; it does not capture or store raw video.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OLD_HELPERS = REPO / "experiments" / "python-codec-study"
MEDIA = REPO.parents[1] / "media"
SUNSHINE = Path(os.environ.get(
    "GAMEBUB_SUNSHINE_TOOLS",
    str(REPO / ".." / "sunshine-30fps-study" / "tools" / "gamebub"),
)).resolve()
for _path in (str(OLD_HELPERS), str(SUNSHINE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import corpus  # noqa: E402
import pacing  # noqa: E402
from msv1 import encode_receiver_jpeg  # noqa: E402

WIDTH, HEIGHT = 720, 480
QUALITIES = (35, 50, 65, 80, 90)
FRAME_CAP = 48 * 1024
SCENE_SPECS = (
    ("mass-effect-combat-60-start1", "mass-effect-combat.mp4", 60, 1.0, "primary"),
    ("mass-effect-2600-60-start1", "mass-effect-2600.mp4", 60, 1.0, "primary"),
    ("mass-effect-combat-30-start4-heldout", "mass-effect-combat.mp4", 30, 4.0, "heldout"),
    ("mass-effect-2600-30-start4-heldout", "mass-effect-2600.mp4", 30, 4.0, "heldout"),
)


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)]


def _decode_rgb565(packet: bytes):
    with Image.open(__import__("io").BytesIO(packet)) as decoded:
        decoded.load()
        rgb = decoded.convert("RGB")
    return corpus.expand565(corpus.rgb565(np.asarray(rgb)))


def _measure_scene(name: str, filename: str, requested: int, start: float, role: str) -> dict[str, Any] | None:
    source = MEDIA / filename
    if not source.is_file():
        return None
    frames, manifest = corpus.load_video(source, max_frames=requested,
                                         start_seconds=start, width=WIDTH, height=HEIGHT)
    out: dict[str, Any] = {
        "name": name, "role": role, "requested_frame_count": requested,
        "actual_frame_count": len(frames), "source": manifest,
        "unique_input_hash_count": len(set(manifest["frame_sha256"])),
        "duplicate_input_frame_count": len(frames) - len(set(manifest["frame_sha256"])),
        "qualities": {},
    }
    for quality in QUALITIES:
        sizes: list[int] = []
        wires: list[int] = []
        times_ms: list[float] = []
        records = []
        active_mse, active_psnr = [], []
        for idx, canvas in enumerate(frames):
            image = Image.fromarray(canvas, mode="RGB")
            began = time.perf_counter_ns()
            packet = bytes(encode_receiver_jpeg(image, quality))
            elapsed = (time.perf_counter_ns() - began) / 1_000_000
            reconstructed = _decode_rgb565(packet)
            rect = manifest["active_rects"][idx]
            metrics = corpus.metrics(canvas, reconstructed, rect)["active"]
            wire = pacing.wire_bytes(len(packet), payload=1024, application_header=40)
            sizes.append(len(packet)); wires.append(wire); times_ms.append(elapsed)
            active_mse.append(metrics["mse"])
            if metrics["psnr"] is not None:
                active_psnr.append(metrics["psnr"])
            records.append({
                "index": idx, "pts": manifest["selected_pts"][idx],
                "time_seconds": manifest["selected_times_seconds"][idx],
                "input_sha256": manifest["frame_sha256"][idx],
                "output_rgb565_sha256": hashlib.sha256(reconstructed.tobytes()).hexdigest(),
                "jpeg_bytes": len(packet), "wire_bytes": wire,
                "over_48k_jpeg_cap": len(packet) > FRAME_CAP,
                "active_mse": metrics["mse"], "active_psnr_db": metrics["psnr"],
                "encode_python_wall_ms": elapsed,
            })
        out["qualities"][str(quality)] = {
            "frame_count": len(records), "frames": records,
            "unique_output_rgb565_hash_count": len({r["output_rgb565_sha256"] for r in records}),
            "jpeg_bytes": {"mean": statistics.fmean(sizes) if sizes else None,
                           "p95": _p95(sizes), "max": max(sizes, default=None),
                           "over_48k_count": sum(n > FRAME_CAP for n in sizes)},
            "modeled_wire_bytes": {"mean": statistics.fmean(wires) if wires else None,
                                   "p95": _p95(wires), "max": max(wires, default=None)},
            "active_mse_mean": statistics.fmean(active_mse) if active_mse else None,
            "active_psnr_db_mean": statistics.fmean(active_psnr) if active_psnr else None,
            "encode_python_wall_ms": {"mean": statistics.fmean(times_ms) if times_ms else None,
                                      "p95": _p95(times_ms), "max": max(times_ms, default=None),
                                      "label": "Python wall time; not device encode time"},
        }
    return out


def run_scenes() -> dict[str, Any]:
    """Run all available requested scenes and return a JSON-serializable report."""
    scenes = [_measure_scene(*spec) for spec in SCENE_SPECS]
    scenes = [scene for scene in scenes if scene is not None]
    return {
        "study": "receiver-profile JPEG baseline", "canvas": [WIDTH, HEIGHT],
        "qualities": list(QUALITIES), "jpeg_cap_bytes": FRAME_CAP,
        "wire_model": {"payload_bytes": 1024, "application_header_bytes": 40,
                       "ipv4_udp_header_bytes": 28, "excludes": "Ethernet and Wi-Fi"},
        "encoder": {"name": "Sunshine msv1.encode_receiver_jpeg", "path": str(SUNSHINE / "msv1.py")},
        "scenes": scenes,
    }


def main() -> None:
    report = run_scenes()
    result_path = HERE / "jpeg-results.json"
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {result_path} ({len(report['scenes'])} scenes)")


if __name__ == "__main__":
    main()

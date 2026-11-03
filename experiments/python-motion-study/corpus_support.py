"""Shared real-video and receiver-profile JPEG baseline for motion studies.

The returned frames are native decoded RGB samples letterboxed to 720x480.
JPEG measurements are offline software measurements; they do not imply a
hardware frame rate.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import statistics
import sys
from typing import Any

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OLD_HELPERS = REPO / "experiments" / "python-codec-study"
MEDIA = Path(os.environ.get("GAMEBUB_MEDIA_DIR", str(REPO.parents[1] / "media"))).resolve()
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
QUALITIES = (35, 50, 65, 80)
SCENES = (
    ("mass-effect-combat-start1", "mass-effect-combat.mp4", 1.0, "primary"),
    ("mass-effect-2600-start1", "mass-effect-2600.mp4", 1.0, "primary"),
    ("mass-effect-combat-start4-heldout", "mass-effect-combat.mp4", 4.0, "heldout"),
    ("mass-effect-2600-start4-heldout", "mass-effect-2600.mp4", 4.0, "heldout"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pooled_active_mse(frames: list[np.ndarray], reconstructions: list[np.ndarray],
                       rects: list[tuple[int, int, int, int]]) -> tuple[float | None, float | None]:
    squared_error = 0.0
    samples = 0
    for source, recon, (x, y, w, h) in zip(frames, reconstructions, rects):
        delta = source[y:y+h, x:x+w].astype(np.float64) - recon[y:y+h, x:x+w].astype(np.float64)
        squared_error += float(np.sum(delta * delta))
        samples += delta.size
    if not samples:
        return None, None
    mse = squared_error / samples
    psnr = None if mse == 0 else float(10.0 * np.log10(255.0 ** 2 / mse))
    return mse, psnr


def _measure_jpeg(frames: list[np.ndarray], manifest: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    rects = [tuple(rect) for rect in manifest["active_rects"]]
    for quality in QUALITIES:
        records = []
        reconstructions = []
        wire_sizes = []
        for index, frame in enumerate(frames):
            packet = bytes(encode_receiver_jpeg(Image.fromarray(frame), quality))
            with Image.open(io.BytesIO(packet)) as decoded:
                decoded.load()
                rgb = np.asarray(decoded.convert("RGB"), dtype=np.uint8)
            reconstructed = corpus.expand565(corpus.rgb565(rgb))
            reconstructions.append(reconstructed)
            wire = pacing.wire_bytes(len(packet), payload=1024, application_header=40)
            wire_sizes.append(wire)
            records.append({
                "index": index,
                "input_sha256": manifest["frame_sha256"][index],
                "output_rgb565_sha256": hashlib.sha256(reconstructed.tobytes()).hexdigest(),
                "jpeg_bytes": len(packet), "wire_bytes": wire,
            })
        pooled_mse, pooled_psnr = _pooled_active_mse(frames, reconstructions, rects)
        results[str(quality)] = {
            "frame_count": len(records), "frames": records,
            "jpeg_bytes_total": sum(r["jpeg_bytes"] for r in records),
            "wire_bytes_total": sum(wire_sizes),
            "wire_bytes_mean": statistics.fmean(wire_sizes) if wire_sizes else None,
            "pooled_active_mse": pooled_mse,
            "pooled_active_psnr_db": pooled_psnr,
        }
    return results


def load_scenes(frames_per_scene: int = 30) -> list[dict[str, Any]]:
    """Load four fixed native-frame windows and their per-quality JPEG baseline."""
    if type(frames_per_scene) is not int or frames_per_scene < 0:
        raise ValueError("frames_per_scene must be a nonnegative integer")
    scenes = []
    for name, filename, start, role in SCENES:
        source = MEDIA / filename
        frames, manifest = corpus.load_video(source, max_frames=frames_per_scene,
                                             start_seconds=start, width=WIDTH, height=HEIGHT)
        if len(frames) > frames_per_scene:
            raise AssertionError("corpus helper returned more frames than requested")
        scenes.append({
            "name": name, "role": role, "frames": frames,
            "manifest": manifest,
            "jpeg": _measure_jpeg(frames, manifest),
        })
    return scenes


def _versions() -> dict[str, str | None]:
    out = {}
    for package in ("Pillow", "numpy", "av"):
        try:
            out[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            out[package] = None
    return out


def write_reference(path: Path | None = None, frames_per_scene: int = 30) -> Path:
    """Run the reference measurements and cache JSON beside this module."""
    path = path or HERE / "jpeg-reference.json"
    scenes = load_scenes(frames_per_scene)
    report = {
        "study": "motion-study JPEG reference", "canvas": [WIDTH, HEIGHT],
        "qualities": list(QUALITIES), "versions": _versions(),
        "helper_sha256": _sha256(OLD_HELPERS / "corpus.py"),
        "pacing_helper_sha256": _sha256(OLD_HELPERS / "pacing.py"),
        "sunshine_encoder_sha256": _sha256(SUNSHINE / "msv1.py"),
        "scenes": [{k: v for k, v in scene.items() if k != "frames"} for scene in scenes],
    }
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path


if __name__ == "__main__":
    print(f"wrote {write_reference()}")

#!/usr/bin/env python3
"""Offline verify source canvases and derived hashes; imports no encoder."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zlib
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MEDIA = HERE.parents[3] / "media"
V24_RESULTS = ROOT / "experiments/python-game-standard-v24-study/results.json"
WINDOWS = {
    "mass-effect-10000": (Fraction(6), Fraction(10)),
    "mass-effect-4500": (Fraction(6), Fraction(10)),
    "mass-effect-1600": (Fraction(6), Fraction(10)),
    "mass-effect-combat": (Fraction(20), Fraction(24)),
}
EXPECTED_MEDIA_SHA256 = {
    "mass-effect-10000": "5922669cd29b32407b1eb3d75e78a0bc2c851f388ba825e7e277dca6b00daa2d",
    "mass-effect-4500": "56221ded0e71335960195574f579ee7f82ed6c25e22736461824345d0687b23e",
    "mass-effect-1600": "41318d8042b44b56d441c19f698abf528f6549ea67b32744ab317b8d9fd505b4",
    "mass-effect-combat": "defff415bc1fdff6e18a70b0a0fbbddebb0429c5c0b8b5d5d04d8283bb315d3b",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


corpus = load_module("source_v40_verify_corpus", ROOT / "experiments/python-codec-study/corpus.py")
ft = load_module("source_v40_verify_transform", ROOT / "experiments/python-transform-study/fixed_codec.py")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_pins() -> dict[str, str]:
    paths = [
        HERE / "prepare.py",
        HERE / "verify.py",
        ROOT / "experiments/python-codec-study/corpus.py",
        ROOT / "experiments/python-transform-study/fixed_codec.py",
        V24_RESULTS,
    ]
    return {p.relative_to(ROOT).as_posix(): file_sha256(p) for p in sorted(paths)}


def read_canvas(desc: dict) -> bytes:
    rel = Path(desc["path"])
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] != "objects":
        raise ValueError("unsafe canvas object path")
    path = HERE / rel
    compressed = path.read_bytes()
    if len(compressed) != desc["stored_bytes"] or digest(compressed) != desc["stored_sha256"]:
        raise ValueError("stored object size/hash mismatch")
    decomp = zlib.decompressobj()
    raw = decomp.decompress(compressed, desc["raw_bytes"] + 1)
    if not decomp.eof or decomp.unused_data or decomp.unconsumed_tail:
        raise ValueError("object is not exactly one bounded zlib stream")
    if len(raw) != desc["raw_bytes"] or digest(raw) != desc["raw_sha256"]:
        raise ValueError("canvas object raw size/hash mismatch")
    if len(raw) != 720 * 480 * 3:
        raise ValueError("unexpected RGB24 canvas size")
    return raw


def calibration_prefixes() -> dict[str, dict]:
    old = json.loads(V24_RESULTS.read_text())
    prefixes = {}
    for case in old["inputs"]:
        if case["scene"] in ("mass-effect-2600", "mass-effect-7200"):
            prefixes[case["scene"]] = {
                "source_media_sha256": case["manifest"]["source_sha256"],
                "first_12": [
                    {
                        "id": row["id"],
                        "pts": case["manifest"]["selected_pts"][i],
                        "timestamp_seconds": case["manifest"]["selected_times_seconds"][i],
                        "canvas_rgb_sha256": row["input_rgb_sha256"],
                    }
                    for i, row in enumerate(case["rows"][:12])
                ],
            }
    if set(prefixes) != {"mass-effect-2600", "mass-effect-7200"}:
        raise ValueError("calibration prefix records missing")
    return prefixes


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    if manifest.get("schema") != "gamebub-source-qualification-v40":
        raise ValueError("unexpected manifest schema")
    if manifest["source_code_sha256"] != source_pins():
        raise ValueError("source pin mismatch")
    if manifest["external_media_sha256"] != EXPECTED_MEDIA_SHA256:
        raise ValueError("external media pin table mismatch")
    calibration = calibration_prefixes()
    object_hashes = set()
    total_rows = 0
    reports = []
    for case in manifest["cases"]:
        name = case["name"]
        if name not in WINDOWS or case["media_file"] != f"media/{name}.mp4":
            raise ValueError("unexpected qualification media")
        t0, t1 = WINDOWS[name]
        if case["requested_interval_seconds_half_open"] != {"start": str(t0), "end": str(t1)}:
            raise ValueError(f"window mismatch for {name}")
        if case["media_sha256_before"] != EXPECTED_MEDIA_SHA256[name] or case["media_sha256_after"] != EXPECTED_MEDIA_SHA256[name]:
            raise ValueError(f"media digest mismatch for {name}")
        if not case["sha_before_after_match"]:
            raise ValueError(f"media changed while preparing {name}")
        media_path = MEDIA / f"{name}.mp4"
        if file_sha256(media_path) != case["media_sha256_after"]:
            raise ValueError(f"current external media differs from manifest: {name}")
        if not 0 < case["selected_frame_count"] <= 144:
            raise ValueError(f"invalid selected-frame count for {name}")
        if case["decoded_frame_count_actual"] != case["decoded_frame_count_reported"] - case["reported_minus_decoded_frame_count"]:
            raise ValueError(f"decoded frame-count arithmetic mismatch for {name}")

        rows = case["frames"]
        if len(rows) != case["selected_frame_count"]:
            raise ValueError(f"selected row count mismatch for {name}")
        previous_timestamp = None
        unique_canvas = set()
        unique_native = set()
        overlaps = {k: [] for k in calibration}
        for index, row in enumerate(rows):
            if row["id"] != index:
                raise ValueError(f"unordered selected IDs for {name}")
            timestamp = Fraction(*row["time_base"]) * row["pts"]
            if str(timestamp) != row["timestamp_fraction"]:
                raise ValueError(f"fractional timestamp mismatch for {name}/{index}")
            if float(timestamp) != row["timestamp_seconds"]:
                raise ValueError(f"timestamp float mismatch for {name}/{index}")
            if not t0 <= timestamp < t1:
                raise ValueError(f"frame outside PTS interval for {name}/{index}")
            if row["decoded_order"] < 0 or row["decoded_order"] >= case["decoded_frame_count_actual"]:
                raise ValueError(f"invalid decoded-order index for {name}/{index}")
            if previous_timestamp is not None and timestamp <= previous_timestamp:
                raise ValueError(f"selected timestamps not strictly increasing for {name}")
            expected_gap = None if previous_timestamp is None else str(timestamp - previous_timestamp)
            if row["gap_from_previous_selected_seconds"] != expected_gap:
                raise ValueError(f"selected PTS gap mismatch for {name}/{index}")
            previous_timestamp = timestamp

            raw = read_canvas(row["canvas_rgb24"])
            canvas = np.frombuffer(raw, np.uint8).reshape(480, 720, 3)
            canvas_hash = digest(raw)
            if canvas_hash != row["canvas_rgb_sha256"]:
                raise ValueError(f"canvas hash mismatch for {name}/{index}")
            words = corpus.rgb565(canvas).astype("<u2", copy=False)
            rgb565_bytes = np.ascontiguousarray(words).tobytes()
            if digest(rgb565_bytes) != row["rgb565_sha256"]:
                raise ValueError(f"derived RGB565 hash mismatch for {name}/{index}")
            planes = ft.rgb_to_planes(canvas)
            yuv = b"".join(np.ascontiguousarray(p.astype(np.uint8)).tobytes() for p in planes)
            if digest(yuv) != row["common_yuv420_u8_sha256"]:
                raise ValueError(f"derived common YUV hash mismatch for {name}/{index}")
            rect = tuple(row["active_rect_xywh"])
            if rect != tuple(case["active_rect_xywh"]):
                raise ValueError(f"active rectangle changed for {name}/{index}")
            object_hashes.add(row["canvas_rgb24"]["stored_sha256"])
            unique_canvas.add(canvas_hash)
            unique_native.add(row["native_rgb_sha256"])
            for calibration_name, prefix in calibration.items():
                if canvas_hash in {x["canvas_rgb_sha256"] for x in prefix["first_12"]}:
                    overlaps[calibration_name].append({"qualification_id": index, "canvas_rgb_sha256": canvas_hash})

        if len(unique_canvas) != case["selected_unique_canvas_frames"]:
            raise ValueError(f"unique canvas count mismatch for {name}")
        if len(unique_native) != case["selected_unique_native_rgb_frames"]:
            raise ValueError(f"unique native count mismatch for {name}")
        for calibration_name in calibration:
            recorded = case["calibration_hash_overlap"][calibration_name]
            if recorded["frame_hash_overlap_count"] != len(overlaps[calibration_name]) or recorded["matches"] != overlaps[calibration_name]:
                raise ValueError(f"AB38 overlap mismatch for {name}/{calibration_name}")
        if [r["decoded_order"] for r in rows] != sorted(r["decoded_order"] for r in rows):
            raise ValueError(f"decoded frame order mismatch for {name}")
        total_rows += len(rows)
        reports.append({
            "clip": name,
            "selected_frames": len(rows),
            "unique_canvas_frames": len(unique_canvas),
            "first_timestamp": rows[0]["timestamp_fraction"],
            "last_timestamp": rows[-1]["timestamp_fraction"],
            "ab38_calibration_overlaps": {k: len(v) for k, v in overlaps.items()},
        })

    if len(manifest["cases"]) != len(WINDOWS) or {c["name"] for c in manifest["cases"]} != set(WINDOWS):
        raise ValueError("qualification clip cohort mismatch")
    if manifest["counts"]["clips"] != len(WINDOWS) or manifest["counts"]["selected_frames"] != total_rows:
        raise ValueError("manifest aggregate counts mismatch")
    if manifest["counts"]["content_addressed_objects"] != len(object_hashes):
        raise ValueError("manifest object count mismatch")
    actual_stored_raw = sum(r["canvas_rgb24"]["raw_bytes"] for c in manifest["cases"] for r in c["frames"])
    if manifest["counts"]["stored_rgb24_raw_bytes"] != actual_stored_raw:
        raise ValueError("manifest raw storage count mismatch")
    print(json.dumps({"verified_clips": len(reports), "verified_frames": total_rows,
                      "verified_objects": len(object_hashes), "reports": reports,
                      "imports_encoder": False, "performs_native_comparison": False}, indent=2), flush=True)


if __name__ == "__main__":
    main()

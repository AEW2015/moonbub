#!/usr/bin/env python3
"""Prepare immutable PTS-selected common RGB canvases; no codec is run."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import PIL

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MEDIA = HERE.parents[3] / "media"
V24_RESULTS = ROOT / "experiments/python-game-standard-v24-study/results.json"
MAX_FRAMES_PER_CLIP = 144
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


corpus = load_module("source_v40_frozen_corpus", ROOT / "experiments/python-codec-study/corpus.py")
ft = load_module("source_v40_frozen_transform", ROOT / "experiments/python-transform-study/fixed_codec.py")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def store_canvas(canvas: np.ndarray) -> dict:
    raw = np.ascontiguousarray(canvas, dtype=np.uint8).tobytes()
    compressed = zlib.compress(raw, 6)
    stored_sha = digest(compressed)
    relpath = f"objects/{stored_sha}.zlib"
    target = HERE / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if file_sha256(target) != stored_sha or zlib.decompress(target.read_bytes()) != raw:
            raise ValueError(f"content-addressed object mismatch: {target}")
    else:
        target.write_bytes(compressed)
    return {
        "path": relpath,
        "raw_bytes": len(raw),
        "raw_sha256": digest(raw),
        "stored_bytes": len(compressed),
        "stored_sha256": stored_sha,
    }


def selected_pts_from_calibration() -> dict[str, dict]:
    old = json.loads(V24_RESULTS.read_text())
    selected = {}
    for case in old["inputs"]:
        if case["scene"] not in ("mass-effect-2600", "mass-effect-7200"):
            continue
        rows = case["rows"][:12]
        selected[case["scene"]] = {
            "source_media_sha256": case["manifest"]["source_sha256"],
            "first_12": [
                {
                    "id": row["id"],
                    "pts": case["manifest"]["selected_pts"][i],
                    "timestamp_seconds": case["manifest"]["selected_times_seconds"][i],
                    "canvas_rgb_sha256": row["input_rgb_sha256"],
                }
                for i, row in enumerate(rows)
            ],
        }
    if set(selected) != {"mass-effect-2600", "mass-effect-7200"}:
        raise ValueError("frozen v24 calibration prefixes are incomplete")
    return selected


def pin_sources() -> dict[str, str]:
    paths = [
        HERE / "prepare.py",
        HERE / "verify.py",
        ROOT / "experiments/python-codec-study/corpus.py",
        ROOT / "experiments/python-transform-study/fixed_codec.py",
        V24_RESULTS,
    ]
    return {p.relative_to(ROOT).as_posix(): file_sha256(p) for p in sorted(paths)}


def main() -> None:
    started = time.perf_counter()
    before_pins = pin_sources()
    calibration = selected_pts_from_calibration()
    cases = []
    for name, (t0, t1) in WINDOWS.items():
        media_path = MEDIA / f"{name}.mp4"
        if not media_path.is_file():
            raise FileNotFoundError(media_path)
        media_sha_before = file_sha256(media_path)
        if media_sha_before != EXPECTED_MEDIA_SHA256[name]:
            raise ValueError(f"media digest differs from reviewed input: {name}")

        rows = []
        all_decoded = 0
        last_timestamp = None
        all_pts_gaps = []
        selected_canvas_hashes = set()
        source_unique_native_hashes = set()
        with av.open(str(media_path)) as container:
            stream = next((s for s in container.streams if s.type == "video"), None)
            if stream is None:
                raise ValueError(f"no video stream: {media_path}")
            stream_info = {
                "codec": stream.codec_context.name,
                "width": stream.codec_context.width,
                "height": stream.codec_context.height,
                "average_rate": str(stream.average_rate) if stream.average_rate is not None else None,
                "stream_time_base": str(stream.time_base) if stream.time_base is not None else None,
                "reported_stream_frame_count": stream.frames,
            }
            active_rect = None
            for decoded_order, frame in enumerate(container.decode(stream)):
                all_decoded += 1
                if frame.pts is None or frame.time_base is None:
                    raise ValueError(f"missing PTS/time_base in {name} decoded frame {decoded_order}")
                timestamp = Fraction(frame.pts) * frame.time_base
                if last_timestamp is not None:
                    if timestamp <= last_timestamp:
                        raise ValueError(f"nonincreasing timestamp in {name} at decoded frame {decoded_order}")
                    all_pts_gaps.append(timestamp - last_timestamp)
                last_timestamp = timestamp
                if timestamp < t0 or timestamp >= t1:
                    continue
                if len(rows) >= MAX_FRAMES_PER_CLIP:
                    raise ValueError(f"{name} interval exceeds {MAX_FRAMES_PER_CLIP} frame cap")

                native_rgb = frame.to_ndarray(format="rgb24")
                native_hash = digest(np.ascontiguousarray(native_rgb).tobytes())
                source_unique_native_hashes.add(native_hash)
                canvas, rect = corpus._letterbox(native_rgb, 720, 480)
                if canvas.shape != (480, 720, 3) or canvas.dtype != np.uint8:
                    raise ValueError("frozen letterbox returned unexpected canvas")
                rect = tuple(int(x) for x in rect)
                if active_rect is None:
                    active_rect = rect
                elif rect != active_rect:
                    raise ValueError(f"active rectangle changed within {name}")

                canvas_bytes = np.ascontiguousarray(canvas).tobytes()
                canvas_hash = digest(canvas_bytes)
                words = corpus.rgb565(canvas).astype("<u2", copy=False)
                rgb565_bytes = np.ascontiguousarray(words).tobytes()
                planes = ft.rgb_to_planes(canvas)
                yuv_bytes = b"".join(np.ascontiguousarray(p.astype(np.uint8)).tobytes() for p in planes)
                if len(yuv_bytes) != 720 * 480 + 2 * 360 * 240:
                    raise AssertionError("unexpected YUV420 byte geometry")

                previous_selected = rows[-1]["timestamp_fraction"] if rows else None
                selected_gap = None
                if previous_selected is not None:
                    selected_gap = str(timestamp - Fraction(previous_selected))
                rows.append({
                    "id": len(rows),
                    "decoded_order": decoded_order,
                    "native_rgb_sha256": native_hash,
                    "canvas_rgb_sha256": canvas_hash,
                    "rgb565_sha256": digest(rgb565_bytes),
                    "common_yuv420_u8_sha256": digest(yuv_bytes),
                    "pts": int(frame.pts),
                    "time_base": [int(frame.time_base.numerator), int(frame.time_base.denominator)],
                    "timestamp_fraction": str(timestamp),
                    "timestamp_seconds": float(timestamp),
                    "gap_from_previous_selected_seconds": selected_gap,
                    "active_rect_xywh": list(rect),
                    "canvas_rgb24": store_canvas(canvas),
                })
                selected_canvas_hashes.add(canvas_hash)

        if not rows:
            raise ValueError(f"empty selected PTS interval for {name}")
        media_sha_after = file_sha256(media_path)
        if media_sha_after != media_sha_before:
            raise ValueError(f"media changed during preparation: {name}")

        overlap = {}
        for calibration_name, info in calibration.items():
            hashes = {r["canvas_rgb_sha256"] for r in info["first_12"]}
            matches = [r for r in rows if r["canvas_rgb_sha256"] in hashes]
            overlap[calibration_name] = {
                "frame_hash_overlap_count": len(matches),
                "matches": [
                    {"qualification_id": r["id"], "canvas_rgb_sha256": r["canvas_rgb_sha256"]}
                    for r in matches
                ],
            }
        gaps = [float(x) for x in all_pts_gaps]
        cases.append({
            "name": name,
            "media_file": f"media/{name}.mp4",
            "media_sha256_before": media_sha_before,
            "media_sha256_after": media_sha_after,
            "sha_before_after_match": media_sha_before == media_sha_after,
            "requested_interval_seconds_half_open": {"start": str(t0), "end": str(t1)},
            "stream": stream_info,
            "decoded_frame_count_actual": all_decoded,
            "decoded_frame_count_reported": stream_info["reported_stream_frame_count"],
            "reported_minus_decoded_frame_count": stream_info["reported_stream_frame_count"] - all_decoded,
            "selected_frame_count": len(rows),
            "selected_unique_native_rgb_frames": len(source_unique_native_hashes),
            "selected_unique_canvas_frames": len(selected_canvas_hashes),
            "selected_pts_first": rows[0]["pts"],
            "selected_pts_last": rows[-1]["pts"],
            "selected_timestamp_first": rows[0]["timestamp_fraction"],
            "selected_timestamp_last": rows[-1]["timestamp_fraction"],
            "all_decoded_pts_gap_seconds": {
                "count": len(gaps),
                "minimum": min(gaps),
                "median": float(np.median(gaps)),
                "maximum": max(gaps),
            },
            "active_rect_xywh": list(active_rect),
            "calibration_hash_overlap": overlap,
            "frames": rows,
        })
        print(json.dumps({"clip": name, "decoded": all_decoded, "selected": len(rows),
                          "unique_canvas": len(selected_canvas_hashes),
                          "pts_first": rows[0]["timestamp_fraction"],
                          "pts_last": rows[-1]["timestamp_fraction"],
                          "sha256": media_sha_after}), flush=True)

    if before_pins != pin_sources():
        raise ValueError("source code or calibration file changed during preparation")
    manifest = {
        "schema": "gamebub-source-qualification-v40",
        "source_code_sha256": before_pins,
        "external_media_sha256": EXPECTED_MEDIA_SHA256,
        "media_provenance": {
            "known_lineage": "Noire Blue Mass Effect (2007) walkthrough, previously compressed H.264 extracts",
            "shared_source_manifest": "/home/lori/gamebub-streaming-prototype/results/mass-effect-benchmark/source-manifest.json",
            "documented_extracts": {
                "mass-effect-4500": {"approx_source_seconds": 4500, "extraction": "12-second stream-copy window"},
                "mass-effect-10000": {"approx_source_seconds": 10000, "extraction": "12-second stream-copy window"},
            },
            "undocumented_in_shared_manifest": ["mass-effect-1600", "mass-effect-combat"],
            "known_prior_use": {
                "mass-effect-10000": "FPGA near-30-Hz JPEG replay starts at local second 1 and spans about three seconds",
                "mass-effect-combat": "used extensively by earlier codec and predictor studies",
            },
            "qualification_claim": "New PTS windows within existing media only; no new game, capture, or project-wide unseen-data claim.",
        },
        "input_formation": {
            "decoder": "PyAV frame decode in stream order; PTS*time_base half-open selection; no resampling",
            "canvas": "frozen corpus._letterbox(native_rgb24,720,480), Pillow BOX, centered black letterbox",
            "active_rect_expected_for_16_9": [0, 37, 720, 405],
            "rgb565": "frozen corpus.rgb565; R5/G6/B5 truncation; hash of little-endian uint16 canvas",
            "yuv420": "frozen fixed_codec.rgb_to_planes; int16 planes cast to u8 and concatenated only for hash",
            "stored_per_frame_data": "only post-letterbox RGB24 canvas, zlib content-addressed object",
            "window_policy": "all decoded frames with exact PTS timestamp in [start,end); preserve native PTS gaps",
            "max_frames_per_clip": MAX_FRAMES_PER_CLIP,
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pyav": av.__version__,
            "pillow": PIL.__version__,
            "ffmpeg_libraries": {k: list(v) for k, v in av.library_versions.items()},
        },
        "calibration_exclusion": {
            "source_manifest": "experiments/python-game-standard-v24-study/results.json",
            "excluded": "first 12 canvas RGB hashes for mass-effect-2600 and mass-effect-7200; AB38 calibration prefixes",
            "inventory_claim": "This dataset is a new PTS-selected cohort from media with prior repository use; no project-wide unseen claim.",
        },
        "cases": cases,
        "counts": {
            "clips": len(cases),
            "selected_frames": sum(c["selected_frame_count"] for c in cases),
            "stored_rgb24_raw_bytes": sum(r["canvas_rgb24"]["raw_bytes"] for c in cases for r in c["frames"]),
            "content_addressed_objects": len({r["canvas_rgb24"]["stored_sha256"] for c in cases for r in c["frames"]}),
        },
        "scope": [
            "Source preparation only: no codec, candidate generation, native comparison, or quality selection.",
            "No PTS resampling, interpolation, frame duplication, or deduplication; actual decoded frames are archived.",
            "External original files are checked against the separately declared media hashes before and after decode.",
            "The 1600 and combat source origin is not in the reviewed shared source manifest and needs explicit provenance in downstream claims.",
            "All windows are portions of precompressed footage from a single Mass Effect source lineage; this is not new game/capture or project-wide unseen content.",
        ],
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"manifest": "manifest.json", "frames": manifest["counts"]["selected_frames"],
                      "objects": manifest["counts"]["content_addressed_objects"],
                      "elapsed_seconds": time.perf_counter() - started}), flush=True)


if __name__ == "__main__":
    main()

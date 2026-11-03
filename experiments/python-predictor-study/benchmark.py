"""Measure MP01 Python profiles on the exact receiver-JPEG scene windows."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parents[1]
HELPERS = REPO / "experiments" / "python-codec-study"
MEDIA = ROOT / "media"
for p in (str(HERE), str(HELPERS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import corpus  # noqa: E402
import pacing  # noqa: E402
import codec as oldcodec  # noqa: E402
import med_codec  # noqa: E402

INPUT = HERE / "jpeg-results.json"
OUTPUT = HERE / "results.json"
PROFILES = ((2, "above"), (2, "med"), (4, "above"), (4, "med"))
CAP = 48 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return values[math.ceil(.95 * len(values)) - 1]


def file_hashes() -> dict[str, str]:
    return {str(p): sha256_file(p) for p in
            (Path(__file__).resolve(), Path(med_codec.__file__).resolve(),
             Path(oldcodec.__file__).resolve(), Path(corpus.__file__).resolve(),
             Path(pacing.__file__).resolve(), INPUT)}


def compare_scene(scene: dict[str, Any]) -> dict[str, Any]:
    source_manifest = scene["source"]
    source_path = Path(source_manifest["source"])
    if not source_path.is_absolute():
        source_path = MEDIA / source_path
    frames, recaptured = corpus.load_video(
        source_path, max_frames=scene["actual_frame_count"],
        start_seconds=source_manifest["start_seconds"],
        width=source_manifest["target_width"], height=source_manifest["target_height"])
    for key in ("source_sha256", "selected_pts", "selected_times_seconds", "frame_sha256", "active_rects"):
        expected = source_manifest[key]
        actual = recaptured[key]
        if key == "active_rects":
            actual = [list(rect) for rect in actual]
        if actual != expected:
            raise RuntimeError(f"{scene['name']}: recaptured manifest mismatch in {key}")
    if len(frames) != scene["actual_frame_count"]:
        raise RuntimeError(f"{scene['name']}: recaptured frame count mismatch")

    active_sse_by_profile = {f"q{q}_{pred}": 0.0 for q, pred in PROFILES}
    active_pixels = 0
    jpeg_sse = {int(q): 0.0 for q in scene["qualities"]}
    for qstr, qdata in scene["qualities"].items():
        for i, row in enumerate(qdata["frames"]):
            if row["input_sha256"] != recaptured["frame_sha256"][i]:
                raise RuntimeError(f"{scene['name']}: JPEG input hash mismatch at frame {i}")
            rect = recaptured["active_rects"][i]
            jpeg_sse[int(qstr)] += row["active_mse"] * rect[2] * rect[3] * 3

    profiles: dict[str, Any] = {}
    for q, predictor in PROFILES:
        name = f"q{q}_{predictor}"
        records = []
        sizes: list[int] = []
        wires: list[int] = []
        encode_ms: list[float] = []
        decode_ms: list[float] = []
        sse = 0.0
        mode_counts: dict[str, int] = {}
        for idx, canvas in enumerate(frames):
            words = corpus.rgb565(canvas)
            t0 = time.perf_counter_ns()
            packet = med_codec.encode(words, quant_step=q, predictor=predictor)
            encoded = (time.perf_counter_ns() - t0) / 1e6
            t0 = time.perf_counter_ns()
            reconstructed_words = med_codec.decode(packet)
            decoded = (time.perf_counter_ns() - t0) / 1e6
            expected_words = oldcodec.quantize(words, q)
            if not np.array_equal(reconstructed_words, expected_words):
                raise RuntimeError(f"{scene['name']} {name}: decode mismatch at frame {idx}")
            reconstructed = corpus.expand565(reconstructed_words)
            x, y, width, height = recaptured["active_rects"][idx]
            delta = canvas[y:y+height, x:x+width].astype(np.int32) - reconstructed[y:y+height, x:x+width].astype(np.int32)
            frame_sse = int(np.sum(delta.astype(np.int64) ** 2))
            sse += frame_sse
            size = len(packet)
            wire = pacing.wire_bytes(size, payload=1024, application_header=40)
            stats = med_codec.stats(packet)
            for mode, count in stats["modes"].items():
                mode_counts[mode] = mode_counts.get(mode, 0) + count
            encode_ms.append(encoded); decode_ms.append(decoded); sizes.append(size); wires.append(wire)
            records.append({
                "index": idx, "pts": recaptured["selected_pts"][idx],
                "time_seconds": recaptured["selected_times_seconds"][idx],
                "input_sha256": recaptured["frame_sha256"][idx],
                "output_quantized_rgb565_sha256": hashlib.sha256(reconstructed_words.tobytes()).hexdigest(),
                "packet_bytes": size, "wire_bytes": wire, "over_48k": size > CAP,
                "active_sse": frame_sse,
                "active_mse": frame_sse / (width * height * 3),
                "encode_python_wall_ms": encoded, "decode_python_wall_ms": decoded,
                "mode_counts": stats["modes"],
            })
        pixel_samples = sum(r["active_mse"] * recaptured["active_rects"][r["index"]][2] *
                            recaptured["active_rects"][r["index"]][3] * 3 for r in records)
        active_pixels_scene = sum(r[2] * r[3] * 3 for r in recaptured["active_rects"])
        mse = sse / active_pixels_scene if active_pixels_scene else 0.0
        psnr = None if mse == 0 else 10 * math.log10(255.0**2 / mse)
        profiles[name] = {
            "quant_step": q, "predictor": predictor, "frame_count": len(records), "frames": records,
            "unique_output_quantized_hash_count": len({r["output_quantized_rgb565_sha256"] for r in records}),
            "packet_bytes": {"mean": statistics.fmean(sizes) if sizes else None, "p95": p95(sizes),
                             "max": max(sizes, default=None), "over_48k_count": sum(v > CAP for v in sizes)},
            "mode_tile_counts": mode_counts,
            "modeled_wire_bytes": {"mean": statistics.fmean(wires) if wires else None,
                                   "p95": p95(wires), "max": max(wires, default=None)},
            "projected_wire_mbps_at_30fps": (statistics.fmean(wires) * 30 * 8 / 1_000_000
                                             if wires else None),
            "pooled_active_mse": mse, "pooled_active_psnr_db": psnr,
            "encode_python_wall_ms": {"mean": statistics.fmean(encode_ms) if encode_ms else None,
                                      "p95": p95(encode_ms), "max": max(encode_ms, default=None)},
            "decode_python_wall_ms": {"mean": statistics.fmean(decode_ms) if decode_ms else None,
                                      "p95": p95(decode_ms), "max": max(decode_ms, default=None)},
        }
        active_sse_by_profile[name] += sse
        active_pixels += active_pixels_scene

    # Compare pooled active PSNR for this scene against each recorded JPEG quality.
    scene_pixels = sum(r[2] * r[3] * 3 for r in recaptured["active_rects"])
    for data in profiles.values():
        candidates = []
        for q, jpeg_sse_total in jpeg_sse.items():
            mse = jpeg_sse_total / scene_pixels
            jpeg_psnr = None if mse == 0 else 10 * math.log10(255.0**2 / mse)
            codec_psnr = data["pooled_active_psnr_db"]
            if codec_psnr is not None and jpeg_psnr is not None:
                candidates.append((abs(codec_psnr - jpeg_psnr), q, jpeg_psnr))
        if candidates:
            difference, jpeg_quality, jpeg_psnr = min(candidates)
            data["nearest_jpeg_by_psnr"] = {
                "quality": jpeg_quality, "jpeg_pooled_active_psnr_db": jpeg_psnr,
                "absolute_psnr_difference_db": difference,
                "codec_minus_jpeg_psnr_db": data["pooled_active_psnr_db"] - jpeg_psnr,
                "interpolation": False,
            }
        else:
            data["nearest_jpeg_by_psnr"] = None
    return {"name": scene["name"], "role": scene["role"],
            "source_sha256": recaptured["source_sha256"],
            "actual_frame_count": len(frames), "unique_input_hash_count": len(set(recaptured["frame_sha256"])),
            "selected_pts": recaptured["selected_pts"],
            "selected_times_seconds": recaptured["selected_times_seconds"],
            "input_frame_sha256": recaptured["frame_sha256"], "profiles": profiles}


def run() -> dict[str, Any]:
    initial_hashes = file_hashes()
    baseline = json.loads(INPUT.read_text())
    output = {
        "study": "MP01 codec Python benchmark", "input_jpeg_results_sha256": initial_hashes[str(INPUT)],
        "helper_hashes_start": initial_hashes, "cap_bytes": CAP,
        "wire_model": {"payload_bytes": 1024, "application_header_bytes": 40,
                       "ipv4_udp_header_bytes": 28, "excludes": "Ethernet and Wi-Fi"},
        "profiles": [f"q{q}_{pred}" for q, pred in PROFILES],
        "scenes": [compare_scene(scene) for scene in baseline["scenes"]],
    }
    final_hashes = file_hashes()
    if final_hashes != initial_hashes:
        raise RuntimeError("helper or jpeg-results.json changed during benchmark")
    output["helper_hashes_end"] = final_hashes
    output["hashes_unchanged"] = True
    return output


if __name__ == "__main__":
    report = run()
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUTPUT} ({len(report['scenes'])} scenes)")

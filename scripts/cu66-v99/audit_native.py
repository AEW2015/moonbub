#!/usr/bin/env python3
"""Independently audit fresh native output authority and actual RGB565 pixels.

Uses only stdlib and NumPy; does not import the encoder or benchmark metrics.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import struct
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v99"
BASELINE = "35949d6f41366cd5725b433a136fadb1b6ce95f6"
FROZEN = {
    "experiments/python-gamebub-v99/native/main.cpp": "b54184dea2971560d719ef1ed912278529389d736f02d90101d1b2545de2de92",
    "scripts/cu66-v99/run_native.py": "d82314b2377b7b9b974b015bb37dbf96181f254cab8af597ca09beaa218a5dae",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def resolve(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def close(actual, expected, label):
    if actual is None or expected is None:
        require(actual is expected, label)
    else:
        require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9), label)


def mask(rectangles):
    result = np.zeros((480, 720), dtype=bool)
    for rect in rectangles:
        x, y, w, h = map(int, rect)
        require(x >= 0 and y >= 0 and w > 0 and h > 0 and x+w <= 720 and y+h <= 480,
                "invalid source region rectangle")
        result[y:y+h, x:x+w] = True
    return result


def rgb_from_words(raw):
    require(len(raw) == 691200, "native RGB565 length")
    words = np.frombuffer(raw, dtype="<u2").reshape(480, 720)
    red = (words >> 11) & 31
    green = (words >> 5) & 63
    blue = words & 31
    rgb = np.empty((480, 720, 3), dtype=np.uint8)
    rgb[..., 0] = (red << 3) | (red >> 2)
    rgb[..., 1] = (green << 2) | (green >> 4)
    rgb[..., 2] = (blue << 3) | (blue >> 2)
    return rgb


def region_stats(channel_sse, pixels):
    mse = channel_sse / (3 * pixels)
    return {"channel_squared_error_sum": channel_sse, "pixels": pixels,
            "mse": mse, "psnr_db": 10 * math.log10(65025 / mse) if mse else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-run", type=Path, required=True)
    parser.add_argument("--fresh-index", type=Path, default=AREA / "fresh/index.json")
    parser.add_argument("--output", type=Path, default=AREA / "audit-native.json")
    args = parser.parse_args()
    report = {"schema": "v99-independent-native-authority-pixel-audit-v1", "status": "FAIL",
              "auditor_source_path": str(Path(__file__).resolve().relative_to(ROOT)),
              "auditor_source_sha256": digest(Path(__file__).read_bytes()),
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "environment": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
              "scope": "Fresh native C++ output and numeric pixel error against shared original NPZ RGB inputs; no subjective quality or hardware latency claim",
              "method": {"rgb565_expand": "r8=(r5<<3)|(r5>>2); g8=(g6<<2)|(g6>>4); b8=(b5<<3)|(b5>>2)",
                         "mse": "exact integer sum of squared RGB channel errors divided by 3*pixel_count",
                         "roi": "union of source manifest ROI rectangles intersected with active rectangle",
                         "quality_comparison_tolerance": {"relative": 1e-12, "absolute": 1e-9},
                         "imports_encoder_or_benchmark_metrics": False},
              "pins": {}, "counts": {}, "cases": [], "frames": [], "hardware_measured": False}
    pins = report["pins"]
    counts = Counter()

    def pinned(path, expected=None):
        path = resolve(path)
        raw = path.read_bytes()
        hashed = digest(raw)
        if expected is not None:
            require(hashed == expected, f"file SHA256 differs: {path}")
            counts["expected_file_hashes_verified"] += 1
        pins[str(path)] = {"sha256": hashed, "bytes": len(raw)}
        return raw

    def document(path, expected=None):
        return json.loads(pinned(path, expected))

    def golden(path, expected):
        path = resolve(path)
        compressed = pinned(path, fresh["artifact_sha256"][str(path.relative_to(fresh_attempt))])
        raw = gzip.decompress(compressed) if path.suffix == ".gz" else compressed
        require(digest(raw) == expected, f"golden raw SHA256 differs: {path}")
        counts["golden_raw_hashes_verified"] += 1
        return raw

    try:
        index = document(args.fresh_index)
        fresh = document(index["attempt_json"], index["sha256"])
        require(fresh["status"] == "PASS_SOFTWARE_CAMPAIGN", "fresh campaign did not pass")
        require(fresh["baseline_commit"] == BASELINE, "unexpected campaign baseline")
        fresh_attempt = resolve(fresh["attempt"])
        native = resolve(args.native_run)
        receipt = document(native / "receipt.json")
        require(receipt["status"] == "passed" and receipt["native_exit_code"] == 0,
                "native attempt did not pass")
        report["native_receipt_path"] = str(native / "receipt.json")
        report["fresh_report_path"] = str(resolve(index["attempt_json"]))
        for path, expected in {**fresh["source_sha256"], **receipt["sources"]}.items():
            pinned(path, expected)
            counts["source_pins_unchanged"] += 1
        for path, expected in FROZEN.items():
            require(receipt["sources"][path] == expected, "unexpected frozen native source receipt")
            pinned(path, expected)
        baseline_headers = {}
        for path in receipt["sources"]:
            if path.startswith("experiments/cu66-native-v69/"):
                baseline_bytes = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
                require(digest(baseline_bytes) == receipt["sources"][path], "baseline decoder changed")
                baseline_headers[path] = digest(baseline_bytes)
        report["baseline_decoder_headers_verified"] = baseline_headers
        binary = resolve(receipt["binary"]["path"])
        require(not binary.is_relative_to(ROOT), "binary must be retained outside Git repository")
        require(len(pinned(binary, receipt["binary"]["sha256"])) == receipt["binary"]["bytes"], "binary size differs")
        require(all(flag in receipt["compile_command"] for flag in ("-std=c++17", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror")),
                "required native compiler flags missing")
        pinned(native / "compile.log")
        native_stderr = document(native / "native.stderr")
        require(native_stderr["pass"] is True and native_stderr["known_answer_tests"] == 2, "native KAT/exit record")
        ledger_path = resolve(fresh["ledger_path"])
        require(resolve(receipt["ledger"]["path"]) == ledger_path, "native used different ledger")
        require(receipt["ledger"]["sha256"] == fresh["ledger_sha256"], "native/fresh ledger pin differs")
        ledger = [json.loads(line) for line in pinned(ledger_path, fresh["ledger_sha256"]).splitlines()]
        manifest = pinned(native / "causal_manifest.tsv", receipt["manifest_sha256"]).decode().splitlines()
        observations = [json.loads(line) for line in pinned(native / "observations.jsonl", receipt["observations_sha256"]).splitlines()]
        raw_observations = [json.loads(line) for line in pinned(native / "native.jsonl").splitlines()]
        inputs = document(native / "inputs.json")
        summary = document(native / "summary.json", receipt["summary_sha256"])
        require(len(ledger) == len(manifest) == len(observations) == len(raw_observations) == len(inputs) == fresh["accepted_frames"] == 360,
                "complete 360-frame authority row count")
        require(summary["pass"] is True and summary["timing_is_fpga"] is False, "summary scope/status")
        source_manifest = document(ROOT / "experiments/python-gamebub-v98/sources/manifest.json", fresh["source_manifest_sha256"])
        require(source_manifest["clips"] == fresh["source_clips"], "source manifest differs from fresh report")
        sources = {clip["clip_id"]: clip for clip in fresh["source_clips"]}
        case_metadata = {case["case_id"]: case for case in fresh["cases"]}
        require(len(case_metadata) == 12, "expected four clips by three quantization scales")
        grouped = {}
        timings = []
        for index_number, (entry, observation, raw_observation, fields, input_entry) in enumerate(
                zip(ledger, observations, raw_observations, manifest, inputs)):
            key = (entry["clip_id"], entry["frame_id"])
            fields = fields.split("\t")
            require(len(fields) == 8, "native manifest width")
            require(entry["accepted"] is True and entry["ack_verified"] is True and entry["adapter_exact_checked"] is True,
                    "fresh ledger authority flags")
            require(key == (observation["clip_id"], observation["frame_id"]), "native row identity differs")
            require(all(observation[name] == value for name, value in raw_observation.items()), "native raw observation modified")
            require(fields[:2] == [str(key[0]), str(key[1])], "manifest row identity differs")
            require(resolve(fields[2]) == resolve(entry["packet_path"]), "manifest packet differs")
            require(fields[3:7] == [entry["expected"][name] for name in
                ("canonical_sha256", "hud_sha256", "rgb565_sha256", "canonical_tag")], "manifest golden differs")
            require(input_entry["clip_id"] == key[0] and input_entry["frame_id"] == key[1] and
                    resolve(input_entry["packet_path"]) == resolve(entry["packet_path"]), "input receipt identity differs")
            packet = pinned(entry["packet_path"], entry["packet_sha256"])
            require(input_entry["packet_sha256"] == entry["packet_sha256"] and
                    input_entry["packet_bytes"] == len(packet) == entry["bytes"] == observation["packet_bytes"], "packet receipt size/hash")
            require(input_entry["expected"] == {k: entry["expected"][k] for k in
                ("canonical_sha256", "hud_sha256", "rgb565_sha256")}, "input expected hash differs")
            require(all(observation[k] == v for k, v in entry["expected"].items()), "native canonical/HUD/display parity differs")
            require(observation["key"] == entry["key"] == bool(packet[5] & 1), "native key identity differs")
            require(all(observation[name] is True for name in ("rejected_published_state_unchanged", "post_reject_valid_same_context", "immutable_publication")),
                    "native rejection/recovery/ownership check missing")
            require(observation["rejections"] == (10 if entry["key"] else 11), "native adversarial check count differs")
            counts["atomic_rejection_checks"] += observation["rejections"]
            yuv = golden(entry["canonical_path"], entry["expected"]["canonical_sha256"])
            require(len(yuv) == 518400 and digest(struct.pack("<HH", 720, 480) + yuv)[:32] == entry["expected"]["canonical_tag"],
                    "golden canonical geometry/tag differs")
            hud = golden(entry["hud_path"], entry["expected"]["hud_sha256"])
            require(len(hud) >= 5 and struct.unpack("<HH", hud[:4]) == (720, 480), "golden HUD geometry")
            position = 5
            for _ in range(hud[4]):
                require(position + 8 <= len(hud), "golden HUD rectangle truncated")
                x, y, w, h = struct.unpack_from("<4H", hud, position)
                require(w > 0 and h > 0 and x+w <= 720 and y+h <= 480, "golden HUD rectangle bounds")
                position += 8 + 2*w*h
            require(position == len(hud), "golden HUD exact size")
            golden_display = golden(entry["rgb565_path"], entry["expected"]["rgb565_sha256"])
            require(resolve(fields[7] + ".rgb565.gz") == resolve(observation["display_rgb565_path"]), "native output path differs from manifest")
            display_file = pinned(observation["display_rgb565_path"], observation["display_rgb565_file_sha256"])
            require(display_file[:2] == b"\x1f\x8b" and display_file[4:8] == b"\0\0\0\0", "native gzip mtime is not zero")
            display = gzip.decompress(display_file)
            require(len(display) == 691200 and digest(display) == observation["rgb565_sha256"] and display == golden_display,
                    "actual native display file does not match published/golden pixels")
            observation_ms = observation["receive_to_published_rgb565_ms"]
            require(math.isfinite(observation_ms) and observation_ms >= 0, "invalid native CPU timing")
            timings.append(observation_ms)
            grouped.setdefault(key[0], []).append((entry, observation, display))
            counts["canonical_hud_display_parity_frames"] += 1
            counts["native_actual_display_files_verified"] += 1
        for case_id, rows in grouped.items():
            case = case_metadata[case_id]
            clip = sources[case["source_clip_id"]]
            records = document(case["records_path"], case["records_sha256"])
            quality_doc = document(case["quality_path"], case["quality_sha256"])
            quality = quality_doc["quality"]
            require(quality_doc["accepted_input_ids"] == case["accepted_input_ids"] and len(rows) == case["accepted_frames"], "case accepted set differs")
            npz_path = ROOT / "experiments/python-gamebub-v98/sources" / clip["npz_path"]
            pinned(npz_path, clip["npz_sha256"])
            with np.load(npz_path, allow_pickle=False) as archive:
                originals = archive[clip.get("rgb_key", "rgb")]
            require(originals.dtype == np.uint8 and list(originals.shape) == clip["shape"], "source RGB NPZ dtype/shape")
            original_hashes = [digest(frame.tobytes()) for frame in originals]
            require(original_hashes == clip["frame_sha256"] == case["source_frame_sha256"], "source frame hashes differ")
            active = mask([clip["active_rect"]])
            rectangles = [r["rect"] if isinstance(r, dict) else r for r in clip["roi"]["rectangles"]]
            regions = {"active": active, "roi": mask(rectangles) & active}
            require(all(region.any() for region in regions.values()), "empty pixel audit region")
            pooled = {name: {"sse": 0, "pixels": 0} for name in regions}
            case_frame_reports = []
            for accepted_index, (entry, observation, display) in enumerate(rows):
                source_id = case["accepted_input_ids"][accepted_index]
                source = originals[source_id]
                require(entry["source_rgb_sha256"] == original_hashes[source_id], "ledger original input hash differs")
                require(records["records"][source_id]["source_rgb_sha256"] == original_hashes[source_id], "records original input hash differs")
                rgb = rgb_from_words(display)
                compare = quality["frames"][accepted_index]
                require(compare["id"] == accepted_index, "fresh quality frame order")
                require(digest(rgb.tobytes()) == compare["display_rgb_sha256"], "expanded native actual RGB differs from quality input")
                # int32 multiplication is exact for [-255,255]; int64 reduction cannot overflow here.
                errors = rgb.astype(np.int32) - source.astype(np.int32)
                squared_channels = np.square(errors)
                frame_report = {"clip_id": case_id, "frame_id": entry["frame_id"], "source_frame_id": source_id,
                                "source_rgb_sha256": original_hashes[source_id],
                                "display_rgb565_path": observation["display_rgb565_path"],
                                "display_rgb565_file_sha256": observation["display_rgb565_file_sha256"],
                                "display_rgb565_sha256": observation["rgb565_sha256"], "regions": {}}
                for name, region in regions.items():
                    sse = int(squared_channels[region].sum(dtype=np.int64))
                    pixels = int(np.count_nonzero(region))
                    measured = region_stats(sse, pixels)
                    reference = compare["regions"][name]
                    require(pixels == reference["pixels"], "quality region pixel count differs")
                    close(sse/3, reference["squared_error_sum"], "quality squared RGB error sum differs")
                    close(measured["mse"], reference["mse"], "quality frame MSE differs")
                    close(measured["psnr_db"], reference["psnr_db"], "quality frame PSNR differs")
                    frame_report["regions"][name] = measured
                    pooled[name]["sse"] += sse
                    pooled[name]["pixels"] += pixels
                    counts["per_frame_region_quality_checks"] += 1
                case_frame_reports.append(frame_report)
            measured_pooled = {}
            for name, values in pooled.items():
                measured_pooled[name] = region_stats(values["sse"], values["pixels"])
                for field in ("mse", "psnr_db"):
                    close(measured_pooled[name][field], quality["pooled"][name][field], f"case pooled {name} {field} differs")
                close(measured_pooled[name]["psnr_db"], case[name+"_psnr_db_accepted_only"], "campaign quality differs")
                counts["pooled_region_quality_checks"] += 1
            report["cases"].append({"case_id": case_id, "source_clip_id": clip["clip_id"], "quant_scale": case["quant_scale"],
                                    "source_npz_path": str(npz_path), "source_npz_sha256": clip["npz_sha256"],
                                    "active_rect": clip["active_rect"], "roi_rectangles": rectangles,
                                    "frames_verified": len(rows), "pooled": measured_pooled})
            report["frames"].extend(case_frame_reports)
            counts["source_frames_hashed_including_scale_reuse"] += len(originals)
            counts["actual_pixel_frames_recomputed"] += len(rows)
        ordered = sorted(timings)
        timing = {"min": min(timings), "mean": statistics.mean(timings), "median": statistics.median(timings),
                  "p95_nearest_rank": ordered[math.ceil(.95*len(ordered))-1], "max": max(timings)}
        for name, value in timing.items():
            close(value, summary["receive_to_published_rgb565_ms"][name], "native timing summary differs")
        require(summary["frames"] == native_stderr["accepted"] == len(ledger) and
                summary["clips"] == len(grouped) == 12 and
                summary["rejections"] == native_stderr["rejected"] == counts["atomic_rejection_checks"], "native aggregate check counts differ")
        report["cpu_receive_to_published_rgb565_ms"] = timing
        report["cpu_timing_scope"] = receipt["timing_scope"]
        report["cpu_timing_excludes"] = receipt["timing_excludes"]
        report["authority"] = {"native_source_frozen": True, "baseline_decoder_unchanged": True,
                               "external_binary_hash_verified": True, "all_360_actual_displays_verified": True,
                               "all_360_actual_pixel_errors_recomputed": True,
                               "fresh_quality_matches_independent_actual_native_pixels": True,
                               "native_atomic_rejection_and_ownership_flags_verified": True}
        # Recheck all pinned sources and files after the audit, including the external binary.
        for path, pin in pins.items():
            require(digest(Path(path).read_bytes()) == pin["sha256"], "audit input changed during verification")
        report["status"] = "PASS_INDEPENDENT_NATIVE_PIXEL_AUDIT"
        return_code = 0
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        print(report["error"], file=sys.stderr)
        return_code = 1
    report["counts"] = dict(counts)
    report["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.output.resolve().write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "output": str(args.output.resolve())}, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())

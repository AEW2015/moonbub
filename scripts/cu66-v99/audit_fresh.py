#!/usr/bin/env python3
"""Independent read-only audit of the V99 fresh-RGB campaign ledger.

This auditor uses Python stdlib plus NumPy only. It deliberately does not import
the campaign runner, CU66 encoder, receiver, or metrics modules.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v99"
V98_AREA = ROOT / "experiments/python-gamebub-v98"
MANIFEST_PATH = V98_AREA / "sources/manifest.json"
V98_INDEX_PATH = V98_AREA / "index.json"
DEFAULT_INDEX = AREA / "fresh/index.json"
OUTPUT = AREA / "audit-fresh.json"
CAP_BYTES = 49_152
FRAME_COUNT = 30
EXPECTED_CASES = 12
EXPECTED_ATTEMPTS = 360


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inside(attempt: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(attempt.resolve()):
        raise ValueError(f"artifact escapes campaign attempt: {value}")
    return resolved


class Audit:
    def __init__(self):
        self.checks = 0
        self.failures: list[str] = []

    def require(self, ok: bool, message: str):
        self.checks += 1
        if not ok:
            self.failures.append(message)


def crc_packet(audit: Audit, packet: bytes, label: str) -> tuple[int, int] | None:
    """Check CU66/GU66 nested envelopes with the native-v69 wire offsets."""
    try:
        audit.require(88 <= len(packet) <= CAP_BYTES, f"{label}: packet size bounds")
        if len(packet) < 88:
            return None
        audit.require(packet[:4] == b"CU66", f"{label}: CU66 outer magic")
        audit.require(zlib.crc32(packet[:-4]) == struct.unpack_from("<I", packet, len(packet)-4)[0],
                      f"{label}: outer CRC32")
        epoch = struct.unpack_from("<H", packet, 6)[0]
        frame_id, reference_id = struct.unpack_from("<II", packet, 8)
        width, height = struct.unpack_from("<HH", packet, 16)
        inner_bytes, hud_bytes = struct.unpack_from("<II", packet, 68)
        inner_start = 76
        inner_end = inner_start + inner_bytes
        audit.require(epoch == 25, f"{label}: outer epoch")
        audit.require((width, height) == (720, 480), f"{label}: outer geometry")
        audit.require(inner_end + hud_bytes + 4 == len(packet), f"{label}: exact outer lengths")
        if inner_end > len(packet) - 4 or inner_bytes < 67:
            return frame_id, reference_id
        inner = packet[inner_start:inner_end]
        audit.require(inner[:4] == b"GU66", f"{label}: GU66 inner magic")
        audit.require(zlib.crc32(inner[:-4]) == struct.unpack_from("<I", inner, len(inner)-4)[0],
                      f"{label}: inner CRC32")
        if len(inner) >= 16:
            inner_epoch, inner_fid, inner_rid = struct.unpack_from("<III", inner, 6)
            audit.require(inner_epoch == epoch and inner_fid == frame_id and inner_rid == reference_id,
                          f"{label}: inner identity matches outer")
        return frame_id, reference_id
    except (IndexError, struct.error, ValueError) as exc:
        audit.failures.append(f"{label}: malformed packet: {type(exc).__name__}: {exc}")
        return None


def verify_manifest(audit: Audit):
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes)
    v98_index = read_json(V98_INDEX_PATH)
    v98_report_path = (ROOT / v98_index["attempt_json"]).resolve(strict=True)
    v98_report_bytes = v98_report_path.read_bytes()
    v98_report = json.loads(v98_report_bytes)
    audit.require(sha_bytes(v98_report_bytes) == v98_index.get("sha256"), "V98 index binds frozen report")
    audit.require(v98_report.get("status") == "PASS", "V98 anchor report passed")
    audit.require(v98_report.get("input_manifest_sha256") == sha_bytes(manifest_bytes),
                  "V98 report binds frozen source manifest")
    clips = {c["clip_id"]: c for c in manifest["clips"]}
    audit.require(len(clips) == 4, "frozen V98 manifest has four inputs")
    frames_by_clip: dict[str, list[str]] = {}
    fps_by_clip: dict[str, float] = {}
    for clip_id, clip in clips.items():
        npz_path = (MANIFEST_PATH.parent / clip["npz_path"]).resolve(strict=True)
        audit.require(sha_file(npz_path) == clip["npz_sha256"], f"{clip_id}: source NPZ hash")
        with np.load(npz_path, allow_pickle=False) as npz:
            audit.require(set(npz.files) == {clip.get("rgb_key", "rgb")}, f"{clip_id}: NPZ keys")
            rgb = npz[clip.get("rgb_key", "rgb")]
            audit.require(rgb.dtype == np.uint8 and rgb.shape == (FRAME_COUNT, 480, 720, 3),
                          f"{clip_id}: RGB array contract")
            computed = [sha_bytes(np.ascontiguousarray(frame).tobytes()) for frame in rgb]
        expected = clip["frame_sha256"]
        audit.require(computed == expected, f"{clip_id}: all RGB frame hashes match frozen manifest")
        audit.require(len(clip.get("timestamps", [])) == FRAME_COUNT, f"{clip_id}: timestamp count")
        timestamps = clip.get("timestamps", [])
        exact_times = []
        for index, ts in enumerate(timestamps):
            pts = int(ts["pts"])
            tb_num, tb_den = map(int, ts["time_base"].split("/"))
            frac = (pts * tb_num, tb_den)
            seconds_num, seconds_den = map(int, ts["seconds"].split("/"))
            audit.require(math.gcd(frac[0], frac[1]) == 0 or
                          frac[0] * seconds_den == seconds_num * frac[1],
                          f"{clip_id}: timestamp {index} seconds equal PTS*time_base")
            exact_times.append((pts, tb_num, tb_den))
        intervals = []
        for left, right in zip(exact_times, exact_times[1:]):
            # Compare rational timestamp delta without float conversion.
            l_num, l_den = left[0] * left[1], left[2]
            r_num, r_den = right[0] * right[1], right[2]
            intervals.append((r_num * l_den - l_num * r_den, r_den * l_den))
        audit.require(bool(intervals) and all(a*d == c*b for (a,b),(c,d) in zip(intervals, intervals[1:])),
                      f"{clip_id}: selected PTS cadence is constant")
        cadence = clip.get("selected_fps", clip.get("source_metadata", {}).get("selected_fps",
                              clip.get("source_fps", clip.get("frame_rate", "0/1"))))
        if isinstance(cadence, str) and "/" in cadence:
            fps_n, fps_d = map(int, cadence.split("/"))
        else:
            fps_n, fps_d = int(cadence), 1
        audit.require(bool(intervals) and intervals[0][0] * fps_n == intervals[0][1] * fps_d,
                      f"{clip_id}: selected PTS cadence agrees with exact FPS {cadence}")
        frames_by_clip[clip_id] = computed
        fps_by_clip[clip_id] = fps_n / fps_d
    return manifest, clips, frames_by_clip, fps_by_clip, sha_bytes(manifest_bytes), v98_index


def audit_attempt(index_path: Path, audit: Audit) -> dict:
    manifest, clips, frames_by_clip, fps_by_clip, manifest_sha, v98_index = verify_manifest(audit)
    index_path = index_path.resolve(strict=True)
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes)
    report_path = (ROOT / index["attempt_json"]).resolve(strict=True)
    report_bytes = report_path.read_bytes()
    audit.require(sha_bytes(report_bytes) == index.get("sha256"), "fresh index binds exact report bytes")
    report = json.loads(report_bytes)
    attempt = (ROOT / report["attempt"]).resolve(strict=True)
    audit.require(attempt.is_dir(), "campaign attempt directory exists")
    audit.require(report.get("schema") == "v99-fresh-cu66-campaign-v1", "fresh campaign schema")
    audit.require(report.get("status") == "PASS_SOFTWARE_CAMPAIGN", "fresh software campaign passed")
    audit.require(report.get("hardware_measured") is False, "campaign explicitly marks hardware unmeasured")
    audit.require(report.get("source_manifest_sha256") == manifest_sha,
                  "fresh campaign binds frozen V98 source manifest")
    audit.require(report.get("source_clips") == manifest["clips"], "fresh report carries exact frozen clip descriptors")
    audit.require(report.get("v98_anchor_report", {}).get("attempt_json") == v98_index.get("attempt_json") and
                  report.get("v98_anchor_report", {}).get("sha256") == v98_index.get("sha256"),
                  "fresh report binds the frozen V98 anchor index")

    # The campaign copies every source pin. Verify the immutable snapshot and
    # note whether the current worktree still matches that frozen pin.
    pins = report.get("source_sha256", {})
    current_pin_matches = 0
    current_pin_mismatches = []
    for relative, expected in pins.items():
        snap = attempt / "source-snapshot" / relative
        audit.require(snap.is_file() and sha_file(snap) == expected,
                      f"source snapshot hash: {relative}")
        current = ROOT / relative
        if current.is_file() and sha_file(current) == expected:
            current_pin_matches += 1
        else:
            current_pin_mismatches.append(relative)
    audit.require(bool(pins), "fresh report has source pins")
    runner_rel = "scripts/cu66-v99/run_fresh.py"
    runner_snap = attempt / "source-snapshot" / runner_rel
    if runner_snap.is_file():
        runner_text = runner_snap.read_text(encoding="utf-8")
        audit.require("frames.setflags(write=False)" in runner_text,
                      "pinned runner marks loaded RGB frame array read-only")
        audit.require("assert frame_shas == clip['frame_sha256']" in runner_text,
                      "pinned runner checks every loaded source frame identity")

    cases = report.get("cases", [])
    audit.require(len(cases) == EXPECTED_CASES, f"campaign has {EXPECTED_CASES} cases")
    seen_case_ids = set()
    totals = {"attempts": 0, "accepted": 0, "rejected": 0, "candidate_bytes": 0,
              "accepted_bytes": 0, "over_cap_attempts": 0}
    row_checks = 0
    component_npz_count = 0
    for case in cases:
        case_id = case.get("case_id", "<missing>")
        audit.require(case_id not in seen_case_ids, f"unique case ID: {case_id}")
        seen_case_ids.add(case_id)
        clip_id = case.get("source_clip_id")
        audit.require(clip_id in clips, f"{case_id}: manifest clip exists")
        if clip_id not in clips:
            continue
        expected_hashes = frames_by_clip[clip_id]
        fps = fps_by_clip[clip_id]
        records_path = resolve_inside(attempt, case["records_path"])
        audit.require(sha_file(records_path) == case.get("records_sha256"), f"{case_id}: records hash")
        records_doc = read_json(records_path)
        rows = records_doc.get("records", [])
        audit.require(len(rows) == FRAME_COUNT, f"{case_id}: exactly 30 input rows")
        audit.require(records_doc.get("input_frames") == FRAME_COUNT, f"{case_id}: record input count")
        audit.require(records_doc.get("cap_bytes") == CAP_BYTES, f"{case_id}: research cap")
        audit.require(records_doc.get("epoch") == 25 and records_doc.get("key_interval") == 30,
                      f"{case_id}: epoch/key interval")
        audit.require(case.get("source_npz_sha256") == clips[clip_id]["npz_sha256"],
                      f"{case_id}: source NPZ identity")
        audit.require(case.get("source_frame_sha256") == expected_hashes,
                      f"{case_id}: frame identity list matches frozen input")
        accepted_count = rejected_count = all_bytes = accepted_bytes = over_cap = 0
        last_acked_id: int | None = None
        last_row_rejected = False
        for i, row in enumerate(rows):
            row_checks += 1
            label = f"{case_id}/frame-{i}"
            fid = row.get("frame_id")
            rid = row.get("reference_id")
            accepted = row.get("accepted") is True
            ack = row.get("ack_verified") is True
            key = row.get("key") is True
            packet_path = resolve_inside(attempt, row["packet_path"])
            packet = packet_path.read_bytes()
            size = len(packet)
            audit.require(fid == i, f"{label}: frame identity")
            audit.require(row.get("source_rgb_sha256") == expected_hashes[i],
                          f"{label}: source RGB hash matches frozen V98 frame")
            audit.require(size == row.get("bytes"), f"{label}: packet byte count")
            audit.require(row.get("packet_sha256") == sha_bytes(packet), f"{label}: packet SHA-256")
            parsed_ids = crc_packet(audit, packet, label)
            audit.require(row.get("cap_fit") is (size <= CAP_BYTES), f"{label}: cap-fit flag")
            audit.require(accepted == ack, f"{label}: accepted status requires verified ACK")
            audit.require(not accepted or size <= CAP_BYTES, f"{label}: admitted packet within 49152 cap")
            audit.require(not ack or size <= CAP_BYTES, f"{label}: no ACK for over-cap packet")
            if parsed_ids:
                audit.require(parsed_ids == (fid, rid), f"{label}: packet frame/reference identity")
            should_be_key = last_acked_id is None or i % 30 == 0
            audit.require(key is should_be_key, f"{label}: key follows ACK state")
            audit.require(rid == (0xFFFFFFFF if should_be_key else last_acked_id),
                          f"{label}: reference points only to last ACKed frame")
            if accepted:
                accepted_count += 1
                accepted_bytes += size
                last_acked_id = i
                last_row_rejected = False
            else:
                rejected_count += 1
                over_cap += int(size > CAP_BYTES)
                last_row_rejected = True
                audit.require(size > CAP_BYTES, f"{label}: rejected attempt is over cap, not receiver ACK")
                audit.require(row.get("rejection_reason") == "complete CU66 cap exceeded",
                              f"{label}: rejection is explicit cap rejection")
            all_bytes += size
            if i + 1 < len(rows) and last_row_rejected:
                nxt = rows[i + 1]
                audit.require(nxt.get("key") is True and nxt.get("reference_id") == 0xFFFFFFFF,
                              f"{case_id}/frame-{i+1}: rejection forces next independent key")

            expected = row.get("expected", {})
            for kind in ("canonical", "hud", "rgb565"):
                comp_path = resolve_inside(attempt, row[f"{kind}_path"])
                raw = gzip.decompress(comp_path.read_bytes())
                audit.require(row.get(f"{kind}_compression") == "gzip-mtime0",
                              f"{label}: {kind} golden compression metadata")
                audit.require(sha_bytes(raw) == expected.get(f"{kind}_sha256"),
                              f"{label}: decompressed {kind} golden hash")
            comp_npz = resolve_inside(attempt, row["rtl_components_path"])
            component_npz_count += 1
            # Opening and enumerating arrays also detects truncated/corrupt NPZ
            # files; the enclosing report artifact ledger binds their bytes.
            with np.load(comp_npz, allow_pickle=False) as comp:
                audit.require({"coefficients_y", "coefficients_u", "coefficients_v", "plane_y",
                               "plane_u", "plane_v", "qmap", "hud", "operations", "key",
                               "frame_id", "reference_id", "block_size"}.issubset(set(comp.files)),
                              f"{label}: RTL component NPZ members")
                audit.require(int(comp["frame_id"]) == i and int(comp["reference_id"]) == rid and
                              bool(comp["key"]) == key and int(comp["block_size"]) == 32,
                              f"{label}: RTL component NPZ identity")
        audit.require(case.get("input_frames") == FRAME_COUNT, f"{case_id}: reported input frames")
        audit.require(case.get("accepted_frames") == accepted_count, f"{case_id}: accepted row recount")
        audit.require(case.get("rejected_frames") == rejected_count, f"{case_id}: rejected row recount")
        audit.require(case.get("candidate_bytes_all_attempts") == all_bytes,
                      f"{case_id}: all candidate bytes recount")
        audit.require(case.get("accepted_bytes") == accepted_bytes, f"{case_id}: accepted bytes recount")
        audit.require(case.get("offered_candidate_mbps_at_selected_cadence_including_rejects") is not None and
                      math.isclose(case["offered_candidate_mbps_at_selected_cadence_including_rejects"],
                                   all_bytes / FRAME_COUNT * 8 * fps / 1e6, rel_tol=1e-12, abs_tol=1e-12),
                      f"{case_id}: selected-cadence offered rate recount")
        totals["attempts"] += len(rows)
        totals["accepted"] += accepted_count
        totals["rejected"] += rejected_count
        totals["candidate_bytes"] += all_bytes
        totals["accepted_bytes"] += accepted_bytes
        totals["over_cap_attempts"] += over_cap

    # Every generated artifact, including every component NPZ and gzip golden,
    # must be named and hashed by the report's retained artifact ledger.
    expected_artifacts = report.get("artifact_sha256", {})
    actual_artifacts = {}
    for path in sorted(attempt.rglob("*")):
        if not path.is_file() or "source-snapshot" in path.parts or path == report_path:
            continue
        actual_artifacts[path.relative_to(attempt).as_posix()] = sha_file(path)
    audit.require(actual_artifacts == expected_artifacts,
                  "report artifact ledger exactly matches all retained attempt artifacts")
    audit.require(totals["attempts"] == EXPECTED_ATTEMPTS, "recount is 360 attempts")
    audit.require(totals["accepted"] + totals["rejected"] == totals["attempts"],
                  "accepted/rejected rows partition all attempts")
    audit.require(report.get("candidate_attempts") == totals["attempts"], "campaign attempt total recount")
    audit.require(report.get("accepted_frames") == totals["accepted"], "campaign accepted total recount")
    audit.require(report.get("rejected_frames") == totals["rejected"], "campaign rejected total recount")
    audit.require(report.get("complete_case_count") == sum(c.get("all_inputs_admitted") is True for c in cases),
                  "complete-case count recount")

    return {
        "schema": "v99-fresh-independent-audit-v1",
        "status": "PASS_SOFTWARE_LEDGER" if not audit.failures else "FAIL",
        "auditor": str(Path(__file__).relative_to(ROOT)),
        "auditor_sha256": sha_file(Path(__file__)),
        "campaign_index": str(index_path.relative_to(ROOT)),
        "campaign_index_sha256": sha_bytes(index_bytes),
        "campaign_report": str(report_path.relative_to(ROOT)),
        "campaign_report_sha256": sha_bytes(report_bytes),
        "v98_manifest_sha256": manifest_sha,
        "v98_anchor_index_sha256": sha_file(V98_INDEX_PATH),
        "baseline_commit": report.get("baseline_commit"),
        "source_pins": {
            "count": len(pins),
            "snapshot_verified": len(pins) - len([p for p in pins if not (attempt / "source-snapshot" / p).is_file() or sha_file(attempt / "source-snapshot" / p) != pins[p]]),
            "current_worktree_matches": current_pin_matches,
            "current_worktree_mismatches": current_pin_mismatches,
        },
        "recount": {**totals, "cases": len(cases), "component_npz": component_npz_count,
                    "row_level_checks": row_checks},
        "checks": {"count": audit.checks, "failed": len(audit.failures)},
        "failures": audit.failures,
        "limitations": [
            "Software input/packet/ledger audit only; no native CLI receipt is included here.",
            "No hardware capture, physical frame-rate, full-frame FPS, ESP32 resource or FPGA timing claim is made.",
            "The four video inputs are decoded/composited or synthetic sources, not raw gameplay capture evidence.",
            "Historical last-published display behavior is not counted as acceptance of a rejected current frame.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX,
                        help="fresh campaign index JSON (default: V99 fresh index)")
    parser.add_argument("--output", type=Path, default=OUTPUT,
                        help="audit JSON output (default: experiments/python-gamebub-v99/audit-fresh.json)")
    args = parser.parse_args()
    audit = Audit()
    try:
        result = audit_attempt(args.index, audit)
    except Exception as exc:
        result = {"schema": "v99-fresh-independent-audit-v1", "status": "FAIL",
                  "auditor": str(Path(__file__).relative_to(ROOT)),
                  "auditor_sha256": sha_file(Path(__file__)),
                  "checks": {"count": audit.checks, "failed": len(audit.failures) + 1},
                  "failures": audit.failures + [f"fatal audit error: {type(exc).__name__}: {exc}"],
                  "limitations": ["Campaign evidence could not be fully audited."]}
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": result.get("checks"),
                      "failures": result.get("failures", [])[:8], "output": str(output)}, indent=2))
    return 0 if result["status"] == "PASS_SOFTWARE_LEDGER" else 1


if __name__ == "__main__":
    raise SystemExit(main())

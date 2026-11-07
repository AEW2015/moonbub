#!/usr/bin/env python3
"""Independent read-only audit of the V99 direct-CS88 sender campaign.

Uses Python stdlib plus NumPy for source NPZ identity. Does not import the
encoder, campaign runner, or timing/metrics modules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import zlib

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v99"
MANIFEST_PATH = ROOT / "experiments/python-gamebub-v98/sources/manifest.json"
DEFAULT_INDEX = AREA / "direct/index.json"
OUTPUT = AREA / "audit-direct.json"
CONTROL_PATH = AREA / "cs88/attempts/20261107T190043503Z/results.json"
CAP = 49_152
REAL_FRAMES = 120
SYNTHETIC_FRAMES = 32
PREFIX = struct.Struct(">4sBBBBIIQHHHHIIIII")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(attempt: Path, value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        local = attempt / p
        p = local if local.exists() else ROOT / p
    p = p.resolve(strict=True)
    if not p.is_relative_to(attempt.resolve()):
        raise ValueError(f"artifact path escapes attempt: {value}")
    return p


class Checks:
    def __init__(self):
        self.count = 0
        self.failures: list[str] = []

    def need(self, ok: bool, message: str):
        self.count += 1
        if not ok:
            self.failures.append(message)


def verify_cs88_packet(checks: Checks, packet: bytes, row: dict, label: str):
    checks.need(132 <= len(packet) <= CAP, f"{label}: CS88 size and complete-wire cap")
    if len(packet) < PREFIX.size + 32 + 32 + 12 + 4:
        return
    fields = PREFIX.unpack_from(packet)
    (magic, version, key_flag, group, method, fid, rid, generation, width,
     height, block, reserved, chunk_cap, mode_len, qm_len, hud_len,
     residual_len) = fields
    checks.need(magic == b"CS88" and version == 1, f"{label}: CS88 version/magic")
    checks.need(key_flag in (0, 1) and group == 16 and block == 32 and reserved == 0,
                f"{label}: key/group/block/reserved profile fields")
    checks.need(method == (0 if key_flag else 3), f"{label}: key0/delta grouped mode method3")
    checks.need((width, height, chunk_cap) == (720, 480, 65536), f"{label}: geometry/chunk cap")
    checks.need(fid == row.get("frame_id") and rid == row.get("reference_id") and
                generation == row.get("generation"), f"{label}: wire identity/generation")
    checks.need(bool(key_flag) is row.get("key"), f"{label}: wire key flag")
    body_start = PREFIX.size + 32 + 32 + 12
    checks.need(body_start == 128, f"{label}: documented 128-byte CS88 header")
    checks.need(body_start + mode_len + qm_len + residual_len + hud_len + 4 == len(packet),
                f"{label}: exact component lengths")
    checks.need(zlib.crc32(packet[:-4]) == struct.unpack_from(">I", packet, len(packet)-4)[0],
                f"{label}: outer CRC32")
    qstart = body_start + mode_len
    qend = qstart + qm_len
    checks.need(qm_len >= 12 and packet[qstart:qstart+4] == b"QM87",
                f"{label}: QM87 component")
    if qm_len >= 12 and qend <= len(packet) - 4:
        qblock = packet[qstart:qend]
        checks.need(qblock[5] == row.get("qmap_method"), f"{label}: row QM87 method matches packet")
        checks.need(row.get("qmap_method") == (2 if row.get("key") else 6),
                    f"{label}: key run-map 2 / P inherited map 6")
        checks.need(zlib.crc32(qblock[:-4]) == struct.unpack_from(">I", qblock, len(qblock)-4)[0],
                    f"{label}: QM87 CRC32")
    checks.need(0 <= generation <= 0xFFFFFFFFFFFFFFFF, f"{label}: generation field range")
    # CS88 carries generation in its 64-bit header field; there is no epoch
    # field. The direct ledger must not claim the CU66 upstream epoch 25 here.
    checks.need("epoch" not in row, f"{label}: no invented CS88 wire epoch field")


def verify_container_file(checks: Checks, attempt: Path, artifact_names: set[str]):
    name = "container-inspect-sanitized.json"
    checks.need(name in artifact_names, "sanitized Docker inspect artifact is ledger-bound")
    checks.need("container-inspect.json" not in artifact_names,
                "no unsanitized Docker inspect artifact retained")
    p = attempt / name
    if not p.is_file():
        return None
    item = load_json(p)
    allowed = {"Id", "Image", "Name", "State", "Mounts", "HostConfig"}
    checks.need(set(item) == allowed, "container inspect stores only approved top-level fields")
    checks.need(set(item.get("State", {})) == {"Running"}, "container state stores Running only")
    checks.need(all(set(m) <= {"Source", "Destination", "Type", "RW"} for m in item.get("Mounts", [])),
                "container mounts store only approved fields")
    checks.need(set(item.get("HostConfig", {})) == {"Memory", "NanoCpus", "CpusetCpus"},
                "container host config stores only resource fields")
    return item


def source_frames(checks: Checks):
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = load_json(MANIFEST_PATH)
    clips = {item["clip_id"]: item for item in manifest["clips"]}
    hashes = {}
    for clip_id, clip in clips.items():
        path = MANIFEST_PATH.parent / clip["npz_path"]
        checks.need(sha_file(path) == clip["npz_sha256"], f"{clip_id}: frozen V98 source NPZ hash")
        with np.load(path, allow_pickle=False) as npz:
            rgb = npz[clip.get("rgb_key", "rgb")]
            checks.need(rgb.dtype == np.uint8 and rgb.shape == (30, 480, 720, 3),
                        f"{clip_id}: frozen V98 RGB shape/dtype")
            actual = [sha_bytes(np.ascontiguousarray(frame).tobytes()) for frame in rgb]
        checks.need(actual == clip["frame_sha256"], f"{clip_id}: every source frame matches V98 manifest")
        hashes[clip_id] = actual
    return manifest_bytes, manifest, clips, hashes


def distributions(rows: list[dict], field: str) -> dict:
    values = [float(row[field]) for row in rows]
    ordered = sorted(values)
    return {"n": len(values), "min_ms": min(values), "median_ms": statistics.median(values),
            "mean_ms": statistics.fmean(values),
            "p95_nearest_rank_ms": ordered[(95 * len(values) + 99) // 100 - 1],
            "max_ms": max(values)}


def phase_distributions(rows: list[dict]) -> dict:
    names = tuple(rows[0]["phases"])
    result = {}
    for name in names:
        values = [float(row["phases"][name]) for row in rows]
        ordered = sorted(values)
        result[name] = {"n": len(values), "min_ms": min(values),
                        "median_ms": statistics.median(values), "mean_ms": statistics.fmean(values),
                        "p95_nearest_rank_ms": ordered[(95 * len(values) + 99) // 100 - 1],
                        "max_ms": max(values)}
    return result


def check_distribution(checks: Checks, actual: list[dict], field: str, reported: dict,
                       label: str, *, key: str | None = None):
    values = [float(row[field] if key is None else row[key][field]) for row in actual]
    ordered = sorted(values)
    expected = {"n": len(values), "min": min(values), "median": statistics.median(values),
                "p95_nearest_rank": ordered[(95 * len(values) + 99) // 100 - 1], "max": max(values)}
    for metric, expected_value in expected.items():
        observed = reported.get(metric)
        if metric == "n":
            checks.need(observed == expected_value, f"{label}: {metric} recount")
        else:
            checks.need(math.isclose(float(observed if observed is not None else float("nan")),
                                     float(expected_value), rel_tol=1e-10, abs_tol=1e-9),
                        f"{label}: {metric} recount")
    return values


def audit(index_path: Path, checks: Checks) -> dict:
    manifest_bytes, manifest, clips, frame_hashes = source_frames(checks)
    index_path = index_path.resolve(strict=True)
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes)
    report_path = (ROOT / index["attempt_json"]).resolve(strict=True)
    report_bytes = report_path.read_bytes()
    checks.need(sha_bytes(report_bytes) == index.get("sha256"), "direct index binds exact report hash")
    report = json.loads(report_bytes)
    # The direct runner's immutable index names results.json; the attempt root
    # is its containing directory (unlike the older fresh campaign schema).
    attempt = report_path.parent.resolve(strict=True)
    checks.need(attempt.is_dir(), "direct attempt directory exists")
    checks.need(report.get("schema") == "v99-direct-fresh-q16-CS88-v1", "direct report schema")
    checks.need(report.get("status") == "PASS_DIRECT_FRESH_NATIVE_CS88_EXACT", "direct campaign passed")
    checks.need("error" not in report, "passing report contains no failed validation/error field")
    checks.need(report.get("physical_30fps_proven") is False and
                report.get("capture_to_display_measured") is False,
                "report excludes physical throughput and capture/display claims")
    checks.need(report.get("historical_coefficients_as_input") is False,
                "report says historical coefficients were not encoder input")
    checks.need(report.get("source_manifest_sha256") == sha_bytes(manifest_bytes),
                "direct report binds frozen V98 manifest")
    checks.need(report.get("selected_control_report_sha256") == sha_file(CONTROL_PATH),
                "direct report binds selected native-CS88 control report")
    checks.need(report.get("selected_control_report") == str(CONTROL_PATH.resolve()),
                "direct report identifies selected control report")

    control = load_json(CONTROL_PATH)
    control_frames_path = CONTROL_PATH.parent / "frames.jsonl"
    control_frames_bytes = control_frames_path.read_bytes()
    checks.need(sha_bytes(control_frames_bytes) == report.get("selected_control_ledger_sha256"),
                "direct report binds selected control frames ledger")
    control_rows = {}
    for line in control_frames_bytes.splitlines():
        row = json.loads(line)
        if row.get("quant_scale") == 16:
            control_rows[(row["clip_id"], row["frame_id"])] = row
    checks.need(len(control_rows) == REAL_FRAMES, "selected q16 control has 120 unique real identities")

    # Verify pinned source files and their immutable copies. Also inspect only
    # the one deliberately sanitized Docker metadata file.
    pins = report.get("source_sha256", {})
    pin_mismatches = []
    for relative, expected in pins.items():
        snap = attempt / "sources" / relative
        checks.need(snap.is_file() and sha_file(snap) == expected, f"source snapshot hash: {relative}")
        current = ROOT / relative
        if not current.is_file() or sha_file(current) != expected:
            pin_mismatches.append(relative)
    checks.need(bool(pins), "direct report has source pins")
    direct_source_rel = "experiments/python-gamebub-v99/encoder/direct_cs88.py"
    direct_snap = attempt / "sources" / direct_source_rel
    if direct_snap.is_file():
        direct_source = direct_snap.read_text(encoding="utf-8")
        checks.need("All historical/control data" in direct_source and
                    "verification block after the actual packet is ready" in direct_source,
                    "pinned direct sender documents control-only verification boundary")
        checks.need(direct_source.find("packet, counts, work, chunks") < direct_source.find("if control_row is not None:"),
                    "packet construction precedes authoritative control packet comparison")
        checks.need("control_row['coefficients']" not in direct_source and
                    'control_row["coefficients"]' not in direct_source and
                    "control_row.get('coefficients')" not in direct_source,
                    "direct sender does not read historical coefficients from control rows")

    artifact_hashes = report.get("artifact_sha256", {})
    actual_hashes = {}
    for path in sorted(attempt.rglob("*")):
        if not path.is_file() or path == report_path:
            continue
        actual_hashes[path.relative_to(attempt).as_posix()] = sha_file(path)
    checks.need(actual_hashes == artifact_hashes,
                "report artifact ledger exactly matches all retained artifacts")
    sanitized = verify_container_file(checks, attempt, set(artifact_hashes))
    if sanitized is not None:
        checks.need(sanitized.get("Id") == control.get("container", {}).get("id") and
                    sanitized.get("Image") == control.get("container", {}).get("image_id"),
                    "sanitized container identity matches selected control container")
    checks.need(all("Config" not in key and key not in {"Env", "Labels", "Cmd"}
                    for key in report.keys()), "report top-level contains no container Config/env/labels/cmd fields")

    cases = report.get("cases", [])
    checks.need(len(cases) == 4, "direct campaign has four real 30-frame cases")
    rows_by_case: dict[str, list[dict]] = {}
    totals = {"real_attempts": 0, "real_accepted": 0, "real_packet_bytes": 0,
              "native_ack_rows": 0, "synthetic_attempts": 0, "synthetic_accepted": 0}
    for case in cases:
        clip_tag = case["clip_id"]
        clip_id = clip_tag.removesuffix("-q16")
        checks.need(clip_id in clips, f"{clip_tag}: clip exists in frozen V98 manifest")
        if clip_id not in clips:
            continue
        rows_file = attempt / "frames.jsonl"
        checks.need(rows_file.is_file(), f"{clip_tag}: direct frame ledger exists")
        rows = [json.loads(line) for line in rows_file.read_text().splitlines()
                if line and json.loads(line).get("clip_id") == clip_tag]
        rows_by_case[clip_tag] = rows
        checks.need(len(rows) == 30 and case.get("input_frames") == 30,
                    f"{clip_tag}: exactly 30 direct rows")
        checks.need(case.get("accepted_frames") == len(rows) and
                    case.get("all_inputs_admitted") is True and case.get("complete_30frame_clip") is True,
                    f"{clip_tag}: all real frames acknowledged")
        checks.need(case.get("actual_packets_equal_authoritative_control") is True,
                    f"{clip_tag}: case packet parity flag")
        accepted_last = None
        generations = []
        for fid, row in enumerate(rows):
            label = f"{clip_tag}/frame-{fid}"
            checks.need(row.get("frame_id") == fid and row.get("clip_id") == clip_tag,
                        f"{label}: ledger identity")
            expected_source = frame_hashes[clip_id][fid]
            checks.need(row.get("source_rgb_sha256") == expected_source,
                        f"{label}: source RGB frame hash matches V98 manifest")
            checks.need(row.get("source_npz_sha256") == clips[clip_id]["npz_sha256"],
                        f"{label}: source NPZ pin")
            checks.need(row.get("accepted") is True and row.get("ack_verified") is True,
                        f"{label}: native ACK accepted")
            packet_path = artifact_path(attempt, row["packet_path"])
            packet = packet_path.read_bytes()
            checks.need(len(packet) == row.get("packet_bytes") <= CAP,
                        f"{label}: exact wire byte accounting/cap")
            checks.need(sha_bytes(packet) == row.get("packet_sha256"), f"{label}: packet SHA-256")
            checks.need(row.get("actual_packet_equal_control") is True,
                        f"{label}: sender packet equals selected q16 control flag")
            control_key = (clip_tag, fid)
            ctrl = control_rows.get(control_key)
            checks.need(ctrl is not None, f"{label}: matching control ledger row exists")
            if ctrl is not None:
                ctrl_packet = artifact_path(CONTROL_PATH.parent, ctrl["packet_path"]).read_bytes()
                checks.need(row.get("control_packet_sha256") == ctrl.get("packet_sha256") and
                            sha_bytes(ctrl_packet) == ctrl.get("packet_sha256") and
                            packet == ctrl_packet,
                            f"{label}: packet bytes/hash exactly match q16 control")
            should_key = fid == 0
            should_ref = 0xFFFFFFFF if should_key else fid - 1
            checks.need(row.get("key") is should_key and row.get("reference_id") == should_ref,
                        f"{label}: frame uses only prior native-ACKed reference")
            verify_cs88_packet(checks, packet, row, label)
            decoded = row.get("native_decoded", {})
            checks.need(decoded.get("accepted") is True and decoded.get("replayed") is False,
                        f"{label}: native receiver exact ACK receipt")
            checks.need(decoded.get("fid") == fid and decoded.get("generation") == row.get("generation") and
                        decoded.get("wire_bytes") == len(packet),
                        f"{label}: native ACK identity/generation/bytes")
            expected_generation = fid + 1
            checks.need(row.get("generation") == expected_generation,
                        f"{label}: per-context generation advances after ACK")
            generations.append(row.get("generation"))
            ack_ms = row.get("native_ack_roundtrip_ms")
            checks.need(isinstance(ack_ms, (int, float)) and ack_ms >= 0,
                        f"{label}: separately recorded native ACK duration")
            expected = row.get("expected", {})
            for field in ("canonical_sha256", "coefficient_sha256", "hud_sha256", "root", "seal", "display_sha256"):
                checks.need(decoded.get(field) == expected.get(field),
                            f"{label}: native decoded {field} exact comparison")
            totals["real_attempts"] += 1
            totals["real_accepted"] += int(row.get("accepted") is True)
            totals["real_packet_bytes"] += len(packet)
            totals["native_ack_rows"] += 1
        checks.need(generations == list(range(1, 31)), f"{clip_tag}: sequential generation fence")
        # Recount timing distributions from rows and compare the report's
        # packet-ready and phase summaries without treating them as FPS.
        for field in ("packet_ready_ms", "native_ack_roundtrip_ms"):
            reported = case.get(field, {})
            check_distribution(checks, rows, field, reported, f"{clip_tag}: {field}")
        for phase_name in rows[0]["phases"]:
            values = [float(r["phases"][phase_name]) for r in rows]
            ordered = sorted(values)
            expected_phase = {"n": len(values), "min": min(values), "median": statistics.median(values),
                              "p95_nearest_rank": ordered[(95 * len(values) + 99) // 100 - 1],
                              "max": max(values)}
            reported_phase = case.get("phases", {}).get(phase_name, {})
            for metric in ("n", "min", "median", "p95_nearest_rank", "max"):
                if metric == "n":
                    checks.need(reported_phase.get(metric) == expected_phase[metric],
                                f"{clip_tag}: phase {phase_name} {metric} recount")
                    continue
                checks.need(math.isclose(float(reported_phase.get(metric, float("nan"))),
                                         float(expected_phase[metric]), rel_tol=1e-10, abs_tol=1e-9),
                            f"{clip_tag}: phase {phase_name} {metric} recount")
        checks.need(case.get("packet_bytes") == sum(r["packet_bytes"] for r in rows),
                    f"{clip_tag}: complete wire byte total recount")
        checks.need(case.get("max_packet_bytes") == max(r["packet_bytes"] for r in rows),
                    f"{clip_tag}: maximum packet bytes recount")

    # The runner also executes 32 deterministic synthetic inputs to exercise a
    # P frame that references key 30 across the periodic key boundary.
    synthetic_case = report.get("synthetic_cross_key_control", {})
    syn_path = artifact_path(attempt, synthetic_case["ledger_path"])
    syn_rows = [json.loads(line) for line in syn_path.read_text().splitlines() if line]
    checks.need(len(syn_rows) == SYNTHETIC_FRAMES and synthetic_case.get("input_frames") == SYNTHETIC_FRAMES,
                "synthetic control has 32 frames")
    checks.need(synthetic_case.get("native_exact_ACKs") == SYNTHETIC_FRAMES,
                "synthetic control has 32 native exact ACKs")
    checks.need(synthetic_case.get("key_ids") == [0, 30] and syn_rows[31].get("reference_id") == 30,
                "synthetic key0/key30 and P31 references ACKed key30")
    check_distribution(checks, syn_rows, "packet_ready_ms", synthetic_case.get("packet_ready_ms", {}),
                       "synthetic: packet-ready distribution")
    for fid, row in enumerate(syn_rows):
        label = f"synthetic/frame-{fid}"
        packet = artifact_path(attempt, row["packet_path"]).read_bytes()
        rgb = np.full((480, 720, 3), 80, np.uint8)
        x = 210 + fid * 3
        rgb[180:228, x:x+48] = (30 + fid * 3, 180, 220 - fid * 2)
        for bit in range(5):
            rgb[52:60, 24+bit*12:32+bit*12] = ((240, 20, 80) if fid & (1 << bit) else (20, 210, 30))
        synthetic_sha = sha_bytes(rgb.tobytes())
        checks.need(row.get("frame_id") == fid and row.get("source_rgb_sha256") == synthetic_sha,
                    f"{label}: deterministic fresh RGB identity/hash")
        checks.need(row.get("accepted") is True and row.get("ack_verified") is True and
                    row.get("native_decoded", {}).get("accepted") is True,
                    f"{label}: native ACK accepted")
        expected_key = fid in (0, 30)
        expected_ref = 0xFFFFFFFF if expected_key else (30 if fid == 31 else fid - 1)
        checks.need(row.get("key") is expected_key and row.get("reference_id") == expected_ref,
                    f"{label}: synthetic key/reference chain")
        checks.need(row.get("qmap_method") == (2 if expected_key else 6),
                    f"{label}: synthetic key QM2/P QM6 selection")
        checks.need(row.get("generation") == fid + 1 and
                    row.get("native_decoded", {}).get("generation") == fid + 1,
                    f"{label}: synthetic generation fence")
        verify_cs88_packet(checks, packet, row, label)
        totals["synthetic_attempts"] += 1
        totals["synthetic_accepted"] += int(row.get("ack_verified") is True)

    checks.need(report.get("frames") == REAL_FRAMES and report.get("actual_packets_equal_control") == REAL_FRAMES,
                "top-level real frame and exact-packet parity counts")
    checks.need(report.get("native_exact_ACKs") == REAL_FRAMES and
                report.get("complete_120frame_campaign") is True,
                "top-level complete 120-frame native ACK status")
    real_ready = [r for rows in rows_by_case.values() for r in rows]
    ready_times = [float(r["packet_ready_ms"]) for r in real_ready]
    ordered_ready = sorted(ready_times)
    within_budget = sum(value <= (1000 / 30) for value in ready_times)
    real_packet_summary = {
        "n": len(ready_times),
        "min_ms": min(ready_times) if ready_times else None,
        "median_ms": statistics.median(ready_times) if ready_times else None,
        "mean_ms": statistics.fmean(ready_times) if ready_times else None,
        "p95_nearest_rank_ms": ordered_ready[(95 * len(ordered_ready) + 99) // 100 - 1] if ordered_ready else None,
        "max_ms": max(ready_times) if ready_times else None,
        "packet_ready_at_or_below_33_333ms": within_budget,
        "packet_ready_percent_at_or_below_33_333ms": (100 * within_budget / len(ready_times)) if ready_times else None,
        "per_real_case": {
            case_id: {
                "packet_ready_ms": distributions(rows, "packet_ready_ms"),
                "native_ack_roundtrip_ms": distributions(rows, "native_ack_roundtrip_ms"),
                "phases_ms": phase_distributions(rows),
                "within_33_333ms_count": sum(float(r["packet_ready_ms"]) <= (1000 / 30) for r in rows),
                "within_33_333ms_percent": 100 * sum(float(r["packet_ready_ms"]) <= (1000 / 30) for r in rows) / len(rows),
            } for case_id, rows in rows_by_case.items()
        },
        "interpretation": "unpaced host CPU packet-preparation diagnostic; not FPS, capture-to-display latency, or target-device timing",
    }
    # The run report's aggregate arithmetic is independently recounted over
    # all 120 real inputs and separately over each named phase.
    check_distribution(checks, real_ready, "packet_ready_ms", report.get("packet_ready_ms", {}),
                       "campaign: packet-ready distribution")
    for phase_name in real_ready[0]["phases"]:
        values = [float(row["phases"][phase_name]) for row in real_ready]
        ordered = sorted(values)
        expected_phase = {"n": len(values), "min": min(values), "median": statistics.median(values),
                          "p95_nearest_rank": ordered[(95 * len(values) + 99) // 100 - 1],
                          "max": max(values)}
        observed = report.get("phases", {}).get(phase_name, {})
        for metric, expected_value in expected_phase.items():
            if metric == "n":
                checks.need(observed.get(metric) == expected_value,
                            f"campaign: phase {phase_name} {metric} recount")
            else:
                checks.need(math.isclose(float(observed.get(metric, float("nan"))),
                                         float(expected_value), rel_tol=1e-10, abs_tol=1e-9),
                            f"campaign: phase {phase_name} {metric} recount")
    totals["total_native_exact_ACKs"] = totals["native_ack_rows"] + totals["synthetic_accepted"]
    return {
        "schema": "v99-direct-independent-audit-v1",
        "status": "PASS_DIRECT_SOFTWARE_LEDGER" if not checks.failures else "FAIL",
        "auditor": str(Path(__file__).relative_to(ROOT)),
        "auditor_sha256": sha_file(Path(__file__)),
        "campaign_index": str(index_path.relative_to(ROOT)),
        "campaign_index_sha256": sha_bytes(index_bytes),
        "campaign_report": str(report_path.relative_to(ROOT)),
        "campaign_report_sha256": sha_bytes(report_bytes),
        "selected_control_report_sha256": sha_file(CONTROL_PATH),
        "selected_control_ledger_sha256": sha_bytes(control_frames_bytes),
        "source_manifest_sha256": sha_bytes(manifest_bytes),
        "source_pins": {"count": len(pins), "current_mismatches": pin_mismatches,
                        "current_worktree_matches_all": not pin_mismatches},
        "recount": {**totals, "case_count": len(cases), "container_artifact_filtered": sanitized is not None},
        "packet_ready_summary": real_packet_summary,
        "timing_scope": {
            "packet_ready": "fresh RGB through complete CS88 packet construction; excludes verification, golden rendering/hashing, packet I/O and native ACK",
            "BR88": "includes persistent native helper encode plus self-decode exact check and Docker stdio IPC",
            "native_ack": "request through full independent native reconstruction/hash/publication response; separate from sender CPU and not FPGA decode timing",
            "physical_fps": False,
        },
        "validation_fields": {
            "campaign_error_field_absent": "error" not in report,
            "direct_failed_rows": sum(1 for rows in rows_by_case.values() for row in rows if row.get("accepted") is not True),
            "native_receiver_rejection_rows": sum(1 for rows in rows_by_case.values() for row in rows
                                                  if row.get("native_decoded", {}).get("accepted") is not True),
            "explicit_child_return_codes_in_report": [cmd.get("exit_code") for cmd in report.get("commands", [])
                                                       if isinstance(cmd, dict) and "exit_code" in cmd],
            "note": "runner uses checked Docker commands and receiver close() raises on nonzero exit; direct report does not retain an explicit child exit-code field",
        },
        "limitations": [
            "No encoder/runner/metrics import and no new decoder implementation; exact packet-byte parity reuses the authoritative control packet as a byte oracle.",
            "The independent C2/BR88 coefficient reader evidence is tracked separately; byte equality here is not a new coefficient-reader proof.",
            "The four real inputs are existing V98 decoded video/composited sources, not raw 30-fps gameplay captures.",
            "Packet-ready CPU timing is unpaced host preparation and does not establish 30 FPS or target throughput.",
            "No FPGA implementation, hardware frame-rate, or validated decode-under-10ms result is claimed.",
        ],
        "checks": {"count": checks.count, "failed": len(checks.failures)},
        "failures": checks.failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    checks = Checks()
    try:
        result = audit(args.index, checks)
    except Exception as exc:
        result = {"schema": "v99-direct-independent-audit-v1", "status": "FAIL",
                  "auditor": str(Path(__file__).relative_to(ROOT)),
                  "auditor_sha256": sha_file(Path(__file__)),
                  "checks": {"count": checks.count, "failed": len(checks.failures) + 1},
                  "failures": checks.failures + [f"fatal audit error: {type(exc).__name__}: {exc}"]}
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": result.get("checks"),
                      "failures": result.get("failures", [])[:12], "output": str(output)}, indent=2))
    return 0 if result["status"] == "PASS_DIRECT_SOFTWARE_LEDGER" else 1


if __name__ == "__main__":
    raise SystemExit(main())

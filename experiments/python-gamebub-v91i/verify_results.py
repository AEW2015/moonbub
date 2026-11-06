#!/usr/bin/env python3
"""Independently audit V91i1 packet vectors and retained RTL admission receipts.

This parser is deliberately separate from admission-model.py. It validates the
outer CS88 envelope and structural descriptors only; it never decodes AB38 or
BR88 payloads or claims consumer dispatch, frame acceptance, or publication.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "experiments/python-gamebub-v91i"
AREA = ROOT / "fpga/experiments/cu66-v91i"
INDEX = MODEL / "vectors/index.json"
CAP = 49152
MASK_SHA = "e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5"
BASELINE = "f4428dcda2b039f815495d50500695046ce7d4a0"
TILES = (5400, 1350, 1350)
ERROR_TEXT = {
    0: "accepted structural receipt", 1: "size", 2: "input framing",
    3: "outer CRC", 4: "unsupported native profile", 5: "header bounds",
    6: "identity/stale", 7: "reference/cache", 8: "mode map",
    9: "QM CRC", 10: "QM format/run", 11: "QM required count",
    12: "chunk count", 13: "chunk span/coverage", 14: "unknown chunk magic",
}


class Reject(Exception):
    def __init__(self, code: int):
        self.code = code


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return digest(path.read_bytes())


def read_json(path: Path):
    return json.loads(path.read_text())


def frozen_mask() -> tuple[int, ...]:
    """Extract the fixed hidden profile from frozen native constants as data."""
    text = (ROOT / "experiments/cu66-native-v69/generated_constants.hpp").read_text()
    values = []
    for array, n in (("SAFE0", 5400), ("SAFE1", 1350), ("SAFE2", 1350)):
        found = re.search(rf"{array}\[{n}\]=\{{([^}}]+)\}};", text)
        if not found:
            raise ValueError(f"missing fixed mask array {array}")
        row = [int(x) for x in found.group(1).split(",")]
        if len(row) != n or any(x not in (0, 1) for x in row):
            raise ValueError(f"invalid fixed mask array {array}")
        values.extend(row)
    if len(values) != 8100 or digest(bytes(values)) != MASK_SHA:
        raise ValueError("fixed hidden mask identity mismatch")
    return tuple(values)


def active_qcells(modes: tuple[int, ...]) -> int:
    cells = bytearray(1350)
    for t, mode in enumerate(modes):
        if mode != 2:
            continue
        if t < TILES[0]:
            y, x = divmod(t, 90)
            cells[(y // 2) * 45 + x // 2] = 1
        else:
            cells[(t - TILES[0]) % 1350] = 1
    return sum(cells)


def modes_from_group(packet: bytes, start: int, count: int, key: bool,
                     method: int, hidden: tuple[int, ...]) -> tuple[int, ...]:
    body = packet[start:start + count]
    if key:
        if method != 0 or count:
            raise Reject(8)
        return tuple(1 if bit else 2 for bit in hidden)
    if method != 3:
        raise Reject(4)
    position = 0
    result = [1] * 8100
    base = 0
    for plane_n in TILES:
        for first in range(0, plane_n, 16):
            visible = [base + k for k in range(first, min(first + 16, plane_n))
                       if not hidden[base + k]]
            if position + 2 > count * 8:
                raise Reject(8)
            tag = (((body[position // 8] >> (7 - position % 8)) & 1) << 1)
            position += 1
            tag |= (body[position // 8] >> (7 - position % 8)) & 1
            position += 1
            if not visible:
                if tag != 3:
                    raise Reject(8)
                continue
            if tag == 3:
                raise Reject(8)
            if tag in (0, 1):
                for tile in visible:
                    result[tile] = 2 if tag else 0
            else:
                saw_zero = saw_one = False
                for tile in visible:
                    if position >= count * 8:
                        raise Reject(8)
                    bit = (body[position // 8] >> (7 - position % 8)) & 1
                    position += 1
                    saw_zero |= bit == 0
                    saw_one |= bit == 1
                    result[tile] = 2 if bit else 0
                if not (saw_zero and saw_one):
                    raise Reject(8)
        base += plane_n
    if position > count * 8 or (position + 7) // 8 != count:
        raise Reject(8)
    while position < count * 8:
        if (body[position // 8] >> (7 - position % 8)) & 1:
            raise Reject(8)
        position += 1
    return tuple(result)


def qmap(packet: bytes, start: int, size: int, modes: tuple[int, ...],
         key: bool, ref: dict) -> tuple[int, int]:
    if size < 16 or size > 354:
        raise Reject(10)
    block = packet[start:start + size]
    if zlib.crc32(block[:-4]) & 0xFFFFFFFF != int.from_bytes(block[-4:], "big"):
        raise Reject(9)
    magic = block[:4]
    version = block[4]
    method = block[5]
    cells = int.from_bytes(block[6:8], "big")
    body_size = int.from_bytes(block[8:10], "big")
    required = int.from_bytes(block[10:12], "big")
    if magic != b"QM87" or version != 1 or cells != 1350 or len(block) != 16 + body_size:
        raise Reject(10)
    if method not in (2, 6):
        raise Reject(4)
    expected = active_qcells(modes)
    if required != expected:
        raise Reject(11)
    body = block[12:-4]
    if method == 6:
        # Match the RTL's semantic precedence: required-count binding precedes
        # inherited-cache eligibility, which precedes method-6 bodylessness.
        if key or not ref["valid"] or not ref["qcache_valid"]:
            raise Reject(7)
        if body_size:
            raise Reject(10)
    else:
        total = 0
        for byte in body:
            value, run = byte >> 6, (byte & 63) + 1
            if value == 3 or total + run > 1350:
                raise Reject(10)
            total += run
        if total != 1350:
            raise Reject(10)
    return method, required


def parse_outer(packet: bytes, ref: dict, hidden: tuple[int, ...]) -> tuple[int, dict | None]:
    """A separately written byte cursor for the bounded outer structure."""
    if len(packet) < 132 or len(packet) > CAP:
        return 1, None
    if zlib.crc32(packet[:-4]) & 0xFFFFFFFF != int.from_bytes(packet[-4:], "big"):
        return 3, None
    if packet[:4] != b"CS88" or packet[4] != 1 or packet[6] != 16:
        return 4, None
    flags, mode_kind = packet[5], packet[7]
    if flags > 1:
        return 5, None
    key = flags == 1
    fid = int.from_bytes(packet[8:12], "big")
    refid = int.from_bytes(packet[12:16], "big")
    generation = int.from_bytes(packet[16:24], "big")
    width, height, block, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, map_len, q_len, hud_len, residual_len = struct.unpack_from(">IIIII", packet, 32)
    if block != 32 or cap != 65536 or (key and mode_kind != 0) or (not key and mode_kind != 3):
        return 4, None
    if (width, height, reserved) != (720, 480, 0) or map_len > 976 or not 16 <= q_len <= 354 or not 110 <= hud_len <= CAP:
        return 5, None
    if packet[116:128] != bytes(12):
        return 5, None
    if 128 + map_len + q_len + residual_len + hud_len + 4 != len(packet):
        return 5, None
    if fid == 0xFFFFFFFF or generation == 0 or (ref["valid"] and (fid <= ref["fid"] or generation <= ref["generation"])):
        return 6, None
    if (key and refid != 0xFFFFFFFF) or (not key and (not ref["valid"] or refid != ref["fid"])):
        return 7, None
    try:
        modes = modes_from_group(packet, 128, map_len, key, mode_kind, hidden)
        qm, needed = qmap(packet, 128 + map_len, q_len, modes, key, ref)
    except Reject as error:
        return error.code, None
    residual_start = 128 + map_len + q_len
    residual_end = residual_start + residual_len
    cursor = residual_start
    planes = []
    for axis, tiles in enumerate(TILES):
        first = sum(TILES[:axis])
        blocks_needed = sum(mode == 2 for mode in modes[first:first + tiles])
        if cursor + 4 > residual_end:
            return 13, None
        number = int.from_bytes(packet[cursor:cursor + 4], "big")
        cursor += 4
        expected_chunks = (blocks_needed + 65535) // 65536
        if number != expected_chunks:
            return 12, None
        for chunk in range(number):
            if cursor + 8 > residual_end:
                return 13, None
            blocks = int.from_bytes(packet[cursor:cursor + 4], "big")
            byte_count = int.from_bytes(packet[cursor + 4:cursor + 8], "big")
            cursor += 8
            expected_blocks = min(65536, blocks_needed - chunk * 65536)
            if blocks != expected_blocks or blocks == 0 or not 46 <= byte_count <= 46 + 128 * blocks:
                return 13, None
            if cursor + byte_count > residual_end:
                return 13, None
            magic = packet[cursor:cursor + 4]
            if magic == b"AB38":
                entropy_type = 1
            elif magic == b"BR88":
                entropy_type = 2
            else:
                return 14, None
            planes.append(dict(axis=axis, blocks=blocks, offset=cursor,
                               length=byte_count, entropy_type=entropy_type))
            cursor += byte_count
    if cursor != residual_end:
        return 13, None
    return 0, dict(fid=fid, refid=refid, generation=generation, key=key,
                   mode_bytes=map_len, qmap_bytes=q_len, qmap_method=qm,
                   qmap_required=needed, hud_bytes=hud_len, data_bytes=residual_len,
                   hud_offset=residual_end, planes=planes)


def check_expectation(entry: dict, actual_code: int, receipt: dict | None) -> None:
    expected_code = entry["expected_error"]
    if actual_code != expected_code:
        raise AssertionError(f"{entry['id']}: independent parser error {actual_code}, expected {expected_code}")
    expected = entry.get("expected")
    if expected is None:
        if receipt is not None:
            raise AssertionError(f"{entry['id']}: unexpected structural receipt")
        return
    if receipt is None:
        raise AssertionError(f"{entry['id']}: missing independent descriptor")
    for name in ("fid", "refid", "generation", "key", "mode_bytes", "qmap_bytes",
                 "hud_bytes", "data_bytes"):
        if receipt[name] != expected[name]:
            raise AssertionError(f"{entry['id']}: expected descriptor {name} mismatch")
    if receipt["qmap_method"] != expected["qmap_method"] or receipt["qmap_required"] != expected["qmap_required"]:
        raise AssertionError(f"{entry['id']}: qmap descriptor mismatch")
    if receipt["hud_offset"] != expected["hud_offset"]:
        raise AssertionError(f"{entry['id']}: HUD structural offset mismatch")
    if receipt["planes"] != expected["planes"]:
        raise AssertionError(f"{entry['id']}: plane descriptors mismatch")


def verify_vectors(index: dict, hidden: tuple[int, ...]) -> dict:
    entries = index["entries"]
    for source, expected in index["source_pins"].items():
        if file_sha(ROOT / source) != expected:
            raise AssertionError(f"source pin mismatch: {source}")
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)) or not entries:
        raise AssertionError("vector identifiers are empty or duplicated")
    actual = [e for e in entries if e["class_"] == "retained_actual_fixture"]
    v88 = [e for e in actual if e["origin"] == "v88"]
    v90 = [e for e in actual if e["origin"] == "v90"]
    if (len(v88), len(v90), len(actual)) != (35, 16, 51):
        raise AssertionError("retained fixture inventory is not 35 V88 + 16 V90 rows")
    if index["source_inventory"]["retained_fixture_rows"] != 51:
        raise AssertionError("index fixture inventory count mismatch")
    v88_result = read_json(ROOT / "experiments/python-gamebub-v88/wire/results.json")
    v88_attempt = ROOT / v88_result["selected_report"]
    v88_history_rows = [json.loads(line) for line in (v88_attempt.parent / "frames.jsonl").read_text().splitlines()]
    v88_history = {(r["cohort"], r["fid"]): r for r in v88_history_rows
                   if r["policy"] == "AB38_control"}
    admitted = rejected = over_budget = 0
    under_budget = 0
    per_error = {}
    for entry in entries:
        packet_path = ROOT / entry["packet_path"]
        packet = packet_path.read_bytes()
        if len(packet) != entry["packet_bytes"] or digest(packet) != entry["packet_sha256"]:
            raise AssertionError(f"{entry['id']}: vector bytes/hash mismatch")
        if entry["class_"] == "retained_actual_fixture":
            original = ROOT / entry["source_fixture_path"]
            original_bytes = original.read_bytes()
            if len(original_bytes) != entry["packet_bytes"] or digest(original_bytes) != entry["source_sha256"]:
                raise AssertionError(f"{entry['id']}: retained source fixture hash mismatch")
            if original_bytes != packet:
                raise AssertionError(f"{entry['id']}: retained packet changed while vectorizing")
            history = v88_history.get((entry["cohort"], entry["fid"]))
            if history is None or not history["decoded"]["accepted"]:
                raise AssertionError(f"{entry['id']}: missing actual accepted V88 source history")
            if history["decoded"]["fid"] != entry["fid"] or history["decoded"]["generation"] != int.from_bytes(packet[16:24], "big"):
                raise AssertionError(f"{entry['id']}: fixture identity/generation disagrees with V88 history")
            ref = entry["accepted_ref"]
            evidence = entry["accepted_ref_evidence"]
            if entry["fid"] == 0:
                if ref != dict(valid=False, fid=0, generation=0, qcache_valid=False) or evidence.get("kind") != "initial_cohort_state":
                    raise AssertionError(f"{entry['id']}: key snapshot not the initial cohort state")
            else:
                previous = v88_history.get((entry["cohort"], entry["fid"] - 1))
                if previous is None or not previous["decoded"]["accepted"]:
                    raise AssertionError(f"{entry['id']}: missing actual predecessor in V88 history")
                predecessor = previous["decoded"]
                expected_ref = dict(valid=True, fid=predecessor["fid"],
                                    generation=predecessor["generation"], qcache_valid=True)
                if ref != expected_ref:
                    raise AssertionError(f"{entry['id']}: accepted snapshot differs from actual predecessor")
                if (evidence.get("kind") != "actual_prior_accepted_history" or
                    evidence.get("accepted_fid") != predecessor["fid"] or
                    evidence.get("accepted_generation") != predecessor["generation"] or
                    evidence.get("current_generation") != history["decoded"]["generation"]):
                    raise AssertionError(f"{entry['id']}: accepted-reference evidence mismatch")
        elif entry["class_"] == "negative":
            source = ROOT / entry["source_fixture_path"]
            if file_sha(source) != entry["source_sha256"]:
                raise AssertionError(f"{entry['id']}: negative source fixture pin mismatch")
            mutation = entry.get("mutation", {})
            base = ROOT / mutation.get("base_packet", entry["source_fixture_path"])
            base_bytes = base.read_bytes()
            base_sha = mutation.get("base_sha256", entry["source_sha256"])
            if digest(base_bytes) != base_sha:
                raise AssertionError(f"{entry['id']}: negative mutation base hash mismatch")
            if not entry.get("negative_reason"):
                raise AssertionError(f"{entry['id']}: negative lacks mutation rationale")
            packet_crc_good = (zlib.crc32(packet[:-4]) & 0xFFFFFFFF) == int.from_bytes(packet[-4:], "big")
            if mutation.get("outer_crc_recomputed") and not packet_crc_good:
                raise AssertionError(f"{entry['id']}: marked repaired outer CRC is invalid")
            changed = mutation["changed"].lower()
            state_only = any(label in changed for label in ("accepted reference", "accepted snapshot", "external snapshot"))
            if state_only and packet != base_bytes:
                raise AssertionError(f"{entry['id']}: external-state mutation unexpectedly changed packet bytes")
            if not state_only and packet == base_bytes:
                raise AssertionError(f"{entry['id']}: packet mutation has no byte change")
            if any(label in changed for label in ("corrupt outer crc", "flip outer crc")) and packet_crc_good:
                raise AssertionError(f"{entry['id']}: outer-CRC corruption vector has valid CRC")
        elif entry["class_"] == "synthetic_structural_only":
            source = ROOT / entry["source_fixture_path"]
            if file_sha(source) != entry["source_sha256"]:
                raise AssertionError(f"{entry['id']}: synthetic ancestry fixture hash mismatch")
            if entry.get("claims") != "structural admission only; not full native-valid packet":
                raise AssertionError(f"{entry['id']}: synthetic scope fence missing")
        else:
            raise AssertionError(f"{entry['id']}: unknown vector class")
        code, receipt = parse_outer(packet, entry["accepted_ref"], hidden)
        check_expectation(entry, code, receipt)
        per_error[str(code)] = per_error.get(str(code), 0) + 1
        if entry["class_"] == "retained_actual_fixture":
            admitted += code == 0
            rejected += code != 0
            over_budget += code == 1
            under_budget += code == 0 and len(packet) <= CAP
        if entry["class_"] in ("retained_actual_fixture", "synthetic_structural_only"):
            disposition = "within_49152" if len(packet) <= CAP else "over_49152"
            if disposition != entry["packet_policy_disposition"]:
                raise AssertionError(f"{entry['id']}: packet budget disposition mismatch")
    unique_source = len({(e["cohort"], e["fid"]) for e in actual})
    if unique_source != index["source_inventory"]["unique_source_identities"]:
        raise AssertionError("unique source identity count disagrees with index")
    if under_budget + over_budget != len(actual) or rejected != over_budget:
        raise AssertionError("actual fixture byte-budget disposition totals mismatch")
    return dict(vector_rows=len(entries), retained_fixtures=len(actual), v88_fixtures=len(v88),
                v90_fixtures=len(v90), unique_source_frame_identities=unique_source,
                actual_admitted=admitted, actual_rejected=rejected,
                actual_within_budget_admitted=under_budget,
                actual_over_budget_rejections=over_budget, rows_by_independent_error=per_error,
                all_packets_independently_parsed=True,
                inner_entropy_payloads_decoded=False)


def attempt_files():
    selected = []
    wanted = (911101, 911102)
    for seed in wanted:
        candidates = []
        for report_path in sorted((AREA / "admission-attempts").glob("*/results.json")):
            report = read_json(report_path)
            if report.get("seed") != seed or report.get("status") != "PASS_RESTRICTED_CS88_STRUCTURAL_ADMISSION":
                continue
            if not all(file_sha(ROOT / name) == value for name, value in report["source_sha256"].items()):
                continue
            if not all(file_sha(MODEL / "vectors" / name) == value for name, value in report["vectors_sha256"].items()):
                continue
            candidates.append((report_path, report))
        if not candidates:
            raise AssertionError(f"no current-source passing strict RTL attempt for seed {seed}")
        selected.append(candidates[-1])
    return selected


def verify_attempt(path: Path, report: dict, index: dict, hidden: tuple[int, ...]) -> dict:
    out = path.parent
    if report.get("schema") != "cu66-v91i1-outer-admission-rtl-v1":
        raise AssertionError(f"unexpected RTL report schema: {path}")
    if report.get("seed") not in (911101, 911102):
        raise AssertionError(f"unexpected seed in {path}")
    if report.get("hardware_distinct_30fps_proven") or report.get("full_frame_decode_under10ms_proven") or report.get("full_frame_publication_timestamp") is not None:
        raise AssertionError("RTL report makes a forbidden end-to-end claim")
    # Every path/log in the attempt's artifact receipt is checked byte-for-byte.
    recorded = report["artifacts_sha256"]
    for name, expected in recorded.items():
        path_item = out / name
        if not path_item.is_file() or file_sha(path_item) != expected:
            raise AssertionError(f"attempt artifact hash mismatch: {path_item}")
    for source, expected in report["source_sha256"].items():
        live = ROOT / source
        snapshot = out / "sources" / source
        if file_sha(live) != expected or file_sha(snapshot) != expected:
            raise AssertionError(f"current/snapshotted source pin mismatch: {source}")
    for name, expected in report["vectors_sha256"].items():
        live = MODEL / "vectors" / name
        snapshot = out / "vectors" / name
        if file_sha(live) != expected or file_sha(snapshot) != expected:
            raise AssertionError(f"current/snapshotted vector pin mismatch: {name}")
    for command in report["commands"]:
        if command["exit_code"] != 0 or not (out / command["log"]).is_file():
            raise AssertionError(f"failed/missing command receipt in {path}")
    records = [json.loads(line) for line in (out / "simulation.jsonl").read_text().splitlines() if line]
    cases = [row for row in records if row.get("type") == "case"]
    directed = [row for row in records if row.get("type") == "directed"]
    verdicts = [row for row in records if row.get("type") == "verdict"]
    entries = index["entries"]
    if len(cases) != len(entries) or {r["id"] for r in cases} != {e["id"] for e in entries}:
        raise AssertionError(f"case identities/count differ from vectors in {path}")
    by_id = {e["id"]: e for e in entries}
    for row in cases:
        entry = by_id[row["id"]]
        if row.get("status") != "PASS" or row.get("seed") != report["seed"] or row.get("error") != entry["expected_error"]:
            raise AssertionError(f"RTL result mismatch for {row['id']} in {path}")
        receipt = row.get("receipt")
        exp = entry.get("expected")
        if entry["expected_error"]:
            if receipt is not None or row.get("receipt_count") != 0:
                raise AssertionError(f"rejected packet emitted receipt: {row['id']}")
        else:
            if receipt is None or row.get("receipt_count") != 1:
                raise AssertionError(f"positive packet receipt missing/duplicated: {row['id']}")
            for name in ("fid", "refid", "generation", "key", "mode_bytes", "qmap_bytes",
                         "hud_bytes", "data_bytes", "required_cells"):
                expected_name = "qmap_required" if name == "required_cells" else name
                if receipt[name] != exp[expected_name]:
                    raise AssertionError(f"RTL {name} mismatch for {row['id']}")
            if len(receipt["plane"]) != 3:
                raise AssertionError(f"wrong plane descriptor count for {row['id']}")
            for got, want in zip(receipt["plane"], exp["planes"]):
                for name in ("blocks", "offset", "length", "entropy_type"):
                    if got[name] != want[name]:
                        raise AssertionError(f"RTL plane {name} mismatch for {row['id']}")
        if row.get("stage_reads") != row.get("stage_responses"):
            raise AssertionError(f"stage response conservation failed for {row['id']}")
        if row.get("receipt_count", 0) > 1 or row.get("receipt_hold_cycles", 0) < 0:
            raise AssertionError(f"duplicate/invalid receipt accounting for {row['id']}")
    expected_directed = {
        "abort_queued_read", "reset_queued_read", "abort_registered_response", "reset_registered_response",
        "abort_held_receipt", "reset_held_receipt", "replacement_start_pending_response",
        "replacement_start_held_receipt", "early_input_last", "missing_input_last",
        "oversize_start_before_input", "undersize_start_before_input",
        "reference_snapshot_latched_every_case", "receipt_ready_backpressure_every_positive",
    }
    if {r.get("name") for r in directed} != expected_directed or any(r.get("status") != "PASS" for r in directed):
        raise AssertionError(f"directed cancel/stream checks differ in {path}")
    if len(verdicts) != 1 or verdicts[0].get("status") != "TEST_PASS" or verdicts[0].get("seed") != report["seed"]:
        raise AssertionError(f"missing strict test verdict in {path}")
    if verdicts[0].get("cases") != len(cases) or verdicts[0].get("negative_cases") != sum(bool(e["expected_error"]) for e in entries):
        raise AssertionError(f"test verdict totals mismatch in {path}")
    return dict(report=str(path.relative_to(ROOT)), report_sha256=file_sha(path), seed=report["seed"],
                case_rows=len(cases), admitted_rows=sum(e["expected_error"] == 0 for e in entries),
                rejected_rows=sum(e["expected_error"] != 0 for e in entries),
                directed_checks=len(directed), artifact_rows=len(recorded),
                source_hashes_current_and_snapshotted=True,
                vector_hashes_current_and_snapshotted=True,
                receipts_match_independent_parser=True)


def main() -> None:
    index = read_json(INDEX)
    mask = frozen_mask()
    vectors = verify_vectors(index, mask)
    selected = [verify_attempt(path, report, index, mask) for path, report in attempt_files()]
    # Existing V91h evidence is checked against its frozen parent revision.
    unchanged = {}
    for name in ("experiments/python-gamebub-v91h/summary.json",
                 "experiments/python-gamebub-v91h/audit.json", "docs/cu66-v91h/README.md"):
        current = file_sha(ROOT / name)
        frozen = hashlib.sha256(subprocess.check_output(["git", "show", f"{BASELINE}:{name}"], cwd=ROOT)).hexdigest()
        if current != frozen:
            raise AssertionError(f"retained V91h evidence changed: {name}")
        unchanged[name] = current
    result = dict(schema="cu66-v91i1-independent-admission-audit-v1", status="PASS",
                  independent_parser=Path(__file__).name, independent_parser_sha256=file_sha(Path(__file__)),
                  vector_index_sha256=file_sha(INDEX), vectors=vectors, selected_attempts=selected,
                  unchanged_v91h_evidence=unchanged,
                  scope="Outer CS88 framing/admission and structural descriptors only. AB38/BR88 internals, consumer dispatch, accepted-frame/reference commit, HUD semantics/hash, pixel decode/publication, hardware timing and FPS are outside this checkpoint.",
                  no_entropy_decode=True, no_job_dispatch=True, no_frame_acceptance_or_reference_commit=True,
                  no_publication_timestamp=True, full_frame_decode_under10ms_proven=False,
                  hardware_distinct_30fps_proven=False)
    (MODEL / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print("V91I1_INDEPENDENT_AUDIT_PASS", vectors["vector_rows"], "vectors", len(selected), "strict seeded RTL attempts")


if __name__ == "__main__":
    main()

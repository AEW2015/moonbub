#!/usr/bin/env python3
"""Independent V91i2 byte, placement, and retained RTL receipt audit.

This verifier deliberately does not import model.py or the V91i1 admission
model. It parses the wire bytes itself and uses the frozen strict BR88 reader
only as an entropy oracle.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
TILES = (5400, 1350, 1350)
BASES = (0, 5400, 6750)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text())


def frozen_hidden() -> tuple[int, ...]:
    text = (ROOT / "experiments/cu66-native-v69/generated_constants.hpp").read_text()
    result = []
    for name, count in (("SAFE0", 5400), ("SAFE1", 1350), ("SAFE2", 1350)):
        match = re.search(rf"{name}\[{count}\]=\{{([^}}]+)\}};", text)
        if not match:
            raise AssertionError(f"missing frozen profile array {name}")
        row = [int(x) for x in match.group(1).split(",")]
        if len(row) != count or any(x not in (0, 1) for x in row):
            raise AssertionError(f"bad frozen profile array {name}")
        result.extend(row)
    profile = bytes(result)
    assert len(result) == 8100
    assert digest(profile) == "e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5"
    return tuple(result)


class Bits:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def read(self) -> int:
        if self.pos >= 8 * len(self.data):
            raise AssertionError("truncated grouped mode bits")
        value = (self.data[self.pos >> 3] >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return value


def decode_operations(packet: bytes, mode_off: int, mode_len: int, key: bool,
                      mode_method: int, hidden: tuple[int, ...]) -> bytes:
    body = packet[mode_off:mode_off + mode_len]
    if key:
        assert mode_method == 0 and mode_len == 0
        return bytes(1 if flag else 2 for flag in hidden)
    assert mode_method == 3
    bits = Bits(body)
    ops = [1] * 8100
    for plane, (base, count) in enumerate(zip(BASES, TILES)):
        for first in range(0, count, 16):
            tag = bits.read() * 2 + bits.read()
            visible = [t for t in range(first, min(first + 16, count)) if not hidden[base + t]]
            if not visible:
                assert tag == 3
            elif tag == 3:
                raise AssertionError("noncanonical grouped mode tag")
            elif tag in (0, 1):
                op = 0 if tag == 0 else 2
                for tile in visible:
                    ops[base + tile] = op
            else:
                values = [bits.read() for _ in visible]
                assert any(values) and not all(values)
                for tile, value in zip(visible, values):
                    ops[base + tile] = 2 if value else 0
    assert (bits.pos + 7) // 8 == mode_len
    for pos in range(bits.pos, mode_len * 8):
        assert ((body[pos >> 3] >> (7 - (pos & 7))) & 1) == 0
    return bytes(ops)


def cell_for(plane: int, tile: int) -> int:
    if plane == 0:
        return ((tile // 90) // 2) * 45 + (tile % 90) // 2
    return tile


def parse_packet(packet: bytes, supplied_ops: bytes, prior: bytes, current: bytes,
                 ref_valid: int, ref_fid: int, ref_generation: int,
                 qcache_valid: int, cache_fid: int, cache_generation: int,
                 hidden: tuple[int, ...], decode_planes: int = 3) -> dict:
    assert len(packet) >= 132 and packet[:4] == b"CS88"
    assert zlib.crc32(packet[:-4]) & 0xffffffff == int.from_bytes(packet[-4:], "big")
    version, flags, group, method = packet[4], packet[5], packet[6], packet[7]
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    width, height, block, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, mode_len, q_len, hud_len, residual_len = struct.unpack_from(">IIIII", packet, 32)
    assert (version, group, width, height, block, reserved, cap) == (1, 16, 720, 480, 32, 0, 65536)
    assert flags in (0, 1) and len(packet) <= 49152
    assert 128 + mode_len + q_len + residual_len + hud_len + 4 == len(packet)
    assert packet[116:128] == bytes(12)
    key = flags == 1
    if key:
        assert refid == 0xffffffff and not ref_valid
    else:
        assert ref_valid and refid == ref_fid and fid > ref_fid and generation > ref_generation
    ops = decode_operations(packet, 128, mode_len, key, method, hidden)
    assert len(supplied_ops) == 8100 and ops == supplied_ops
    needed = {cell_for(0, t) for t in range(5400) if ops[t] == 2}
    needed |= {t for t in range(1350) if ops[5400 + t] == 2}
    needed |= {t for t in range(1350) if ops[6750 + t] == 2}
    assert len(prior) == len(current) == 1350

    qoff = 128 + mode_len
    qblock = packet[qoff:qoff + q_len]
    assert len(qblock) >= 16 and digest(qblock)  # exact span is checked above
    assert zlib.crc32(qblock[:-4]) & 0xffffffff == int.from_bytes(qblock[-4:], "big")
    magic, qver, qmethod, cells, body_len, required = struct.unpack_from(">4sBBHHH", qblock)
    assert magic == b"QM87" and qver == 1 and cells == 1350
    assert len(qblock) == 16 + body_len and required == len(needed)
    body = qblock[12:-4]
    if qmethod == 2:
        scales = bytearray()
        for byte in body:
            value, count = byte >> 6, (byte & 63) + 1
            assert value < 3 and len(scales) + count <= 1350
            scales.extend([value] * count)
        assert len(scales) == 1350
        scales = bytes(scales)
        assert scales == current
    elif qmethod == 6:
        assert not key and body_len == 0 and qcache_valid
        assert (cache_fid, cache_generation) == (ref_fid, ref_generation)
        assert prior == current
        scales = prior
    else:
        raise AssertionError(f"unsupported qmap method {qmethod}")
    assert all(scales[c] < 3 for c in needed)

    residual_start = qoff + q_len
    residual_end = residual_start + residual_len
    cursor = residual_start
    planes = []
    for plane, base, count in ((0, 0, 5400), (1, 5400, 1350), (2, 6750, 1350)):
        assert cursor + 4 <= residual_end
        chunks = int.from_bytes(packet[cursor:cursor + 4], "big")
        cursor += 4
        expected_tiles = [t for t in range(count) if ops[base + t] == 2]
        assert chunks == (1 if expected_tiles else 0)
        span = None
        decoded = b""
        if chunks:
            assert cursor + 8 <= residual_end
            nblocks, size = struct.unpack_from(">II", packet, cursor)
            cursor += 8
            off = cursor
            payload = packet[off:off + size]
            assert len(payload) == size and payload[:4] == b"BR88"
            assert nblocks == len(expected_tiles)
            cursor += size
            span = {"plane": plane, "offset": off, "length": size,
                    "blocks": nblocks, "chunk_sha256": digest(payload)}
            if plane < decode_planes:
                decoded = bytes().join(struct.pack("<h", v) for v in BR88.decode(payload, nblocks, 1))
                assert len(decoded) == nblocks * 128
            else:
                try:
                    BR88.decode(payload, nblocks, 1)
                except ValueError as exc:
                    assert "CRC" in str(exc), f"expected inner CRC failure, got {exc}"
                else:
                    raise AssertionError("mutated third-plane BR88 CRC unexpectedly passed")
        planes.append({"tiles": expected_tiles, "span": span, "dense": decoded})
    assert cursor == residual_end
    return {"fid": fid, "refid": refid, "generation": generation, "key": key,
            "qmap_method": qmethod, "required_cells": len(needed), "qscales": scales,
            "operations": ops, "planes": planes, "residual_start": residual_start,
            "residual_end": residual_end}


def inspect_residual_magics(packet: bytes) -> list[list[str]]:
    mode_len, q_len, hud_len, residual_len = struct.unpack_from(">IIII", packet, 36)
    cursor = 128 + mode_len + q_len
    end = cursor + residual_len
    groups = []
    for _ in range(3):
        assert cursor + 4 <= end
        count = int.from_bytes(packet[cursor:cursor + 4], "big")
        cursor += 4
        row = []
        for _ in range(count):
            assert cursor + 8 <= end
            blocks, length = struct.unpack_from(">II", packet, cursor)
            cursor += 8
            payload = packet[cursor:cursor + length]
            assert len(payload) == length and blocks > 0 and length >= 46
            row.append(payload[:4].decode("ascii", "replace"))
            cursor += length
        groups.append(row)
    assert cursor == end and end + hud_len + 4 == len(packet)
    return groups


def tuple_digest(plane: int, tiles: list[int], scales: bytes, dense: bytes) -> str:
    h = hashlib.sha256()
    for ordinal, tile in enumerate(tiles):
        cell = cell_for(plane, tile)
        for index in range(64):
            value = int.from_bytes(dense[ordinal * 128 + index * 2:ordinal * 128 + index * 2 + 2],
                                   "little", signed=True)
            h.update(struct.pack(">BIIBHBh", plane, tile, ordinal, index, cell,
                                  scales[cell], value))
    return h.hexdigest()


def fnv_coefficient_block(data: bytes) -> int:
    state = 1469598103934665603
    for byte in data:
        state = ((state ^ byte) * 1099511628211) & 0xffffffffffffffff
    return state


def read_cases() -> list[dict]:
    csv.field_size_limit(100_000_000)
    with (VECTORS / "cases.tsv").open(newline="") as f:
        names = ("id", "expected_error", "packet_hex", "ref_valid", "ref_fid",
                 "ref_generation", "qcache_valid", "cache_fid", "cache_generation",
                 "prior_qscale_hex", "current_qscale_hex", "operations_hex",
                 "denseY_hex", "denseCb_hex", "denseCr_hex")
        rows = [dict(zip(names, row, strict=True)) for row in csv.reader(f, delimiter="\t")]
    assert len(rows) >= 9
    for row in rows:
        row["expected_error"] = int(row["expected_error"])
        for name in ("ref_valid", "ref_fid", "ref_generation", "qcache_valid", "cache_fid", "cache_generation"):
            row[name] = int(row[name])
    return rows


def compare_sidecar(case: dict, independent: dict, decode_planes: int = 3) -> dict:
    by_plane = []
    for plane, expected in enumerate(independent["planes"]):
        if plane >= decode_planes:
            by_plane.append([])
            continue
        raw = bytes.fromhex(case[f"dense{'Y' if plane == 0 else 'Cb' if plane == 1 else 'Cr'}_hex"])
        assert raw == expected["dense"], f"{case['id']} plane {plane} entropy golden mismatch"
        tiles = expected["tiles"]
        rows = []
        for ordinal, tile in enumerate(tiles):
            cell = cell_for(plane, tile)
            block = raw[ordinal * 128:(ordinal + 1) * 128]
            rows.append({"plane": plane, "block": ordinal, "tile": tile,
                         "qcell": cell, "qscale": independent["qscales"][cell],
                         "coefficient_hash": fnv_coefficient_block(block)})
        by_plane.append(rows)
    return {"planes": by_plane}


def main() -> None:
    global BR88
    codec_path = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
    spec = importlib.util.spec_from_file_location("frozen_br88_strict_reader", codec_path)
    BR88 = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(BR88)

    hidden = frozen_hidden()
    cases = read_cases()
    model = load_json(AREA / "model-results.json")
    manifest = load_json(VECTORS / "manifest.json")
    assert model["status"] == "PASS"
    source_paths = {
        "v91i_index_sha256": ROOT / "experiments/python-gamebub-v91i/vectors/index.json",
        "v91e_coefficients_gzip_sha256": ROOT / "experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz",
        "v87_quantizer_ledger_sha256": ROOT / "experiments/python-gamebub-v87/quantizers/attempts/20261106T142631412759Z-5847ed8e/frames.jsonl",
        "v88_all_br88_history_sha256": ROOT / "experiments/python-gamebub-v88/wire/attempts/20261106T150804504317Z-44bf5035/frames.jsonl",
        "v90_native_history_sha256": ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1/frames.jsonl",
        "v88_receiver_source_sha256": ROOT / "experiments/python-gamebub-v88/wire/receiver.cpp",
        "v91e_vectors_index_sha256": ROOT / "experiments/python-gamebub-v91e/vectors/index.json",
        "frozen_generated_constants_sha256": ROOT / "experiments/cu66-native-v69/generated_constants.hpp",
        "model_source_sha256": AREA / "model.py",
    }
    for key, source in source_paths.items():
        assert digest(source.read_bytes()) == manifest["source_pins"][key], f"source pin changed: {key}"
    assert manifest["source_pins"]["hidden_mask_sha256"] == digest(bytes(hidden))
    assert model["tsv_sha256"] == digest((VECTORS / "cases.tsv").read_bytes())
    assert model["manifest_sha256"] == digest((VECTORS / "manifest.json").read_bytes())
    assert len(manifest["cases"]) == len(cases) == len(model["cases"])
    model_by_id = {c["id"]: c for c in model["cases"]}
    manifest_by_id = {c["id"]: c for c in manifest["cases"]}
    independent_cases = {}
    tuple_total = 0
    for row in cases:
        ident = row["id"]
        packet = bytes.fromhex(row["packet_hex"])
        origin = manifest_by_id[ident]
        assert row["expected_error"] == model_by_id[ident]["expected_error"]
        assert digest(packet) == model_by_id[ident]["packet_sha256"] == manifest_by_id[ident]["packet_sha256"]
        assert origin["expected_error"] == row["expected_error"]
        assert origin["packet_bytes"] == len(packet)
        assert origin["key"] == (packet[5] == 1)
        assert digest(bytes(origin["qscales"])) == origin["qscales_sha256"]
        if row["expected_error"] == 64:
            magics = inspect_residual_magics(packet)
            assert any(magic != "BR88" for group in magics for magic in group)
        if row["expected_error"] == 7:
            q_len = int.from_bytes(packet[40:44], "big")
            mode_len = int.from_bytes(packet[36:40], "big")
            qoff = 128 + mode_len
            assert packet[qoff:qoff + 4] == b"QM87" and packet[qoff + 5] == 6
            if ident.endswith("wrong_cache_tag"):
                assert (row["cache_fid"], row["cache_generation"]) != (row["ref_fid"], row["ref_generation"])
            else:
                assert row["cache_fid"] == row["ref_fid"] and row["cache_generation"] == row["ref_generation"]
                assert bytes.fromhex(row["prior_qscale_hex"])[0] > 2
        if row["expected_error"] not in (0, 147):
            independent_cases[ident] = {"expected_error": row["expected_error"], "planes": [[], [], []]}
            continue
        parsed = parse_packet(packet, bytes.fromhex(row["operations_hex"]),
                              (bytes.fromhex(row["prior_qscale_hex"])
                               if row["prior_qscale_hex"] != "-" else bytes(1350)),
                              bytes.fromhex(row["current_qscale_hex"]),
                              row["ref_valid"], row["ref_fid"], row["ref_generation"],
                              row["qcache_valid"], row["cache_fid"], row["cache_generation"], hidden,
                              decode_planes=2 if row["expected_error"] == 147 else 3)
        assert (parsed["fid"], parsed["refid"], parsed["generation"]) == (
            origin["fid"], origin["refid"], origin["generation"])
        assert parsed["operations"] == bytes.fromhex(row["operations_hex"])
        assert parsed["qscales"] == bytes(origin["qscales"])
        if parsed["qmap_method"] == 6:
            qcache = origin["qcache"]
            assert qcache and qcache["valid"]
            assert bytes.fromhex(qcache["qscales_hex"]) == parsed["qscales"]
            assert qcache["cache_fid"] == row["cache_fid"]
            assert qcache["cache_generation"] == row["cache_generation"]
        else:
            assert origin["qmap_method"] == parsed["qmap_method"]
        if row["denseY_hex"] not in ("", "-"):
            placement = compare_sidecar(row, parsed, decode_planes=2 if row["expected_error"] == 147 else 3)
            for plane in range(2 if row["expected_error"] == 147 else 3):
                expected = parsed["planes"][plane]
                model_plane = model_by_id[ident]["planes"][plane]
                assert model_plane["active_blocks"] == len(expected["tiles"])
                assert model_plane["tuple_count"] == len(expected["tiles"]) * 64
                assert model_plane["tuple_sha256"] == tuple_digest(
                    plane, expected["tiles"], parsed["qscales"], expected["dense"])
                assert model_plane["first"]["tile"] == (expected["tiles"][0] if expected["tiles"] else None)
                assert model_plane["last"]["tile"] == (expected["tiles"][-1] if expected["tiles"] else None)
                tuple_total += len(expected["tiles"]) * 64
            independent_cases[ident] = {"expected_error": row["expected_error"], "parsed": parsed,
                                        "placement": placement, "planes": placement["planes"]}
        else:
            if row["expected_error"] == 0:
                assert all(not expected["tiles"] and not expected["dense"] for expected in parsed["planes"])
                assert model_by_id[ident]["active_blocks_by_plane"] == [0, 0, 0]
                assert model_by_id[ident]["tuple_count"] == 0
                assert model_by_id[ident]["planes"] == []
            independent_cases[ident] = {"expected_error": row["expected_error"], "parsed": parsed, "planes": [[], [], []]}

    # Retained receipts are discovered from the current two seeded root attempts.
    candidates = sorted((ROOT / "fpga/experiments/cu66-v91i2/pipeline-attempts").glob("*/results.json"))
    selected = {}
    for path in candidates:
        receipt = load_json(path)
        if (receipt.get("schema") != "cu66-v91i2a-coefficient-placement-rtl-v1"
                or receipt.get("status") != "PASS_CS88_BR88_COEFFICIENT_PLACEMENT"
                or receipt.get("seed") not in (911201, 911202)):
            continue
        source_ok = all(digest((ROOT / name).read_bytes()) == value
                        for name, value in receipt["source_sha256"].items())
        vectors_ok = all(digest((VECTORS / name).read_bytes()) == value
                         for name, value in receipt["vectors_sha256"].items())
        if source_ok and vectors_ok:
            selected[receipt["seed"]] = path
    if set(selected) != {911201, 911202}:
        raise AssertionError(f"need current-source/vector passes for both seeds, found {sorted(selected)}")
    attempt_paths = [selected[911201], selected[911202]]
    results = []
    rtl_checks = []
    expected_directed = {
        "abort_accepted_write_drain_blocks_start", "warm_reset_accepted_write_drain_blocks_start",
        "abort_held_mapped_coefficient", "good_retry_after_failed_frame_without_reset",
        "partial_cache_load_abort_releases_owner", "one_shot_cache_requires_fresh_preload",
        "zero_frame_epoch_rejected", "snapshot_inputs_latched_every_case",
        "serial_cache_tag_latched_first_byte", "all_coefficients_and_mapped_tuple_fields_exact",
    }
    for path in attempt_paths:
        receipt = load_json(path)
        if receipt.get("schema") != "cu66-v91i2a-coefficient-placement-rtl-v1":
            continue
        assert receipt["status"] == "PASS_CS88_BR88_COEFFICIENT_PLACEMENT"
        trace_path = path.parent / receipt["tile_trace"]["path"]
        packed = trace_path.read_bytes()
        assert digest(packed) == receipt["tile_trace"]["gzip_sha256"]
        raw_jsonl = gzip.decompress(packed)
        assert digest(raw_jsonl) == receipt["tile_trace"]["jsonl_sha256"]
        trace = [json.loads(line) for line in raw_jsonl.splitlines() if line]
        assert len(trace) == receipt["tile_trace"]["records"]
        sim_path = path.parent / "simulation.jsonl"
        sim_raw = sim_path.read_bytes()
        assert receipt["artifacts_sha256"]["simulation.jsonl"] == digest(sim_raw)
        for artifact, expected_hash in receipt["artifacts_sha256"].items():
            assert digest((path.parent / artifact).read_bytes()) == expected_hash
        sim_rows = [json.loads(line) for line in sim_raw.splitlines() if line]
        verdicts = [r for r in sim_rows if r.get("type") == "verdict"]
        case_rows = [r for r in sim_rows if r.get("type") == "case"]
        assert len(verdicts) == 1 and verdicts[0]["status"] == "TEST_PASS"
        assert receipt["verdict"] == verdicts[0]
        assert receipt["case_rows"] == len(case_rows)
        assert receipt["completed_rows"] == 12 and receipt["rejected_rows"] == 10
        assert receipt["tile_trace"]["records"] == verdicts[0]["tile_rows"] == 63412
        assert verdicts[0]["vectors"] == 11 and verdicts[0]["cases"] == 22
        assert verdicts[0]["configurations"] == 2 and verdicts[0]["directed_checks"] == 10
        assert verdicts[0]["dense_comparisons"] == 4058368
        assert verdicts[0]["directed_dense_comparisons"] == 913984
        assert set(verdicts[0]["directed_check_names"]) == expected_directed
        directed_rows = [r for r in sim_rows if r.get("type") == "directed"]
        assert len(directed_rows) == 10 and all(r["status"] == "PASS" for r in directed_rows)
        assert {r["name"] for r in directed_rows} == expected_directed
        by_key = {(r["id"], int(r["memory_profile"])): r for r in case_rows}
        assert len(by_key) == len(case_rows) == 22
        assert {key[1] for key in by_key} == {0, 1}
        assert set(by_key) == {(case["id"], profile) for case in cases for profile in (0, 1)}
        prev_frame_epoch = prev_child_epoch = 0
        events = {}
        for event in trace:
            assert event.get("type") == "tile"
            key = (event["id"], int(event["memory_profile"]))
            events.setdefault(key, []).append(event)
        assert set(events).issubset(set(by_key))
        for (ident, profile), result in by_key.items():
            expected_case = independent_cases[ident]
            assert result["error"] == expected_case["expected_error"]
            vector = next(c for c in cases if c["id"] == ident)
            assert int(result["seed"]) == receipt["seed"]
            assert int(result["frame_epoch"]) == prev_frame_epoch + 1
            prev_frame_epoch = int(result["frame_epoch"])
            assert result["requests"] == result["acks"] and not result["pending_drain"]
            assert not result["full_frame_publication"]
            assert result["cache_bytes"] == (1350 if vector["qcache_valid"] else 0)
            children = [int(x) for x in result["child_epochs"]]
            assert len(children) == int(result["core_starts"])
            assert all(a < b for a, b in zip(children, children[1:]))
            if children:
                assert children[0] > prev_child_epoch
                prev_child_epoch = children[-1]
            case_events = events.get((ident, profile), [])
            if result["error"] == 0 or result["error"] == 147:
                expected_planes = expected_case["planes"]
                expected_rows = [r for plane in expected_planes for r in plane]
                if result["error"] == 147:
                    expected_rows = [r for plane in expected_planes[:2] for r in plane]
                assert len(case_events) == len(expected_rows), (ident, profile, len(case_events), len(expected_rows))
                for actual, expected in zip(case_events, expected_rows, strict=True):
                    for field in ("plane", "block", "tile", "qcell", "qscale"):
                        assert int(actual[field]) == int(expected[field]), (ident, profile, field)
                    assert actual["coefficient_count"] == 64
                    assert int(actual["coefficient_hash"]) == expected["coefficient_hash"]
                    assert actual["frame_epoch"] == result["frame_epoch"]
                    assert actual["child_epoch"] == result["child_epochs"][expected["plane"]]
                    assert result["first_coef"] <= actual["first_cycle"] <= actual["last_cycle"] <= result["last_coef"]
                assert result["status"] == "PASS"
                assert result["coefficients"] == len(expected_rows) * 64
                if expected_rows:
                    assert result["last_input"] < result["first_coef"] <= result["last_coef"]
                    if result["error"] == 0:
                        assert result["last_coef"] < result["done_cycle"]
                    else:
                        assert result["done_cycle"] == 0
                else:
                    assert result["first_coef"] == result["last_coef"] == 0
                    assert result["last_input"] < result["done_cycle"]
            else:
                assert result["status"] == "PASS"
                # AB38 and eligibility failures must happen before a child starts.
                if result["error"] in (7, 64):
                    assert result["core_starts"] == 0 and not case_events
                    assert result["requests"] == result["acks"] == 0
            if result["error"] == 147:
                assert ident.endswith("bad_third_inner_crc")
                assert result["core_starts"] == 3 and result["done_cycle"] == 0
                assert result["last_input"] < result["first_coef"] <= result["last_coef"]
                assert result["coefficients"] == len(case_events) * 64
                assert len(case_events) == sum(len(x) for x in expected_case["planes"][:2])
            rtl_checks.append({"seed": receipt.get("seed"), "id": ident, "memory_profile": profile,
                               "status": result["status"], "events": len(case_events),
                               "core_starts": result.get("core_starts"), "error": result.get("error")})
        results.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path.read_bytes()),
                        "seed": receipt.get("seed"), "trace_records": len(trace), "case_count": len(case_rows),
                        "source_revision": receipt["source_revision"],
                        "source_sha256": receipt["source_sha256"],
                        "vectors_sha256": receipt["vectors_sha256"],
                        "qualification": {name: verdicts[0][name] for name in
                                          ("dense_comparisons", "directed_dense_comparisons", "tile_rows",
                                           "directed_checks", "directed_check_names")}})
    assert {r["seed"] for r in results} == {911201, 911202}
    assert len({json.dumps(load_json(ROOT / result["path"])["source_sha256"], sort_keys=True)
                for result in results}) == 1
    assert len({json.dumps(load_json(ROOT / result["path"])["vectors_sha256"], sort_keys=True)
                for result in results}) == 1
    audit = {
        "schema": "cu66-v91i2-independent-placement-audit-v1",
        "status": "PASS_INDEPENDENT_CS88_BR88_TUPLE_AND_RTL_RECEIPT_AUDIT",
        "independent_parser": str(Path(__file__).relative_to(ROOT)),
        "entropy_oracle": {"path": str(codec_path.relative_to(ROOT)), "sha256": digest(codec_path.read_bytes())},
        "vectors": {"tsv_sha256": digest((VECTORS / "cases.tsv").read_bytes()),
                    "manifest_sha256": digest((VECTORS / "manifest.json").read_bytes()),
                    "case_count": len(cases)},
        "accepted_cases": sum(1 for r in cases if r["expected_error"] == 0),
        "independently_decoded_tuples": tuple_total,
        "retained_rtl_attempts": results,
        "rtl_case_receipts": rtl_checks,
        "scope": "Independent CS88 mode/QM87/residual byte parsing, BR88 dense coefficient decoding, plane/tile/qcell/qscale binding, and retained RTL tuple receipt reconciliation. No pixel reconstruction, dequantization/IDCT, frame acceptance, HUD/root/seal verification, physical timing, hardware throughput, or full-frame latency claim.",
    }
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(audit["status"], "cases=" + str(len(cases)), "tuples=" + str(tuple_total),
          "attempts=" + str(len(results)))


if __name__ == "__main__":
    main()

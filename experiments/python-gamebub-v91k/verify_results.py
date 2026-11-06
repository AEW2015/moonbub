#!/usr/bin/env python3
"""Independent V91k source, pixel, RGB565, and RTL-attempt auditor.

The pixel oracle is recomputed from frozen V91i2 source coefficients and
accepted V82 reference pixels. It does not import V91k model.py or use its
calculated output as the expected result.
"""
from __future__ import annotations

import argparse
import csv
from functools import lru_cache
import gzip
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
CASE_TSV = ROOT / "experiments/python-gamebub-v91i2/vectors/cases.tsv"
CASE_MANIFEST = ROOT / "experiments/python-gamebub-v91i2/vectors/manifest.json"
V91I2_MODEL = ROOT / "experiments/python-gamebub-v91i2/model.py"
V91J_MODEL = ROOT / "experiments/python-gamebub-v91j/model.py"
V82_DIR = ROOT / "experiments/python-gamebub-v82/native"
V88_HISTORY = ROOT / "experiments/python-gamebub-v88/wire/attempts/20261106T150804504317Z-44bf5035/frames.jsonl"
V90_HISTORY = ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1/frames.jsonl"
CONSTANTS = ROOT / "experiments/cu66-native-v69/generated_constants.hpp"
CASE_IDS = ("actual_001", "actual_006", "actual_043", "actual_031",
            "actual_006_varied_qcache", "structural_all_copy_zero_residual")
CASE_KEYS = {
    "actual_001": ((0, 0), None), "actual_006": ((0, 1), (0, 0)),
    "actual_043": ((0, 3), (0, 2)), "actual_031": ((3, 50), (3, 49)),
    "actual_006_varied_qcache": (None, (0, 0)),
    "structural_all_copy_zero_residual": (None, (0, 0)),
}
PLANE_COUNTS = (5400, 1350, 1350)
PLANE_WIDTHS = (720, 360, 360)
PLANE_HEIGHTS = (480, 240, 240)
PLANE_BASES = (0, 5400, 6750)
CASE_COLUMNS = ("id", "expected_error", "packet_hex", "ref_valid", "ref_fid",
                "ref_generation", "qcache_valid", "cache_fid", "cache_generation",
                "prior_qscale_hex", "current_qscale_hex", "operations_hex",
                "denseY_hex", "denseCb_hex", "denseCr_hex")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_constant(name: str, dims: tuple[int, ...]) -> list[int]:
    source = CONSTANTS.read_text(encoding="ascii")
    pattern = r"\[" + r"\]\[".join(str(x) for x in dims) + r"\]"
    match = re.search(rf"\b{name}{pattern}=\{{(.*?)\}};", source, re.S)
    assert match, f"missing frozen native constant {name}{dims}"
    values = [int(x) for x in re.findall(r"-?\d+", match.group(1))]
    count = 1
    for dim in dims:
        count *= dim
    assert len(values) == count, (name, len(values), count)
    return values


def load_transform_tables():
    dct_values = parse_constant("DCT", (8, 8))
    dct = [dct_values[y * 8:(y + 1) * 8] for y in range(8)]
    q = parse_constant("QTABLES", (2, 3, 8, 8))
    tables = []
    at = 0
    for _plane in range(2):
        by_scale = []
        for _scale in range(3):
            by_scale.append([q[at + y * 8:at + (y + 1) * 8] for y in range(8)])
            at += 64
        tables.append(by_scale)
    return dct, tables


def cases_by_id() -> dict[str, dict[str, str]]:
    csv.field_size_limit(100_000_000)
    with CASE_TSV.open(newline="", encoding="ascii") as stream:
        rows = [dict(zip(CASE_COLUMNS, row, strict=True))
                for row in csv.reader(stream, delimiter="\t")]
    return {row["id"]: row for row in rows}


def load_v82_frames() -> dict[tuple[int, int], dict]:
    sys.path.insert(0, str(V82_DIR))
    import data as v82_data
    frames = {}
    for frame in v82_data.iter_frames(verify=True):
        frames[(int(frame["cohort"]), int(frame["fid"]))] = frame
    return frames


def v82_raster(frame: dict) -> bytes:
    planes = []
    tile_at = 0
    for count, width, height in zip(PLANE_COUNTS, PLANE_WIDTHS, PLANE_HEIGHTS):
        tile_width = width // 8
        plane = bytearray(width * height)
        for tile in range(count):
            by, bx = divmod(tile, tile_width)
            block = frame["tiles"][tile_at + tile]
            assert len(block) == 64
            for y in range(8):
                start = (by * 8 + y) * width + bx * 8
                plane[start:start + 8] = block[y * 8:y * 8 + 8]
        planes.append(bytes(plane))
        tile_at += count
    return b"".join(planes)


def accepted_history() -> dict[tuple[int, int], dict]:
    accepted = {}
    for path in (V88_HISTORY, V90_HISTORY):
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            decoded = item.get("decoded", {})
            if decoded.get("accepted"):
                accepted[(int(item["cohort"]), int(item["fid"]))] = {
                    "canonical_sha256": decoded["canonical_sha256"],
                    "packet_sha256": item["packet_sha256"],
                }
    return accepted


def transform(coeff: tuple[int, ...], plane: int, scale: int, dct, tables) -> list[int]:
    assert len(coeff) == 64 and all(-2048 <= c <= 2048 for c in coeff)
    qtable = tables[0 if plane == 0 else 1][scale]
    dequant = [coeff[y * 8 + x] * qtable[y][x] for y in range(8) for x in range(8)]
    intermediate = [[(sum(dequant[y * 8 + k] * dct[k][x] for k in range(8)) + 8192) // 16384
                      for x in range(8)] for y in range(8)]
    return [(sum(dct[k][y] * intermediate[k][x] for k in range(8)) + 8192) // 16384
            for y in range(8) for x in range(8)]


def quant_cell(plane: int, tile: int) -> int:
    return tile if plane else ((tile // 90) // 2) * 45 + (tile % 90) // 2


def independently_reconstruct(case: dict[str, str], reference: bytes | None, dct, tables) -> bytes:
    modes = bytes.fromhex(case["operations_hex"])
    qscales = bytes.fromhex(case["current_qscale_hex"])
    assert len(modes) == 8100 and len(qscales) == 1350
    if reference is not None:
        assert len(reference) == 518400
    dense_fields = ("denseY_hex", "denseCb_hex", "denseCr_hex")
    coefficient_streams = [bytes.fromhex(case[key]) if case[key] != "-" else b""
                           for key in dense_fields]
    output_planes = []
    raster_offset = 0
    for plane, (count, width, height, tilebase) in enumerate(
            zip(PLANE_COUNTS, PLANE_WIDTHS, PLANE_HEIGHTS, PLANE_BASES)):
        tile_width = width // 8
        active_tiles = [t for t in range(count) if modes[tilebase + t] == 2]
        coeff_data = coefficient_streams[plane]
        assert len(coeff_data) == 128 * len(active_tiles), (case["id"], plane)
        prior = reference[raster_offset:raster_offset + width * height] if reference is not None else None
        out = bytearray(width * height)
        coeff_index = 0
        for tile in range(count):
            mode = modes[tilebase + tile]
            bx, by = tile % tile_width, tile // tile_width
            if mode == 0:
                assert prior is not None, (case["id"], "COPY on key")
                block = [prior[(by * 8 + y) * width + bx * 8 + x]
                         for y in range(8) for x in range(8)]
            elif mode == 1:
                block = [128] * 64
            elif mode == 2:
                coeff = struct.unpack_from("<64h", coeff_data, coeff_index * 128)
                coeff_index += 1
                residual = transform(coeff, plane, qscales[quant_cell(plane, tile)], dct, tables)
                prediction = ([128] * 64 if prior is None else
                              [prior[(by * 8 + y) * width + bx * 8 + x]
                               for y in range(8) for x in range(8)])
                block = [max(0, min(255, p + r)) for p, r in zip(prediction, residual)]
            else:
                raise AssertionError((case["id"], plane, tile, mode))
            for y in range(8):
                offset = (by * 8 + y) * width + bx * 8
                out[offset:offset + 8] = bytes(block[y * 8:y * 8 + 8])
        assert coeff_index == len(active_tiles)
        output_planes.append(bytes(out))
        raster_offset += width * height
    return b"".join(output_planes)


@lru_cache(maxsize=32)
def rgb565_oracle(planar: bytes) -> bytes:
    assert len(planar) == 518400
    y_plane, cb_plane, cr_plane = planar[:345600], planar[345600:432000], planar[432000:]
    out = bytearray(720 * 480 * 2)
    for y in range(480):
        cy, cy1 = y // 2, min(y // 2 + 1, 239)
        for x in range(720):
            cx, cx1 = x // 2, min(x // 2 + 1, 359)
            idx = y * 720 + x
            def upsample(chroma: bytes) -> int:
                top = chroma[cy * 360 + cx]
                if x & 1:
                    top = (top + chroma[cy * 360 + cx1] + 1) // 2
                if y & 1:
                    bottom = chroma[cy1 * 360 + cx]
                    if x & 1:
                        bottom = (bottom + chroma[cy1 * 360 + cx1] + 1) // 2
                    top = (top + bottom + 1) // 2
                return top - 128
            cb, cr = upsample(cb_plane), upsample(cr_plane)
            lum = y_plane[idx]
            red = max(0, min(255, lum + (359 * cr + 128) // 256))
            green = max(0, min(255, lum - (88 * cb + 183 * cr + 128) // 256))
            blue = max(0, min(255, lum + (454 * cb + 128) // 256))
            word = ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3)
            struct.pack_into("<H", out, idx * 2, word)
    return bytes(out)


def load_rows(path: Path, columns: int, expected_sha: str, expected_raw_sha: str):
    compressed = path.read_bytes()
    assert sha(compressed) == expected_sha, (path, "compressed digest")
    raw = gzip.decompress(compressed)
    assert sha(raw) == expected_raw_sha, (path, "raw rows digest")
    rows = {}
    for line in raw.decode("ascii").splitlines():
        fields = line.split("\t")
        assert len(fields) == columns, (path, len(fields))
        assert fields[0] not in rows, (path, fields[0])
        rows[fields[0]] = fields[1:]
    return rows, raw


def verify_goldens() -> dict:
    dct, tables = load_transform_tables()
    source_cases = cases_by_id()
    source_frames = load_v82_frames()
    history = accepted_history()
    results_path = AREA / "model-results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    assert results["schema"] == "cu66-v91k-model-results-v1" and results["status"] == "PASS"
    canonical_path = ROOT / results["canonical_goldens"]["path"]
    rgb_path = ROOT / results["rgb_goldens"]["path"]
    canonical_rows, canonical_raw = load_rows(canonical_path, 3,
        results["canonical_goldens"]["sha256"], results["canonical_goldens"]["raw_rows_sha256"])
    rgb_rows, rgb_raw = load_rows(rgb_path, 2,
        results["rgb_goldens"]["sha256"], results["rgb_goldens"]["raw_rows_sha256"])
    assert tuple(canonical_rows) == CASE_IDS and tuple(rgb_rows) == CASE_IDS
    assert set(item["id"] for item in results["cases"]) == set(CASE_IDS)
    recorded = {item["id"]: item for item in results["cases"]}
    computed_source = {
        "experiments/python-gamebub-v91i2/vectors/cases.tsv": CASE_TSV,
        "experiments/python-gamebub-v91i2/vectors/manifest.json": CASE_MANIFEST,
        "experiments/python-gamebub-v91j/model.py": V91J_MODEL,
        "experiments/python-gamebub-v82/native/data.py": V82_DIR / "data.py",
        "experiments/python-gamebub-v82/native/index.json": V82_DIR / "index.json",
        "experiments/cu66-native-v69/generated_constants.hpp": CONSTANTS,
        str(V88_HISTORY.relative_to(ROOT)): V88_HISTORY,
        str(V90_HISTORY.relative_to(ROOT)): V90_HISTORY,
        "experiments/python-gamebub-v91k/model.py": AREA / "model.py",
    }
    for rel, path in computed_source.items():
        assert path.is_file(), path
        pin_key = {
            "experiments/python-gamebub-v91i2/vectors/cases.tsv": "v91i2_cases_tsv_sha256",
            "experiments/python-gamebub-v91i2/vectors/manifest.json": "v91i2_manifest_sha256",
            "experiments/python-gamebub-v91j/model.py": "v91j_model_sha256",
            "experiments/python-gamebub-v82/native/data.py": "v82_loader_sha256",
            "experiments/python-gamebub-v82/native/index.json": "v82_index_sha256",
            "experiments/cu66-native-v69/generated_constants.hpp": "generated_constants_sha256",
            str(V88_HISTORY.relative_to(ROOT)): "v88_receiver_history_sha256",
            str(V90_HISTORY.relative_to(ROOT)): "v90_receiver_history_sha256",
            "experiments/python-gamebub-v91k/model.py": "model_source_sha256",
        }[rel]
        assert sha(path.read_bytes()) == results["inputs"][pin_key], (rel, "source pin mismatch")
    assert sha(V91I2_MODEL.read_bytes()) == results["inputs"]["v91i2_model_sha256"]
    expected_cases = 0
    for cid in CASE_IDS:
        assert cid in source_cases
        case = source_cases[cid]
        assert int(case["expected_error"]) == 0, (cid, "golden must name accepted case")
        current_key, reference_key = CASE_KEYS[cid]
        reference = v82_raster(source_frames[reference_key]) if reference_key is not None else None
        expected = independently_reconstruct(case, reference, dct, tables)
        if current_key is not None:
            source_raster = v82_raster(source_frames[current_key])
            assert expected == source_raster, (cid, "independent reconstruction vs V82 tiles")
            assert history[current_key]["canonical_sha256"] == source_frames[current_key]["canonical_sha256"]
            assert history[current_key]["canonical_sha256"] == sha(source_raster)
            assert history[current_key]["packet_sha256"] == recorded[cid]["receiver_history_packet_sha256"]
        expected_fields = canonical_rows[cid]
        ref_hex, output_hex = expected_fields
        assert (reference.hex() if reference is not None else "-") == ref_hex, (cid, "reference raster provenance")
        actual = bytes.fromhex(output_hex)
        assert actual == expected, (cid, "independent canonical/reference pixels")
        assert sha(actual) == recorded[cid]["canonical_sha256"]
        assert sha(actual) == recorded[cid]["planar_raster_sha256"]
        rgb = bytes.fromhex(rgb_rows[cid][0])
        rgb_expected = rgb565_oracle(expected)
        assert rgb == rgb_expected, (cid, "independent RGB565 conversion")
        assert sha(rgb) == recorded[cid]["rgb565le_sha256"]
        assert sha(bytes.fromhex(case["packet_hex"])) == recorded[cid]["source_case_packet_sha256"]
        assert sha(bytes.fromhex(case["operations_hex"])) == recorded[cid]["source_operations_sha256"]
        assert sha(bytes.fromhex(case["current_qscale_hex"])) == recorded[cid]["source_qscales_sha256"]
        coeff_bytes = b"".join(bytes.fromhex(case[field]) for field in
                                ("denseY_hex", "denseCb_hex", "denseCr_hex") if case[field] != "-")
        assert sha(coeff_bytes) == recorded[cid]["source_dense_coefficients_sha256"]
        assert recorded[cid]["ref_valid"] is (reference is not None)
        if reference_key is not None:
            assert history[reference_key]["canonical_sha256"] == recorded[cid]["reference_canonical_sha256"]
            assert history[reference_key]["canonical_sha256"] == sha(reference)
            assert history[reference_key]["packet_sha256"] == recorded[cid]["reference_receiver_history_packet_sha256"]
        if current_key is not None:
            assert recorded[cid]["validated_against_v82"] and recorded[cid]["validated_against_receiver_history"]
        expected_cases += 1
    ref_bindings = sum(reference_key is not None for _, reference_key in CASE_KEYS.values())
    unique_refs = {reference_key for _, reference_key in CASE_KEYS.values() if reference_key is not None}
    return {
        "status": "PASS_INDEPENDENT_SOURCE_RECONSTRUCTION_AND_RGB565",
        "cases": expected_cases,
        "canonical_rows_sha256": sha(canonical_raw),
        "rgb_rows_sha256": sha(rgb_raw),
        "canonical_gzip_sha256": sha(canonical_path.read_bytes()),
        "rgb_gzip_sha256": sha(rgb_path.read_bytes()),
        "accepted_v82_frames_checked": 4,
        "reference_snapshot_bindings_checked": ref_bindings,
        "unique_reference_snapshots_checked": len(unique_refs),
    }


def fnv64(data: bytes) -> int:
    value = 1469598103934665603
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return value


def actual_write_rows(path: Path, receipt: dict, expected_by_id: dict[str, bytes]):
    compressed = path.read_bytes()
    assert sha(compressed) == receipt["gzip_sha256"]
    raw = gzip.decompress(compressed)
    assert sha(raw) == receipt["raw_sha256"]
    rows = []
    for line in raw.decode("ascii").splitlines():
        cid, profile_s, raster_hex = line.split("\t")
        profile = int(profile_s)
        raster = bytes.fromhex(raster_hex)
        assert cid in expected_by_id and raster == expected_by_id[cid], (cid, profile, "actual canonical SRAM writes")
        assert len(raster) == 518400
        rows.append((cid, profile, raster))
    assert len(rows) == receipt["rows"] == 12
    assert [(cid, profile) for cid, profile, _ in rows] == [
        (cid, profile) for profile in (0, 1) for cid in EXPECTED_ACCEPTED_ORDER]
    return rows, raw


EXPECTED_ACCEPTED_ORDER = ()


@lru_cache(maxsize=32)
def rgb_read_schedule_hash(canonical: bytes) -> int:
    h = 1469598103934665603
    for pixel in range(720 * 480):
        y, x = divmod(pixel, 720)
        for part in range(9):
            if part == 0:
                address = pixel
            else:
                k = (part - 1) % 4
                cx = min(x // 2 + k % 2, 359)
                cy = min(y // 2 + k // 2, 239)
                address = (345600 if part <= 4 else 432000) + cy * 360 + cx
            for shift in (0, 8, 16, 24):
                h = ((h ^ ((address >> shift) & 0xff)) * 1099511628211) & 0xffffffffffffffff
            h = ((h ^ canonical[address]) * 1099511628211) & 0xffffffffffffffff
    return h


def verify_trace(events: list[dict], expected_by_id: dict[str, bytes], cases: dict[str, dict[str, str]],
                 simulation_cases: dict[tuple[str, int], dict], profiles=(0, 1)) -> dict:
    canonical_rows = defaultdict(dict)
    canonical_order = defaultdict(list)
    ref_requests = defaultdict(list)
    stages = defaultdict(dict)
    token_owners = {}
    group_owners = {}
    expected_transforms = {}
    dct, tables = load_transform_tables()
    for cid, case in cases.items():
        if int(case["expected_error"]) not in (0, 147):
            continue
        operation = bytes.fromhex(case["operations_hex"])
        scales = bytes.fromhex(case["current_qscale_hex"])
        dense = [bytes.fromhex(case[field]) if case[field] != "-" else b""
                 for field in ("denseY_hex", "denseCb_hex", "denseCr_hex")]
        for plane, count in enumerate(PLANE_COUNTS):
            active = [tile for tile in range(count) if operation[PLANE_BASES[plane] + tile] == 2]
            assert len(dense[plane]) % 128 == 0
            available = len(dense[plane]) // 128
            if int(case["expected_error"]) == 0:
                assert available == len(active), (cid, plane, available, len(active))
            else:
                assert available <= len(active), (cid, plane, available, len(active))
            for ordinal, tile in enumerate(active[:available]):
                coeff_raw = dense[plane][ordinal * 128:(ordinal + 1) * 128]
                coeff = struct.unpack("<64h", coeff_raw)
                cell = quant_cell(plane, tile)
                scale = scales[cell]
                qtable = tables[0 if plane == 0 else 1][scale]
                dq_values = [coeff[y * 8 + x] * qtable[y][x] for y in range(8) for x in range(8)]
                mid = [[(sum(dq_values[y * 8 + k] * dct[k][x] for k in range(8)) + 8192) // 16384
                        for x in range(8)] for y in range(8)]
                residual = [(sum(dct[k][y] * mid[k][x] for k in range(8)) + 8192) // 16384
                            for y in range(8) for x in range(8)]
                expected_transforms[(cid, plane, ordinal)] = (tile, cell, scale, coeff_raw,
                    b"".join(struct.pack("<i", value) for value in dq_values),
                    b"".join(struct.pack("<i", value) for value in residual))
    for event in events:
        kind = event.get("type")
        if kind == "canonical":
            cid = event["id"]
            assert cid in expected_by_id or cid == "actual_001_bad_third_inner_crc"
            profile, plane, tile = int(event["memory_profile"]), int(event["plane"]), int(event["tile"])
            key = (profile, plane, tile)
            assert key not in canonical_rows[cid]
            mode_base = (0, 5400, 6750)[plane]
            case_id = "actual_001" if cid == "actual_001_bad_third_inner_crc" else cid
            if case_id in cases:
                mode = bytes.fromhex(cases[case_id]["operations_hex"])[mode_base + tile]
                assert int(event["mode"]) == mode
            width = (720, 360, 360)[plane]
            base = (0, 345600, 432000)[plane]
            tile_width = width // 8
            bx, by = tile % tile_width, tile // tile_width
            raster = expected_by_id[case_id]
            pixels = b"".join(raster[base + (by * 8 + y) * width + bx * 8:
                                         base + (by * 8 + y) * width + bx * 8 + 8]
                               for y in range(8))
            samples = int(event["samples"])
            assert 0 < samples <= 64
            assert int(event["value_hash"]) == fnv64(pixels[:samples])
            assert bool(event["complete"]) == (samples == 64)
            assert int(event["first_cycle"]) > 0 and int(event["first_cycle"]) <= int(event["last_cycle"])
            row = simulation_cases[(cid, profile)]
            assert int(event["frame_epoch"]) == int(row["frame_epoch"])
            assert int(event["fid"]) == int.from_bytes(bytes.fromhex(cases[case_id]["packet_hex"])[8:12], "big")
            if not event["complete"]:
                assert cid == "actual_001_bad_third_inner_crc"
            canonical_rows[cid][key] = event
            canonical_order[(cid, profile)].append(event)
        elif kind == "reference_request":
            cid = event["id"]
            assert cid in cases
            ref_requests[(cid, int(event["memory_profile"]))].append(event)
        elif kind == "transform":
            cid, profile, plane, block = event["id"], int(event["memory_profile"]), int(event["plane"]), int(event["block"])
            stage = event["stage"]
            key = (cid, profile, plane, block)
            assert stage in ("assemble", "dequant", "residual") and stage not in stages[key]
            expected_key = (cid, plane, block)
            assert expected_key in expected_transforms, (cid, plane, block, stage)
            tile, cell, scale, coeff, dq_bytes, residual_bytes = expected_transforms[expected_key]
            assert (int(event["tile"]), int(event["qcell"]), int(event["qscale"])) == (tile, cell, scale)
            epoch, child, token = int(event["frame_epoch"]), int(event["child_epoch"]), int(event["token"])
            assert epoch > 0 and child > 0 and token > 0
            owner = (epoch, token)
            owner_key = (cid, profile, plane, block, child)
            assert token_owners.setdefault(owner, owner_key) == owner_key
            assert group_owners.setdefault(key, (epoch, child, token)) == (epoch, child, token)
            if stage == "assemble":
                data = coeff
            elif stage == "dequant":
                data = dq_bytes
            else:
                data = residual_bytes
            samples = int(event["samples"])
            assert 0 < samples <= 64
            assert bool(event["complete"]) == (samples == 64)
            assert int(event["value_hash"]) == fnv64(data[:samples * (2 if stage == "assemble" else 4)])
            assert stage != "assemble" or samples == 64
            assert stage != "dequant" or samples == 64
            stages[key][stage] = event
    for cid in set(k[0] for k in expected_transforms):
        for profile in profiles:
            ordered_expected = [key for key in expected_transforms if key[0] == cid]
            observed_residual = sorted((plane, block, int(event["samples"]), bool(event["complete"]))
                for (got_id, got_profile, plane, block), stage_map in stages.items()
                if got_id == cid and got_profile == profile
                for event in [stage_map.get("residual")] if event is not None)
            ordered_observed = [(plane, block, samples, complete)
                                for plane, block, samples, complete in observed_residual]
            wanted = [(plane, block, 64, True) for _id, plane, block in ordered_expected]
            if int(cases[cid]["expected_error"]) == 147:
                assert ordered_observed == wanted[:len(ordered_observed)] or (
                    len(ordered_observed) > 0 and ordered_observed[:-1] == wanted[:len(ordered_observed)-1]
                    and ordered_observed[-1][:2] == wanted[len(ordered_observed)-1][:2]
                    and 0 < ordered_observed[-1][2] < 64 and not ordered_observed[-1][3])
            else:
                assert ordered_observed == wanted, (cid, profile, len(ordered_observed), len(wanted))
            for key, stage_map in stages.items():
                if key[0] == cid and key[1] == profile:
                    assert {"assemble", "dequant"} <= set(stage_map), (cid, profile, key)
                    if int(cases[cid]["expected_error"]) != 147 or "residual" in stage_map:
                        assert "residual" in stage_map
            observed_groups = [stage_map for key, stage_map in stages.items()
                               if key[0] == cid and key[1] == profile]
            case_row = simulation_cases[(cid, profile)]
            inv = case_row["inverse"]
            assert sum("assemble" in group for group in observed_groups) == int(inv["assembled_tiles"])
            assert sum("dequant" in group for group in observed_groups) == int(inv["dq_tiles"])
            assert sum("residual" in group for group in observed_groups) == int(inv["residual_tiles"])
            assert sum(int(group["residual"]["samples"]) for group in observed_groups if "residual" in group) == int(inv["residual_samples"])

    for cid in (*EXPECTED_ACCEPTED_ORDER, "actual_001_bad_third_inner_crc"):
        for profile in profiles:
            seq = canonical_order[(cid, profile)]
            case_row = simulation_cases[(cid, profile)]
            expected_samples = int(case_row["canonical"]["samples"])
            assert sum(int(event["samples"]) for event in seq) == expected_samples
            expected_tiles = [(plane, tile) for plane, count in enumerate(PLANE_COUNTS)
                              for tile in range(count)]
            assert [(int(event["plane"]), int(event["tile"])) for event in seq] == expected_tiles[:len(seq)]
            assert all(int(event["samples"]) == 64 for event in seq[:-1])
            if cid in EXPECTED_ACCEPTED_ORDER:
                assert len(seq) == 8100 and expected_samples == 518400
                assert all(event["complete"] for event in seq)
            else:
                assert int(case_row["done_cycle"]) == 0 and len(seq) < 8100
            mode_counts = {0: 0, 1: 0, 2: 0}
            for event in seq:
                mode_counts[int(event["mode"])] += 1
            observed = case_row["canonical"]
            assert mode_counts[0] == int(observed["copy_tiles"])
            assert mode_counts[1] == int(observed["const_tiles"])
            assert mode_counts[2] == int(observed["residual_tiles"])
            if int(cases[cid]["ref_valid"]):
                requests = ref_requests[(cid, profile)]
                assert len(requests) == int(observed["reference_requests"]) == int(observed["reference_acks"])
                assert all(int(item["frame_epoch"]) == int(case_row["frame_epoch"]) for item in requests)
            else:
                assert not ref_requests[(cid, profile)]
    for cid in EXPECTED_ACCEPTED_ORDER:
        case = cases[cid]
        mode_bytes = bytes.fromhex(case["operations_hex"])
        for profile in profiles:
            want = {(plane, tile) for plane, count in enumerate(PLANE_COUNTS)
                    for tile in range(count) if mode_bytes[PLANE_BASES[plane] + tile] != 1}
            # Only inter frames with a valid prior reference issue reads. Key frames
            # synthesize the prediction base and must not request a prior frame.
            if int(case["ref_valid"]):
                requests = ref_requests[(cid, profile)]
                got = {(int(item["plane"]), int(item["tile"])) for item in requests}
                assert len(got) == len(requests) and got == want, (cid, profile, len(got), len(want))
                for item in requests:
                    assert int(item["fid"]) == int(case["ref_fid"])
                    assert int(item["generation"]) == int(case["ref_generation"])
                    assert int(item["frame_epoch"]) > 0
            else:
                assert not ref_requests[(cid, profile)], (cid, profile, "key frame requested a reference")
        for profile in profiles:
            tiles = canonical_rows[cid]
            keys = {key for key in tiles if key[0] == profile}
            assert len(keys) == 8100, (cid, profile, "canonical tile trace coverage")
    return {"canonical_tile_events": sum(len(x) for x in canonical_rows.values()),
            "reference_requests": sum(len(x) for x in ref_requests.values()),
            "transform_stage_groups": len(stages), "opaque_transform_owners": len(token_owners)}


def audit_attempt(report_path: Path, expected_goldens: dict[str, bytes], rgb_goldens: dict[str, bytes],
                  source_results: dict) -> dict:
    global EXPECTED_ACCEPTED_ORDER
    report_path = report_path.resolve()
    attempt = report_path.parent
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema"] == "cu66-v91k-canonical-and-rgb-rtl-v1"
    assert report["status"] == "PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY"
    assert report["seed"] in (911501, 911502)
    assert report["hardware_distinct_30fps_proven"] is False
    assert report["full_frame_decode_under10ms_proven"] is False
    assert report["full_frame_publication_timestamp"] is None
    assert report["monolithic_full_frame_rtl_proven"] is False
    assert all(command.get("exit_code") == 0 for command in report["commands"])
    assert all("--assert" in command["argv"] and "-Wall" in command["argv"]
               for command in report["commands"] if "--build" in command["argv"])
    assert any("-Wextra -Werror" in " ".join(command["argv"])
               for command in report["commands"] if "--build" in command["argv"])
    assert len([command for command in report["commands"] if "--build" in command["argv"]]) == 2
    for rel, digest in report["source_sha256"].items():
        snapshot = attempt / "sources" / rel
        live = ROOT / rel
        assert snapshot.is_file() and sha(snapshot.read_bytes()) == digest, (rel, "retained source pin")
        assert live.is_file() and sha(live.read_bytes()) == digest, (rel, "current source pin")
    for rel, digest in report["vectors_sha256"].items():
        retained, current = attempt / "vectors" / rel, VECTORS / rel
        assert retained.is_file() and sha(retained.read_bytes()) == digest, (rel, "retained vector pin")
        assert current.is_file() and sha(current.read_bytes()) == digest, (rel, "current vector pin")
    for rel, digest in report["inputs_sha256"].items():
        assert sha((ROOT / rel).read_bytes()) == digest, (rel, "current input pin")
    for rel, digest in report["artifacts_sha256"].items():
        artifact = attempt / rel
        assert artifact.is_file() and sha(artifact.read_bytes()) == digest, (rel, "attempt artifact hash")
    assert len(report["input_expansions"]) == 3
    for expansion in report["input_expansions"]:
        compressed_path = attempt / expansion["compressed_path"]
        compressed_bytes = compressed_path.read_bytes()
        assert sha(compressed_bytes) == expansion["compressed_sha256"]
        raw_bytes = gzip.decompress(compressed_bytes)
        assert sha(raw_bytes) == expansion["raw_sha256"]
        assert len(raw_bytes.splitlines()) == expansion["rows"]
    simulation = [json.loads(line) for line in (attempt / "simulation.jsonl").read_text().splitlines()]
    cases = cases_by_id()
    EXPECTED_ACCEPTED_ORDER = tuple(row["id"] for row in _case_rows_in_order()
                                    if row["id"] in expected_goldens and int(row["expected_error"]) == 0)
    assert len(EXPECTED_ACCEPTED_ORDER) == 6
    sim_cases = [row for row in simulation if row.get("type") == "case"]
    assert len(sim_cases) == 22 and {(row["id"], int(row["memory_profile"])) for row in sim_cases} == {
        (cid, p) for cid in cases for p in (0, 1)}
    assert all(row["status"] == "PASS" and int(row["error"]) == int(cases[row["id"]]["expected_error"])
               for row in sim_cases)
    late = [row for row in sim_cases if int(row["error"]) == 147]
    assert len(late) == 2 and all(row["done_cycle"] == 0 and row["full_frame_publication"] is False for row in late)
    for row in sim_cases:
        if int(cases[row["id"]]["expected_error"]) in (64, 7, 65):
            assert row["done_cycle"] == 0 and row["canonical"]["samples"] == 0
    integrated = [row for row in sim_cases if int(row["error"]) == 0]
    assert len(integrated) == 12
    for row in integrated:
        assert row["done_cycle"] > 0 and row["pending_drain"] is False
        assert row["requests"] == row["acks"]
        assert row["canonical"]["samples"] == 518400 and row["canonical"]["tiles"] == 8100
        assert row["canonical"]["ref_pending"] == 0
        assert row["inverse"]["max_owned_banks"] <= 2
    verdict = report["verdict"]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == report["seed"]
    assert verdict["cases"] == 22 and verdict["configurations"] == 2
    required_pipeline = {
        "abort_queued_and_pending_refill", "warm_reset_queued_and_pending_refill",
        "abort_accepted_write_drain_blocks_start", "warm_reset_accepted_write_drain_blocks_start",
        "abort_held_canonical_output", "abort_owned_idct_job",
        "mismatched_reference_tag_rejects_and_drains_real_owner",
        "matching_reference_bus_error_retires_owner_and_rejects",
        "clean_retry_after_reference_error", "canonical_exact_all_modes_and_hidden_normalization",
        "finite_candidate_write_and_reference_service", "snapshot_inputs_latched_every_case",
        "all_coefficients_and_mapped_tuple_fields_exact",
    }
    pipeline_checks = set(verdict["directed_check_names"])
    assert required_pipeline <= pipeline_checks, sorted(required_pipeline - pipeline_checks)
    assert sum(row["canonical"]["reference_requests"] for row in integrated) == sum(
        len([t for t in range(PLANE_COUNTS[p])
             if bytes.fromhex(cases[cid]["operations_hex"])[PLANE_BASES[p] + t] != 1])
        for cid in EXPECTED_ACCEPTED_ORDER if int(cases[cid]["ref_valid"]) for p in range(3)) * 2

    canonical_trace = report["canonical_trace"]
    trace_path = attempt / canonical_trace["path"]
    trace_raw = gzip.decompress(trace_path.read_bytes())
    assert sha(trace_path.read_bytes()) == canonical_trace["gzip_sha256"]
    assert sha(trace_raw) == canonical_trace["raw_sha256"]
    assert len(trace_raw.splitlines()) == canonical_trace["rows"]
    trace_events = [json.loads(line) for line in trace_raw.splitlines()]
    simulation_by_key = {(row["id"], int(row["memory_profile"])): row for row in sim_cases}
    trace_summary = verify_trace(trace_events, expected_goldens, cases, simulation_by_key)
    canonical_events = [event for event in trace_events if event.get("type") == "canonical"]
    assert sum(int(event["samples"]) for event in canonical_events) == verdict["canonical_comparisons"]
    assert sum(int(event["samples"]) for event in canonical_events
               if event["complete"] and event["id"] in EXPECTED_ACCEPTED_ORDER) == 2 * 518400 * 6
    late_prefix = [event for event in canonical_events if not event["complete"]]
    assert all(event["id"] == "actual_001_bad_third_inner_crc" for event in late_prefix)
    assert sum(int(event["samples"]) for event in canonical_events
               if event["id"] == "actual_001_bad_third_inner_crc") == sum(
        row["canonical"]["samples"] for row in sim_cases if row["id"] == "actual_001_bad_third_inner_crc")

    actual_receipt = report["canonical_actual"]
    actual_path = attempt / actual_receipt["path"]
    actual_rows, actual_raw = actual_write_rows(actual_path, actual_receipt, expected_goldens)
    rgb_rows = [json.loads(line) for line in (attempt / "rgb.jsonl").read_text().splitlines()]
    rgb_cases = [row for row in rgb_rows if row.get("type") == "case"]
    assert len(rgb_cases) == 12 and all(row["status"] == "PASS" for row in rgb_cases)
    actual_hashes = {(cid, profile): (raster, fnv64(raster)) for cid, profile, raster in actual_rows}
    for row in rgb_cases:
        cid, profile = row["id"], int(row["memory_profile"])
        canonical, canonical_fnv = actual_hashes[(cid, profile)]
        recomputed_rgb = rgb565_oracle(canonical)
        assert recomputed_rgb == rgb_goldens[cid], (cid, profile, "RGB derived from actual candidate writes")
        assert int(row["canonical_input_hash"]) == canonical_fnv
        assert int(row["rgb565_hash"]) == fnv64(recomputed_rgb)
        assert int(row["read_schedule_hash"]) == rgb_read_schedule_hash(canonical)
        assert int(row["reads"]) == int(row["responses"]) == 3110400
        assert int(row["pixels"]) == 345600 and row["publication"] is False
        if profile:
            assert row["output_stalls"] > 0 and row["request_stalls"] > 0
    rgb_verdict = report["rgb_verdict"]
    required_rgb = {"warm_reset_pending_read_drain", "abort_pending_read_drain",
                    "warm_reset_held_pixel", "abort_held_pixel", "response_epoch_mismatch",
                    "response_bus_error", "zero_epoch_rejected", "clean_retry_after_cancel_and_fault"}
    assert rgb_verdict["status"] == "TEST_PASS" and rgb_verdict["seed"] == report["seed"]
    assert rgb_verdict["cases"] == 12 and rgb_verdict["pixels"] == 4147200
    rgb_checks = set(rgb_verdict["directed_check_names"])
    assert required_rgb <= rgb_checks, sorted(required_rgb - rgb_checks)
    assert len(rgb_cases) == 12
    return {"seed": report["seed"], "path": str(report_path.relative_to(ROOT)),
            "sha256": sha(report_path.read_bytes()), "status": report["status"],
            "case_rows": len(sim_cases), "canonical_actual_rows": len(actual_rows),
            "rgb_rows": len(rgb_cases), "trace": trace_summary,
            "pipeline_directed_checks": sorted(pipeline_checks),
            "rgb_directed_checks": sorted(rgb_checks),
            "canonical_actual_raw_sha256": sha(actual_raw)}


def _case_rows_in_order() -> list[dict[str, str]]:
    csv.field_size_limit(100_000_000)
    with CASE_TSV.open(newline="", encoding="ascii") as stream:
        return [dict(zip(CASE_COLUMNS, row, strict=True)) for row in csv.reader(stream, delimiter="\t")]


def run_audit(attempt_arg: str | None, golden_only: bool) -> dict:
    result_details = json.loads((AREA / "model-results.json").read_text(encoding="utf-8"))
    canonical_rows, _ = load_rows(ROOT / result_details["canonical_goldens"]["path"], 3,
                                  result_details["canonical_goldens"]["sha256"],
                                  result_details["canonical_goldens"]["raw_rows_sha256"])
    rgb_rows, _ = load_rows(ROOT / result_details["rgb_goldens"]["path"], 2,
                            result_details["rgb_goldens"]["sha256"],
                            result_details["rgb_goldens"]["raw_rows_sha256"])
    expected = {cid: bytes.fromhex(row[1]) for cid, row in canonical_rows.items()}
    rgb_expected = {cid: bytes.fromhex(row[0]) for cid, row in rgb_rows.items()}
    report = {
        "schema": "cu66-v91k-independent-integration-audit-v1",
        "status": "PASS_GOLDENS_ONLY" if golden_only else "NOT_AUDITED",
        "source_sha256": {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in
            (CASE_TSV, CASE_MANIFEST, V91I2_MODEL, V91J_MODEL, V82_DIR / "data.py", V82_DIR / "index.json",
             V88_HISTORY, V90_HISTORY, CONSTANTS, AREA / "model.py", AREA / "verify_results.py")},
        "goldens": verify_goldens(),
        "integration": {"status": "NOT_CHECKED"},
    }
    if not golden_only:
        if attempt_arg:
            attempts = [Path(attempt_arg)]
        else:
            attempts = sorted((ROOT / "fpga/experiments/cu66-v91k/pipeline-attempts").glob("*/results.json"))
        current_passing = {}
        for path in attempts:
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if item.get("status") != "PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY":
                continue
            seed = item.get("seed")
            if seed not in (911501, 911502):
                continue
            if any(not (ROOT / rel).is_file() or sha((ROOT / rel).read_bytes()) != digest
                   for rel, digest in item.get("source_sha256", {}).items()):
                continue
            if any(not (VECTORS / rel).is_file() or sha((VECTORS / rel).read_bytes()) != digest
                   for rel, digest in item.get("vectors_sha256", {}).items()):
                continue
            current_passing[seed] = path
        if attempt_arg:
            run_rows = [audit_attempt(attempts[0], expected, rgb_expected, result_details)]
            report["status"] = "PASS_GOLDENS_AND_ONE_RTL_SEED"
        else:
            assert set(current_passing) == {911501, 911502}, {k: str(v) for k, v in current_passing.items()}
            run_rows = [audit_attempt(current_passing[seed], expected, rgb_expected, result_details)
                        for seed in (911501, 911502)]
            report["status"] = "PASS_INDEPENDENT_GOLDENS_AND_BOTH_RTL_SEEDS"
        assert len({row["seed"] for row in run_rows}) == len(run_rows)
        report["integration"] = {"status": "PASS_TRACE_AND_CONTROL", "attempts": run_rows}
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", help="retained V91k run results.json; default finds current passing seeds")
    parser.add_argument("--goldens-only", action="store_true", help="audit source-backed pixel vectors without RTL attempts")
    args = parser.parse_args()
    result = run_audit(args.attempt, args.goldens_only)
    (AREA / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

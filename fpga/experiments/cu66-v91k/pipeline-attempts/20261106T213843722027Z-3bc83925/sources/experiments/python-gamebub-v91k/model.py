#!/usr/bin/env python3
"""Independent CS88 pixel reconstruction and no-HUD RGB565 goldens for V91k."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
CASES = ROOT / "experiments/python-gamebub-v91i2/vectors/cases.tsv"
V82_DIR = ROOT / "experiments/python-gamebub-v82/native"
V88_HISTORY = ROOT / "experiments/python-gamebub-v88/wire/attempts/20261106T150804504317Z-44bf5035/frames.jsonl"
V90_HISTORY = ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1/frames.jsonl"
CONSTANTS = ROOT / "experiments/cu66-native-v69/generated_constants.hpp"
SAMPLE_COUNTS = (5400, 1350, 1350)
TILE_WIDTHS = (90, 45, 45)
PLANE_DIMS = ((720, 480), (360, 240), (360, 240))
CASES_OF_INTEREST = ("actual_001", "actual_006", "actual_043", "actual_031",
                     "actual_006_varied_qcache", "structural_all_copy_zero_residual")
REAL_CANONICAL = {
    "actual_001": "927e4b27b815228919275cdbd3cbdfcc8b7cbd0eae60749a3919e1754e5d6257",
    "actual_006": "37209129ec076f8d4ca1d0a9b269d1c5450a0e459f0d066dc5da119cec259628",
    "actual_043": "83f5a53d57975f1f385ded9c2c35bf9f2ef408a82fb7fa30c0142946852b5968",
    "actual_031": "46cb1992fcfd1126d7d1d868c49c615482e85a6dbe78f22321b9203f97711a6f",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_array(name: str, dimensions: tuple[int, ...]) -> list[int]:
    source = CONSTANTS.read_text()
    dims = r"\[" + r"\]\[".join(map(str, dimensions)) + r"\]"
    match = re.search(rf"\b{name}{dims}=\{{(.*?)\}};", source, re.S)
    if not match:
        raise ValueError(f"missing frozen {name}{dimensions}")
    vals = [int(v) for v in re.findall(r"-?\d+", match.group(1))]
    expected = 1
    for n in dimensions:
        expected *= n
    if len(vals) != expected:
        raise ValueError(f"{name}: expected {expected} entries, found {len(vals)}")
    return vals


def transform(coeff: tuple[int, ...], plane: int, scale: int,
              dct: list[list[int]], quant: list) -> list[int]:
    if len(coeff) != 64 or any(c < -2048 or c > 2048 for c in coeff):
        raise ValueError("invalid signed12 coefficient tile")
    q = quant[0 if plane == 0 else 1][scale]
    dq = [coeff[y * 8 + x] * q[y][x] for y in range(8) for x in range(8)]
    mid = [[(sum(dq[y * 8 + k] * dct[k][x] for k in range(8)) + 8192) // 16384
            for x in range(8)] for y in range(8)]
    return [(sum(dct[k][y] * mid[k][x] for k in range(8)) + 8192) // 16384
            for y in range(8) for x in range(8)]


def load_tables():
    dct_flat = parse_array("DCT", (8, 8))
    dct = [dct_flat[i:i+8] for i in range(0, 64, 8)]
    q_flat = parse_array("QTABLES", (2, 3, 8, 8))
    n, quant = 0, []
    for _plane in range(2):
        scales = []
        for _scale in range(3):
            block = []
            for _y in range(8):
                block.append(q_flat[n:n+8]); n += 8
            scales.append(block)
        quant.append(scales)
    return dct, quant


def cases_by_id() -> dict[str, dict]:
    csv.field_size_limit(100_000_000)
    cols = ["id", "expected_error", "packet_hex", "ref_valid", "ref_fid",
            "ref_generation", "qcache_valid", "cache_fid", "cache_generation",
            "prior_qscale_hex", "current_qscale_hex", "operations_hex",
            "denseY_hex", "denseCb_hex", "denseCr_hex"]
    with CASES.open(newline="", encoding="ascii") as f:
        rows = [dict(zip(cols, r)) for r in csv.reader(f, delimiter="\t")]
    return {r["id"]: r for r in rows}


def load_v82_frames() -> dict[tuple[int, int], dict]:
    sys.path.insert(0, str(V82_DIR))
    import data as v82_data
    frames = {}
    for frame in v82_data.iter_frames(verify=True):
        key = frame["cohort"], frame["fid"]
        frames[key] = frame
    return frames


def frame_raster(frame: dict) -> bytes:
    planes = []
    at = 0
    for count, tile_width, (width, height) in zip(SAMPLE_COUNTS, TILE_WIDTHS, PLANE_DIMS):
        out = bytearray(width * height)
        for tile_i in range(count):
            tile = frame["tiles"][at + tile_i]
            by, bx = divmod(tile_i, tile_width)
            for y in range(8):
                start = (by * 8 + y) * width + bx * 8
                out[start:start + 8] = tile[y * 8:y * 8 + 8]
        planes.append(bytes(out))
        at += count
    return b"".join(planes)


def source_history_hashes() -> dict[tuple[int, int], str]:
    hashes = {}
    for path in (V88_HISTORY, V90_HISTORY):
        for line in path.read_text().splitlines():
            obj = json.loads(line)
            dec = obj.get("decoded", {})
            if dec.get("accepted"):
                hashes[(obj["cohort"], obj["fid"])] = {
                    "canonical_sha256": dec["canonical_sha256"],
                    "packet_sha256": obj["packet_sha256"],
                    "policy": obj.get("policy"),
                }
    return hashes


def qcell(plane: int, tile: int) -> int:
    if plane:
        return tile
    return (tile // 90 // 2) * 45 + (tile % 90 // 2)


def reconstruct(case: dict, reference: bytes | None, dct, quant) -> bytes:
    ops = bytes.fromhex(case["operations_hex"])
    qscales = bytes.fromhex(case["current_qscale_hex"])
    dense = [bytes.fromhex(case[k]) if case[k] != "-" else b""
             for k in ("denseY_hex", "denseCb_hex", "denseCr_hex")]
    if len(ops) != 8100 or len(qscales) != 1350:
        raise ValueError("mode/qscale vector extent")
    if reference is not None and len(reference) != 518400:
        raise ValueError("reference raster extent")
    outplanes = []
    tile_base = 0
    raster_base = 0
    for plane, (count, tw, (width, height)) in enumerate(zip(SAMPLE_COUNTS, TILE_WIDTHS, PLANE_DIMS)):
        ntiles = 0
        plane_out = bytearray(width * height)
        active = [t for t in range(count) if ops[tile_base + t] == 2]
        if len(dense[plane]) != len(active) * 128:
            raise ValueError(f"{case['id']} plane {plane}: coeff blocks mismatch")
        refplane = reference[raster_base:raster_base + width * height] if reference is not None else None
        for tile in range(count):
            mode = ops[tile_base + tile]
            by, bx = divmod(tile, tw)
            if mode == 0:
                if refplane is None:
                    raise ValueError("key frame cannot COPY")
                block = [refplane[(by * 8 + y) * width + bx * 8 + x]
                         for y in range(8) for x in range(8)]
            elif mode == 1:
                block = [128] * 64
            elif mode == 2:
                coeffs = struct.unpack_from("<64h", dense[plane], ntiles * 128)
                res = transform(coeffs, plane, qscales[qcell(plane, tile)], dct, quant)
                ntiles += 1
                pred = [128] * 64 if refplane is None else [
                    refplane[(by * 8 + y) * width + bx * 8 + x]
                    for y in range(8) for x in range(8)]
                block = [max(0, min(255, r + p)) for r, p in zip(res, pred)]
            else:
                raise ValueError(f"unknown operation mode {mode}")
            for y in range(8):
                start = (by * 8 + y) * width + bx * 8
                plane_out[start:start+8] = bytes(block[y*8:y*8+8])
        if ntiles != len(active):
            raise ValueError("not all coefficient tiles consumed")
        outplanes.append(bytes(plane_out))
        tile_base += count
        raster_base += width * height
    return b"".join(outplanes)


def rgb565le(planar: bytes) -> bytes:
    if len(planar) != 518400:
        raise ValueError("expected 720x480 Y and 360x240 Cb/Cr")
    y_plane = planar[:345600]
    cb_plane = planar[345600:432000]
    cr_plane = planar[432000:]
    out = bytearray(720 * 480 * 2)
    for y in range(480):
        yy, yy1 = y // 2, min(y // 2 + 1, 239)
        for x in range(720):
            xx, xx1 = x // 2, min(x // 2 + 1, 359)
            idx = y * 720 + x
            def chroma(p):
                top = p[yy * 360 + xx]
                if x & 1:
                    top = (top + p[yy * 360 + xx1] + 1) // 2
                if y & 1:
                    bottom = p[yy1 * 360 + xx]
                    if x & 1:
                        bottom = (bottom + p[yy1 * 360 + xx1] + 1) // 2
                    top = (top + bottom + 1) // 2
                return top - 128
            cb, cr = chroma(cb_plane), chroma(cr_plane)
            Y = y_plane[idx]
            r = max(0, min(255, Y + (359 * cr + 128) // 256))
            g = max(0, min(255, Y - (88 * cb + 183 * cr + 128) // 256))
            b = max(0, min(255, Y + (454 * cb + 128) // 256))
            word = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            struct.pack_into("<H", out, idx * 2, word)
    return bytes(out)


def write_gzip_rows(path: Path, rows) -> tuple[str, str, int]:
    raw_hash = hashlib.sha256()
    raw_bytes = 0
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
            with io.TextIOWrapper(gz, encoding="ascii", newline="") as out:
                for row in rows:
                    line = "\t".join(row) + "\n"
                    out.write(line)
                    raw_hash.update(line.encode("ascii"))
                    raw_bytes += len(line.encode("ascii"))
    return sha(path.read_bytes()), raw_hash.hexdigest(), raw_bytes


def main() -> None:
    VECTORS.mkdir(parents=True, exist_ok=True)
    cases = cases_by_id()
    source_manifest = json.loads((ROOT / "experiments/python-gamebub-v91i2/vectors/manifest.json").read_text())
    source_case_records = {c["id"]: c for c in source_manifest["cases"]}
    frames = load_v82_frames()
    receiver_hashes = source_history_hashes()
    dct, quant = load_tables()
    target_map = {
        "actual_001": ((0, 0), None),
        "actual_006": ((0, 1), (0, 0)),
        "actual_043": ((0, 3), (0, 2)),
        "actual_031": ((3, 50), (3, 49)),
        "actual_006_varied_qcache": (None, (0, 0)),
        "structural_all_copy_zero_residual": (None, (0, 0)),
    }
    canonical_rows, rgb_rows, case_records = [], [], []
    for case_id in CASES_OF_INTEREST:
        if case_id not in cases:
            raise ValueError(f"missing frozen V91i2 case {case_id}")
        current_key, reference_key = target_map[case_id]
        reference = frame_raster(frames[reference_key]) if reference_key else None
        reconstructed = reconstruct(cases[case_id], reference, dct, quant)
        v82 = frame_raster(frames[current_key]) if current_key else None
        if v82 is not None and reconstructed != v82:
            raise ValueError(f"{case_id}: independent integer reconstruction differs from retained V82 pixels")
        expected = v82 if v82 is not None else reconstructed
        if current_key is not None:
            actual_digest = frames[current_key]["canonical_sha256"]
            if actual_digest != sha(expected):
                raise ValueError(f"{case_id}: V82 canonical metadata mismatch")
            if REAL_CANONICAL.get(case_id) != actual_digest:
                raise ValueError(f"{case_id}: frozen V91k canonical digest mismatch")
            if receiver_hashes.get(current_key, {}).get("canonical_sha256") != actual_digest:
                raise ValueError(f"{case_id}: accepted V88/V90 receiver history mismatch")
        if reference_key is not None:
            ref_meta = frames[reference_key]
            if receiver_hashes.get(reference_key, {}).get("canonical_sha256") != ref_meta["canonical_sha256"]:
                raise ValueError(f"{case_id}: accepted reference receiver history mismatch")
        else:
            ref_meta = None
        rgb = rgb565le(expected)
        canonical_rows.append((case_id, reference.hex() if reference is not None else "-", expected.hex()))
        rgb_rows.append((case_id, rgb.hex()))
        case_records.append({
            "id": case_id,
            "kind": "native_actual" if current_key is not None else "synthetic",
            "cohort_fid": list(current_key) if current_key is not None else None,
            "reference_cohort_fid": list(reference_key) if reference_key is not None else None,
            "reference_canonical_sha256": ref_meta["canonical_sha256"] if ref_meta else None,
            "canonical_sha256": sha(expected),
            "planar_raster_sha256": sha(expected),
            "rgb565le_sha256": sha(rgb),
            "ref_valid": reference is not None,
            "validated_against_v82": v82 is not None,
            "validated_against_receiver_history": current_key is not None,
            "source_case_packet_sha256": sha(bytes.fromhex(cases[case_id]["packet_hex"])),
            "source_fixture_path": source_case_records[case_id].get("source_fixture_path"),
            "source_packet_path": source_case_records[case_id].get("packet_path"),
            "source_operations_sha256": sha(bytes.fromhex(cases[case_id]["operations_hex"])),
            "source_qscales_sha256": sha(bytes.fromhex(cases[case_id]["current_qscale_hex"])),
            "source_dense_coefficients_sha256": sha(b"".join(
                bytes.fromhex(cases[case_id][field]) for field in
                ("denseY_hex", "denseCb_hex", "denseCr_hex") if cases[case_id][field] != "-")),
            "v82_raw_pixel_source_sha256": frames[current_key]["canonical_sha256"] if current_key is not None else None,
            "receiver_history_canonical_sha256": receiver_hashes[current_key]["canonical_sha256"] if current_key is not None else None,
            "receiver_history_packet_sha256": receiver_hashes[current_key]["packet_sha256"] if current_key is not None else None,
            "reference_receiver_history_packet_sha256": receiver_hashes[reference_key]["packet_sha256"] if reference_key is not None else None,
        })
    canonical_gz_sha, canonical_raw_sha, canonical_raw_bytes = write_gzip_rows(
        VECTORS / "canonical_goldens.tsv.gz", canonical_rows)
    rgb_gz_sha, rgb_raw_sha, rgb_raw_bytes = write_gzip_rows(
        VECTORS / "rgb_goldens.tsv.gz", rgb_rows)
    results = {
        "schema": "cu66-v91k-model-results-v1",
        "status": "PASS",
        "inputs": {
            "v91i2_cases_tsv_sha256": sha(CASES.read_bytes()),
            "v91i2_manifest_sha256": sha((ROOT / "experiments/python-gamebub-v91i2/vectors/manifest.json").read_bytes()),
            "v91i2_model_sha256": sha((ROOT / "experiments/python-gamebub-v91i2/model.py").read_bytes()),
            "v91j_model_sha256": sha((ROOT / "experiments/python-gamebub-v91j/model.py").read_bytes()),
            "v82_loader_sha256": sha((V82_DIR / "data.py").read_bytes()),
            "v82_index_sha256": sha((V82_DIR / "index.json").read_bytes()),
            "generated_constants_sha256": sha(CONSTANTS.read_bytes()),
            "v88_receiver_history_sha256": sha(V88_HISTORY.read_bytes()),
            "v90_receiver_history_sha256": sha(V90_HISTORY.read_bytes()),
            "model_source_sha256": sha(Path(__file__).read_bytes()),
        },
        "canonical_goldens": {"path": "experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz",
                              "sha256": canonical_gz_sha, "raw_rows_sha256": canonical_raw_sha,
                              "rows": len(canonical_rows), "decompressed_bytes": canonical_raw_bytes,
                              "columns": ["id", "ref_planar_raster_hex_or_dash", "expected_planar_raster_hex"],
                              "planar_encoding": "full raster Y 720x480, Cb 360x240, Cr 360x240, each unsigned byte"},
        "rgb_goldens": {"path": "experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz",
                         "sha256": rgb_gz_sha, "raw_rows_sha256": rgb_raw_sha,
                         "rows": len(rgb_rows), "decompressed_bytes": rgb_raw_bytes,
                         "columns": ["id", "rgb565le_hex"],
                         "encoding": "720x480 packed RGB565 words, little-endian; base conversion excludes HUD"},
        "cases": case_records,
        "scope": "Exact zero-motion COPY/CONST128/residual reconstruction for four accepted CS88 all-BR88 frames, one varied-qcache synthetic transform, and one structural all-COPY packet; exact no-HUD V69 bilinear YCbCr to RGB565 conversion. No RTL timing/performance claims.",
    }
    (AREA / "model-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

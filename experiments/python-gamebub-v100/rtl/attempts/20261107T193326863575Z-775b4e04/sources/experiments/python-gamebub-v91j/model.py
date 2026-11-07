#!/usr/bin/env python3
"""Independent V91j dequantization and two-pass integer IDCT goldens.

Reads the frozen V91i2 placement vectors and generated constants as data. It
does not import or call the native C++ transform implementation.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
SOURCE_TSV = ROOT / "experiments/python-gamebub-v91i2/vectors/cases.tsv"
SOURCE_MANIFEST = ROOT / "experiments/python-gamebub-v91i2/vectors/manifest.json"
CONSTANTS = ROOT / "experiments/cu66-native-v69/generated_constants.hpp"
NATIVE_IDS = ("actual_001", "actual_006", "actual_043", "actual_031")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_array(name: str, dimensions: tuple[int, ...]) -> list[int]:
    source = CONSTANTS.read_text()
    dims = r"\[" + r"\]\[".join(map(str, dimensions)) + r"\]"
    match = re.search(rf"\b{name}{dims}=\{{(.*?)\}};", source, re.S)
    if not match:
        raise ValueError(f"missing frozen {name}{dimensions}")
    values = [int(v) for v in re.findall(r"-?\d+", match.group(1))]
    expected = 1
    for dimension in dimensions:
        expected *= dimension
    if len(values) != expected:
        raise ValueError(f"{name}: expected {expected} values, got {len(values)}")
    return values


def tables() -> tuple[list[list[int]], list[list[int]]]:
    dct = [parse_array("DCT", (8, 8))[i:i + 8] for i in range(0, 64, 8)]
    qtflat = parse_array("QTABLES", (2, 3, 8, 8))
    qt = []
    n = 0
    for _plane_class in range(2):
        scales = []
        for _scale in range(3):
            block = []
            for _y in range(8):
                block.append(qtflat[n:n + 8])
                n += 8
            scales.append(block)
        qt.append(scales)
    return dct, qt


def signed_bytes(values: list[int], width: int) -> bytes:
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    if any(v < lo or v > hi for v in values):
        raise ValueError(f"value outside signed{width}")
    # Use 32-bit little-endian containers for the RTL-facing transform ports.
    return b"".join(struct.pack("<i", v) for v in values)


def transform(coeff: list[int], plane: int, scale: int,
              dct: list[list[int]], qtables: list) -> tuple[list[int], list[int]]:
    if plane not in (0, 1, 2) or scale not in (0, 1, 2):
        raise ValueError("invalid plane or qscale")
    if len(coeff) != 64 or any(v < -2048 or v > 2048 for v in coeff):
        raise ValueError("coefficient block violates signed 12-bit component bounds")
    q = qtables[0 if plane == 0 else 1][scale]
    dq = [coeff[y * 8 + x] * q[y][x] for y in range(8) for x in range(8)]
    if any(v < -(1 << 19) or v > (1 << 19) - 1 for v in dq):
        raise ValueError("dequantized value outside signed20")
    mid = [[(sum(dq[y * 8 + k] * dct[k][x] for k in range(8)) + 8192) // 16384
            for x in range(8)] for y in range(8)]
    residual = [(sum(dct[k][y] * mid[k][x] for k in range(8)) + 8192) // 16384
                for y in range(8) for x in range(8)]
    if any(v < -(1 << 23) or v > (1 << 23) - 1 for v in residual):
        raise ValueError("residual outside signed24")
    return dq, residual


def input_cases() -> list[dict]:
    csv.field_size_limit(100_000_000)
    with SOURCE_TSV.open(newline="", encoding="ascii") as src:
        rows = list(csv.reader(src, delimiter="\t"))
    cols = ["id", "expected_error", "packet_hex", "ref_valid", "ref_fid",
            "ref_generation", "qcache_valid", "cache_fid", "cache_generation",
            "prior_qscale_hex", "current_qscale_hex", "operations_hex",
            "denseY_hex", "denseCb_hex", "denseCr_hex"]
    cases = [dict(zip(cols, row)) for row in rows]
    if len(cases) != 11:
        raise ValueError(f"expected pinned 11 V91i2 cases, got {len(cases)}")
    return cases


def encode_block(coeff_bytes: bytes, plane: int, scale: int,
                 dct, qtables) -> tuple[bytes, bytes]:
    coeff = list(struct.unpack("<64h", coeff_bytes))
    dq, residual = transform(coeff, plane, scale, dct, qtables)
    return signed_bytes(dq, 20), signed_bytes(residual, 24)


def main() -> None:
    VECTORS.mkdir(parents=True, exist_ok=True)
    dct, qtables = tables()
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    source_tsv_sha = sha(SOURCE_TSV.read_bytes())
    cases = input_cases()
    results = {"schema": "cu66-v91j-model-results-v1", "status": "PASS",
               "source_v91i2_cases_sha256": source_tsv_sha,
               "source_v91i2_manifest_sha256": sha(SOURCE_MANIFEST.read_bytes()),
               "generated_constants_sha256": sha(CONSTANTS.read_bytes()),
               "cases": []}
    row_count = 0
    raw_hash = hashlib.sha256()
    out_path = VECTORS / "transform_tiles.tsv.gz"
    with out_path.open("wb") as raw_gzip:
        with gzip.GzipFile(filename="", fileobj=raw_gzip, mode="wb", mtime=0,
                         compresslevel=9) as compressed:
            with io.TextIOWrapper(compressed, encoding="ascii", newline="") as out:
                for case in cases:
                    case_id = case["id"]
                    if case_id not in NATIVE_IDS and case_id not in (
                            "actual_006_varied_qcache", "actual_001_bad_third_inner_crc"):
                        continue
                    qscales = bytes.fromhex(case["current_qscale_hex"])
                    ops = bytes.fromhex(case["operations_hex"])
                    plane_start = 0
                    per_plane = []
                    case_hash = hashlib.sha256()
                    for plane, (tile_count, dense_col) in enumerate(zip(
                            (5400, 1350, 1350), ("denseY_hex", "denseCb_hex", "denseCr_hex"))):
                        # V91i2's late inner-CRC mutation deliberately exposes only the
                        # completed-plane prefix; the failing plane has no accepted data.
                        if case[dense_col] == "-":
                            per_plane.append({"plane": plane, "active_blocks": 0,
                                              "rows_sha256": sha(b""), "unavailable": True})
                            plane_start += tile_count
                            continue
                        dense = b"" if case[dense_col] == "-" else bytes.fromhex(case[dense_col])
                        active_tiles = [tile for tile in range(tile_count)
                                        if ops[plane_start + tile] == 2]
                        if len(dense) != len(active_tiles) * 128:
                            raise ValueError(f"{case_id} plane {plane}: residual/placement length mismatch")
                        nblocks = 0
                        for ordinal, tile in enumerate(active_tiles):
                            cell = ((tile // 90 // 2) * 45 + (tile % 90 // 2)) if plane == 0 else tile
                            scale = qscales[cell]
                            if scale > 2:
                                raise ValueError(f"{case_id}: invalid qscale code {scale}")
                            coeff = dense[ordinal * 128:(ordinal + 1) * 128]
                            dq, residual = encode_block(coeff, plane, scale, dct, qtables)
                            row = (f"{case_id}\t{plane}\t{ordinal}\t{tile}\t{cell}\t{scale}\t"
                                   f"{coeff.hex()}\t{dq.hex()}\t{residual.hex()}\n")
                            out.write(row)
                            encoded = row.encode("ascii")
                            case_hash.update(encoded)
                            raw_hash.update(encoded)
                            row_count += 1
                            nblocks += 1
                        per_plane.append({"plane": plane, "active_blocks": nblocks,
                                          "rows_sha256": case_hash.hexdigest() if nblocks else sha(b"")})
                        plane_start += tile_count
                    results["cases"].append({"id": case_id, "planes": per_plane,
                                             "tile_rows": sum(p["active_blocks"] for p in per_plane),
                                             "rows_sha256": case_hash.hexdigest()})

    boundary_path = VECTORS / "boundary.tsv"
    boundary_cases = []
    with boundary_path.open("w", encoding="ascii", newline="") as out:
        for plane in (0, 1):
            for scale in (0, 1, 2):
                patterns = {
                    "zero": [0] * 64,
                    "dc_pos_limit": [2048] + [0] * 63,
                    "dc_neg_limit": [-2048] + [0] * 63,
                    "ac_pos_limit": [0, 2048] + [0] * 62,
                    "ac_neg_limit": [0, -2048] + [0] * 62,
                    "rounding_signed_extremes": [2048 if i % 2 == 0 else -2048
                                                  for i in range(64)],
                    "rounding_checkerboard": [((-1) ** (i // 8 + i % 8)) * (i % 17)
                                               for i in range(64)],
                }
                for label, coeff in patterns.items():
                    coeff_bytes = struct.pack("<64h", *coeff)
                    dq, residual = transform(coeff, plane, scale, dct, qtables)
                    dq_bytes = signed_bytes(dq, 20)
                    residual_bytes = signed_bytes(residual, 24)
                    case_id = f"p{plane}_q{scale}_{label}"
                    row = (f"{case_id}\t0\t{plane}\t{scale}\t{coeff_bytes.hex()}\t"
                           f"{dq_bytes.hex()}\t{residual_bytes.hex()}\n")
                    out.write(row)
                    boundary_cases.append({"id": case_id, "plane": plane, "qscale": scale,
                                           "class": label, "sha256": sha(row.encode("ascii"))})
        # Invalid component cases are expected to reject before producing a transform result.
        for plane in (0, 1):
            for value in (2049, -2049):
                coeff = [0] * 64
                coeff[0] = value
                case_id = f"invalid_coeff_{value}_p{plane}"
                out.write(f"{case_id}\t3\t{plane}\t0\t{struct.pack('<64h', *coeff).hex()}\t-\t-\n")
                boundary_cases.append({"id": case_id, "plane": plane,
                                       "expected_error": 3,
                                       "reason": f"coefficient {value} outside +/-2048"})
            case_id = f"invalid_qcode3_p{plane}"
            out.write(f"{case_id}\t3\t{plane}\t3\t{bytes(128).hex()}\t-\t-\n")
            boundary_cases.append({"id": case_id, "plane": plane, "qscale": 3,
                                   "expected_error": 3, "reason": "reserved qscale code 3"})
    results["tile_rows"] = row_count
    results["raw_rows_sha256"] = raw_hash.hexdigest()
    results["transform_tiles_sha256"] = sha(out_path.read_bytes())
    results["boundary_tiles_sha256"] = sha(boundary_path.read_bytes())
    results["boundary_cases"] = boundary_cases
    results["scope"] = "Exact integer dequantization and two rounded IDCT passes; unclipped signed24 residuals only. No prediction, pixels, entropy or performance claims."
    manifest = {"schema": "cu66-v91j-vector-manifest-v1",
                "source_pins": {"v91i2_cases_tsv_sha256": source_tsv_sha,
                                "v91i2_manifest_sha256": sha(SOURCE_MANIFEST.read_bytes()),
                                "v91i2_model_source_sha256": source_manifest["source_pins"]["model_source_sha256"],
                                "v91e_coefficients_gzip_sha256": source_manifest["source_pins"]["v91e_coefficients_gzip_sha256"],
                                "frozen_generated_constants_sha256": sha(CONSTANTS.read_bytes()),
                                "model_source_sha256": sha(Path(__file__).read_bytes())},
                "transform_tiles": {"path": "experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz",
                                    "sha256": results["transform_tiles_sha256"],
                                    "columns": ["id", "plane", "block", "tile", "qcell", "qscale", "coeff_hex", "dq_hex", "residual_hex"],
                                    "encodings": {"coeff_hex": "64 signed int16 LE coefficients (128 bytes)",
                                                  "dq_hex": "64 signed int32 LE containers; each value must fit signed20 (256 bytes)",
                                                  "residual_hex": "64 signed int32 LE containers; each value must fit signed24 (256 bytes)"},
                                    "rows": row_count, "raw_rows_sha256": raw_hash.hexdigest()},
                "boundary": {"path": "experiments/python-gamebub-v91j/vectors/boundary.tsv",
                                   "sha256": results["boundary_tiles_sha256"],
                                   "columns": ["id", "expected_error", "plane", "qscale", "coeff_hex", "dq_hex", "residual_hex"],
                                   "cases": boundary_cases},
                "scope": results["scope"]}
    (VECTORS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    results["manifest_sha256"] = sha((VECTORS / "manifest.json").read_bytes())
    (AREA / "model-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

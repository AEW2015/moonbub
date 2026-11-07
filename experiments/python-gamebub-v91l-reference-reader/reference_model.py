#!/usr/bin/env python3
"""Source-derived V91l 64-byte reference tile traffic model.

This checks frozen V91i2 BR88 operation tables against the V91k safe-hidden
rule, and models aligned 16-byte reads from accepted canonical reference tiles.
It is a deterministic Python traffic/byte oracle, not RTL or timing evidence.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
RESULT = AREA / "model-results.json"
VALIDATION = ROOT / "experiments/python-gamebub-v91l/vectors/validation.tsv.gz"
MODES = ROOT / "experiments/python-gamebub-v91i2/vectors/cases.tsv"
RECONSTRUCTION_RTL = ROOT / "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv"
ADMISSION_RTL = ROOT / "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv"
GENERATOR = ROOT / "experiments/python-gamebub-v91l/vectors/source-export/v91l_make_packets.py"
BASELINE = "380539d99164cc88b1b92b2620fcaca57ef2216c"
COUNTS = (5400, 1350, 1350)
BASES = (0, 345600, 432000)
WIDTHS = (90, 45, 45)
CHUNK_BYTES = 16
TILE_BYTES = 64
CHUNKS_PER_TILE = 4
DELTA_CASES = {
    "c0_f1": ("actual_006", "c0_f0"),
    "c0_f3": ("actual_043", "c0_f2"),
    "c3_f50": ("actual_031", "c3_f49"),
}
CASE_FRAME_IDS = {"actual_001": "c0_f0", "actual_006": "c0_f1", "actual_043": "c0_f3", "actual_031": "c3_f50"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def safe_hidden(plane: int, tile: int) -> bool:
    """Literal source rule from cu66_reconstruct_stream_v91k.sv."""
    x, y = tile % WIDTHS[plane], tile // WIDTHS[plane]
    if plane == 0:
        return ((3 <= x < 22 and (7 <= y < 9 or 11 <= y < 13))
                or (21 <= x < 61 and 45 <= y < 48)
                or (21 <= x < 51 and 49 <= y < 51))
    return 11 <= x < 30 and y == 23


def parse_validation() -> dict[str, dict]:
    csv.field_size_limit(100_000_000)
    with gzip.open(VALIDATION, "rt", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    result = {}
    for row in rows:
        data = bytes.fromhex(row["canonical_tiles_hex"])
        if len(data) != sum(COUNTS) * TILE_BYTES:
            raise ValueError(f"canonical tile bytes for {row['id']}")
        row["tiles"] = tuple(data[i:i + TILE_BYTES] for i in range(0, len(data), TILE_BYTES))
        result[row["id"]] = row
    return result


def parse_mode_tables() -> dict[str, tuple[int, ...]]:
    csv.field_size_limit(100_000_000)
    tables = {}
    with MODES.open(newline="", encoding="ascii") as stream:
        for row in csv.reader(stream, delimiter="\t"):
            ident = row[0]
            if ident not in CASE_FRAME_IDS:
                continue
            operation_bytes = bytes.fromhex(row[11])
            if len(operation_bytes) != sum(COUNTS):
                raise ValueError(f"operation table size for {ident}")
            tables[CASE_FRAME_IDS[ident]] = tuple(operation_bytes)
    if set(tables) != set(CASE_FRAME_IDS.values()):
        raise ValueError("missing frozen actual BR88 mode table")
    return tables


def tile_global_index(plane: int, tile: int) -> int:
    if not 0 <= plane < 3 or not 0 <= tile < COUNTS[plane]:
        raise ValueError("plane/tile bounds")
    return sum(COUNTS[:plane]) + tile


def physical_address(plane: int, tile: int, chunk: int) -> int:
    if not 0 <= chunk < CHUNKS_PER_TILE:
        raise ValueError("chunk bounds")
    address = BASES[plane] + tile * TILE_BYTES + chunk * CHUNK_BYTES
    if address % CHUNK_BYTES or address > 518384 or address > 0x7FFFF:
        raise ValueError("physical address is not an aligned 19-bit canonical line")
    return address


def identity(epoch: int, fid: int, generation: int, plane: int,
             tile: int, chunk: int) -> tuple[int, int, int, int, int, int]:
    """Full transaction identity; physical address is a separate uint32."""
    if not 0 <= epoch <= 0xFFFFFFFF or not 0 <= fid <= 0xFFFFFFFF:
        raise ValueError("epoch/fid width")
    if not 0 <= generation <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("generation width")
    tile_global_index(plane, tile)
    if not 0 <= chunk < CHUNKS_PER_TILE:
        raise ValueError("chunk width")
    return epoch, fid, generation, plane, tile, chunk


def verify_mode_table(frame_id: str, ops: tuple[int, ...], is_key: bool) -> dict:
    counts = {"copy": 0, "const": 0, "residual": 0}
    requests = []
    base = 0
    for plane, count in enumerate(COUNTS):
        for tile in range(count):
            mode = ops[base + tile]
            hidden = safe_hidden(plane, tile)
            if mode not in (0, 1, 2) or hidden != (mode == 1) or (is_key and mode == 0):
                raise ValueError(f"mode/hidden/key mismatch {frame_id} p{plane}t{tile} mode={mode}")
            counts[("copy", "const", "residual")[mode]] += 1
            if not is_key and mode in (0, 2):
                requests.append((plane, tile, mode))
        base += count
    if counts["const"] != 294:
        raise ValueError(f"hidden CONST count {frame_id}: {counts['const']}")
    if not is_key and len(requests) != 7806:
        raise ValueError(f"delta reference request count {frame_id}: {len(requests)}")
    return {"mode_counts": counts, "request_tiles": requests}


def check_request_stream(frame_id: str, ref_id: str, modes: tuple[int, ...],
                         current: tuple[bytes, ...], reference: tuple[bytes, ...]) -> dict:
    is_key = frame_id == "c0_f0"
    mode_report = verify_mode_table(frame_id, modes, is_key)
    requested = mode_report["request_tiles"]
    if is_key:
        if requested:
            raise ValueError("key frame unexpectedly reads a reference")
        return {"request_tiles": 0, "bl8_reads": 0, "x16_read_words": 0,
                "reference_data_bytes": 0, "mode_counts": mode_report["mode_counts"]}

    all_tile_bytes = 0
    bl8_reads = 0
    copy_checks = 0
    requested_ids = set()
    for plane, tile, mode in requested:
        key = (plane, tile)
        if key in requested_ids:
            raise ValueError("duplicate reference tile")
        requested_ids.add(key)
        tile_i = tile_global_index(plane, tile)
        chunks = []
        for chunk in range(CHUNKS_PER_TILE):
            address = physical_address(plane, tile, chunk)
            # Exact 16-byte physical response, using the independently retained
            # accepted canonical reference, with no address/index aliasing.
            read = reference[tile_i][chunk * CHUNK_BYTES:chunk * CHUNK_BYTES + CHUNK_BYTES]
            if len(read) != CHUNK_BYTES:
                raise ValueError("short physical reference response")
            chunks.append(read)
            bl8_reads += 1
        assembled = b"".join(chunks)
        if assembled != reference[tile_i]:
            raise ValueError(f"reference chunk assembly mismatch {frame_id} p{plane}t{tile}")
        if mode == 0:
            if current[tile_i] != assembled:
                raise ValueError(f"COPY output differs from reference {frame_id} p{plane}t{tile}")
            copy_checks += 1
        all_tile_bytes += len(assembled)
    if len(requested_ids) != 7806 or bl8_reads != 31224 or all_tile_bytes != 499584:
        raise ValueError(f"aggregate delta traffic mismatch {frame_id}")
    return {"request_tiles": len(requested_ids), "bl8_reads": bl8_reads,
            "x16_read_words": all_tile_bytes // 2,
            "reference_data_bytes": all_tile_bytes, "copy_bytes_checked": copy_checks * TILE_BYTES,
            "mode_counts": mode_report["mode_counts"]}


def edge_examples(tiles: tuple[bytes, ...]) -> list[dict]:
    out = []
    for plane, tile in ((0, 5399), (1, 1349), (2, 1349)):
        tile_i = tile_global_index(plane, tile)
        chunks = [tiles[tile_i][i * CHUNK_BYTES:(i + 1) * CHUNK_BYTES]
                  for i in range(CHUNKS_PER_TILE)]
        addresses = [physical_address(plane, tile, i) for i in range(CHUNKS_PER_TILE)]
        assembled = b"".join(chunks)
        if assembled != tiles[tile_i] or addresses != list(range(addresses[0], addresses[0] + 64, 16)):
            raise ValueError("full-plane edge example mismatch")
        out.append({"plane": plane, "tile": tile, "global_tile_index": tile_i,
                    "tile_address": BASES[plane] + tile * TILE_BYTES,
                    "chunk_addresses": addresses, "assembled_sha256": sha(assembled),
                    "bytes": len(assembled)})
    return out


def derive() -> dict:
    validation = parse_validation()
    mode_tables = parse_mode_tables()
    traffic = {}
    for frame_id, (mode_case, ref_id) in DELTA_CASES.items():
        traffic[frame_id] = check_request_stream(
            frame_id, ref_id, mode_tables[frame_id], validation[frame_id]["tiles"],
            validation[ref_id]["tiles"])
        traffic[frame_id]["accepted_reference_frame"] = ref_id
        traffic[frame_id]["mode_table_case"] = mode_case
    traffic["c0_f0"] = check_request_stream(
        "c0_f0", "", mode_tables["c0_f0"], validation["c0_f0"]["tiles"], ())

    # Transaction generation remains full-width in the ticket identity and is
    # not packed into the separately bounded physical address.
    gen_a, gen_b = 0xFEDCBA9876543210, 0x0000000076543210
    ticket_a = identity(0x12345678, 50, gen_a, 2, 1349, 3)
    ticket_b = identity(0x12345678, 50, gen_b, 2, 1349, 3)
    edge_addr = physical_address(2, 1349, 3)
    if ticket_a == ticket_b or ticket_a[2] != gen_a or ticket_b[2] != gen_b or not 0 <= edge_addr <= 0x7FFFF:
        raise ValueError("64-bit generation identity was truncated/aliased")

    delta = traffic["c0_f1"]
    expected_per_delta = {"request_tiles": 7806, "bl8_reads": 31224,
                          "x16_read_words": 249792, "reference_data_bytes": 499584}
    if any(delta[k] != v for k, v in expected_per_delta.items()):
        raise ValueError("reference traffic arithmetic")
    words = {"candidate_and_rgb_words_per_frame": 539520,
             "reference_x16_words_per_delta": delta["x16_read_words"],
             "combined_payload_words_per_delta": 539520 + delta["x16_read_words"]}
    return {
        "schema": "cu66-v91l-reference-reader-model-v1",
        "status": "PASS_SOURCE_DERIVED_TRAFFIC_AND_BYTE_ASSEMBLY",
        "baseline_revision": BASELINE,
        "frozen_inputs": {
            str(p.relative_to(ROOT)): file_sha(p)
            for p in (VALIDATION, MODES, RECONSTRUCTION_RTL, ADMISSION_RTL, GENERATOR)
        },
        "validation_vector_sha256": file_sha(VALIDATION),
        "validation_rows": sorted(validation),
        "mode_table_frame_ids": sorted(mode_tables),
        "source_rules": {"mode_codes": {"0": "COPY", "1": "CONST/hidden", "2": "RESIDUAL"},
                         "safe_hidden_source": "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv",
                         "mode_table_source": "experiments/python-gamebub-v91i2/vectors/cases.tsv",
                         "const_hidden_tiles": 294,
                         "visible_reference_tiles_per_delta": 7806},
        "physical_layout": {"tile_payload_bytes": TILE_BYTES, "chunk_bytes": CHUNK_BYTES,
                            "chunks_per_tile": CHUNKS_PER_TILE,
                            "plane_bases": {"Y": BASES[0], "Cb": BASES[1], "Cr": BASES[2]},
                            "address_formula": "plane_base + tile_index*64 + chunk_index*16",
                            "physical_address_bits": 19, "max_line_start_address": 518384,
                            "physical_ticket_bits": 32, "reference_generation_bits": 64,
                            "ticket_identity_separate_from_physical_address": True},
        "traffic_by_frame": traffic,
        "delta_payload_words": words,
        "edge_examples": edge_examples(validation["c0_f1"]["tiles"]),
        "generation_identity_check": {"generation_a": gen_a, "generation_b": gen_b,
                                       "same_physical_address": edge_addr,
                                       "full_width_reference_identities_distinct": ticket_a != ticket_b},
        "scope": {"adapter_payload_bytes": 64, "latency_budget_closed": False,
                  "fit_proven": False, "includes_scratch_or_commands": False,
                  "claim": "Source-derived Python reference traffic and golden byte assembly only."}
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare derivation with frozen result JSON")
    args = parser.parse_args()
    derived = derive()
    encoded = json.dumps(derived, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULT.exists() or RESULT.read_text() != encoded:
            print("reference model results differ; rerun without --check to update", file=sys.stderr)
            return 1
        print("PASS", RESULT.relative_to(ROOT))
    else:
        RESULT.write_text(encoded)
        print("WROTE", RESULT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent byte-address schedule and RGB565 model for V91k two-row chroma reuse."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
ATTEMPT = ROOT / "fpga/experiments/cu66-v91k/pipeline-attempts/20261106T214341304797Z-cb9ea57e"
CANONICAL = ATTEMPT / "canonical_actual.tsv.gz"
RGB_GOLDENS = ATTEMPT / "vectors/rgb_goldens.tsv.gz"
EDGE_CANONICAL_OUT = AREA / "vectors/edge_actual.tsv.gz"
EDGE_RGB_OUT = AREA / "vectors/edge_rgb_goldens.tsv.gz"
FROZEN_REPORT = ROOT / "fpga/experiments/cu66-v91k/pipeline-results.json"
WIDTH, HEIGHT = 720, 480
CW, CH = 360, 240
Y_BYTES, C_BYTES = WIDTH * HEIGHT, CW * CH
FRAME_BYTES = Y_BYTES + 2 * C_BYTES
PIXELS = WIDTH * HEIGHT
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
MASK64 = (1 << 64) - 1


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_gzip_rows(path: Path, rows: list[list[str]]) -> dict[str, object]:
    raw = "".join("\t".join(row) + "\n" for row in rows).encode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        with gzip.GzipFile(filename="", fileobj=f, mode="wb", mtime=0, compresslevel=9) as gz:
            gz.write(raw)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()),
            "raw_sha256": sha(raw), "rows": len(rows), "decompressed_bytes": len(raw)}


def fnv_update(h: int, data: bytes) -> int:
    for byte in data:
        h = ((h ^ byte) * FNV_PRIME) & MASK64
    return h


def fnv_read(h: int, addr: int, value: int) -> int:
    return fnv_update(h, struct.pack("<I", addr) + bytes((value,)))


def slot_bank_word(y: int, x: int) -> tuple[int, int, int]:
    """Return (row slot, x parity bank, word) for a chroma coordinate."""
    if not (0 <= y < CH and 0 <= x < CW):
        raise ValueError("chroma coordinate outside plane")
    return (y & 1, x & 1, x >> 1)


def load_canonical() -> dict[tuple[str, str], bytes]:
    csv.field_size_limit(100_000_000)
    frames: dict[tuple[str, str], bytes] = {}
    with gzip.open(CANONICAL, "rt", encoding="ascii", newline="") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) != 3:
                raise ValueError(f"canonical actual row has {len(row)} columns")
            frame_id, profile, hex_bytes = row
            data = bytes.fromhex(hex_bytes)
            if len(data) != FRAME_BYTES:
                raise ValueError(f"{frame_id}/{profile}: expected {FRAME_BYTES} bytes")
            frames[(frame_id, profile)] = data
    return frames


def load_rgb() -> dict[str, bytes]:
    csv.field_size_limit(100_000_000)
    out: dict[str, bytes] = {}
    with gzip.open(RGB_GOLDENS, "rt", encoding="ascii", newline="") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) != 2:
                raise ValueError("RGB golden must have id and RGB565 bytes")
            out[row[0]] = bytes.fromhex(row[1])
    return out


def address_value(frame: bytes, addr: int) -> int:
    return frame[addr]


def cached_schedule(frame: bytes) -> tuple[int, int, dict[str, int]]:
    """Hash address/data reads in accepted order; count coverage and bank mapping."""
    h = FNV_OFFSET
    counts = {"Y": 0, "Cb": 0, "Cr": 0}
    seen = bytearray(FRAME_BYTES)

    def read(addr: int, plane: str) -> None:
        nonlocal h
        if seen[addr]:
            raise AssertionError(f"duplicate cache external read at {addr}")
        seen[addr] = 1
        counts[plane] += 1
        h = fnv_read(h, addr, frame[addr])

    # Row fills are whole plane rows. Each byte is written into parity bank
    # (slot=row&1, bank=column&1, word=column//2); tags become valid afterward.
    for row in (0, 1):
        for plane, base in (("Cb", Y_BYTES), ("Cr", Y_BYTES + C_BYTES)):
            for col in range(CW):
                slot, bank, word = slot_bank_word(row, col)
                if (slot, bank, word) != (row & 1, col & 1, col >> 1):
                    raise AssertionError("parity-bank mapping changed")
                read(base + row * CW + col, plane)
    rowfills = 2
    for y in range(HEIGHT):
        cy = y // 2
        # New even luma rows advance the chroma pair. The new bottom row is
        # loaded before accepting the first luma byte for that output row.
        if y >= 2 and (y & 1) == 0 and cy + 1 < CH:
            new_row = cy + 1
            for plane, base in (("Cb", Y_BYTES), ("Cr", Y_BYTES + C_BYTES)):
                for col in range(CW):
                    read(base + new_row * CW + col, plane)
            rowfills += 1
        for x in range(WIDTH):
            addr = y * WIDTH + x
            read(addr, "Y")
    if not all(seen):
        raise AssertionError("cached schedule left canonical bytes unread")
    if counts != {"Y": 345600, "Cb": 86400, "Cr": 86400}:
        raise AssertionError(f"cached plane read counts: {counts}")
    if rowfills != CH:
        raise AssertionError(f"expected {CH} paired-row fills, got {rowfills}")
    return h, rowfills, counts


def uncached_schedule(frame: bytes) -> tuple[int, dict[str, int]]:
    h = FNV_OFFSET
    counts = {"Y": 0, "Cb": 0, "Cr": 0}
    for y in range(HEIGHT):
        cy, cy1 = y // 2, min(y // 2 + 1, CH - 1)
        for x in range(WIDTH):
            cx, cx1 = x // 2, min(x // 2 + 1, CW - 1)
            yaddr = y * WIDTH + x
            h = fnv_read(h, yaddr, frame[yaddr]); counts["Y"] += 1
            for row, col in ((cy, cx), (cy, cx1), (cy1, cx), (cy1, cx1)):
                addr = Y_BYTES + row * CW + col
                h = fnv_read(h, addr, frame[addr]); counts["Cb"] += 1
            for row, col in ((cy, cx), (cy, cx1), (cy1, cx), (cy1, cx1)):
                addr = Y_BYTES + C_BYTES + row * CW + col
                h = fnv_read(h, addr, frame[addr]); counts["Cr"] += 1
    return h, counts


def floor_shift_8(value: int) -> int:
    return value // 256


def convert(frame: bytes) -> bytes:
    yplane = frame[:Y_BYTES]
    cbplane = frame[Y_BYTES:Y_BYTES + C_BYTES]
    crplane = frame[Y_BYTES + C_BYTES:]
    out = bytearray(PIXELS * 2)
    for y in range(HEIGHT):
        cy, cy1 = y // 2, min(y // 2 + 1, CH - 1)
        for x in range(WIDTH):
            cx, cx1 = x // 2, min(x // 2 + 1, CW - 1)
            def chroma(plane: bytes) -> int:
                top = plane[cy * CW + cx]
                if x & 1:
                    top = (top + plane[cy * CW + cx1] + 1) // 2
                if y & 1:
                    bottom = plane[cy1 * CW + cx]
                    if x & 1:
                        bottom = (bottom + plane[cy1 * CW + cx1] + 1) // 2
                    top = (top + bottom + 1) // 2
                return top - 128
            cb, cr = chroma(cbplane), chroma(crplane)
            yy = yplane[y * WIDTH + x]
            r = max(0, min(255, yy + floor_shift_8(359 * cr + 128)))
            g = max(0, min(255, yy - floor_shift_8(88 * cb + 183 * cr + 128)))
            b = max(0, min(255, yy + floor_shift_8(454 * cb + 128)))
            word = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            struct.pack_into("<H", out, (y * WIDTH + x) * 2, word)
    return bytes(out)


def edge_pattern() -> bytes:
    """Deterministic, nonconstant stress frame whose final rows/columns differ."""
    yplane = bytes((37 * x + 19 * y + (x * y) % 251) % 256
                   for y in range(HEIGHT) for x in range(WIDTH))
    cbplane = bytes((11 * x + 29 * y + 17) % 256
                    for y in range(CH) for x in range(CW))
    crplane = bytes((23 * x + 7 * y + 91) % 256
                    for y in range(CH) for x in range(CW))
    return yplane + cbplane + crplane


def edge_seam_diagnostics(frame: bytes) -> dict[str, int | bool]:
    cb = frame[Y_BYTES:Y_BYTES + C_BYTES]
    cr = frame[Y_BYTES + C_BYTES:]
    row_changes = sum(cb[238 * CW + x] != cb[239 * CW + x] for x in range(CW))
    row_changes += sum(cr[238 * CW + x] != cr[239 * CW + x] for x in range(CW))
    col_changes = sum(cb[y * CW + 358] != cb[y * CW + 359] for y in range(CH))
    col_changes += sum(cr[y * CW + 358] != cr[y * CW + 359] for y in range(CH))
    return {
        "different_last_two_chroma_rows": row_changes > 0,
        "different_last_two_chroma_columns": col_changes > 0,
        "differing_row_neighbor_values": row_changes,
        "differing_column_neighbor_values": col_changes,
    }


def main() -> None:
    report = json.loads(FROZEN_REPORT.read_text())
    if report.get("schema") != "cu66-v91k-canonical-and-rgb-rtl-v1":
        raise ValueError("unexpected frozen V91k report schema")
    expected_pins = {
        "canonical_actual.tsv.gz": "03fab04d4273388cb1477c6db11c19486d7f0ad1ebc2e39b18fe6cc3508c0192",
        "vectors/rgb_goldens.tsv.gz": "abe85556017a634b43711306763af93d39cbf3207b9547842edd0064c3e6547b",
    }
    actual_inputs = {"canonical_actual.tsv.gz": CANONICAL, "vectors/rgb_goldens.tsv.gz": RGB_GOLDENS}
    input_pins = {}
    for name, path in actual_inputs.items():
        digest = sha(path.read_bytes())
        if digest != expected_pins[name]:
            raise ValueError(f"frozen artifact changed: {name} {digest}")
        input_pins[name] = {"sha256": digest, "path": str(path.relative_to(ROOT))}
    frames, rgb_goldens = load_canonical(), load_rgb()
    if len(frames) != 12 or len(rgb_goldens) != 6:
        raise ValueError("expected six canonical inputs under two profiles and six RGB goldens")
    rows = []
    computed = {}
    for (frame_id, profile), frame in sorted(frames.items()):
        content_hash = sha(frame)
        if content_hash not in computed:
            golden = rgb_goldens[frame_id]
            actual = convert(frame)
            if actual != golden:
                mismatch = next(i for i, (a, b) in enumerate(zip(actual, golden)) if a != b)
                raise AssertionError(f"RGB mismatch {frame_id}/{profile} byte {mismatch}")
            cache_hash, rowfills, cache_counts = cached_schedule(frame)
            baseline_hash, baseline_counts = uncached_schedule(frame)
            computed[content_hash] = (sha(golden), cache_hash, rowfills, cache_counts,
                                      baseline_hash, baseline_counts)
        golden_hash, cache_hash, rowfills, cache_counts, baseline_hash, baseline_counts = computed[content_hash]
        rows.append({
            "id": frame_id,
            "profile": profile,
            "canonical_frame_sha256": sha(frame),
            "rgb565_sha256": golden_hash,
            "rgb565_matches_independent_golden": True,
            "cached_external_reads": sum(cache_counts.values()),
            "cached_reads_by_plane": cache_counts,
            "cached_schedule_fnv1a64": f"{cache_hash:016x}",
            "uncached_external_reads": sum(baseline_counts.values()),
            "uncached_reads_by_plane": baseline_counts,
            "uncached_schedule_fnv1a64": f"{baseline_hash:016x}",
            "paired_row_fills": rowfills,
        })
    edge_frame = edge_pattern()
    seam = edge_seam_diagnostics(edge_frame)
    if not seam["different_last_two_chroma_rows"] or not seam["different_last_two_chroma_columns"]:
        raise AssertionError(f"synthetic edge fixture does not distinguish edge neighbors: {seam}")
    edge_golden = convert(edge_frame)
    edge_cache_hash, edge_rowfills, edge_cache_counts = cached_schedule(edge_frame)
    edge_baseline_hash, edge_baseline_counts = uncached_schedule(edge_frame)
    edge_canonical_rows = [["cache_edge_pattern", profile, edge_frame.hex()]
                           for profile in ("0", "1")]
    edge_rgb_rows = [["cache_edge_pattern", edge_golden.hex()]]
    edge_vector_pins = {
        "canonical": write_gzip_rows(EDGE_CANONICAL_OUT, edge_canonical_rows),
        "rgb565_golden": write_gzip_rows(EDGE_RGB_OUT, edge_rgb_rows),
    }
    edge_result = {
        "id": "cache_edge_pattern",
        "source_kind": "synthetic_deterministic_formula",
        "profile_rows": ["0", "1"],
        "golden_provenance": "Independent Python rendering of frozen normative RGB565 arithmetic; not derived from DUT output.",
        "canonical_frame_sha256": sha(edge_frame),
        "rgb565_sha256": sha(edge_golden),
        "rgb565_matches_independent_golden": True,
        "cached_external_reads": sum(edge_cache_counts.values()),
        "cached_reads_by_plane": edge_cache_counts,
        "cached_schedule_fnv1a64": f"{edge_cache_hash:016x}",
        "uncached_external_reads": sum(edge_baseline_counts.values()),
        "uncached_reads_by_plane": edge_baseline_counts,
        "uncached_schedule_fnv1a64": f"{edge_baseline_hash:016x}",
        "paired_row_fills": edge_rowfills,
        "edge_seam_diagnostics": seam,
        "canonical_vector": edge_vector_pins["canonical"],
        "rgb565_golden_vector": edge_vector_pins["rgb565_golden"],
        "formula": {
            "Y": "(37*x + 19*y + (x*y)%251) % 256",
            "Cb": "(11*x + 29*y + 17) % 256",
            "Cr": "(23*x + 7*y + 91) % 256",
        },
    }
    source_runs = [
        {"seed": 911501, "report": "fpga/experiments/cu66-v91k/pipeline-attempts/20261106T214205162842Z-fe63b2f2/results.json",
         "report_sha256": "e246d93104ca9df23b13588edc098370ee047ecf6e5b4db28ae26a41efcbf130",
         "canonical_actual_sha256": expected_pins["canonical_actual.tsv.gz"]},
        {"seed": 911502, "report": "fpga/experiments/cu66-v91k/pipeline-attempts/20261106T214341304797Z-cb9ea57e/results.json",
         "report_sha256": "62b2636354b178b3601689711ebc43200c53072b5fe129b8605b3b51d625af36",
         "canonical_actual_sha256": expected_pins["canonical_actual.tsv.gz"]},
    ]
    for run in source_runs:
        if sha((ROOT / run["report"]).read_bytes()) != run["report_sha256"]:
            raise ValueError(f"frozen source report changed: seed {run['seed']}")
    payload = {
        "schema": "cu66-v91k-chroma-cache-independent-model-v1",
        "status": "PASS_SCHEDULE_AND_RGB_PARITY",
        "frozen_report": {
            "path": str(FROZEN_REPORT.relative_to(ROOT)),
            "sha256": sha(FROZEN_REPORT.read_bytes()),
            "source_revision": report["source_revision"],
            "source_sha256": report["source_sha256"],
            "vectors_sha256": report["vectors_sha256"],
        },
        "inputs": input_pins,
        "source_runs": source_runs,
        "dimensions": {"luma": [WIDTH, HEIGHT], "chroma": [CW, CH]},
        "expected": {
            "cached_reads_per_frame": 518400,
            "cached_y_reads": 345600,
            "cached_cb_reads": 86400,
            "cached_cr_reads": 86400,
            "uncached_reads_per_frame": 3110400,
            "paired_row_fills_per_frame": 240,
            "logical_cache_bytes": 1440,
            "row_bank_mapping": "slot=row&1, bank=column&1, word=column//2; each 16-bit word pairs Cb and Cr",
            "fnv": {"offset": FNV_OFFSET, "prime": FNV_PRIME, "address_encoding": "u32 little-endian followed by byte value", "modulus": "2^64"},
        },
        "frames": rows,
        "synthetic_edge_cases": [edge_result],
        "proof_scope": "Independent software schedule/address-data hash and RGB565 parity against frozen independent goldens. No RTL, RAM inference, frequency, routed timing, physical bandwidth, 30fps, or under-10ms proof.",
    }
    (AREA / "model-results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export BR88 context vectors from the frozen V88 Python decoder.

Each context is kept as a separate exact-bit stream.  The payload and sparse
outputs are derived from V88's verified decoded chunk; no V91 implementation is
used as an oracle.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTROPY = ROOT / "experiments/python-gamebub-v88/entropy"
OUT = ROOT / "experiments/python-gamebub-v91b/context-vectors"
SELECTED = ((0, 0), (0, 1), (0, 3), (3, 50))
BAND_LIMITS = (1, 6, 21, 64)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def zigzag_order() -> list[int]:
    return sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                             (i // 8) if (i // 8 + i % 8) % 2 else -(i // 8)))


ZIGZAG = zigzag_order()


def packet_streams(packet: bytes) -> list[dict]:
    """Read the BR88 stream descriptors after frozen decode validates the packet."""
    if packet[:4] != b"BR88":
        raise ValueError("unexpected BR88 packet")
    lengths = struct.unpack_from("<4I", packet, 14)
    offset = 42
    result = []
    for length in lengths:
        if length < 6 or offset + length > len(packet) - 4:
            raise ValueError("invalid BR88 stream extent")
        k0, k1, bit_size = struct.unpack_from("<BBI", packet, offset)
        data = packet[offset + 6:offset + length]
        if len(data) != (bit_size + 7) // 8:
            raise ValueError("BR88 exact context bit length mismatch")
        result.append({"k0": k0, "k1": k1, "bit_size": bit_size, "data": data})
        offset += length
    if offset != len(packet) - 4:
        raise ValueError("BR88 stream length mismatch")
    return result


def sparse_outputs(coefficients: list[int], blocks: int, band: int) -> list[list[int]]:
    if band == 0:
        return [[block, 0, coefficients[block * 64]] for block in range(blocks)]
    lo, hi = BAND_LIMITS[band - 1], BAND_LIMITS[band]
    width = hi - lo
    result = []
    # Position increases monotonically in the stream: block, then zigzag slot.
    for block in range(blocks):
        for pos in range(lo, hi):
            value = coefficients[block * 64 + ZIGZAG[pos]]
            if value:
                result.append([block, ZIGZAG[pos], value])
    return result


def signed_code(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def signed_value(value: int) -> int:
    return -(value // 2) - 1 if value & 1 else value // 2


def rice_bits(value: int, k: int, escape: int) -> list[int]:
    if value < 0 or k < 0:
        raise ValueError("Rice input out of range")
    quotient = value >> k
    if quotient < 15:
        return [0] * quotient + [1] + [
            (value >> shift) & 1 for shift in range(k - 1, -1, -1)
        ]
    if value >= 1 << escape:
        raise ValueError("Rice escape input out of range")
    return [0] * 15 + [(value >> shift) & 1 for shift in range(escape - 1, -1, -1)]


def pack_bits(bits: list[int]) -> bytes:
    packed = bytearray((len(bits) + 7) // 8)
    for at, bit in enumerate(bits):
        packed[at // 8] |= bit << (7 - at % 8)
    return bytes(packed)


def synthetic_row(case_id: str, blocks: int, band: int, k0: int, k1: int,
                  values: list[tuple[int, int]] | None = None,
                  dc_values: list[int] | None = None, rice_cls=None) -> dict:
    """Build a small valid isolated context for boundaries the corpus may miss.

    AC `values` are (linear band position, signed coefficient) pairs. DC values
    are one signed DC coefficient per block. These fixtures are independent of
    the corpus and are tagged synthetic in their ids.
    """
    if band == 0:
        assert dc_values is not None and len(dc_values) == blocks
        bits: list[int] = []
        expected = []
        for block, value in enumerate(dc_values):
            bits.extend(rice_bits(signed_code(value), k0, 14))
            expected.append([block, 0, value])
        event_count = blocks
    else:
        assert values is not None
        lo, hi = BAND_LIMITS[band - 1], BAND_LIMITS[band]
        width = hi - lo
        bits = []
        expected = []
        previous = -1
        for position, value in values:
            if not previous < position < blocks * width or value == 0:
                raise ValueError("invalid synthetic AC event")
            bits.extend(rice_bits(position - previous - 1, k0, 24))
            bits.extend(rice_bits(signed_code(value) - 1, k1, 12))
            block, local = divmod(position, width)
            expected.append([block, ZIGZAG[lo + local], value])
            previous = position
        event_count = len(values)
    data = pack_bits(bits)
    if rice_cls is not None:
        reader = rice_cls(data, len(bits))
        observed = []
        if band == 0:
            observed = [[block, 0, signed_value(reader.value(k0, 14))]
                        for block in range(blocks)]
        else:
            position = -1
            lo = BAND_LIMITS[band - 1]
            width = BAND_LIMITS[band] - lo
            for _ in range(event_count):
                position += reader.value(k0, 24) + 1
                value = signed_value(reader.value(k1, 12) + 1)
                block, local = divmod(position, width)
                observed.append([block, ZIGZAG[lo + local], value])
        reader.end()
        if observed != expected:
            raise AssertionError(f"synthetic frozen-reader mismatch: {case_id}")
    return {
        "id": case_id,
        "blocks": blocks,
        "band": band,
        "k0": k0,
        "k1": 255 if band == 0 else k1,
        "event_count": event_count,
        "bit_size": len(bits),
        "data_hex": data.hex(),
        "expected": expected,
        "expected_error": 0,
        "case_type": "synthetic",
        "expected_sha256": sha_bytes(json.dumps(expected, separators=(",", ":")).encode()),
    }


def synthetic_rows(rice_cls=None) -> list[dict]:
    rows = [
        synthetic_row("synthetic:dc:signed-extremes", 5, 0, 0, 255,
                      dc_values=[-2048, 2048, -1, 0, 1], rice_cls=rice_cls),
        synthetic_row("synthetic:ac1:empty", 3, 1, 0, 0, values=[], rice_cls=rice_cls),
        synthetic_row("synthetic:ac2:empty", 3, 2, 0, 0, values=[], rice_cls=rice_cls),
        synthetic_row("synthetic:ac3:empty", 3, 3, 0, 0, values=[], rice_cls=rice_cls),
        # Wide gaps cross block boundaries and finish at the last valid slot.
        synthetic_row("synthetic:ac1:run-gaps", 5, 1, 0, 0,
                      values=[(0, 1), (4, -1), (5, 2048), (24, -2048)], rice_cls=rice_cls),
        synthetic_row("synthetic:ac1:level-extremes", 1, 1, 0, 0,
                      values=[(0, -2048), (1, 2048)], rice_cls=rice_cls),
        # Exercise ordinary and escape codes in the run context at a nonzero k.
        synthetic_row("synthetic:ac3:run-escape", 2, 3, 2, 1,
                      values=[(0, 1), (64, -7)], rice_cls=rice_cls),
    ]
    return rows


def main() -> None:
    data_mod = load_module("v91b_frozen_data", ENTROPY / "data.py")
    codec = load_module("v91b_frozen_codec", ENTROPY / "codec.py")
    rows = []
    selected_seen = set()
    actual_chunks = 0
    for frame in data_mod.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        if identity not in SELECTED:
            continue
        selected_seen.add(identity)
        for plane_index, plane in enumerate(frame["variants"]["65536"]):
            for chunk_index, chunk in enumerate(plane):
                packet = chunk["br88"]
                coefficients = codec.decode(packet, chunk["blocks"], 1)
                coefficient_sha = sha_bytes(struct.pack("<" + "h" * len(coefficients), *coefficients))
                if coefficient_sha != chunk["coefficient_sha256"]:
                    raise AssertionError(f"frozen V88 coefficient hash mismatch: {identity}/{plane_index}/{chunk_index}")
                contexts = packet_streams(packet)
                counts = (chunk["blocks"], *struct.unpack_from("<3I", packet, 30))
                for band, context in enumerate(contexts):
                    expected = sparse_outputs(coefficients, chunk["blocks"], band)
                    row = {
                        "id": f"actual:c{identity[0]}:f{identity[1]}:p{plane_index}:t{chunk_index}:b{band}",
                        "blocks": chunk["blocks"],
                        "band": band,
                        "k0": context["k0"],
                        "k1": 255 if band == 0 else context["k1"],
                        "event_count": counts[band],
                        "bit_size": context["bit_size"],
                        "data_hex": context["data"].hex(),
                        "expected": expected,
                        "expected_error": 0,
                        "case_type": "actual",
                        "source": {"cohort": identity[0], "fid": identity[1],
                                   "plane": plane_index, "chunk": chunk_index},
                        "coefficient_sha256": coefficient_sha,
                        "expected_sha256": sha_bytes(json.dumps(expected, separators=(",", ":")).encode()),
                    }
                    if len(expected) != counts[band]:
                        raise AssertionError(f"context output count mismatch: {row['id']} {len(expected)} != {counts[band]}")
                    rows.append(row)
                actual_chunks += 1
    if selected_seen != set(SELECTED):
        raise AssertionError(f"selected sources missing: {set(SELECTED) - selected_seen}")
    if actual_chunks != 12:
        raise AssertionError(f"expected 12 selected chunks, got {actual_chunks}")

    extra = synthetic_rows(codec.Rice)
    rows.extend(extra)
    OUT.mkdir(parents=True, exist_ok=True)
    jsonl = b"".join((json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n").encode() for row in rows)
    fixture_path = OUT / "contexts.jsonl.gz"
    with fixture_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            stream.write(jsonl)
    index = {
        "schema": "cu66-v91b-br88-context-vectors-v1",
        "status": "PASS_FROZEN_V88_CONTEXT_VECTOR_EXPORT",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selection": [list(item) for item in SELECTED],
        "actual_chunks": actual_chunks,
        "actual_contexts": sum(row["case_type"] == "actual" for row in rows),
        "synthetic_contexts": len(extra),
        "contexts": len(rows),
        "actual_event_counts": {
            "dc": sum(row["event_count"] for row in rows if row["case_type"] == "actual" and row["band"] == 0),
            "ac_nonzero": sum(row["event_count"] for row in rows if row["case_type"] == "actual" and row["band"] != 0),
        },
        "fixture": {"path": fixture_path.name, "gzip_sha256": sha_file(fixture_path),
                    "jsonl_sha256": sha_bytes(jsonl)},
        "source_sha256": {
            "scripts/cu66-v91b/build_vectors.py": sha_file(Path(__file__).resolve()),
            "experiments/python-gamebub-v88/entropy/data.py": sha_file(ENTROPY / "data.py"),
            "experiments/python-gamebub-v88/entropy/codec.py": sha_file(ENTROPY / "codec.py"),
            "experiments/python-gamebub-v88/entropy/index.json": sha_file(ENTROPY / "index.json"),
            "experiments/python-gamebub-v88/entropy/attempts/20261106T150638168868Z-fb236a5e/data.bin.gz": sha_file(ENTROPY / "attempts/20261106T150638168868Z-fb236a5e/data.bin.gz"),
        },
        "input_counts": {"native_sources": 457, "chunks": 1371},
        "format": "One JSONL row is one isolated BR88 context: id, blocks, band (0=DC; 1..3=AC), k0, k1 (255 for DC), event_count, exact bit_size, MSB-first packed data_hex, expected [[block,rasterindex,signedvalue],...], expected_error (0=success). Padding is zero and excluded from bit_size. Actual rows carry source identity and full/sparse coefficient hashes.",
        "scope": "Actual context bytes and sparse outputs are derived by the frozen V88 Python decoder after it validates packet CRC, bounds, and full coefficient hash. The RTL interface receives contexts only; upstream BR88 CRC metadata is not validated by RTL. Synthetic rows exercise empty AC, signed extremes, and run gaps. No RTL or timing claim.",
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps({"actual_chunks": actual_chunks, "actual_contexts": index["actual_contexts"],
                      "synthetic_contexts": len(extra), "events": index["actual_event_counts"],
                      "fixture_sha256": index["fixture"]["gzip_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

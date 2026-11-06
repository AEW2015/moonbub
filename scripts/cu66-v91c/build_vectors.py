#!/usr/bin/env python3
"""Export complete BR88 packet fixtures using the frozen V88 decoder as oracle.

Actual packet bytes and source coefficients come from V88's frozen corpus.
Synthetic packets are built here from explicit coefficient values and must
round-trip through that same frozen decoder before they are exported.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTROPY = ROOT / "experiments/python-gamebub-v88/entropy"
OUT = ROOT / "experiments/python-gamebub-v91c/packet-vectors"
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


def signed_code(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def rice_bits(value: int, k: int, escape: int) -> list[int]:
    if value < 0 or k < 0:
        raise ValueError("Rice value must be nonnegative")
    quotient = value >> k
    if quotient < 15:
        return [0] * quotient + [1] + [
            (value >> shift) & 1 for shift in range(k - 1, -1, -1)
        ]
    if value >= 1 << escape:
        raise ValueError("Rice escape value out of range")
    return [0] * 15 + [(value >> shift) & 1 for shift in range(escape - 1, -1, -1)]


def pack_bits(bits: list[int]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for at, bit in enumerate(bits):
        out[at // 8] |= bit << (7 - at % 8)
    return bytes(out)


def make_coded_packet(coefficients: list[int], blocks: int) -> bytes:
    if len(coefficients) != blocks * 64:
        raise ValueError("coefficient count mismatch")
    streams: list[tuple[int, int, int, bytes]] = []
    dc_bits = []
    for block in range(blocks):
        value = coefficients[block * 64]
        if not -2048 <= value <= 2048:
            raise ValueError("DC out of range")
        dc_bits.extend(rice_bits(signed_code(value), 0, 14))
    streams.append((0, 255, len(dc_bits), pack_bits(dc_bits)))

    counts = []
    for band, (lo, hi) in enumerate(zip(BAND_LIMITS, BAND_LIMITS[1:])):
        width = hi - lo
        events = []
        for block in range(blocks):
            for slot in range(lo, hi):
                index = ZIGZAG[slot]
                value = coefficients[block * 64 + index]
                if value:
                    if not -2048 <= value <= 2048:
                        raise ValueError("AC out of range")
                    events.append((block * width + slot - lo, value))
        counts.append(len(events))
        bits = []
        previous = -1
        for position, value in events:
            bits.extend(rice_bits(position - previous - 1, 0, 24))
            bits.extend(rice_bits(signed_code(value) - 1, 0, 12))
            previous = position
        streams.append((0, 0, len(bits), pack_bits(bits)))

    body = bytearray(struct.pack("<4sBBIHH", b"BR88", 1, 0, blocks, 1, 0))
    body.extend(struct.pack("<4I", *(6 + len(data) for _, _, _, data in streams)))
    body.extend(struct.pack("<3I", *counts))
    for k0, k1, bit_size, data in streams:
        body.extend(struct.pack("<BBI", k0, k1, bit_size))
        body.extend(data)
    body.extend(struct.pack("<I", zlib.crc32(body) & 0xFFFFFFFF))
    return bytes(body)


def make_raw_packet(coefficients: list[int], blocks: int) -> bytes:
    if len(coefficients) != blocks * 64 or any(not -2048 <= value <= 2048 for value in coefficients):
        raise ValueError("invalid raw coefficients")
    payload = struct.pack("<" + "h" * len(coefficients), *coefficients)
    body = bytearray(struct.pack("<4sBBIHH", b"BR88", 1, 1, blocks, 1, 0))
    body.extend(struct.pack("<4I", 128 * blocks, 0, 0, 0))
    body.extend(struct.pack("<3I", 0, 0, 0))
    body.extend(payload)
    body.extend(struct.pack("<I", zlib.crc32(body) & 0xFFFFFFFF))
    return bytes(body)


def coefficient_hash(coefficients: list[int]) -> str:
    return sha_bytes(struct.pack("<" + "h" * len(coefficients), *coefficients))


def outputs(coefficients: list[int], blocks: int, raw_dense: bool = False) -> list[list[int]]:
    if raw_dense:
        return [[block, index, coefficients[block * 64 + index]]
                for block in range(blocks) for index in range(64)]
    result = [[block, 0, coefficients[block * 64]] for block in range(blocks)]
    for lo, hi in zip(BAND_LIMITS, BAND_LIMITS[1:]):
        for block in range(blocks):
            for slot in range(lo, hi):
                index = ZIGZAG[slot]
                value = coefficients[block * 64 + index]
                if value:
                    result.append([block, index, value])
    return result


def make_row(case_id: str, packet: bytes, coefficients: list[int], blocks: int,
             case_type: str, source=None, raw_dense: bool = False) -> dict:
    packed = struct.pack("<" + "h" * len(coefficients), *coefficients)
    expected = outputs(coefficients, blocks, raw_dense)
    return {
        "id": case_id,
        "blocks": blocks,
        "packet_hex": packet.hex(),
        "expected": expected,
        "expected_error": 0,
        "coefficient_sha256": sha_bytes(packed),
        "canonical_dense_sha256": sha_bytes(packed),
        "packet_sha256": sha_bytes(packet),
        "case_type": case_type,
        "expected_encoding": "dense-raster-tuples" if raw_dense else "sparse-dc-then-ac-bands",
        **({"source": source} if source is not None else {}),
    }


def main() -> None:
    data_mod = load_module("v91c_frozen_data", ENTROPY / "data.py")
    codec = load_module("v91c_frozen_codec", ENTROPY / "codec.py")
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
                coefficient_sha = coefficient_hash(coefficients)
                if coefficient_sha != chunk["coefficient_sha256"]:
                    raise AssertionError(f"frozen V88 coefficient hash mismatch: {identity}/{plane_index}/{chunk_index}")
                if sha_bytes(packet) != chunk["br88_sha256"]:
                    raise AssertionError(f"frozen V88 fullpacket hash mismatch: {identity}/{plane_index}/{chunk_index}")
                source = {"cohort": identity[0], "fid": identity[1],
                          "plane": plane_index, "chunk": chunk_index,
                          "packet_sha256": chunk["br88_sha256"],
                          "coefficient_sha256": chunk["coefficient_sha256"]}
                rows.append(make_row(
                    f"actual:c{identity[0]}:f{identity[1]}:p{plane_index}:t{chunk_index}",
                    packet, coefficients, chunk["blocks"], "actual", source,
                    raw_dense=bool(packet[5] & 1)))
                actual_chunks += 1
    if selected_seen != set(SELECTED) or actual_chunks != 12:
        raise AssertionError(f"selection mismatch: seen={selected_seen}, chunks={actual_chunks}")

    synthetic = []
    zero_coefficients = [0] * 64
    synthetic.append(("synthetic:coded:zero-ac", make_coded_packet(zero_coefficients, 1), zero_coefficients, 1, False))

    extreme_coefficients = [0] * 128
    extreme_coefficients[0] = -2048
    extreme_coefficients[64] = 2048
    # Exercise both signs and both coefficient limits in several AC bands.
    for index, value in ((ZIGZAG[1], -2048), (ZIGZAG[5], 2048),
                         (ZIGZAG[6], 2048), (ZIGZAG[20], -2048),
                         (ZIGZAG[21], -2048), (ZIGZAG[63], 2048)):
        extreme_coefficients[index] = value
    synthetic.append(("synthetic:coded:signed-extreme-dc-ac",
                      make_coded_packet(extreme_coefficients, 2), extreme_coefficients, 2, False))

    raw_extremes = [0] * 64
    raw_extremes[0] = -2048
    raw_extremes[1] = 2048
    raw_extremes[63] = -2048
    synthetic.append(("synthetic:raw:signed-extremes",
                      make_raw_packet(raw_extremes, 1), raw_extremes, 1, True))
    raw_zero = [0] * 64
    synthetic.append(("synthetic:raw:all-zero",
                      make_raw_packet(raw_zero, 1), raw_zero, 1, True))

    for case_id, packet, expected_coefficients, blocks, raw_dense in synthetic:
        decoded = codec.decode(packet, blocks, 1)
        if decoded != expected_coefficients:
            raise AssertionError(f"synthetic frozen-reader mismatch: {case_id}")
        rows.append(make_row(case_id, packet, decoded, blocks, "synthetic", raw_dense=raw_dense))

    OUT.mkdir(parents=True, exist_ok=True)
    jsonl = b"".join((json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n").encode() for row in rows)
    fixture_path = OUT / "packets.jsonl.gz"
    with fixture_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            stream.write(jsonl)
    source_index = json.loads((ENTROPY / "index.json").read_text())
    data_path = ENTROPY / source_index["data"]["path"]
    index = {
        "schema": "cu66-v91c-br88-fullpacket-vectors-v1",
        "status": "PASS_FROZEN_V88_FULLPACKET_ORACLE_EXPORT",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selection": [list(item) for item in SELECTED],
        "actual_chunks": actual_chunks,
        "synthetic_packets": len(synthetic),
        "packets": len(rows),
        "fixture": {"path": fixture_path.name, "gzip_sha256": sha_file(fixture_path),
                    "jsonl_sha256": sha_bytes(jsonl)},
        "source_sha256": {
            "scripts/cu66-v91c/build_vectors.py": sha_file(Path(__file__).resolve()),
            "experiments/python-gamebub-v88/entropy/data.py": sha_file(ENTROPY / "data.py"),
            "experiments/python-gamebub-v88/entropy/codec.py": sha_file(ENTROPY / "codec.py"),
            "experiments/python-gamebub-v88/entropy/index.json": sha_file(ENTROPY / "index.json"),
            f"experiments/python-gamebub-v88/entropy/{source_index['data']['path']}": sha_file(data_path),
        },
        "source_data": {"path": source_index["data"]["path"],
                        "gzip_sha256": source_index["data"]["gzip_sha256"],
                        "raw_sha256": source_index["data"]["raw_sha256"],
                        "native_sources": source_index["data"].get("native_sources", source_index.get("native_sources")),
                        "chunks": source_index.get("chunks")},
        "format": "One JSONL row is a complete BR88 packet: id, blocks, packet_hex, expected [[block,raster_index,signed_value],...], expected_error, coefficient_sha256, canonical_dense_sha256, packet_sha256, case_type, expected_encoding, and source for corpus rows. Actual/coded expected tuples are DC then nonzero AC in bands 1, 2, 3; raw synthetic tuples include every raster coefficient, including zeros. Dense SHA-256 is over all coefficients packed signed-16 little-endian in block/raster order.",
        "scope": "The frozen V88 Python decoder validates complete packet bounds, metadata, streams/raw payload, coefficient range, and CRC before outputs are exported. Synthetic packets are checked by that decoder. This is a packet coefficient oracle only, not a full-pixel reconstruction proof.",
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps({"actual_chunks": actual_chunks, "synthetic_packets": len(synthetic),
                      "packets": len(rows), "fixture_sha256": index["fixture"]["gzip_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

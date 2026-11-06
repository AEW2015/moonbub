#!/usr/bin/env python3
"""Build V91d coefficient and packed-scratch memory goldens.

Inputs are the frozen V91c complete BR88 packet vectors. Every packet is
decoded by the frozen V88 codec, then this script independently constructs
the sparse coefficient stream and packed scratch byte image. No RTL is read
or imported here.
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
V91C = ROOT / "experiments/python-gamebub-v91c/packet-vectors"
ENTROPY = ROOT / "experiments/python-gamebub-v88/entropy"
OUT = ROOT / "experiments/python-gamebub-v91d/vectors"
BURST = 16
HEADER = 32
MAX_BLOCKS = 8192
BAND_LIMITS = (1, 6, 21, 64)
ZIGZAG = tuple(sorted(range(64), key=lambda i: (
    i // 8 + i % 8,
    i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
INVERSE = {raster: slot for slot, raster in enumerate(ZIGZAG)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def align16(n: int) -> int:
    return (n + BURST - 1) // BURST * BURST


def dense_bytes(coefficients: list[int]) -> bytes:
    return struct.pack("<" + "h" * len(coefficients), *coefficients)


def rows_for(coefficients: list[int], blocks: int, raw: bool):
    counts = [0, 0, 0]
    sparse = []
    if raw:
        sparse = [[0, block, index, coefficients[block * 64 + index]]
                  for block in range(blocks) for index in range(64)]
    else:
        for block in range(blocks):
            sparse.append([0, block, 0, coefficients[block * 64]])
        for band, (lo, hi) in enumerate(zip(BAND_LIMITS, BAND_LIMITS[1:]), 1):
            for block in range(blocks):
                for slot in range(lo, hi):
                    index = ZIGZAG[slot]
                    value = coefficients[block * 64 + index]
                    if value:
                        counts[band - 1] += 1
                        sparse.append([band, block, index, value])
    return counts, sparse


def packed_image(coefficients: list[int], blocks: int, raw: bool,
                 counts: list[int]) -> bytes:
    if raw:
        segments = [dense_bytes(coefficients)]
    else:
        dc = struct.pack("<" + "h" * blocks,
                         *(coefficients[block * 64] for block in range(blocks)))
        ac = []
        for band, (lo, hi) in enumerate(zip(BAND_LIMITS, BAND_LIMITS[1:]), 1):
            events = []
            for block in range(blocks):
                for slot in range(lo, hi):
                    index = ZIGZAG[slot]
                    value = coefficients[block * 64 + index]
                    if value:
                        word = (block << 19) | (index << 13) | (value & 0x1fff)
                        events.append(word)
            assert len(events) == counts[band - 1]
            ac.append(struct.pack("<" + "I" * len(events), *events))
        segments = [dc, *ac]
    sizes = [len(segment) for segment in segments]
    used_bytes = HEADER + sum(align16(size) for size in sizes)
    starts = []
    at = HEADER
    for size in sizes:
        starts.append(at)
        at += align16(size)
    header = struct.pack("<8I", 0x43393150, blocks, int(raw), *counts,
                         used_bytes, 0)
    image = bytearray(header)
    for segment in segments:
        image.extend(segment)
        image.extend(bytes(align16(len(segment)) - len(segment)))
    assert len(image) == used_bytes
    # Explicitly pin the fixed layout for a simple C++ consumer.
    assert starts[0] == HEADER
    return bytes(image)


def rice_bits(value: int, escape: int) -> list[int]:
    quotient = value
    if quotient < 15:
        return [0] * quotient + [1]
    if value >= 1 << escape:
        raise ValueError("Rice escape value out of range")
    return [0] * 15 + [(value >> shift) & 1 for shift in range(escape - 1, -1, -1)]


def pack_bits(bits: list[int]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        out[i // 8] |= bit << (7 - i % 8)
    return bytes(out)


def packet_max_blocks() -> bytes:
    blocks = MAX_BLOCKS
    # One DC stream, two empty AC streams, then band-3 final record.
    dc_data = pack_bits([1] * blocks)
    pos = (blocks - 1) * 43 + 42
    ac_bits = rice_bits(pos, 24) + rice_bits((2 * 2048 - 1) - 1, 12)
    ac_data = pack_bits(ac_bits)
    streams = (([1] * blocks, dc_data), ([], b""), ([], b""), (ac_bits, ac_data))
    out = bytearray(struct.pack("<4sBBIHH", b"BR88", 1, 0, blocks, 1, 0))
    out.extend(struct.pack("<4I", *(6 + len(data) for _, data in streams)))
    out.extend(struct.pack("<3I", 0, 0, 1))
    for stream_index, (bits, data) in enumerate(streams):
        out.extend(struct.pack("<BBI", 0, 255 if stream_index == 0 else 0, len(bits)))
        out.extend(data)
    out.extend(struct.pack("<I", zlib.crc32(out) & 0xffffffff))
    return bytes(out)


def make_case(case_id: str, packet: bytes, blocks: int, coefficients: list[int],
              raw: bool, case_type: str, source=None, receipt=None) -> dict:
    counts, sparse = rows_for(coefficients, blocks, raw)
    if raw:
        assert counts == [0, 0, 0]
    dense = dense_bytes(coefficients)
    image = packed_image(coefficients, blocks, raw, counts)
    return {
        "id": case_id, "blocks": blocks, "raw": raw, "counts": counts,
        "packet_hex": packet.hex(), "sparse": sparse,
        "dense_hex": dense.hex(), "coefficient_sha256": sha(dense),
        "packed_hex": image.hex(), "packed_sha256": sha(image),
        "used_bytes": len(image), "case_type": case_type,
        **({"source": source} if source else {}),
        **({"v91c_scratch_sha256": receipt["scratch_sha256"]} if receipt else {}),
    }


def main() -> None:
    codec = load_module("v91d_frozen_v88_codec", ENTROPY / "codec.py")
    packet_path = V91C / "packets.jsonl.gz"
    packet_index = json.loads((V91C / "index.json").read_text())
    assert sha(packet_path.read_bytes()) == packet_index["fixture"]["gzip_sha256"]
    rows = []
    receipts_path = ROOT / "experiments/python-gamebub-v91c/scratch-attempts/20261106T173557536651Z-250df7c8/chunks.jsonl"
    receipts = {}
    if receipts_path.exists():
        for line in receipts_path.read_text().splitlines():
            item = json.loads(line)
            key = (item["cohort"], item["fid"], item["plane"], item["chunk"])
            receipts[key] = item
    source_packets = [json.loads(line) for line in gzip.decompress(packet_path.read_bytes()).splitlines()]
    assert len(source_packets) == 16
    for item in source_packets:
        packet, blocks = bytes.fromhex(item["packet_hex"]), item["blocks"]
        coefficients = codec.decode(packet, blocks, 1)
        dense = dense_bytes(coefficients)
        assert sha(dense) == item["coefficient_sha256"] == item["canonical_dense_sha256"]
        assert sha(packet) == item["packet_sha256"]
        raw = bool(packet[5] & 1)
        counts = list(struct.unpack_from("<3I", packet, 30))
        expected_counts, sparse = rows_for(coefficients, blocks, raw)
        assert counts == expected_counts
        old_sparse = [[block, index, value] for _, block, index, value in sparse]
        assert old_sparse == item["expected"]
        source = item.get("source")
        receipt = receipts.get((source["cohort"], source["fid"], source["plane"], source["chunk"])) if source else None
        if item.get("case_type") == "actual":
            assert receipt is not None, f"missing V91c scratch receipt for {item['id']}"
            packed = packed_image(coefficients, blocks, raw, counts)
            assert sha(packed) == receipt["scratch_sha256"], f"V91c scratch mismatch: {item['id']}"
        rows.append(make_case(item["id"], packet, blocks, coefficients, raw,
                              item.get("case_type", "frozen"), source, receipt))

    max_packet = packet_max_blocks()
    max_coefficients = codec.decode(max_packet, MAX_BLOCKS, 1)
    assert max_coefficients[-64 + ZIGZAG[63]] == -2048
    rows.append(make_case("scratch_8192_last_record", max_packet, MAX_BLOCKS,
                          max_coefficients, False, "directed"))

    # Capacity exact vs. one burst short: RAW 2048 has exactly this image size.
    exact_raw_bytes = HEADER + align16(2048 * 128)
    assert exact_raw_bytes == 262176 and exact_raw_bytes % BURST == 0
    assert exact_raw_bytes - BURST < exact_raw_bytes

    OUT.mkdir(parents=True, exist_ok=True)
    jsonl = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                    for row in rows)
    fixture = OUT / "coefficients.jsonl.gz"
    with fixture.open("wb") as raw_out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, mtime=0, compresslevel=9) as stream:
            stream.write(jsonl)
    source_hashes = {
        "scripts/cu66-v91d/build_vectors.py": sha(Path(__file__).read_bytes()),
        "scripts/cu66-v91c/build_vectors.py": sha((ROOT / "scripts/cu66-v91c/build_vectors.py").read_bytes()),
        "experiments/python-gamebub-v91c/packet-vectors/index.json": sha((V91C / "index.json").read_bytes()),
        "experiments/python-gamebub-v91c/packet-vectors/packets.jsonl.gz": sha(packet_path.read_bytes()),
        "experiments/python-gamebub-v88/entropy/codec.py": sha((ENTROPY / "codec.py").read_bytes()),
        "experiments/python-gamebub-v88/entropy/data.py": sha((ENTROPY / "data.py").read_bytes()),
        "experiments/python-gamebub-v88/entropy/index.json": sha((ENTROPY / "index.json").read_bytes()),
    }
    frozen_data_index = json.loads((ENTROPY / "index.json").read_text())
    frozen_data_path = ENTROPY / frozen_data_index["data"]["path"]
    source_hashes[f"experiments/python-gamebub-v88/entropy/{frozen_data_index['data']['path']}"] = sha(frozen_data_path.read_bytes())
    index = {
        "schema": "cu66-v91d-coefficient-packed-image-v1",
        "status": "PASS_FROZEN_V88_COEFFICIENT_AND_PACKED_IMAGE_GOLDENS",
        "parent_commit": "4ff660d4be06ef522de977bb78badd2b64a79e72",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "packets": len(rows), "actual_cases": sum(row["case_type"] == "actual" for row in rows),
        "synthetic_cases": sum(row["case_type"] == "synthetic" for row in rows),
        "directed_cases": sum(row["case_type"] == "directed" for row in rows),
        "fixture": {"path": fixture.name, "gzip_sha256": sha(fixture.read_bytes()), "jsonl_sha256": sha(jsonl)},
        "source_sha256": source_hashes,
        "scratch_layout": {"header_bytes": HEADER, "burst_bytes": BURST,
                           "max_blocks": MAX_BLOCKS, "packed_word": "block[31:19]|raster[18:13]|signed13[12:0]",
                           "exact_capacity_case": {"raw_blocks": 2048, "used_bytes": exact_raw_bytes,
                                                    "one_burst_short_bytes": exact_raw_bytes - BURST}},
        "format": "JSONL rows include packet bytes, every sparse scratch write tuple [band,block,raster_index,signed_value], dense signed16LE coefficient bytes, packed scratch image bytes (descriptor, segment contents and burst padding), and SHA-256 values. C++ can parse hex directly; no full-pixel pipeline is represented.",
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(f"V91D_VECTOR_PASS cases={len(rows)} gzip_sha256={index['fixture']['gzip_sha256']}")


if __name__ == "__main__":
    main()

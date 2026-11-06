#!/usr/bin/env python3
"""Export replayable BR88 Rice symbol vectors using the frozen V88 reader."""
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
OUT = ROOT / "experiments/python-gamebub-v91/rtl-vectors"
SELECTED = ((0, 0), (0, 1), (0, 3), (3, 50))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bits_for(value: int, k: int, escape: int, force_escape: bool = False) -> list[int]:
    """Inverse of the frozen Rice.value syntax, used only to make fixtures."""
    if value < 0 or (force_escape and value >= (1 << escape)):
        raise ValueError("synthetic Rice value out of range")
    quotient = 15 if force_escape else value >> k
    if quotient < 15:
        return [0] * quotient + [1] + [
            (value >> shift) & 1 for shift in range(k - 1, -1, -1)
        ]
    return [0] * 15 + [
        (value >> shift) & 1 for shift in range(escape - 1, -1, -1)
    ]


def pack_bits(bits: list[int]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for at, bit in enumerate(bits):
        out[at // 8] |= bit << (7 - at % 8)
    return bytes(out)


def value_for_q(q: int, k: int, salt: int) -> int:
    if q == 15:
        return (1 << (max(k, 0))) + (salt & 7)
    return (q << k) | ((salt * 13) & ((1 << k) - 1 if k else 0))


def synthetic_case(reader_cls, case_id: str, k: int, escape: int, alignment: int):
    # Find a short prefix of valid ordinary values that places the first target
    # at the requested word alignment. No unparsed leading bits are inserted.
    paths = {0: ()}
    frontier = [0]
    while alignment not in paths:
        residue = frontier.pop(0)
        for q in range(15):
            nxt = (residue + k + q + 1) % 32
            if nxt not in paths:
                paths[nxt] = paths[residue] + (q,)
                frontier.append(nxt)
    stream_bits: list[int] = []
    values: list[int] = []
    for n, q in enumerate(paths[alignment]):
        value = value_for_q(q, k, n)
        stream_bits.extend(bits_for(value, k, escape))
        values.append(value)
    for q in range(16):
        value = value_for_q(q, k, q + alignment)
        stream_bits.extend(bits_for(value, k, escape, force_escape=(q == 15)))
        values.append(value)
    data = pack_bits(stream_bits)
    reader = reader_cls(data, len(stream_bits))
    for value in values:
        observed = reader.value(k, escape)
        if observed != value:
            raise AssertionError((case_id, observed, value))
    reader.end()
    return {
        "id": case_id,
        "bit_size": len(stream_bits),
        "data_hex": data.hex(),
        "requests": reader.requests,
    }


def main() -> None:
    data_mod = load_module("v91_frozen_data", ENTROPY / "data.py")
    codec = load_module("v91_frozen_codec", ENTROPY / "codec.py")
    original_rice = codec.Rice

    class RecordingRice(original_rice):
        def __init__(self, data, size):
            super().__init__(data, size)
            self.requests = []
            self.stream_data = bytes(data)
            self.stream_size = size
            if active_streams is not None:
                active_streams.append(self)

        def value(self, k, escape):
            value = super().value(k, escape)
            self.requests.append([k, escape, value, self.at])
            return value

    codec.Rice = RecordingRice
    rows = []
    selected_seen = set()
    stream_number = 0
    active_streams = None
    for frame in data_mod.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        if identity not in SELECTED:
            continue
        selected_seen.add(identity)
        for plane_index, plane in enumerate(frame["variants"]["65536"]):
            for chunk_index, chunk in enumerate(plane):
                active_streams = []
                coefficients = codec.decode(chunk["br88"], chunk["blocks"], 1)
                if hashlib.sha256(struct.pack("<" + "h" * len(coefficients), *coefficients)).hexdigest() != chunk["coefficient_sha256"]:
                    raise AssertionError(f"chunk coefficient hash mismatch: {identity}/{plane_index}/{chunk_index}")
                # decode() constructs exactly four Rice streams on coded (not
                # raw) packets. Raw packets correctly have no stream requests.
                streams = active_streams
                if not chunk["br88_raw"] and len(streams) != 4:
                    raise AssertionError("expected four BR88 Rice streams")
                for stream_index, stream in enumerate(streams):
                    rows.append({
                        "id": f"actual:c{identity[0]}:f{identity[1]}:p{plane_index}:t{chunk_index}:s{stream_index}",
                        "bit_size": stream.stream_size,
                        "data_hex": stream.stream_data.hex(),
                        "requests": stream.requests,
                    })
                    stream_number += 1
    if selected_seen != set(SELECTED):
        raise AssertionError(f"selected sources missing: {set(SELECTED) - selected_seen}")

    # Capture all streams made during frozen decode by wrapping the class.
    # (The class above records each instance below through __init__.)
    # Synthetic direct-reader cases supplement the actual corpus with complete
    # q/offset coverage for normal, DC-escape and level-escape widths.
    synthetic_rows = []
    for escape, k_values in ((24, range(20)), (14, range(14)), (12, range(12))):
        label = {24: "rice24", 14: "dc14", 12: "level12"}[escape]
        for k in k_values:
            for alignment in range(32):
                synthetic_rows.append(synthetic_case(
                    RecordingRice, f"synthetic:{label}:k{k}:a{alignment}",
                    k, escape, alignment,
                ))
    rows.extend(synthetic_rows)

    OUT.mkdir(parents=True, exist_ok=True)
    jsonl = b"".join((json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n").encode() for row in rows)
    fixture_path = OUT / "cases.jsonl.gz"
    with fixture_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            stream.write(jsonl)

    requests = sum(len(row["requests"]) for row in rows)
    bits = sum(row["bit_size"] for row in rows)
    index = {
        "schema": "cu66-v91-rtl-rice-vectors-v1",
        "status": "PASS_FROZEN_READER_VECTOR_EXPORT",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selection": [list(item) for item in SELECTED],
        "actual_cases": stream_number,
        "synthetic_cases": len(synthetic_rows),
        "cases": len(rows),
        "requests": requests,
        "coded_bits": bits,
        "fixture": {"path": fixture_path.name, "gzip_sha256": sha(fixture_path), "jsonl_sha256": hashlib.sha256(jsonl).hexdigest()},
        "source_sha256": {
            "scripts/cu66-v91/build_rtl_vectors.py": sha(Path(__file__).resolve()),
            "experiments/python-gamebub-v88/entropy/data.py": sha(ENTROPY / "data.py"),
            "experiments/python-gamebub-v88/entropy/codec.py": sha(ENTROPY / "codec.py"),
            "experiments/python-gamebub-v88/entropy/index.json": sha(ENTROPY / "index.json"),
            "experiments/python-gamebub-v88/entropy/attempts/20261106T150638168868Z-fb236a5e/data.bin.gz": sha(ENTROPY / "attempts/20261106T150638168868Z-fb236a5e/data.bin.gz"),
        },
        "input_counts": {"native_sources": 457, "chunks": 1371},
        "format": "Each JSONL line is one Rice stream: id, bit_size, MSB-first packed data_hex, requests [[k, escape, expected_value, bit_position_after], ...]. Padding is zero and excluded from bit_size.",
        "scope": "Frozen Python bit reader generated actual stream requests; synthetic streams are validated by the same frozen Rice.value/end reader. No RTL timing claim.",
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "actual_cases": stream_number, "synthetic_cases": len(synthetic_rows), "requests": requests, "coded_bits": bits, "fixture_sha256": index["fixture"]["gzip_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

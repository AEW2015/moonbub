#!/usr/bin/env python3
"""Build additive V91e packed-scratch vectors from the frozen V88 corpus.

The frozen V91d 17 rows are retained verbatim and first.  New corpus rows are
selected by source identity using auditable corpus metrics, then independently
decoded and packed here using the frozen V88 Python decoder.
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
OLD = ROOT / "experiments/python-gamebub-v91d/vectors"
OUT = ROOT / "experiments/python-gamebub-v91e/vectors"
BURST, HEADER = 16, 32
BAND_LIMITS = (1, 6, 21, 64)
ZIGZAG = tuple(sorted(range(64), key=lambda i: (
    i // 8 + i % 8,
    i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


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
                        events.append((block << 19) | (index << 13) | (value & 0x1fff))
            assert len(events) == counts[band - 1]
            ac.append(struct.pack("<" + "I" * len(events), *events))
        segments = [dc, *ac]
    used_bytes = HEADER + sum(align16(len(segment)) for segment in segments)
    image = bytearray(struct.pack("<8I", 0x43393150, blocks, int(raw), *counts,
                                  used_bytes, 0))
    for segment in segments:
        image.extend(segment)
        image.extend(bytes(align16(len(segment)) - len(segment)))
    assert len(image) == used_bytes
    return bytes(image)


def make_case(case_id: str, packet: bytes, blocks: int,
              coefficients: list[int], raw: bool, source: dict,
              scratch_sha: str) -> dict:
    counts, sparse = rows_for(coefficients, blocks, raw)
    dense = dense_bytes(coefficients)
    packed = packed_image(coefficients, blocks, raw, counts)
    return {
        "id": case_id, "blocks": blocks, "raw": raw, "counts": counts,
        "packet_hex": packet.hex(), "sparse": sparse,
        "dense_hex": dense.hex(), "coefficient_sha256": sha(dense),
        "packed_hex": packed.hex(), "packed_sha256": sha(packed),
        "used_bytes": len(packed), "case_type": "actual", "source": source,
        "v91c_scratch_sha256": scratch_sha,
    }


def source_tuple(source: dict):
    return tuple(source[key] for key in ("cohort", "fid", "plane", "chunk"))


def main() -> None:
    data_mod = load_module("v91e_frozen_v88_data", ENTROPY / "data.py")
    codec = load_module("v91e_frozen_v88_codec", ENTROPY / "codec.py")
    source_index = json.loads((ENTROPY / "index.json").read_text())
    data_path = ENTROPY / source_index["data"]["path"]
    assert file_sha(data_path) == source_index["data"]["gzip_sha256"]

    old_index = json.loads((OLD / "index.json").read_text())
    old_fixture = OLD / old_index["fixture"]["path"]
    old_raw = gzip.decompress(old_fixture.read_bytes())
    old_lines = old_raw.splitlines(keepends=True)
    assert sha(old_fixture.read_bytes()) == old_index["fixture"]["gzip_sha256"]
    old_rows = [json.loads(line) for line in old_raw.splitlines()]
    assert len(old_rows) == 17 and old_rows[-1]["id"] == "scratch_8192_last_record"

    receipts_path = ROOT / "experiments/python-gamebub-v91c/scratch-attempts/20261106T173557536651Z-250df7c8/chunks.jsonl"
    receipts = {}
    for line in receipts_path.read_text().splitlines():
        item = json.loads(line)
        receipts[(item["cohort"], item["fid"], item["plane"], item["chunk"])] = item

    # Full 457-source scan.  No timing or fitted values influence selection.
    source_metrics: dict[tuple[int, int], dict] = {}
    rows_by_source: dict[tuple[int, int], list[dict]] = {}
    selected_chunks: dict[tuple[int, int, int, int], dict] = {}
    for frame in data_mod.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        frame_rows = []
        for plane, chunks in enumerate(frame["variants"]["65536"]):
            for chunk_index, chunk in enumerate(chunks):
                packet = chunk["br88"]
                assert 1 <= chunk["blocks"] <= 8192, f"strict block cap exceeded: {identity}/{plane}/{chunk_index}"
                coefficients = codec.decode(packet, chunk["blocks"], 1)
                assert all(-2048 <= value <= 2048 for value in coefficients)
                dense = dense_bytes(coefficients)
                assert sha(dense) == chunk["coefficient_sha256"]
                assert sha(packet) == chunk["br88_sha256"]
                raw = bool(packet[5] & 1)
                counts, sparse = rows_for(coefficients, chunk["blocks"], raw)
                packed = packed_image(coefficients, chunk["blocks"], raw, counts)
                scratch_sha = sha(packed)
                receipt_key = (*identity, plane, chunk_index)
                receipt = receipts.get(receipt_key)
                if receipt is not None:
                    assert receipt["scratch_sha256"] == scratch_sha, f"V91c scratch mismatch: {receipt_key}"
                source = {"cohort": identity[0], "fid": identity[1], "plane": plane,
                          "chunk": chunk_index, "ordinal": frame["ordinal"],
                          "key": frame["key"], "packet_sha256": sha(packet),
                          "coefficient_sha256": sha(dense)}
                metric = {"plane": plane, "chunk": chunk_index,
                          "blocks": chunk["blocks"], "br88_bytes": len(packet),
                          "packed_bytes": len(packed), "nonzero_ac": sum(counts),
                          "sparse_writes": len(sparse)}
                frame_rows.append((source, chunk, coefficients, metric, scratch_sha))
                selected_chunks[receipt_key] = {
                    "source": source, "chunk": chunk, "coefficients": coefficients,
                    "metric": metric, "scratch_sha256": scratch_sha}
        rows_by_source[identity] = frame_rows
        metrics = [row[3] for row in frame_rows]
        source_metrics[identity] = {
            "cohort": identity[0], "fid": identity[1],
            "ordinal": frame["ordinal"], "key": frame["key"],
            "chunks": len(metrics), "planes": len({m["plane"] for m in metrics}),
            "br88_bytes_total": sum(m["br88_bytes"] for m in metrics),
            "max_br88_chunk_bytes": max(m["br88_bytes"] for m in metrics),
            "packed_bytes_total": sum(m["packed_bytes"] for m in metrics),
            "max_packed_chunk_bytes": max(m["packed_bytes"] for m in metrics),
            "max_blocks": max(m["blocks"] for m in metrics),
            "max_nonzero_ac": max(m["nonzero_ac"] for m in metrics),
            "max_sparse_writes": max(m["sparse_writes"] for m in metrics),
            "chunk_metrics": metrics,
        }
    assert len(source_metrics) == source_index["native_sources"] == 457
    assert sum(m["chunks"] for m in source_metrics.values()) == source_index["chunks"] == 1371

    metrics_list = list(source_metrics.values())
    max_scratch_chunk = max(selected_chunks.values(), key=lambda x: x["metric"]["packed_bytes"])
    max_packet_chunk = max(selected_chunks.values(), key=lambda x: x["metric"]["br88_bytes"])
    max_writes_chunk = max(selected_chunks.values(), key=lambda x: x["metric"]["sparse_writes"])
    max_blocks_chunk = max(selected_chunks.values(), key=lambda x: x["metric"]["blocks"])
    max_nonzero_chunk = max(selected_chunks.values(), key=lambda x: x["metric"]["nonzero_ac"])
    # Frame identity selections; all planes/chunks for selected frames are included.
    selected_ids = list(dict.fromkeys([
        source_tuple(max_scratch_chunk["source"])[:2],
        source_tuple(max_packet_chunk["source"])[:2],
        source_tuple(max_writes_chunk["source"])[:2],
        source_tuple(max_nonzero_chunk["source"])[:2],
        source_tuple(max_blocks_chunk["source"])[:2],
    ]))
    # Make the requested evidence sources explicit and stable in the rationale.
    assert (3, 28) in selected_ids and (3, 50) in selected_ids and (0, 0) in selected_ids

    rows = list(old_rows)
    old_source_keys = {source_tuple(row["source"]) for row in old_rows if row.get("source")}
    appended = []
    selection_map = []
    for identity in selected_ids:
        source_record = source_metrics[identity]
        source_chunk_cases = []
        for source, chunk, coefficients, metric, scratch_sha in rows_by_source[identity]:
            key = source_tuple(source)
            if key in old_source_keys:
                continue
            case_id = f"actual:c{source['cohort']}:f{source['fid']}:p{source['plane']}:t{source['chunk']}"
            row = make_case(case_id, chunk["br88"], chunk["blocks"], coefficients,
                            bool(chunk["br88"][5] & 1), source, scratch_sha)
            assert row["coefficient_sha256"] == chunk["coefficient_sha256"]
            appended.append(row)
            old_source_keys.add(key)
            source_chunk_cases.append(case_id)
        selection_map.append({"cohort": identity[0], "fid": identity[1],
                              "ordinal": source_record["ordinal"], "key": source_record["key"],
                              "included_new_case_ids": source_chunk_cases,
                              "selection_metrics": {k: source_record[k] for k in (
                                  "max_packed_chunk_bytes", "max_br88_chunk_bytes",
                                  "max_sparse_writes", "max_nonzero_ac", "max_blocks")}})
    rows.extend(appended)

    # The old rows remain byte-identical JSON objects and at the same positions.
    assert rows[:17] == old_rows
    jsonl = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                    for row in rows)
    assert jsonl.splitlines(keepends=True)[:17] == old_lines
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = OUT / "coefficients.jsonl.gz"
    with fixture.open("wb") as raw_out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, mtime=0, compresslevel=9) as stream:
            stream.write(jsonl)

    old_dense_outputs = sum(row["blocks"] * 64 for row in old_rows)
    new_dense_outputs = sum(row["blocks"] * 64 for row in appended)
    actual_rows = [row for row in rows if row["case_type"] == "actual"]
    block_values = [row["blocks"] for row in rows]
    used_values = [row["used_bytes"] for row in rows]
    source_hashes = {
        "scripts/cu66-v91e/build_vectors.py": file_sha(Path(__file__).resolve()),
        "scripts/cu66-v91d/build_vectors.py": file_sha(ROOT / "scripts/cu66-v91d/build_vectors.py"),
        "experiments/python-gamebub-v91d/vectors/index.json": file_sha(OLD / "index.json"),
        f"experiments/python-gamebub-v91d/vectors/{old_index['fixture']['path']}": file_sha(old_fixture),
        "experiments/python-gamebub-v88/entropy/data.py": file_sha(ENTROPY / "data.py"),
        "experiments/python-gamebub-v88/entropy/codec.py": file_sha(ENTROPY / "codec.py"),
        "experiments/python-gamebub-v88/entropy/index.json": file_sha(ENTROPY / "index.json"),
        f"experiments/python-gamebub-v88/entropy/{source_index['data']['path']}": file_sha(data_path),
        "experiments/python-gamebub-v91c/scratch-attempts/20261106T173557536651Z-250df7c8/chunks.jsonl": file_sha(receipts_path),
    }
    index = {
        "schema": "cu66-v91e-coefficient-packed-image-v1",
        "status": "PASS_FROZEN_V88_FULLCORPUS_COEFFICIENT_AND_PACKED_IMAGE_GOLDENS",
        "parent_commit": "bebd308ca",
        "last_functional_commit": "c9bc0f98e",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "fixture": {"path": fixture.name, "gzip_sha256": file_sha(fixture), "jsonl_sha256": sha(jsonl)},
        "counts": {"total_cases": len(rows), "original_v91d_cases": 17,
                   "appended_actual_cases": len(appended), "actual_cases": len(actual_rows),
                   "synthetic_or_directed_cases": len(rows) - len(actual_rows),
                   "selected_source_identities": len(selected_ids),
                   "dense_coefficient_outputs": sum(row["blocks"] * 64 for row in rows),
                   "appended_dense_coefficient_outputs": new_dense_outputs},
        "ranges": {"blocks": {"min": min(block_values), "max": max(block_values)},
                   "used_bytes": {"min": min(used_values), "max": max(used_values)}},
        "source_sha256": source_hashes,
        "v88_corpus": {"path": source_index["data"]["path"],
                       "gzip_sha256": source_index["data"]["gzip_sha256"],
                       "raw_sha256": source_index["data"]["raw_sha256"],
                       "native_sources": 457, "chunks": 1371},
        "selection": {
            "method": "Complete actual V88 corpus scan. Select source identities containing the maximum single-chunk packed scratch bytes, BR88 packet bytes, sparse-write count, nonzero AC count, or block count. Include every chunk in all three planes for each selected frame, deduplicating source tuple (cohort,fid,plane,chunk) against earlier selections and the frozen V91d rows. No timing or fitted metric is used.",
            "maxima": {
                "packed_scratch_bytes": {"value": max_scratch_chunk["metric"]["packed_bytes"], "source": max_scratch_chunk["source"]},
                "br88_chunk_bytes": {"value": max_packet_chunk["metric"]["br88_bytes"], "source": max_packet_chunk["source"]},
                "sparse_writes": {"value": max_writes_chunk["metric"]["sparse_writes"], "source": max_writes_chunk["source"]},
                "nonzero_ac": {"value": max_nonzero_chunk["metric"]["nonzero_ac"], "source": max_nonzero_chunk["source"]},
                "dense_blocks": {"value": max_blocks_chunk["metric"]["blocks"], "source": max_blocks_chunk["source"]},
            },
            "selected_source_identities": selection_map,
            "full_457_source_scan": [source_metrics[key] for key in sorted(source_metrics)],
        },
        "old_fixture_compatibility": {
            "path": f"experiments/python-gamebub-v91d/vectors/{old_index['fixture']['path']}",
            "gzip_sha256": old_index["fixture"]["gzip_sha256"],
            "row_count": 17,
            "mapping": [{"old_row_index": i, "old_id": row["id"],
                         "v91e_row_index": i, "v91e_id": row["id"]}
                        for i, row in enumerate(old_rows)],
            "preserved_decompressed_rows_byte_for_byte": True,
        },
        "scope": "Actual related V88 corpus chunks and synthetic/directed legacy rows only; no new gameplay was captured.",
        "format": "JSONL records preserve packet_hex, sparse [band,block,raster_index,signed_value] tuples, dense signed16LE coefficient bytes, packed scratch image bytes, counts, raw, used_bytes, and hashes. New actual rows carry source cohort/fid/plane/chunk/ordinal/key plus packet and coefficient hashes.",
        "scratch_layout": {"header_bytes": HEADER, "burst_bytes": BURST,
                           "packed_word": "block[31:19]|raster[18:13]|signed13[12:0]"},
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(f"V91E_VECTOR_PASS cases={len(rows)} added={len(appended)} "
          f"gzip_sha256={index['fixture']['gzip_sha256']}")


if __name__ == "__main__":
    main()

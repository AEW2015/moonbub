#!/usr/bin/env python3
"""Independent V91i2 CS88 admission-to-dense-coefficient placement model.

This reads retained V91i packets and coefficient goldens as data. It does not
import a packet producer, entropy decoder, or native receiver. The model binds
each dense residual ordinal to its native tile and QM87 cell/scale, then emits
the TSV consumed by the V91i2 RTL harness.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
V91I = ROOT / "experiments/python-gamebub-v91i"
V91E = ROOT / "experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz"
MASK_SHA256 = "e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5"
PLANE_TILES = (5400, 1350, 1350)
PLANE_WIDTHS = (90, 45, 45)
PRIMARY = ("actual_001", "actual_006", "actual_043", "actual_031")
EXTRA_ROWS = ("actual_000", "actual_003", "structural_all_copy_zero_residual")
SYNTHETIC_ROWS = ("actual_006_varied_qcache", "actual_006_wrong_cache_tag",
                  "actual_006_reserved_qcache_code", "actual_001_bad_third_inner_crc")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_hidden_mask() -> tuple[int, ...]:
    header = (ROOT / "experiments/cu66-native-v69/generated_constants.hpp").read_text()
    import re
    rows = []
    for name, count in (("SAFE0", 5400), ("SAFE1", 1350), ("SAFE2", 1350)):
        m = re.search(rf"{name}\[{count}\]=\{{([^}}]+)\}};", header)
        if not m:
            raise ValueError(f"missing frozen {name} data")
        row = tuple(int(v) for v in m.group(1).split(","))
        if len(row) != count or any(v not in (0, 1) for v in row):
            raise ValueError(f"invalid {name} data")
        rows.extend(row)
    result = tuple(rows)
    if len(result) != 8100 or sha(bytes(result)) != MASK_SHA256:
        raise ValueError("frozen hidden mask digest mismatch")
    return result


def bit(data: bytes, pos: int) -> int:
    if pos >= len(data) * 8:
        raise ValueError("truncated mode bitstream")
    return (data[pos // 8] >> (7 - pos % 8)) & 1


def decode_modes(packet: bytes, mode_off: int, mode_n: int, key: bool,
                 method: int, hidden: tuple[int, ...]) -> tuple[int, ...]:
    body = packet[mode_off:mode_off + mode_n]
    if key:
        if method != 0 or mode_n != 0:
            raise ValueError("unsupported key mode syntax")
        return tuple(1 if h else 2 for h in hidden)
    if method != 3:
        raise ValueError("unsupported delta mode syntax")
    out = [1] * 8100
    pos = 0
    base = 0
    for axis, ntile in enumerate(PLANE_TILES):
        for begin in range(0, ntile, 16):
            tag = (bit(body, pos) << 1) | bit(body, pos + 1)
            pos += 2
            ids = [base + t for t in range(begin, min(begin + 16, ntile))
                   if not hidden[base + t]]
            if not ids:
                if tag != 3:
                    raise ValueError("noncanonical hidden-only group")
                continue
            if tag == 3:
                raise ValueError("tag 3 on visible group")
            if tag < 2:
                value = 2 if tag else 0
                for t in ids:
                    out[t] = value
            else:
                values = [bit(body, pos + i) for i in range(len(ids))]
                pos += len(ids)
                if not any(values) or all(values):
                    raise ValueError("noncanonical mixed group")
                for t, value in zip(ids, values):
                    out[t] = 2 if value else 0
        base += ntile
    if base != 8100 or (pos + 7) // 8 != mode_n:
        raise ValueError("mode coverage/length")
    if any(bit(body, p) for p in range(pos, mode_n * 8)):
        raise ValueError("nonzero mode padding")
    return tuple(out)


def parse_header(packet: bytes) -> dict:
    if len(packet) < 132 or packet[:4] != b"CS88":
        raise ValueError("not a complete CS88 packet")
    if zlib.crc32(packet[:-4]) & 0xFFFFFFFF != int.from_bytes(packet[-4:], "big"):
        raise ValueError("outer CRC mismatch")
    flags, method = packet[5], packet[7]
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    width, height, block, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, mode_n, q_n, hud_n, data_n = struct.unpack_from(">IIIII", packet, 32)
    if (flags > 1 or width != 720 or height != 480 or block != 32 or reserved != 0
            or cap != 65536 or 128 + mode_n + q_n + data_n + hud_n + 4 != len(packet)):
        raise ValueError("unsupported or malformed V91i envelope")
    return {"key": bool(flags), "mode_method": method, "fid": fid, "refid": refid,
            "generation": generation, "mode_n": mode_n, "q_n": q_n,
            "hud_n": hud_n, "data_n": data_n, "mode_off": 128,
            "q_off": 128 + mode_n, "data_off": 128 + mode_n + q_n}


def required_cells(ops: tuple[int, ...]) -> int:
    cells = set()
    base = 0
    for axis, ntile in enumerate(PLANE_TILES):
        for tile in range(ntile):
            if ops[base + tile] != 2:
                continue
            if axis == 0:
                cell = (tile // 90 // 2) * 45 + (tile % 90 // 2)
            else:
                cell = tile
            cells.add(cell)
        base += ntile
    return len(cells)


def decode_qmap(packet: bytes, h: dict, ops: tuple[int, ...], inherited: bytes | None) -> tuple[int, bytes]:
    off, size = h["q_off"], h["q_n"]
    block = packet[off:off + size]
    if len(block) < 16 or zlib.crc32(block[:-4]) & 0xFFFFFFFF != int.from_bytes(block[-4:], "big"):
        raise ValueError("QM87 CRC/size")
    magic, ver, method, cells, body_n, required = struct.unpack_from(">4sBBHHH", block)
    if magic != b"QM87" or ver != 1 or cells != 1350 or len(block) != 16 + body_n:
        raise ValueError("QM87 header")
    if required != required_cells(ops):
        raise ValueError("QM87 required-cell mismatch")
    body = block[12:-4]
    if method == 6:
        if h["key"] or body_n != 0 or inherited is None or len(inherited) != 1350:
            raise ValueError("QM6 without concrete inherited cache")
        return method, inherited
    if method != 2:
        raise ValueError(f"unsupported V91i2 model qmap method {method}")
    values: list[int] = []
    for b in body:
        value, run = b >> 6, (b & 63) + 1
        if value == 3 or len(values) + run > 1350:
            raise ValueError("invalid QM2 run")
        values.extend([value] * run)
    if len(values) != 1350:
        raise ValueError("QM2 run coverage")
    return method, bytes(values)


def residual_spans(packet: bytes, h: dict) -> list[dict]:
    start, end = h["data_off"], h["data_off"] + h["data_n"]
    cursor = start
    spans = []
    for axis in range(3):
        if cursor + 4 > end:
            raise ValueError("short plane directory")
        nchunk = int.from_bytes(packet[cursor:cursor + 4], "big")
        cursor += 4
        for chunk in range(nchunk):
            if cursor + 8 > end:
                raise ValueError("short chunk directory")
            blocks, length = struct.unpack_from(">II", packet, cursor)
            cursor += 8
            off = cursor
            payload = packet[off:off + length]
            if len(payload) != length:
                raise ValueError("short chunk payload")
            spans.append({"axis": axis, "chunk": chunk, "blocks": blocks, "offset": off,
                          "length": length, "magic": payload[:4].decode("ascii", "replace"),
                          "sha256": sha(payload)})
            cursor += length
    if cursor != end:
        raise ValueError("residual span directory mismatch")
    return spans


def placement(ops: tuple[int, ...], qscales: bytes, dense: tuple[bytes, ...], plane_limit: int = 3) -> dict:
    result = {"planes": [], "tuple_count": 0}
    base = 0
    for axis, (ntile, width) in enumerate(zip(PLANE_TILES[:plane_limit], PLANE_WIDTHS[:plane_limit])):
        tiles = [t for t in range(ntile) if ops[base + t] == 2]
        raw = dense[axis]
        if len(raw) != len(tiles) * 128:
            raise ValueError(f"axis {axis} dense bytes do not match residual tiles")
        rows = []
        h = hashlib.sha256()
        for ordinal, tile in enumerate(tiles):
            cell = ((tile // 90 // 2) * 45 + (tile % 90 // 2)) if axis == 0 else tile
            scale = qscales[cell]
            if scale > 2:
                raise ValueError("unsupported qscale code")
            for index in range(64):
                value = int.from_bytes(raw[ordinal * 128 + index * 2:ordinal * 128 + index * 2 + 2],
                                       "little", signed=True)
                h.update(struct.pack(">BIIBHBh", axis, tile, ordinal, index, cell, scale, value))
            rows.append({"tile": tile, "block": ordinal, "qcell": cell, "qscale": scale,
                         "coefficient_sha256": sha(raw[ordinal * 128:(ordinal + 1) * 128])})
        result["planes"].append({"axis": axis, "active_blocks": len(tiles),
                                 "tuple_count": len(tiles) * 64, "tuple_sha256": h.hexdigest(),
                                 "first": rows[0] if rows else None,
                                 "last": rows[-1] if rows else None,
                                 "placements": rows})
        result["tuple_count"] += len(tiles) * 64
        base += ntile
    return result


def read_index() -> tuple[dict, dict[str, dict]]:
    path = V91I / "vectors/index.json"
    doc = json.loads(path.read_text())
    return doc, {e["id"]: e for e in doc["entries"]}


def read_golden_records() -> dict[tuple[int, int, int], dict]:
    out = {}
    with gzip.open(V91E, "rt", encoding="utf-8") as src:
        for line in src:
            row = json.loads(line)
            if row.get("case_type") != "actual":
                continue
            s = row["source"]
            out[(s["cohort"], s["fid"], s["plane"])] = row
    return out


def cache_context(entries: dict[str, dict], row_id: str, hidden: tuple[int, ...]) -> tuple[bytes | None, dict | None]:
    row = entries[row_id]
    ref = row["accepted_ref"]
    if not ref["valid"]:
        return None, None
    if row["class_"] == "synthetic_structural_only":
        key = entries["actual_001"]
        key_packet = (ROOT / key["packet_path"]).read_bytes()
        kh = parse_header(key_packet)
        km = decode_modes(key_packet, kh["mode_off"], kh["mode_n"], kh["key"], kh["mode_method"], hidden)
        _, scales = decode_qmap(key_packet, kh, km, None)
        return scales, {"valid": True, "cache_fid": ref["fid"], "cache_generation": ref["generation"],
                        "accepted_history_packet_sha256": "synthetic_external_snapshot",
                        "accepted_history_policy": None, "value_source_packet_sha256": key["packet_sha256"],
                        "value_source_fixture_id": key["id"], "value_source_qmap_method": 2,
                        "qscales_sha256": sha(scales), "qscales_hex": scales.hex(),
                        "history_evidence": row["accepted_ref_evidence"]}
    evidence = row["accepted_ref_evidence"]
    source_hash = evidence["receiver_history_packet_sha256"]
    source_entry = next((e for e in entries.values() if e.get("packet_sha256") == source_hash), None)
    source_of_values = source_entry
    if source_entry is not None:
        source_packet = (ROOT / source_entry["packet_path"]).read_bytes()
        sh = parse_header(source_packet)
        method = source_packet[sh["q_off"] + 5] if sh["q_n"] >= 6 else -1
    else:
        method = 6
    # QM6 preserves the previous map. If the immediate accepted packet is a
    # QM6 row or is retained only as history metadata, trace values to the
    # retained QM2 key whose raw block hash is checked against the V87 ledger.
    if method == 6:
        candidates = [e for e in entries.values()
                      if e.get("class_") == "retained_actual_fixture"
                      and e.get("cohort") == row["cohort"]
                      and e.get("expected", {}).get("qmap_method") == 2
                      and e.get("expected", {}).get("key")]
        if not candidates:
            raise ValueError(f"no retained QM2 source for {row_id}")
        source_of_values = min(candidates, key=lambda e: (e["origin"] != row["origin"], e["fid"]))
    source_packet = (ROOT / source_of_values["packet_path"]).read_bytes()
    sh = parse_header(source_packet)
    smodes = decode_modes(source_packet, sh["mode_off"], sh["mode_n"], sh["key"], sh["mode_method"], hidden)
    _, scales = decode_qmap(source_packet, sh, smodes, None)
    value_qblock = source_packet[sh["q_off"]:sh["q_off"] + sh["q_n"]]
    lineage = []
    ledger_path = ROOT / "experiments/python-gamebub-v87/quantizers/attempts/20261106T142631412759Z-5847ed8e/frames.jsonl"
    with ledger_path.open() as ledger:
        for line in ledger:
            r = json.loads(line)
            if (r.get("configuration") == "copy_group_cap65536" and
                    r.get("cohort") == row["cohort"] and r.get("fid", 0) <= ref["fid"]):
                lineage.append({"fid": r["fid"], "accepted": r.get("decoded", {}).get("accepted"),
                                "q_method": r.get("q_method"), "qmap_block_sha256": r.get("qmap_sha256")})
    lineage_proof = None
    if lineage:
        expected_fids = list(range(ref["fid"] + 1))
        if [x["fid"] for x in lineage] != expected_fids or any(not x["accepted"] for x in lineage):
            raise ValueError(f"incomplete/unaccepted quantizer lineage for {row_id}")
        latest_key = max(x["fid"] for x in lineage if x["q_method"] != 6)
        key_row = next(x for x in lineage if x["fid"] == latest_key)
        if key_row["q_method"] != 2 or key_row["qmap_block_sha256"] != sha(value_qblock):
            raise ValueError(f"QM2 retained value source does not match latest ledger key for {row_id}")
        if any(x["q_method"] != 6 for x in lineage[latest_key + 1:]):
            raise ValueError(f"QM6 did not persist through accepted predecessor for {row_id}")
        lineage_proof = {"ledger": "experiments/python-gamebub-v87/quantizers/attempts/20261106T142631412759Z-5847ed8e/frames.jsonl",
                         "ledger_configuration": "copy_group_cap65536", "rows_through_accepted_ref": lineage,
                         "latest_qm2_fid": latest_key, "latest_qm2_block_sha256": key_row["qmap_block_sha256"],
                         "retained_value_source_fid": source_of_values["fid"],
                         "retained_value_source_qblock_sha256": sha(value_qblock),
                         "retained_value_source_matches_latest_qm2": True}
    record = {"valid": True, "cache_fid": ref["fid"], "cache_generation": ref["generation"],
              "accepted_history_packet_sha256": source_hash,
              "accepted_history_policy": evidence.get("receiver_history_policy"),
              "value_source_packet_sha256": source_of_values["packet_sha256"],
              "value_source_fixture_id": source_of_values["id"],
              "value_source_qmap_method": 2,
              "value_source_qblock_sha256": sha(value_qblock),
              "qscales_sha256": sha(scales), "qscales_hex": scales.hex(),
              "history_evidence": evidence, "lineage_proof": lineage_proof}
    return scales, record


def main() -> None:
    hidden = read_hidden_mask()
    index_doc, entries = read_index()
    goldens = read_golden_records()
    selected = list(PRIMARY) + list(EXTRA_ROWS) + list(SYNTHETIC_ROWS)
    cases = []
    results = {"schema": "cu66-v91i2-model-results-v1", "status": "PASS", "cases": []}
    tsv_path = VECTORS / "cases.tsv"
    VECTORS.mkdir(parents=True, exist_ok=True)
    with tsv_path.open("w", encoding="ascii", newline="") as out:
        for case_id in selected:
            synthetic_kind = case_id if case_id in SYNTHETIC_ROWS else None
            base_id = ("actual_001" if case_id == "actual_001_bad_third_inner_crc" else "actual_006") if synthetic_kind else case_id
            entry = entries[base_id]
            packet = (ROOT / entry["packet_path"]).read_bytes()
            h = parse_header(packet)
            ops = decode_modes(packet, h["mode_off"], h["mode_n"], h["key"], h["mode_method"], hidden)
            prior, cache_info = cache_context(entries, base_id, hidden)
            if synthetic_kind == "actual_006_varied_qcache":
                prior = bytes(i % 3 for i in range(1350))
                cache_info = {"valid": True, "cache_fid": h["refid"], "cache_generation": h["generation"] - 1,
                              "synthetic_component_fixture": True, "qscales_sha256": sha(prior),
                              "qscales_hex": prior.hex(), "scale_domain": [0, 1, 2]}
            if synthetic_kind == "actual_006_reserved_qcache_code":
                prior = bytes([3]) + (prior or bytes(1350))[1:]
                cache_info = {"valid": True, "cache_fid": h["refid"], "cache_generation": h["generation"] - 1,
                              "synthetic_component_fixture": True, "preload_error": 3,
                              "qscales_sha256": sha(prior), "qscales_hex": prior.hex()}
            if synthetic_kind in ("actual_006_varied_qcache", "actual_006_reserved_qcache_code"):
                qmethod, qscales = 6, prior
            else:
                qmethod, qscales = decode_qmap(packet, h, ops, prior)
            spans = residual_spans(packet, h)
            original_packet_sha = sha(packet)
            if synthetic_kind == "actual_006_wrong_cache_tag":
                cache_info = dict(cache_info or {})
                cache_info["synthetic_component_fixture"] = True
                cache_info["supplied_cache_fid"] = h["refid"] + 1
                cache_info["supplied_cache_generation"] = h["generation"] - 1
            if synthetic_kind == "actual_001_bad_third_inner_crc":
                cr = next(s for s in spans if s["axis"] == 2)
                damaged = bytearray(packet)
                damaged[cr["offset"] + cr["length"] - 1] ^= 1
                damaged[-4:] = (zlib.crc32(damaged[:-4]) & 0xFFFFFFFF).to_bytes(4, "big")
                packet = bytes(damaged)
                spans = residual_spans(packet, h)
            all_br88 = bool(spans) and all(s["magic"] == "BR88" for s in spans)
            expected_error = 0
            dense = [b"", b"", b""]
            golden_sources = []
            if case_id in PRIMARY or synthetic_kind in ("actual_006_varied_qcache", "actual_001_bad_third_inner_crc"):
                if not all_br88:
                    raise ValueError(f"selected golden case {case_id} is not all-BR88")
                for axis in range(3):
                    if synthetic_kind == "actual_001_bad_third_inner_crc" and axis == 2:
                        continue
                    g = goldens.get((entry["cohort"], entry["fid"], axis))
                    if g is None:
                        raise ValueError(f"missing V91e dense golden for {case_id} axis {axis}")
                    span = next(s for s in spans if s["axis"] == axis)
                    if sha(bytes.fromhex(g["packet_hex"])) != span["sha256"]:
                        raise ValueError(f"V91e source chunk mismatch for {case_id} axis {axis}")
                    dense[axis] = bytes.fromhex(g["dense_hex"])
                    if sha(dense[axis]) != g["coefficient_sha256"]:
                        raise ValueError("V91e dense coefficient digest mismatch")
                    golden_sources.append({"axis": axis, "id": g["id"],
                                           "chunk_sha256": span["sha256"],
                                           "dense_sha256": sha(dense[axis]),
                                           "packet_sha256": g["source"]["packet_sha256"]})
            if case_id in PRIMARY or synthetic_kind == "actual_006_varied_qcache":
                expected_error = 0
            elif case_id in ("actual_000", "actual_003"):
                expected_error = 64
            elif case_id == "structural_all_copy_zero_residual":
                expected_error = 0
            elif synthetic_kind == "actual_006_wrong_cache_tag":
                expected_error = 7
            elif synthetic_kind == "actual_006_reserved_qcache_code":
                expected_error = 7
            elif synthetic_kind == "actual_001_bad_third_inner_crc":
                expected_error = 147
            elif synthetic_kind == "actual_006_varied_qcache":
                expected_error = 0
            else:
                raise AssertionError(case_id)
            if case_id in PRIMARY or synthetic_kind == "actual_006_varied_qcache":
                mapped = placement(ops, qscales, tuple(dense))
            elif synthetic_kind == "actual_001_bad_third_inner_crc":
                mapped = placement(ops, qscales, (dense[0], dense[1]), plane_limit=2)
            else:
                mapped = {"planes": [], "tuple_count": 0}
            ref = entry["accepted_ref"]
            prior_hex = prior.hex() if prior is not None else "-"
            qhex = qscales.hex()
            dense_hex = [d.hex() if d else "-" for d in dense]
            cache_fid = int(cache_info.get("supplied_cache_fid", ref["fid"])) if ref["valid"] else 0
            cache_generation = int(cache_info.get("supplied_cache_generation", ref["generation"])) if ref["valid"] else 0
            fields = [case_id, str(expected_error), packet.hex(), str(int(ref["valid"])),
                      str(ref["fid"]), str(ref["generation"]), str(int(ref["qcache_valid"])),
                      str(cache_fid), str(cache_generation),
                      prior_hex, qhex, bytes(ops).hex(), *dense_hex]
            out.write("\t".join(fields) + "\n")
            cases.append({"id": case_id, "fixture_id": entry["id"], "fixture_origin": entry.get("origin"),
                          "cohort": entry.get("cohort"), "fid": h["fid"], "refid": h["refid"],
                          "generation": h["generation"], "key": h["key"],
                          "packet_path": ("generated mutation; see `packet_mutation` and cases.tsv"
                                          if synthetic_kind == "actual_001_bad_third_inner_crc" else entry["packet_path"]),
                          "packet_sha256": sha(packet), "original_packet_sha256": original_packet_sha,
                          "packet_bytes": len(packet),
                          "packet_mutation": ("third plane BR88 CRC byte XOR 1; outer CS88 CRC recomputed"
                                              if synthetic_kind == "actual_001_bad_third_inner_crc" else None),
                          "mode_method": h["mode_method"], "qmap_method": qmethod,
                          "qmap_required_cells": required_cells(ops),
                          "operations_sha256": sha(bytes(ops)), "qscales_sha256": sha(qscales),
                          "qscales": list(qscales), "qcache": cache_info,
                          "accepted_ref": ref, "spans": spans, "all_br88": all_br88,
                          "dense_goldens": golden_sources, "placement": mapped,
                          "expected_error": expected_error,
                          "synthetic_structural_only": entry.get("class_") == "synthetic_structural_only"})
            results["cases"].append({"id": case_id, "expected_error": expected_error,
                                     "packet_sha256": sha(packet), "qmap_method": qmethod,
                                     "required_cells": required_cells(ops),
                                     "active_blocks_by_plane": [sum(v == 2 for v in ops[sum(PLANE_TILES[:a]):sum(PLANE_TILES[:a+1])]) for a in range(3)],
                                     "tuple_count": mapped["tuple_count"],
                                     "planes": [{k: v for k, v in p.items() if k != "placements"}
                                                for p in mapped["planes"]]})
    manifest = {"schema": "cu66-v91i2-vector-manifest-v1",
                "scope": "Four actual all-BR88 frames with exact V91e coefficient goldens; two native AB38/mixed early rejects; one structural-only all-COPY empty-residual admission. No entropy, pixels or performance claims.",
                "source_pins": {"v91i_index_sha256": sha((V91I / "vectors/index.json").read_bytes()),
                                "v91e_coefficients_gzip_sha256": sha(V91E.read_bytes()),
                                "v87_quantizer_ledger_sha256": sha((ROOT / "experiments/python-gamebub-v87/quantizers/attempts/20261106T142631412759Z-5847ed8e/frames.jsonl").read_bytes()),
                                "v88_all_br88_history_sha256": sha((ROOT / "experiments/python-gamebub-v88/wire/attempts/20261106T150804504317Z-44bf5035/frames.jsonl").read_bytes()),
                                "v90_native_history_sha256": sha((ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1/frames.jsonl").read_bytes()),
                                "v88_receiver_source_sha256": sha((ROOT / "experiments/python-gamebub-v88/wire/receiver.cpp").read_bytes()),
                                "hidden_mask_sha256": MASK_SHA256},
                "tsv": {"path": "experiments/python-gamebub-v91i2/vectors/cases.tsv",
                        "sha256": sha(tsv_path.read_bytes()),
                        "columns": ["id", "expected_error", "packet_hex", "ref_valid", "ref_fid", "ref_generation", "qcache_valid", "cache_fid", "cache_generation", "prior_qscale_hex", "current_qscale_hex", "operations_hex", "denseY_hex", "denseCb_hex", "denseCr_hex"],
                        "byte_encodings": {"qscale": "1350 bytes, one 0..2 scale code per QM87 cell", "operations": "8100 bytes, 0=COPY, 1=CONST/hidden, 2=RESIDUAL", "dense_planes": "signed int16 little-endian; residual ordinal block-major then coefficient raster index"}},
                "cases": cases}
    (VECTORS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    results["manifest_sha256"] = sha((VECTORS / "manifest.json").read_bytes())
    results["tsv_sha256"] = sha(tsv_path.read_bytes())
    (AREA / "model-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

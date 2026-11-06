#!/usr/bin/env python3
"""Independent V91l C2/hash-trace audit. Uses only stdlib hashlib/struct.

This deliberately does not import the fixture model or testbench. It replays
the frozen V88 C2 grammar over each retained canonical tile list and compares
every recorded RTL node digest, including the HUD SHA and seal.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v91l"
VECTORS = ROOT / "experiments/python-gamebub-v91l/vectors"
DOMAIN = b"CU66V82C2\x00"
CONTEXT_TEXT = (b'{"geometry":[720,480,5400,1350,1350],"granularity":16,'
                b'"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}')
CONTEXT = hashlib.sha256(CONTEXT_TEXT).digest()
TILES = (5400, 1350, 1350)
WIDTHS = (720, 360, 360)
HEIGHTS = (480, 240, 240)


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def be(value: int, width: int) -> bytes:
    return value.to_bytes(width, "big")


def parse_header(packet: bytes) -> dict:
    assert len(packet) >= 132 and packet[:4] == b"CS88", "CS88 packet shape/magic"
    assert zlib.crc32(packet[:-4]) & 0xffffffff == int.from_bytes(packet[-4:], "big"), "CS88 outer CRC"
    assert packet[4] == 1 and packet[5] in (0, 1) and packet[6] == 16, "CS88 version/flags/group"
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    assert struct.unpack_from(">HHH", packet, 24) == (720, 480, struct.unpack_from(">H", packet, 28)[0])
    assert packet[30:32] == b"\x00\x00"
    lengths = struct.unpack_from(">IIIII", packet, 32)
    mode_n, qmap_n, hud_n, residual_n = lengths[1:]
    assert 128 + mode_n + qmap_n + hud_n + residual_n + 4 == len(packet), "CS88 body lengths"
    assert packet[116:128] == bytes(12), "CS88 reserved bytes"
    return {"fid": fid, "refid": refid, "generation": generation, "key": packet[5] == 1,
            "root": packet[52:84], "seal": packet[84:116]}


def raster_sha(tiles: bytes) -> bytes:
    assert len(tiles) == 8100 * 64
    result = bytearray()
    base = 0
    for count, width, height in zip(TILES, WIDTHS, HEIGHTS):
        plane = bytearray(width * height)
        tile_w = width // 8
        for idx in range(count):
            tile = tiles[(base + idx) * 64:(base + idx + 1) * 64]
            by, bx = divmod(idx, tile_w)
            for y in range(8):
                dst = (by * 8 + y) * width + bx * 8
                plane[dst:dst + 8] = tile[y * 8:y * 8 + 8]
        assert len(plane) == width * height
        result += plane
        base += count
    return sha(bytes(result))


def c2_tree(tiles: bytes) -> tuple[bytes, dict[int, bytes], int, int]:
    assert len(tiles) == sum(TILES) * 64
    nodes: dict[int, bytes] = {}
    leaf_number = 0
    base_tiles = 0
    msg_bytes = 0
    blocks = 0
    for plane, count in enumerate(TILES):
        for start in range(0, count, 16):
            n = min(16, count - start)
            payload = tiles[(base_tiles + start) * 64:(base_tiles + start + n) * 64]
            message = DOMAIN + b"L\x00" + CONTEXT + struct.pack(">BIH", plane, start, n) + payload
            assert len(message) == 51 + 64 * n
            nodes[512 + leaf_number] = sha(message)
            msg_bytes += len(message)
            blocks += (len(message) + 9 + 63) // 64
            leaf_number += 1
        base_tiles += count
    assert leaf_number == 508
    for idx in range(508, 512):
        message = DOMAIN + b"E\x00" + CONTEXT + struct.pack(">II", idx, 512)
        nodes[512 + idx] = sha(message)
        msg_bytes += len(message)
        blocks += (len(message) + 9 + 63) // 64
    width, level = 256, 1
    while width:
        for idx in range(width):
            message = (DOMAIN + b"N\x00" + struct.pack(">HI", level, idx)
                       + nodes[2 * (width + idx)] + nodes[2 * (width + idx) + 1])
            assert len(message) == 82
            nodes[width + idx] = sha(message)
            msg_bytes += len(message)
            blocks += (len(message) + 9 + 63) // 64
        width //= 2
        level += 1
    assert len(nodes) == 1023
    return nodes[1], nodes, msg_bytes, blocks


def c2_seal(header: dict, previous: bytes, hud_sha: bytes, root: bytes) -> tuple[bytes, bytes]:
    message = (DOMAIN + b"S\x00" + CONTEXT + struct.pack(">IIBQ", header["fid"], header["refid"],
               int(header["key"]), header["generation"]) + previous + hud_sha + root)
    assert len(message) == 157
    return sha(message), message


def input_rows(path: Path) -> list[dict]:
    csv.field_size_limit(8 * 1024 * 1024)
    with gzip.open(path, "rt", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    assert len(rows) == 7 and rows[0].keys() == {
        "id", "cohort", "role", "packet_hex", "canonical_tiles_hex", "hud_words_le_hex",
        "canonical_raster_sha256", "hud_semantic_sha256", "computed_root_hex", "computed_seal_hex"}
    return rows


def audit_attempt(attempt: Path) -> dict:
    report_path = attempt / "results.json"
    report = json.loads(report_path.read_text())
    assert report["schema"] == "cu66-v91l-heterogeneous-c2-publication-v1"
    assert report["status"] == "PASS_C2_AND_ATOMIC_PUBLICATION_WITH_SOFTWARE_HUD"
    # A reproducibility run may be captured after this work is committed. Keep
    # accepting descendant revisions, while the exact source/vector snapshots
    # below continue to bind the implementation that was actually tested.
    subprocess.run(["git", "merge-base", "--is-ancestor",
                    "1e974dcaab4b86646b0480f8987d3469316c06b3",
                    report["source_revision"]], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert report["verdict"]["status"] == "TEST_PASS" and report["verdict"]["cases"] == 14
    assert report["verdict"]["source_fixture_frames"] == 7
    assert report["verdict"]["directed_checks"] == len(report["verdict"]["directed_check_names"])
    assert report["verdict"]["directed_checks"] == 54
    check_counts = Counter(report["verdict"]["directed_check_names"])
    identity_checks = ("cold_delta_requires_accepted_reference", "zero_epoch_start_rejects",
                      "zero_generation_start_rejects", "reserved_frame_id_start_rejects",
                      "replayed_frame_id_start_rejects", "stale_generation_start_rejects",
                      "wrong_delta_reference_start_rejects", "key_non_sentinel_reference_start_rejects")
    assert all(check_counts[name] == 2 for name in identity_checks), "start identity probes must pass in both profiles"
    assert report["full_rtl_hud_decoder"] is False and report["complete_v91l_full_rtl_proven"] is False
    assert report["hardware_distinct_30fps_proven"] is False and report["full_frame_decode_under10ms_proven"] is False
    assert report["physical_bank_fit_proven"] is False
    assert all(cmd["exit_code"] == 0 for cmd in report["commands"])

    # Verify every attempt artifact and source/vector snapshot against the report's own pins.
    for rel, digest in report["artifacts_sha256"].items():
        p = attempt / rel
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"artifact hash: {rel}"
    for rel, digest in report["source_sha256"].items():
        p = attempt / "sources" / rel
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"source hash: {rel}"
    snap_model_results = attempt / "model-results.json"
    assert hashlib.sha256(snap_model_results.read_bytes()).hexdigest() == report["model_results_sha256"]
    for rel, digest in report["vectors_sha256"].items():
        p = attempt / "vectors" / rel
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"vector hash: {rel}"
    vecpack = attempt / "vectors/validation.tsv.gz"
    assert hashlib.sha256(vecpack.read_bytes()).hexdigest() == report["input_expansion"]["compressed_sha256"]
    assert hashlib.sha256(gzip.decompress(vecpack.read_bytes())).hexdigest() == report["input_expansion"]["raw_sha256"]
    rows = input_rows(vecpack)
    assert len(rows) == report["input_expansion"]["rows"] == 7

    expected: dict[str, dict] = {}
    previous_roots: dict[int, bytes] = {}
    for row in rows:
        ident = row["id"]
        cohort = int(row["cohort"])
        packet = bytes.fromhex(row["packet_hex"])
        header = parse_header(packet)
        assert header["fid"] >= 0 and ident == f"c{cohort}_f{header['fid']}"
        tiles = bytes.fromhex(row["canonical_tiles_hex"])
        hud = bytes.fromhex(row["hud_words_le_hex"])
        assert len(tiles) == 518400 and len(hud) == 42240
        assert raster_sha(tiles).hex() == row["canonical_raster_sha256"]
        hud_digest = sha(hud)
        assert hud_digest.hex() == row["hud_semantic_sha256"]
        root, nodes, node_msg_bytes, node_blocks = c2_tree(tiles)
        previous = bytes(32) if header["key"] else previous_roots[cohort]
        seal, seal_message = c2_seal(header, previous, hud_digest, root)
        assert root == header["root"] and seal == header["seal"], f"packet commitment {ident}"
        assert root.hex() == row["computed_root_hex"] and seal.hex() == row["computed_seal_hex"]
        previous_roots[cohort] = root
        # V91l's HUD job hashes exactly the transferred semantic word bytes;
        # unlike C2 tree/seal jobs it has no message prefix.
        hud_message = hud
        all_msg_bytes = node_msg_bytes + len(hud_message) + len(seal_message)
        all_blocks = node_blocks + (len(hud_message) + 9 + 63) // 64 + (len(seal_message) + 9 + 63) // 64
        assert all_msg_bytes == 628815 and all_blocks == 10298
        expected[ident] = {"header": header, "nodes": nodes, "root": root, "hud": hud_digest,
                           "seal": seal, "hud_msg": hud_message,
                           "seal_msg": seal_message, "tree_msg_bytes": node_msg_bytes,
                           "message_bytes": all_msg_bytes, "blocks": all_blocks}

    simulation = [json.loads(line) for line in (attempt / "simulation.jsonl").read_text().splitlines()]
    cases = [x for x in simulation if x.get("type") == "case"]
    verdicts = [x for x in simulation if x.get("type") == "verdict"]
    assert len(cases) == 14 and len(verdicts) == 1
    events_path = attempt / "events.jsonl.gz"
    events = [json.loads(line) for line in gzip.open(events_path, "rt")]
    assert len(events) == report["hash_trace"]["rows"] == 14350
    assert all(row.get("type") == "hash" for row in events)
    checks = 0
    event_groups: dict[tuple[str, int, int], dict[tuple[int, int], str]] = {}
    for event in events:
        key = (event["id"], int(event["profile"]), int(event["epoch"]))
        group = event_groups.setdefault(key, {})
        node_key = (int(event["kind"]), int(event["node"]))
        assert node_key not in group, f"duplicate hash job {key} {node_key}"
        group[node_key] = event["digest"]
    for case in cases:
        assert case["status"] == "PASS"
        ident, profile, epoch = case["id"], int(case["profile"]), int(case["epoch"])
        data = expected[ident]
        assert (case["root"], case["hud_sha256"], case["seal"]) == (
            data["root"].hex(), data["hud"].hex(), data["seal"].hex())
        assert (case["fid"], case["generation"]) == (
            data["header"]["fid"], data["header"]["generation"])
        assert case["canonical_bytes"] == 518400 and case["hud_bytes"] == 42240
        assert case["hash_jobs"] == 1025 and case["hash_message_bytes"] == 628815 and case["hash_blocks"] == 10298
        assert case["write_requests"] == case["write_acks"] == 560640
        trace = event_groups.pop((ident, profile, epoch))
        want = {(0, node): digest.hex() for node, digest in data["nodes"].items() if node >= 512}
        # Empty leaves and internal nodes share the RTL's global heap node numbers.
        want = {(0, node): data["nodes"][node].hex() for node in range(512, 1024)}
        want.update({(1, node): data["nodes"][node].hex() for node in range(1020, 1024)})
        # The separate empty-leaf job kind is assigned the same heap positions 1020..1023.
        want.update({(2, node): data["nodes"][node].hex() for node in range(1, 512)})
        want[(3, 0)] = data["hud"].hex()
        want[(4, 0)] = data["seal"].hex()
        # Regular leaves are kind 0 at 512..1019, not the generic leaves+empty range above.
        want = {(0, node): data["nodes"][node].hex() for node in range(512, 1020)}
        want.update({(1, node): data["nodes"][node].hex() for node in range(1020, 1024)})
        want.update({(2, node): data["nodes"][node].hex() for node in range(1, 512)})
        want[(3, 0)] = data["hud"].hex(); want[(4, 0)] = data["seal"].hex()
        assert trace == want, f"complete RTL digest trace mismatch {ident}/profile{profile}: missing={set(want)-set(trace)}, extra={set(trace)-set(want)}"
        checks += len(want)
    assert not event_groups, "unmatched RTL hash trace groups"
    assert checks == 14 * 1025
    vector_manifest = json.dumps(report["vectors_sha256"], sort_keys=True, separators=(",", ":")).encode()
    return {"attempt": str(attempt.relative_to(ROOT)), "seed": report["seed"],
            "status": "PASS_INDEPENDENT_C2_AND_TRACE_AUDIT", "cases": len(cases),
            "profiles": 2, "independently_checked_rtl_digest_jobs": checks,
            "results_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "event_trace_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
            "model_source_sha256": report["source_sha256"]["experiments/python-gamebub-v91l/model.py"],
            "fixture_manifest_sha256": hashlib.sha256(vector_manifest).hexdigest(),
            "directed_checks": report["verdict"]["directed_checks"],
            "identity_guard_check_counts": {name: check_counts[name] for name in identity_checks},
            "hash_message_bytes_per_frame_profile": 628815,
            "hash_blocks_per_frame_profile": 10298,
            "frames": [{"id": ident, "root": data["root"].hex(), "hud_sha256": data["hud"].hex(),
                        "seal": data["seal"].hex()} for ident, data in expected.items()],
            "scope": "Independent C2/HUD/seal commitments and all recorded RTL SHA digest jobs; accepted publication is assessed from the RTL testbench's direct assertions and attempt evidence. Per-case RTL cycles include finite candidate writes and hashing, but exclude native C++ HUD decode CPU time, which completes before the measured interval.",
            "source_revision": report["source_revision"],
            "limitations": ["software C++ HUD decoder is a heterogeneous partition, not full RTL HUD decode/overlay",
                            "canonical inputs are captured replay, not a live producer join",
                            "no hardware, distinct 30-fps, sub-10-ms, or physical bank-fit proof"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", nargs="*", type=Path, help="one or more validation-attempt directories")
    args = parser.parse_args()
    if args.attempt:
        attempts = args.attempt
    else:
        candidates = []
        for p in sorted((AREA / "validation-attempts").glob("*/results.json")):
            try:
                r = json.loads(p.read_text())
                if r.get("status") == "PASS_C2_AND_ATOMIC_PUBLICATION_WITH_SOFTWARE_HUD":
                    # Ignore older PASS artifacts whose testbench, model, or inputs
                    # no longer match the current source/vector pins.
                    sources_current = all(
                        (ROOT / rel).is_file() and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in r.get("source_sha256", {}).items())
                    vectors_current = all(
                        (VECTORS / rel).is_file() and hashlib.sha256((VECTORS / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in r.get("vectors_sha256", {}).items())
                    model_current = hashlib.sha256((ROOT / "experiments/python-gamebub-v91l/model-results.json").read_bytes()).hexdigest() == r.get("model_results_sha256")
                    if sources_current and vectors_current and model_current:
                        candidates.append((r.get("seed"), p.parent))
            except (OSError, json.JSONDecodeError):
                pass
        by_seed = {seed: p for seed, p in candidates}
        missing = [s for s in (911801, 911802) if s not in by_seed]
        if missing:
            raise SystemExit(f"no current-source PASS attempt for required seed(s): {missing}; refusing partial default audit")
        attempts = [by_seed[s] for s in (911801, 911802)]
    results = [audit_attempt(p if p.is_absolute() else ROOT / p) for p in attempts]
    seeds = [r["seed"] for r in results]
    assert len(seeds) == len(set(seeds)), "duplicate seed audit"
    complete = set(seeds) == {911801, 911802}
    model_results_path = ROOT / "experiments/python-gamebub-v91l/model-results.json"
    model_results = json.loads(model_results_path.read_text())
    baseline_pins = model_results["source_sha256"]
    # Validate the frame, decoder, canonical archive, and source-provenance pins
    # supplied by the frozen model result. These include the V82 raster source,
    # V69 HUD decoder/history, V88 wire receiver, and V90 accepted history.
    for rel, digest in baseline_pins.items():
        p = ROOT / rel
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"baseline source pin: {rel}"
    own_sources = {
        "experiments/python-gamebub-v91l/verify_results.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "experiments/python-gamebub-v91l/model-results.json": hashlib.sha256(model_results_path.read_bytes()).hexdigest(),
    }
    own_sources.update(baseline_pins)
    out = {"schema": "cu66-v91l-independent-c2-audit-v1",
           "status": "PASS_BOTH_SEEDS" if complete else "PASS_SELECTED_ATTEMPTS_PARTIAL",
           "source_revision": "1e974dcaab4b86646b0480f8987d3469316c06b3",
           "context_sha256": CONTEXT.hex(), "oracle": "stdlib hashlib/struct/zlib; no model.py import",
           "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "source_sha256": own_sources,
           "results": results,
           "pending_seed": None if complete else next((s for s in (911801, 911802) if s not in seeds), None)}
    target = ROOT / "experiments/python-gamebub-v91l/audit.json"
    target.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "audit": str(target), "seeds": seeds,
                      "digest_jobs": sum(r["independently_checked_rtl_digest_jobs"] for r in results)}, sort_keys=True))


if __name__ == "__main__":
    main()

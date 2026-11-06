#!/usr/bin/env python3
"""Independent audit of V91l byte/row write comparison evidence.

Uses only stdlib hashing/parsing and retained source/input/trace snapshots. It
does not import model.py, RTL, or the C++ bench as an oracle.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from itertools import islice
import gzip
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "2c1562f100a3c47f2096314eb9125144ddad12b5"
AREA = ROOT / "fpga/experiments/cu66-v91l-rows"
FIXTURES = ROOT / "experiments/python-gamebub-v91l/vectors"
DOMAIN = b"CU66V82C2\x00"
CONTEXT_TEXT = (b'{"geometry":[720,480,5400,1350,1350],"granularity":16,'
                b'"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}')
CONTEXT = hashlib.sha256(CONTEXT_TEXT).digest()
TILES = (5400, 1350, 1350)
WIDTHS = (720, 360, 360)
HEIGHTS = (480, 240, 240)


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def be(value: int, width: int) -> bytes:
    return value.to_bytes(width, "big")


def parse_header(packet: bytes) -> dict:
    assert len(packet) >= 132 and packet[:4] == b"CS88"
    assert packet[4] == 1 and packet[5] in (0, 1) and packet[6] == 16
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    assert packet[30:32] == b"\0\0"
    assert struct.unpack_from(">HHH", packet, 24)[:2] == (720, 480)
    assert __import__("zlib").crc32(packet[:-4]) & 0xFFFFFFFF == int.from_bytes(packet[-4:], "big")
    return {"fid": fid, "refid": refid, "generation": generation,
            "key": packet[5] == 1, "root": packet[52:84], "seal": packet[84:116]}


def raster_bytes(tiles: bytes) -> bytes:
    assert len(tiles) == 8100 * 64
    result = bytearray()
    base = 0
    for count, width, height in zip(TILES, WIDTHS, HEIGHTS):
        plane = bytearray(width * height)
        for idx in range(count):
            tile = tiles[(base + idx) * 64:(base + idx + 1) * 64]
            by, bx = divmod(idx, width // 8)
            for y in range(8):
                dst = (by * 8 + y) * width + bx * 8
                plane[dst:dst + 8] = tile[y * 8:y * 8 + 8]
        assert len(plane) == width * height
        result.extend(plane)
        base += count
    return bytes(result)


def c2_tree(tiles: bytes) -> tuple[bytes, dict[int, bytes], int, int]:
    assert len(tiles) == sum(TILES) * 64
    nodes: dict[int, bytes] = {}
    leaf_number = base_tiles = msg_bytes = blocks = 0
    for plane, count in enumerate(TILES):
        for start in range(0, count, 16):
            n = min(16, count - start)
            payload = tiles[(base_tiles + start) * 64:(base_tiles + start + n) * 64]
            message = DOMAIN + b"L\0" + CONTEXT + struct.pack(">BIH", plane, start, n) + payload
            nodes[512 + leaf_number] = sha(message)
            msg_bytes += len(message)
            blocks += (len(message) + 72) // 64
            leaf_number += 1
        base_tiles += count
    assert leaf_number == 508
    for idx in range(508, 512):
        message = DOMAIN + b"E\0" + CONTEXT + struct.pack(">II", idx, 512)
        nodes[512 + idx] = sha(message)
        msg_bytes += len(message)
        blocks += (len(message) + 72) // 64
    width, level = 256, 1
    while width:
        for idx in range(width):
            message = DOMAIN + b"N\0" + struct.pack(">HI", level, idx) + nodes[2 * (width + idx)] + nodes[2 * (width + idx) + 1]
            nodes[width + idx] = sha(message)
            msg_bytes += len(message)
            blocks += (len(message) + 72) // 64
        width //= 2
        level += 1
    assert len(nodes) == 1023
    return nodes[1], nodes, msg_bytes, blocks


def c2_seal(header: dict, previous: bytes, hud_digest: bytes, root: bytes) -> tuple[bytes, bytes]:
    message = (DOMAIN + b"S\0" + CONTEXT + struct.pack(">IIBQ", header["fid"], header["refid"],
               int(header["key"]), header["generation"]) + previous + hud_digest + root)
    assert len(message) == 157
    return sha(message), message


def read_validation(path: Path) -> list[dict]:
    csv.field_size_limit(8 * 1024 * 1024)
    with gzip.open(path, "rt", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    assert len(rows) == 7
    return rows


def read_cases(path: Path) -> dict[str, dict]:
    csv.field_size_limit(8 * 1024 * 1024)
    out = {}
    with path.open() as source:
        for line in source:
            if not line.strip():
                continue
            c = line.rstrip("\n").split("\t")
            ident = c[0]
            out[ident] = {"ref_valid": int(c[3]), "ref_fid": int(c[4]),
                          "ref_generation": int(c[5]), "qvalid": int(c[6]),
                          "cache_fid": int(c[7]), "cache_generation": int(c[8]),
                          "prior": bytes.fromhex(c[9]) if c[9] != "-" else b"",
                          "scales": bytes.fromhex(c[10]) if c[10] != "-" else b""}
    return out


def expected_frames(attempt: Path) -> dict[str, dict]:
    vals = read_validation(attempt / "inputs/validation.tsv.gz")
    expected = {}
    prev_roots: dict[int, bytes] = {}
    for row in vals:
        packet = bytes.fromhex(row["packet_hex"])
        header = parse_header(packet)
        ident = row["id"]
        cohort = int(row["cohort"])
        assert ident == f"c{cohort}_f{header['fid']}"
        tiles = bytes.fromhex(row["canonical_tiles_hex"])
        hud = bytes.fromhex(row["hud_words_le_hex"])
        assert len(tiles) == 518400 and len(hud) == 42240
        assert hashlib.sha256(raster_bytes(tiles)).hexdigest() == row["canonical_raster_sha256"]
        hud_digest = sha(hud)
        assert hud_digest.hex() == row["hud_semantic_sha256"]
        root, nodes, node_bytes, node_blocks = c2_tree(tiles)
        previous = bytes(32) if header["key"] else prev_roots[cohort]
        seal, seal_message = c2_seal(header, previous, hud_digest, root)
        assert root == header["root"] == bytes.fromhex(row["computed_root_hex"])
        assert seal == header["seal"] == bytes.fromhex(row["computed_seal_hex"])
        prev_roots[cohort] = root
        all_bytes = node_bytes + len(hud) + len(seal_message)
        all_blocks = node_blocks + (len(hud) + 72) // 64 + (len(seal_message) + 72) // 64
        assert (all_bytes, all_blocks) == (628815, 10298)
        expected[ident] = {"header": header, "tiles": tiles, "hud": hud,
                           "raster": raster_bytes(tiles), "root": root, "nodes": nodes,
                           "hud_sha": hud_digest, "seal": seal, "message_bytes": all_bytes,
                           "blocks": all_blocks}
    return expected


def artifact_check(attempt: Path, report: dict) -> None:
    for rel, digest in report["artifacts_sha256"].items():
        p = attempt / rel
        assert p.is_file() and sha_file(p) == digest, f"artifact hash mismatch: {rel}"
    for rel, digest in report["source_sha256"].items():
        snap = attempt / "sources" / rel
        assert snap.is_file() and sha_file(snap) == digest, f"source snapshot mismatch: {rel}"
        live = ROOT / rel
        assert live.is_file() and sha_file(live) == digest, f"current source differs from run snapshot: {rel}"
    for rel, digest in report.get("inputs_sha256", {}).items():
        snap = attempt / "inputs" / Path(rel).name
        assert snap.is_file() and sha_file(snap) == digest, f"input snapshot mismatch: {rel}"
        live = ROOT / rel
        assert live.is_file() and sha_file(live) == digest, f"current input differs from run snapshot: {rel}"
    for cmd in report["commands"]:
        assert cmd["exit_code"] == 0
        argv = cmd["argv"]
        if any("--build" in arg for arg in argv):
            assert "--assert" in argv and "-Wall" in argv
            assert "-CFLAGS" in argv
            cflags = argv[argv.index("-CFLAGS") + 1].split()
            assert {"-Wall", "-Wextra", "-Werror"}.issubset(cflags)
            assert not any(flag.startswith("-Wno-") for flag in cflags)
    subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, report["source_revision"]],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def baseline_frozen_sources(report: dict, attempt: Path) -> dict[str, str]:
    # These are historical sources included in both static builds. Prove their
    # copies are byte-identical to the selected immutable baseline commit.
    frozen = ["fpga/experiments/cu66-v91l-live/cu66_write_hash_join_v91l.sv",
              "fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv",
              "fpga/experiments/cu66-v91l-live/tb_live.cpp"]
    found = {}
    for rel in frozen:
        baseline = subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT)
        digest = hashlib.sha256(baseline).hexdigest()
        live = ROOT / rel
        assert live.is_file() and sha_file(live) == digest, f"live frozen source changed from baseline: {rel}"
        if rel in report["source_sha256"]:
            assert digest == report["source_sha256"][rel], f"frozen source changed from baseline: {rel}"
        found[rel] = digest
    # Every pre-existing source dependency must remain exactly the baseline
    # bytes. Newly introduced row experiment files and runner/generators are
    # pinned by their current and snapshotted digests instead.
    baseline_sources = {}
    for rel, digest in report["source_sha256"].items():
        probe = subprocess.run(["git", "cat-file", "-e", f"{BASELINE}:{rel}"], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if probe.returncode == 0:
            raw = subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT)
            baseline_digest = hashlib.sha256(raw).hexdigest()
            assert digest == baseline_digest, f"historical dependency changed from baseline: {rel}"
            baseline_sources[rel] = baseline_digest
        else:
            assert rel.startswith("fpga/experiments/cu66-v91l-rows/") or rel.startswith("scripts/cu66-v91l-rows/")
    # The generator's frozen byte-control module is compiled in the control
    # build. The wrapper and C++ bench are generator inputs, so pin them here.
    assert "fpga/experiments/cu66-v91l-live/cu66_write_hash_join_v91l.sv" in found
    generated_wrapper = attempt / "sources/fpga/experiments/cu66-v91l-rows/cs88_rows_v91l.sv"
    expected = subprocess.check_output(["git", "show", f"{BASELINE}:fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv"], cwd=ROOT).decode()
    expected = expected.replace("// Generated by make_wrapper.py; unchanged producer and validator RTL are instantiated below.",
                                "// Generated from frozen live wrapper; only candidate joiner/bus normalization varies.")
    expected = expected.replace("module cs88_live_v91l (", "module cs88_rows_v91l #(parameter bit ROW_WRITES=1'b1) (")
    expected = expected.replace("output logic [7:0] candidate_req_data,", "output logic [63:0] candidate_req_data,output logic [3:0] candidate_req_bytes,")
    expected = expected.replace("output logic [1:0] join_state", "output logic [2:0] join_state")
    a = expected.index(" cu66_write_hash_join_v91l joiner(")
    b = expected.index("\ncs88_pipeline_v91k producer(", a)
    old = expected[a:b]
    row = old.replace("cu66_write_hash_join_v91l joiner(", "cu66_row_write_hash_join_v91l joiner(")
    row = row.replace(".req_data(candidate_req_data),", ".req_data(candidate_req_data),.req_bytes(candidate_req_bytes),")
    row = row.replace(".state(join_state),", ".state(join_state),.fill_count(unused_fill_count),.deliver_index(unused_deliver_index),")
    old = old.replace(".req_data(candidate_req_data),", ".req_data(byte_req_data),").replace(".state(join_state),", ".state(byte_state),")
    block = (" generate if(ROW_WRITES)begin:rows\n logic [3:0] unused_fill_count;logic [2:0] unused_deliver_index;\n" + row +
             "\n end else begin:bytes_control\n logic [7:0] byte_req_data;logic [1:0] byte_state;\n"
             " assign candidate_req_data={56'd0,byte_req_data};assign candidate_req_bytes=1;\n"
             " assign join_state={1'b0,byte_state};\n" + old + "\n end endgenerate\n")
    expected = expected[:a] + block + expected[b:]
    assert generated_wrapper.read_text() == expected, "static comparison wrapper was not derived from baseline frozen wrapper"
    found.update(baseline_sources)
    return found


def parse_hash_trace(path: Path) -> dict:
    grouped: dict[tuple[str, int, int], dict[tuple[int, int], str]] = {}
    rows = [json.loads(line) for line in gzip.open(path, "rt")]
    for e in rows:
        assert e["type"] == "hash"
        k = (e["id"], int(e["profile"]), int(e["epoch"]))
        node = (int(e["kind"]), int(e["node"]))
        assert node not in grouped.setdefault(k, {})
        grouped[k][node] = e["digest"]
    return grouped


def expected_hash_jobs(frame: dict) -> dict[tuple[int, int], str]:
    nodes = frame["nodes"]
    want = {(0, n): nodes[n].hex() for n in range(512, 1020)}
    want.update({(1, n): nodes[n].hex() for n in range(1020, 1024)})
    want.update({(2, n): nodes[n].hex() for n in range(1, 512)})
    want[(3, 0)] = frame["hud_sha"].hex()
    want[(4, 0)] = frame["seal"].hex()
    return want


def expected_byte_stream(frame: dict):
    """Return (plane,tile,index,address,value) in actual hash delivery order."""
    out = []
    for p, count in enumerate(TILES):
        width = WIDTHS[p]
        for tile in range(count):
            by, bx = divmod(tile, width // 8)
            raw = frame["tiles"][(sum(TILES[:p]) + tile) * 64:(sum(TILES[:p]) + tile + 1) * 64]
            for index, value in enumerate(raw):
                y, x = divmod(index, 8)
                address = sum((720 * 480, 360 * 240)[:p]) + (by * 8 + y) * width + bx * 8 + x
                out.append((p, tile, index, address, value))
    base = 518400
    out.extend((3, i // 64, i % 64, base + i, value) for i, value in enumerate(frame["hud"]))
    return out


def iter_bus(path: Path):
    """Stream packed records in blocks; never hold the multi-million-row log in RAM."""
    record_size = 32
    with gzip.open(path, "rb") as source:
        carry = b""
        while True:
            block = source.read(record_size * 32768)
            if not block:
                break
            block = carry + block
            whole = len(block) - len(block) % record_size
            for at in range(0, whole, record_size):
                yield struct.unpack_from("<BBBBIIIIQI", block, at)
            carry = block[whole:]
        assert not carry, "truncated bus record"


def audit_bus(path: Path, cases: list[dict], frames: dict, mode: str) -> dict:
    records = iter(iter_bus(path))
    checked = rows = writes = acks = deliveries = 0
    request_counts = {0: 0, 1: 0}
    overhead_cycles = {0: 0, 1: 0}
    mode_payload_beats = 0
    expected_sizes = {1} if mode == "control" else {8}
    prior_cycle = 0
    # The bench runs both frames for FAST, then both frames for SLOW.
    for case in sorted(cases, key=lambda c: (int(c["profile"]), int(c["fid"]))):
        ident, profile, epoch, fid = case["id"], int(case["profile"]), int(case["epoch"]), int(case["fid"])
        stream = iter(expected_byte_stream(frames[ident]))
        group_n = 1 if mode == "control" else 8
        case_requests = case_bytes = case_beats = case_overhead = 0
        case_first_token = case_last_token = None
        for offset in range(0, 560640, group_n):
            chunk = list(islice(stream, group_n))
            assert len(chunk) == group_n
            req = next(records)
            kind, prof, bank, size, rf, repoch, token, addr, value, cycle = req
            assert kind == 0 and prof == profile and rf == fid and repoch == epoch and size in expected_sizes
            assert cycle >= prior_cycle, "bus trace cycle regressed"
            assert addr == chunk[0][3] and addr % group_n == 0
            packed = sum(int(b[4]) << (8 * n) for n, b in enumerate(chunk))
            assert value == packed, f"physical write payload differs at {ident}/{profile}/{offset}"
            if group_n == 8:
                assert len(chunk) == 8 and all(chunk[n][0] == chunk[0][0] and chunk[n][1] == chunk[0][1] and chunk[n][2] == chunk[0][2] // 8 * 8 + n for n in range(8))
            assert bank == case["_candidate_bank"]
            if case_first_token is None:
                case_first_token = token
            case_last_token = token
            prior_cycle = cycle
            ack = next(records)
            ak, ap, ab, az, af, ae, atok, aa, avalue, acycle = ack
            assert (ak, ap, ab, az, af, ae, atok, aa, avalue) == (1, profile, bank, size, fid, epoch, token, addr, value)
            assert acycle >= prior_cycle
            payload_beats = (size + 1) // 2
            overhead = acycle - cycle - payload_beats
            assert overhead == 1 if profile == 0 else 2 <= overhead <= 7
            request_counts[profile] += 1
            overhead_cycles[profile] += overhead
            case_requests += 1
            case_bytes += size
            case_beats += payload_beats
            case_overhead += overhead
            mode_payload_beats += payload_beats
            prior_cycle = acycle
            for n, b in enumerate(chunk):
                delivery = next(records)
                dk, dp, db, ds, df, de, dt, da, dv, dc = delivery
                assert (dk, dp, db, ds, df, de, dt, da, dv) == (2, profile, bank, 1, fid, epoch, 0, b[3], b[4])
                assert dc >= acycle and dc >= prior_cycle
                prior_cycle = dc
                deliveries += 1
            rows += 1
            writes += size
            acks += 1
        checked += 560640
        assert case_requests == int(case["write_requests"]) == int(case["write_acks"])
        assert case_bytes == int(case["physical_write_bytes"]) == 560640
        assert case_beats == int(case["x16_data_beats"])
        assert case_overhead == int(case["candidate_response_overhead_cycles"])
        assert case_first_token == int(case["first_token"]) and case_last_token == int(case["last_token"])
    try:
        extra = next(records)
    except StopIteration:
        extra = None
    assert extra is None, f"extra bus event: {extra}"
    return {"cases": len(cases), "request_count": rows, "ack_count": acks,
            "delivered_bytes": deliveries, "physical_write_bytes": writes,
            "exact_hash_order_bytes": checked,
            "x16_data_beats": mode_payload_beats,
            "requests_by_profile": {str(k): v for k, v in request_counts.items()},
            "response_overhead_cycles_by_profile": {str(k): v for k, v in overhead_cycles.items()}}


def audit_attempt(attempt: Path, seed: int) -> dict:
    report_path = attempt / "results.json"
    report = json.loads(report_path.read_text())
    assert report["schema"] == "cu66-v91l-tile-row-write-comparison-v1"
    assert report["status"] == "PASS_EXACT_X16_PRICED_TILE_ROW_WRITES"
    assert int(report["seed"]) == seed
    assert report["live_canonical_producer"] is True
    assert not report["full_rtl_hud_decoder"] and not report["full_rtl_hud_overlay"]
    assert not report["physical_memory_controller"]
    assert not report["hardware_distinct_30fps_proven"] and not report["full_frame_decode_under10ms_proven"]
    assert not report["monolithic_full_frame_rtl_proven"]
    artifact_check(attempt, report)
    frozen = baseline_frozen_sources(report, attempt)
    inputs = [attempt / "inputs" / Path(rel).name for rel in report["inputs_sha256"]]
    for p in inputs:
        assert p.is_file()
    frames = expected_frames(attempt)
    case_goldens = read_cases(attempt / "inputs/cases.tsv")
    # Full uncompressed fixture expansion and compressed pins are checked directly.
    for exp in report["input_expansions"]:
        packed = attempt / exp["compressed_path"]
        assert sha_file(packed) == exp["compressed_sha256"]
        raw = gzip.decompress(packed.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == exp["raw_sha256"]
        assert len(raw.splitlines()) == exp["rows"]

    modes_out = {}
    reference_artifacts = {}
    for mode in report["modes"]:
        name = mode["name"]
        assert mode["status"] == "PASS_EXACT_LIVE_PATH"
        width = 1 if name == "control" else 8
        assert mode["write_batch_bytes"] == width
        assert mode["verdict"]["status"] == "TEST_PASS"
        assert mode["verdict"]["cases"] == 4
        live_cases = mode["live_rows"]
        assert len(live_cases) == 4
        assert {(c["id"], int(c["profile"])) for c in live_cases} == {(i, p) for i in ("c0_f0", "c0_f1") for p in (0, 1)}
        sim_rows = [json.loads(line) for line in (attempt / f"simulation-{name}.jsonl").read_text().splitlines()]
        sim_verdicts = [r for r in sim_rows if r.get("type") == "verdict"]
        sim_cases = [r for r in sim_rows if r.get("type") == "live_case"]
        assert len(sim_verdicts) == 1 and sim_verdicts[0] == mode["verdict"]
        assert len(sim_cases) == len(live_cases) == 4
        assert sim_cases == live_cases
        names = mode["verdict"]["directed_check_names"]
        assert mode["verdict"]["directed_checks"] == len(names) == 39
        counts = Counter(names)
        required_twice = ("wrong_write_ack_retains_then_drains",
                          "partial_candidate_write_error_preserves_accepted_bank",
                          "matching_write_bus_error_rejects", "abort_owned_write_blocks_retry",
                          "warm_reset_owned_write_blocks_retry", "live_bad_root_rejects_after_canonical",
                          "admitted_metadata_binds_start_hints", "wrong_hud_index_rejects_without_write",
                          "wrong_hud_last_rejects_without_write", "extra_hud_token_rejects_before_out_of_range_write",
                          "front_waits_vblank", "front_waits_scanout_drain", "front_presents_after_both_fences")
        assert all(counts[name] == 2 for name in required_twice)
        assert counts["external_start_blocked_while_candidate_owned"] == 8
        required_once = ("live_parser_reconstruct_to_write_ack_to_hash",
                         "actual_accepted_bank_is_delta_reference",
                         "actual_hud_decode_and_acked_hash_transfer",
                         "accepted_qcache_only_published_after_validated_commit",
                         "all_1025_hash_jobs_real_rtl_per_frame")
        assert all(counts[name] == 1 for name in required_once)
        for c in live_cases:
            frame = frames[c["id"]]
            h = frame["header"]
            assert c["status"] == "PASS"
            assert (c["fid"], c["generation"]) == (h["fid"], h["generation"])
            assert (c["root"], c["hud_sha256"], c["seal"]) == (frame["root"].hex(), frame["hud_sha"].hex(), frame["seal"].hex())
            assert (c["canonical_bytes"], c["hud_bytes"], c["hash_jobs"], c["hash_message_bytes"], c["hash_blocks"]) == (518400, 42240, 1025, 628815, 10298)
            assert c["write_batch_bytes"] == width and c["write_requests"] == c["write_acks"] == 560640 // width
            assert c["x16_data_beats"] == (560640 if width == 1 else 280320)
            assert c["physical_write_bytes"] == c["hash_deliveries"] == 560640
            if h["key"]:
                assert c["qcache_bytes"] == 0 and c["reference_requests"] == 0
            else:
                assert c["qcache_bytes"] == 1350 and c["reference_requests"] == 7806
            c["_candidate_bank"] = int(c["accepted_bank"])
        hashes = parse_hash_trace(attempt / mode["compressed_artifacts"][f"hashes-{name}.jsonl"]["path"])
        hash_count = 0
        for c in live_cases:
            key = (c["id"], int(c["profile"]), int(c["epoch"]))
            actual = hashes.pop(key)
            wanted = expected_hash_jobs(frames[c["id"]])
            assert actual == wanted, f"independent RTL SHA-256 mismatch for {name}/{key}"
            hash_count += len(actual)
        assert not hashes and hash_count == 4 * 1025
        bus_meta = mode["compressed_artifacts"][f"bus-{name}.bin"]["path"]
        bus_result = audit_bus(attempt / bus_meta, live_cases, frames, name)

        # Actual bank and qcache exports are checked byte-for-byte independently.
        with gzip.open(attempt / mode["compressed_artifacts"][f"actual-{name}.tsv"]["path"], "rt") as src:
            rows = src.read().splitlines()
        assert len(rows) == 12
        archived = {}
        for line in rows:
            tag, profile, rawhex = line.split("\t")
            assert len(rawhex) % 2 == 0
            archived[(tag, int(profile))] = bytes.fromhex(rawhex)
        for c in live_cases:
            ident, profile = c["id"], int(c["profile"])
            expected_bank = frames[ident]["raster"] + frames[ident]["hud"]
            case = case_goldens[c["pipeline_id"]]
            assert archived[(f"accepted_{c['pipeline_id']}", profile)] == expected_bank
            qcache = archived[(f"qcache_{c['pipeline_id']}", profile)]
            assert len(qcache) == len(case["scales"]) == 1350
            assert qcache == case["scales"]
            if case["qvalid"]:
                assert case["prior"] == archived[(f"qcache_{'actual_001'}", profile)]
            reference_artifacts[f"{name}:{ident}:p{profile}"] = {
                "accepted_bank": int(c["accepted_bank"]),
                "accepted_bank_sha256": hashlib.sha256(expected_bank).hexdigest(),
                "qcache_sha256": hashlib.sha256(qcache).hexdigest(),
                "qcache_bytes": len(qcache),
            }
        modes_out[name] = {"batch_bytes": width, "x16_data_beats": sum(int(c["x16_data_beats"]) for c in live_cases),
                           "candidate_response_overhead_cycles": sum(int(c["candidate_response_overhead_cycles"]) for c in live_cases),
                           "response_overhead_by_profile": {str(p): {"requests": sum(int(c["write_requests"]) for c in live_cases if int(c["profile"]) == p),
                                                                       "overhead_cycles": sum(int(c["candidate_response_overhead_cycles"]) for c in live_cases if int(c["profile"]) == p)} for p in (0, 1)},
                           "write_requests": sum(int(c["write_requests"]) for c in live_cases),
                           "rtl_sha_jobs_independently_verified": hash_count,
                           "bus_replay": bus_result}
        assert bus_result["response_overhead_cycles_by_profile"] == {
            str(p): sum(int(c["candidate_response_overhead_cycles"]) for c in live_cases if int(c["profile"]) == p)
            for p in (0, 1)}

    assert modes_out["control"]["x16_data_beats"] == 4 * 560640
    assert modes_out["rows"]["x16_data_beats"] == 4 * 280320
    for mode in modes_out.values():
        assert mode["response_overhead_by_profile"]["0"]["overhead_cycles"] == mode["response_overhead_by_profile"]["0"]["requests"]
        assert mode["response_overhead_by_profile"]["1"]["overhead_cycles"] in range(2 * mode["response_overhead_by_profile"]["1"]["requests"], 7 * mode["response_overhead_by_profile"]["1"]["requests"] + 1)
    return {"seed": seed, "status": "PASS_INDEPENDENT_ROW_COMPARISON_AUDIT",
            "selected_report": str(report_path.relative_to(ROOT)),
            "selected_report_sha256": sha_file(report_path),
            "source_revision": report["source_revision"],
            "baseline_guard": BASELINE, "frozen_source_sha256_equal_baseline": frozen,
            "mode_results": modes_out,
            "actual_accepted_banks_and_qcache": reference_artifacts,
            "scope": "Independent hashlib C2/HUD/seal recomputation, all recorded RTL SHA digest jobs, canonical/HUD byte writes, byte-order ACK replay, accepted bank and qcache exports. Source-level bench assertions remain simulation evidence, not formal proof.",
            "limitations": ["x16 payload-beat pricing applies only to candidate-write responses; reference reads and scratch traffic remain separate logical services",
                            "candidate response overhead is shared per logical candidate request (FAST 1, SLOW 2..7), not a command-accurate SDRAM bridge or per-word wait schedule",
                            "software HUD decode occurs before start; HUD hash bytes and candidate writes are present in the RTL integration path",
                            "wrong-ACK/abort/reset/bus-error negative cases are source-level self-checking simulation assertions; their partial bus-error writes are not in the nominal binary receipt replay",
                            "no physical SDRAM, achieved clock, FPS, sub-10-ms decode, or hardware distinct-30-fps claim"]}


def audit_standalone_row(seed: int) -> dict:
    matches = []
    for report_path in sorted((AREA / "row-attempts").glob("*/results.json")):
        candidate = json.loads(report_path.read_text())
        if int(candidate.get("seed", -1)) == seed and candidate.get("status") == "PASS_ROW_ACK_BEFORE_ORDERED_HASH":
            matches.append((report_path, candidate))
    assert len(matches) == 1, f"expected one row standalone report for seed {seed}"
    report_path, report = matches[0]
    attempt = report_path.parent
    artifact_check(attempt, report)
    subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, report["source_revision"]],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert report["schema"] == "cu66-v91l-row-standalone-v1"
    assert report["verdict"]["status"] == "TEST_PASS" and report["verdict"]["seed"] == seed
    assert report["verdict"]["exact_bytes"] == 4096 and report["verdict"]["directed_checks"] == 32
    assert all(c["exit_code"] == 0 for c in report["commands"])
    sim_path = attempt / report["simulation_trace"]["path"]
    raw = gzip.decompress(sim_path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == report["simulation_trace"]["raw_sha256"]
    rows = [json.loads(line) for line in raw.splitlines()]
    samples = [x for x in rows if x.get("type") == "sample"]
    cases = [x for x in rows if x.get("type") == "case"]
    directed = [x for x in rows if x.get("type") == "directed"]
    verdicts = [x for x in rows if x.get("type") == "verdict"]
    assert len(samples) == 4096 and len(cases) == 2 and len(directed) == 32 and len(verdicts) == 1
    assert verdicts[0] == report["verdict"]
    assert [(x["profile"], x["rows"], x["bytes"]) for x in cases] == [(0, 256, 2048), (1, 256, 2048)]
    names = Counter(x["name"] for x in directed if x["status"] == "PASS")
    expected_names = {"fast_exact_row_ack_before_all_hash_bytes", "slow_exact_row_ack_before_all_hash_bytes",
                      "cancel_partial_fill", "cancel_unaccepted_offer", "cancel_partial_hash_delivery",
                      "cancel_pending_row_ack_drain", "cancel_matching_ack_same_edge", "reset_partial_fill",
                      "reset_unaccepted_offer", "reset_partial_hash_delivery", "reset_pending_row_ack_drain",
                      "reset_matching_ack_same_edge", "wrong_epoch_ack_retains_row", "wrong_token_ack_retains_row",
                      "wrong_bank_ack_retains_row", "wrong_addr_ack_retains_row",
                      "matching_bus_error_drains_without_hash", "fill_epoch_mismatch", "fill_fid_mismatch",
                      "fill_bank_mismatch", "fill_plane_mismatch", "fill_tile_mismatch", "fill_index_mismatch",
                      "fill_address_mismatch", "fill_kind_mismatch", "fill_early_last_mismatch",
                      "first_zero_epoch", "first_unaligned_address", "first_unaligned_index",
                      "first_invalid_plane", "first_early_last", "clean_row_retry_after_faults"}
    assert set(names) == expected_names and all(count == 1 for count in names.values())
    for sample in samples:
        profile, n, j = int(sample["profile"]), int(sample["row"]), int(sample["byte"])
        assert 0 <= profile < 2 and 0 <= n < 256 and 0 <= j < 8
        hud = n >= 192
        if hud:
            plane, tile, index, addr = 0, 0, 0, 518400 + (n - 192) * 8 + j
        else:
            plane, tile, index = n // 64, (n % 64) // 8, (n % 8) * 8 + j
            width = 720 if plane == 0 else 360
            base = 0 if plane == 0 else 345600 if plane == 1 else 432000
            addr = base + tile * 8 + (index // 8) * width + (index % 8)
        assert sample["hud"] == int(hud) and sample["plane"] == plane and sample["tile"] == tile
        assert sample["index"] == (0 if hud else index)
        assert sample["addr"] == addr and sample["data"] == (n * 17 + j * 37 + 11) & 255
        assert sample["bank"] == 2 and sample["fid"] == 31
        assert sample["token"] == profile * 256 + n + 1
        assert sample["last"] == int(n == 255 and j == 7)
    return {"seed": seed, "status": "PASS_INDEPENDENT_STANDALONE_ROW_AUDIT",
            "selected_report": str(report_path.relative_to(ROOT)),
            "selected_report_sha256": sha_file(report_path),
            "selected_cycles": report["verdict"]["cycles"],
            "directed_checks": len(directed), "checked_actual_hash_bytes": len(samples),
            "row_boundary_protocol_cases": sorted(expected_names),
            "limitations": ["generated standalone payloads; source-level simulation assertions are not formal proof"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("attempt", nargs="*", type=Path)
    args = ap.parse_args()
    if args.attempt:
        attempts = [p if p.is_absolute() else ROOT / p for p in args.attempt]
    else:
        candidates = {}
        for p in sorted((AREA / "comparison-attempts").glob("*/results.json")):
            try:
                r = json.loads(p.read_text())
                if r.get("status") == "PASS_EXACT_X16_PRICED_TILE_ROW_WRITES":
                    for mode in r["modes"]:
                        if mode.get("status") != "PASS_EXACT_LIVE_PATH":
                            raise ValueError("incomplete mode")
                    candidates[int(r["seed"])] = p.parent
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
        required = (912101, 912102)
        missing = [s for s in required if s not in candidates]
        if missing:
            raise SystemExit(f"missing current-source PASS attempt(s) for seed(s): {missing}")
        attempts = [candidates[s] for s in required]
    results = [audit_attempt(p, int(json.loads((p / "results.json").read_text())["seed"])) for p in attempts]
    seeds = [r["seed"] for r in results]
    assert len(seeds) == len(set(seeds))
    assert set(seeds) == {912101, 912102}
    own_sha = sha_file(Path(__file__))
    standalone = [audit_standalone_row(seed) for seed in (912101, 912102)]
    out = {"schema": "cu66-v91l-row-independent-audit-v1", "status": "PASS_BOTH_SEEDS",
           "baseline": BASELINE, "verifier_sha256": own_sha,
           "oracle": "stdlib hashlib/struct/zlib; no model/DUT imports",
           "standalone_row_adapter": standalone, "results": results}
    target = ROOT / "experiments/python-gamebub-v91l-rows/audit.json"
    target.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "audit": str(target), "seeds": seeds,
                      "report_sha256": [r["selected_report_sha256"] for r in results]}, sort_keys=True))


if __name__ == "__main__":
    main()

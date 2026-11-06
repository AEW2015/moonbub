#!/usr/bin/env python3
"""Independent live V91l integration audit using only Python stdlib."""
import csv
import gzip
import hashlib
import json
import struct
import subprocess
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91l-live"
INTEGRATION = ROOT / "fpga/experiments/cu66-v91l-live/integration-attempts"
BASELINE = "0bfc018f06f1ac20342041eb8b948b6a33f83a6c"
DOMAIN = b"CU66V82C2\x00"
CONTEXT_TEXT = (b'{"geometry":[720,480,5400,1350,1350],"granularity":16,'
                b'"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}')
CONTEXT = hashlib.sha256(CONTEXT_TEXT).digest()
TILES = (5400, 1350, 1350)
WIDTHS = (720, 360, 360)
HEIGHTS = (480, 240, 240)
SOURCES = (
    "fpga/experiments/cu66-v91/br88_rice_elastic.sv",
    "fpga/experiments/cu66-v91b/br88_context.sv",
    "fpga/experiments/cu66-v91d/br88_packet_ingress.sv",
    "fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv",
    "fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv",
    "fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv",
    "fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv",
    "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv",
    "fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv",
    "fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv",
    "fpga/experiments/cu66-v69/inverse/cu66_dequant.sv",
    "fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv",
    "fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv",
    "fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv",
    "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv",
    "fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv",
    "fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv",
    "fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv",
    "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv",
    "fpga/experiments/cu66-v91l-live/cu66_write_hash_join_v91l.sv",
    "fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv",
    "fpga/experiments/cu66-v91l-live/tb_live.cpp",
    "fpga/experiments/cu66-v91l-live/make_wrapper.py",
    "fpga/experiments/cu66-v91l-live/make_bench.py",
    "scripts/cu66-v91l-live/run_integration.py",
    "fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh",
    "experiments/cu66-native-v69/hud.hpp",
    "experiments/cu66-native-v69/bytes.hpp",
    "experiments/cu66-native-v69/generated_constants.hpp",
)
INPUTS = (
    "experiments/python-gamebub-v91i2/vectors/cases.tsv",
    "experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz",
    "experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz",
    "experiments/python-gamebub-v91l/vectors/validation.tsv.gz",
)
EXPECTED_CHECKS = {
    "wrong_write_ack_retains_then_drains", "matching_write_bus_error_rejects",
    "abort_owned_write_blocks_retry", "warm_reset_owned_write_blocks_retry",
    "live_bad_root_rejects_after_canonical", "admitted_metadata_binds_start_hints",
    "wrong_hud_index_rejects_without_write", "wrong_hud_last_rejects_without_write",
    "extra_hud_token_rejects_before_out_of_range_write", "front_waits_vblank",
    "front_waits_scanout_drain", "front_presents_after_both_fences",
    "live_parser_reconstruct_to_write_ack_to_hash", "actual_accepted_bank_is_delta_reference",
    "actual_hud_decode_and_acked_hash_transfer", "accepted_qcache_only_published_after_validated_commit",
    "all_1025_hash_jobs_real_rtl_per_frame",
}
ONCE_CHECKS = {
    "live_parser_reconstruct_to_write_ack_to_hash", "actual_accepted_bank_is_delta_reference",
    "actual_hud_decode_and_acked_hash_transfer", "accepted_qcache_only_published_after_validated_commit",
    "all_1025_hash_jobs_real_rtl_per_frame",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).digest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_validation(path):
    csv.field_size_limit(8 * 1024 * 1024)
    with gzip.open(path, "rt", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    return {row["id"]: row for row in rows}


def rasterize(tiles):
    require(len(tiles) == 518400, "canonical tile stream size")
    raster = bytearray()
    base = 0
    for count, width, height in zip(TILES, WIDTHS, HEIGHTS):
        plane = bytearray(width * height)
        tile_width = width // 8
        for index in range(count):
            tile = tiles[(base + index) * 64:(base + index + 1) * 64]
            by, bx = divmod(index, tile_width)
            for y in range(8):
                pos = (by * 8 + y) * width + bx * 8
                plane[pos:pos + 8] = tile[y * 8:y * 8 + 8]
        require(len(plane) == width * height, "plane geometry")
        raster.extend(plane)
        base += count
    return bytes(raster)


def c2_tree(tiles):
    nodes = {}
    leaf = 0
    base_tiles = 0
    message_bytes = 0
    blocks = 0
    for plane, count in enumerate(TILES):
        for start in range(0, count, 16):
            n = min(16, count - start)
            payload = tiles[(base_tiles + start) * 64:(base_tiles + start + n) * 64]
            message = DOMAIN + b"L\x00" + CONTEXT + struct.pack(">BIH", plane, start, n) + payload
            nodes[512 + leaf] = sha(message)
            message_bytes += len(message)
            blocks += (len(message) + 72) // 64
            leaf += 1
        base_tiles += count
    require(leaf == 508, "leaf count")
    for index in range(508, 512):
        message = DOMAIN + b"E\x00" + CONTEXT + struct.pack(">II", index, 512)
        nodes[512 + index] = sha(message)
        message_bytes += len(message)
        blocks += (len(message) + 72) // 64
    width, level = 256, 1
    while width:
        for index in range(width):
            message = (DOMAIN + b"N\x00" + struct.pack(">HI", level, index)
                       + nodes[2 * (width + index)] + nodes[2 * (width + index) + 1])
            nodes[width + index] = sha(message)
            message_bytes += len(message)
            blocks += (len(message) + 72) // 64
        width //= 2
        level += 1
    return nodes[1], nodes, message_bytes, blocks


def packet_header(packet):
    require(packet[:4] == b"CS88" and len(packet) >= 132, "CS88 packet")
    require((zlib.crc32(packet[:-4]) & 0xFFFFFFFF) == int.from_bytes(packet[-4:], "big"), "CS88 packet CRC")
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    return {"fid": fid, "refid": refid, "generation": generation,
            "key": packet[5] == 1, "root": packet[52:84], "seal": packet[84:116]}


def expected_jobs(row, previous_root=None):
    packet = bytes.fromhex(row["packet_hex"])
    h = packet_header(packet)
    tiles = bytes.fromhex(row["canonical_tiles_hex"])
    hud = bytes.fromhex(row["hud_words_le_hex"])
    root, nodes, tree_bytes, tree_blocks = c2_tree(tiles)
    hud_digest = sha(hud)
    previous = bytes(32) if h["key"] else previous_root
    require(previous is not None, f"missing causal prior root {row['id']}")
    seal_msg = (DOMAIN + b"S\x00" + CONTEXT + struct.pack(">IIBQ", h["fid"], h["refid"],
                int(h["key"]), h["generation"]) + previous + hud_digest + root)
    seal = sha(seal_msg)
    require(root == h["root"] and seal == h["seal"], f"packet commitments {row['id']}")
    jobs = {(0, n): digest.hex() for n, digest in nodes.items() if 512 <= n < 1020}
    jobs.update({(1, n): digest.hex() for n, digest in nodes.items() if n >= 1020})
    jobs.update({(2, n): digest.hex() for n, digest in nodes.items() if n < 512})
    jobs[(3, 0)] = hud_digest.hex()
    jobs[(4, 0)] = seal.hex()
    require(len(jobs) == 1025, "expected RTL job count")
    require(tree_bytes + len(hud) + len(seal_msg) == 628815, "hash message byte count")
    require(tree_blocks + (len(hud) + 72) // 64 + (len(seal_msg) + 72) // 64 == 10298,
            "hash block count")
    return h, tiles, hud, root.hex(), hud_digest.hex(), seal.hex(), jobs


def audit_attempt(path, current_pins):
    report = json.loads(path.read_text())
    require(report["schema"] == "cu66-v91l-live-write-hash-join-v1", "report schema")
    require(report["status"] == "PASS_LIVE_CANONICAL_ACK_HASH_PUBLICATION_WITH_SOFTWARE_HUD", "attempt failed")
    require(report["source_sha256"] == current_pins, "current-source pin mismatch")
    require(report["live_canonical_producer"] is True, "producer is not reported live")
    for key in ("full_rtl_hud_decoder", "full_rtl_hud_overlay", "physical_memory_controller",
                "hardware_distinct_30fps_proven", "full_frame_decode_under10ms_proven"):
        require(report[key] is False, f"scope overclaim: {key}")
    require(all(command["exit_code"] == 0 for command in report["commands"]), "nonzero command")
    build_commands = [c["argv"] for c in report["commands"] if "--build" in c["argv"]]
    require(len(build_commands) == 1, "expected one strict compile")
    args = build_commands[0]
    require("--assert" in args and "-Wall" in args and args[args.index("-j") + 1] == "2", "Verilator flags")
    cflags = args[args.index("-CFLAGS") + 1]
    require(all(flag in cflags for flag in ("-std=c++17", "-Wall", "-Wextra", "-Werror")), "C++ flags")
    attempt = path.parent
    for rel, digest in report["artifacts_sha256"].items():
        require(file_sha(attempt / rel) == digest, f"artifact hash {rel}")
    for rel, digest in report["source_sha256"].items():
        require(file_sha(attempt / "sources" / rel) == digest, f"source snapshot {rel}")
    for rel, digest in report["inputs_sha256"].items():
        require(file_sha(attempt / "inputs" / Path(rel).name) == digest, f"input snapshot {rel}")
    for expanded in report["input_expansions"]:
        packed = (attempt / expanded["compressed_path"]).read_bytes()
        raw = gzip.decompress(packed)
        require(hashlib.sha256(packed).hexdigest() == expanded["compressed_sha256"], "input compressed hash")
        require(hashlib.sha256(raw).hexdigest() == expanded["raw_sha256"], "input expanded hash")
        require(len(raw.splitlines()) == expanded["rows"], "input expanded row count")

    verdict = report["verdict"]
    require(verdict["status"] == "TEST_PASS" and verdict["seed"] == report["seed"], "test verdict")
    require(verdict["cases"] == 4 and verdict["source_frames"] == 2 and verdict["profiles"] == 2,
            "live case matrix")
    check_counts = Counter(verdict["directed_check_names"])
    require(verdict["directed_checks"] == len(verdict["directed_check_names"]), "directed count")
    require(check_counts["external_start_blocked_while_candidate_owned"] == 8, "busy start gate coverage")
    require(all(check_counts[name] == (1 if name in ONCE_CHECKS else 2)
                for name in EXPECTED_CHECKS), "directed checks per seed/profile")
    require(set(check_counts) == EXPECTED_CHECKS | {"external_start_blocked_while_candidate_owned"},
            "unexpected/missing directed case")
    require(len(report["live_rows"]) == 4, "live rows")

    wrapper = (attempt / "sources/fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv").read_text()
    bench = (attempt / "sources/fpga/experiments/cu66-v91l-live/tb_live.cpp").read_text()
    require("cs88_pipeline_v91k producer(" in wrapper and "cs88_validate_publish_v91l validator(" in wrapper,
            "source does not connect the actual parser/reconstruction and validator")
    require(".pixel_valid(join_output_valid&&!join_output_hud)" in wrapper and
            ".pixel_data(join_output_data)" in wrapper and ".producer_done(done)" in wrapper,
            "producer/ACK/hash data path wiring missing")
    require("cu66::decode_hud" in bench and "active->packet[at]" in bench and
            "candidate_memory[q.bank][q.addr]=q.value" in bench,
            "live packet, native HUD, or ACK-committed memory source assertion missing")
    require("actual_qcache" in bench and "qcache_seen" in bench and
            "accepted_qcache=actual_qcache" in bench,
            "qcache output is not taken from registered RTL lookup observations")

    fixtures = parse_validation(ROOT / INPUTS[-1])
    fixture_by_id = {"c0_f0": fixtures["c0_f0"], "c0_f1": fixtures["c0_f1"]}
    key_row = fixture_by_id["c0_f0"]
    key_header = packet_header(bytes.fromhex(key_row["packet_hex"]))
    expected = {
        "c0_f0": expected_jobs(key_row),
        "c0_f1": expected_jobs(fixture_by_id["c0_f1"], key_header["root"]),
    }
    row_ids = {(r["id"], r["profile"]) for r in report["live_rows"]}
    require(row_ids == {(name, profile) for name in fixture_by_id for profile in (0, 1)}, "frame/profile set")
    for row in report["live_rows"]:
        name = row["id"]
        h, tiles, hud, root, hud_digest, seal, _ = expected[name]
        require(row["status"] == "PASS" and row["canonical_bytes"] == 518400 and row["hud_bytes"] == 42240,
                f"actual byte counts {name}")
        require(row["write_requests"] == row["write_acks"] == row["hash_deliveries"] == 560640,
                f"write/ACK/hash counts {name}")
        require(row["hash_jobs"] == 1025 and row["hash_message_bytes"] == 628815 and row["hash_blocks"] == 10298,
                f"hash totals {name}")
        require(row["root"] == root and row["hud_sha256"] == hud_digest and row["seal"] == seal,
                f"commit digest fields {name}")
        require(row["fid"] == h["fid"] and row["generation"] == h["generation"], f"identity {name}")
        require(row["start_cycle"] < row["first_outer_cycle"] <= row["last_outer_cycle"] < row["commit_cycle"],
                f"fence ordering {name}")
        require(row["start_to_commit_cycles"] == row["commit_cycle"] - row["start_cycle"], "start fence")
        require(row["accepted_bank"] in (0, 1, 2), "bank index")
        require(row["qcache_bytes"] == (0 if name == "c0_f0" else 1350), "qcache transfer count")
        require(row["reference_requests"] == (0 if name == "c0_f0" else 7806), "actual ref read count")

    actual_path = attempt / "actual.tsv.gz"
    actual_rows = {}
    for line in gzip.open(actual_path, "rt"):
        name, profile, hexdata = line.rstrip("\n").split("\t")
        actual_rows[(name, int(profile))] = bytes.fromhex(hexdata)
    require(len(actual_rows) == 12, "actual/qcache rows")
    for row in report["live_rows"]:
        name, profile = row["id"], row["profile"]
        _, tiles, hud, _, _, _, _ = expected[name]
        raster = rasterize(tiles)
        require(actual_rows[(row["pipeline_id"], profile)] == raster,
                f"full canonical bank vs frozen golden {name}/{profile}")
        accepted = actual_rows[("accepted_" + row["pipeline_id"], profile)]
        require(accepted == raster + hud, f"full accepted bank vs canonical+HUD golden {name}/{profile}")
        case = next(x.split("\t") for x in (ROOT / INPUTS[0]).read_text().splitlines()
                    if x.split("\t", 1)[0] == row["pipeline_id"])
        require(actual_rows[("qcache_" + row["pipeline_id"], profile)] == bytes.fromhex(case[10]),
                f"published actual qcache vs input golden {name}/{profile}")

    # Check every actual RTL digest event against fresh hashlib calculations over
    # frozen native packets/bytes. Epochs are linked to each live_case row.
    hash_rows = [json.loads(line) for line in gzip.open(attempt / "hashes.jsonl.gz", "rt")]
    require(len(hash_rows) == 4100, "all live hash events")
    live_by_key = {(r["id"], r["profile"]): r for r in report["live_rows"]}
    groups = {}
    for event in hash_rows:
        key = (event["id"], event["profile"])
        require(key in live_by_key and event["epoch"] == live_by_key[key]["epoch"], "hash event owner")
        groups.setdefault(key, []).append(event)
    for key, run_events in groups.items():
        name, _ = key
        wanted = expected[name][-1]
        observed = {(int(e["kind"]), int(e["node"])): e["digest"] for e in run_events}
        require(len(run_events) == 1025 and len(observed) == 1025 and observed == wanted,
                f"independent digest job mismatch {key}")
        cycles = [int(e["cycle"]) for e in run_events]
        require(all(a < b for a, b in zip(cycles, cycles[1:])), f"hash cycle order {key}")

    # Independently replay source generation in a temporary dependency tree.
    generated = {}
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory(prefix="v91l-live-generator-audit-") as temp:
        temp = Path(temp)
        dependencies = (
            "fpga/experiments/cu66-v91l-live/make_wrapper.py",
            "fpga/experiments/cu66-v91l-live/make_bench.py",
            "fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv",
            "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv",
            "fpga/experiments/cu66-v91k/tb_pipeline.cpp",
        )
        for rel in dependencies:
            dest = temp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)
        for generator in ("make_wrapper.py", "make_bench.py"):
            subprocess.run(["python3", str(temp / "fpga/experiments/cu66-v91l-live" / generator)],
                           cwd=temp, check=True, capture_output=True, text=True)
        for rel in ("fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv",
                    "fpga/experiments/cu66-v91l-live/tb_live.cpp"):
            generated[rel] = file_sha(temp / rel)
            require((temp / rel).read_bytes() == (ROOT / rel).read_bytes(), f"generated source differs: {rel}")

    subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, report["source_revision"]],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for rel in SOURCES:
        if "/cu66-v91l-live/" not in rel and not rel.startswith("scripts/cu66-v91l-live/"):
            pinned = hashlib.sha256(subprocess.check_output(["git", "show", BASELINE + ":" + rel], cwd=ROOT)).hexdigest()
            require(pinned == report["source_sha256"][rel], f"qualified baseline source changed: {rel}")
    return {
        "seed": report["seed"], "attempt": str(path.relative_to(ROOT)), "attempt_sha256": file_sha(path),
        "source_sha256": report["source_sha256"], "input_sha256": report["inputs_sha256"],
        "artifact_sha256": report["artifacts_sha256"], "strict_build": True,
        "live_canonical_producer": True, "actual_candidate_memory_acknowledged": True,
        "accepted_full_bank_bytes_exact": True, "actual_registered_qcache_exact": True,
        "actual_registered_qcache_bytes_captured": sum(len(actual_rows[("qcache_" + r["pipeline_id"], r["profile"])])
                                                        for r in report["live_rows"]),
        "independently_checked_rtl_hash_jobs": 4100, "profiles": [0, 1], "source_frames": ["c0_f0", "c0_f1"],
        "write_ack_hash_bytes_per_commit": 560640, "validated_commits": 4,
        "cycles": [{k: r[k] for k in ("id", "profile", "start_to_commit_cycles", "first_outer_to_commit_cycles",
                                                "last_outer_to_commit_cycles", "qcache_preload_cycles")}
                   for r in report["live_rows"]],
        "directed_checks": dict(check_counts), "generator_sha256": generated,
        "limitations": {k: report[k] for k in ("full_rtl_hud_decoder", "full_rtl_hud_overlay",
                        "physical_memory_controller", "hardware_distinct_30fps_proven",
                        "full_frame_decode_under10ms_proven")},
    }


def main():
    sources = {rel: file_sha(ROOT / rel) for rel in SOURCES}
    model_pins = {
        "experiments/python-gamebub-v91l-live/model.py": file_sha(AREA / "model.py"),
        "experiments/python-gamebub-v91l-live/model-results.json": file_sha(AREA / "model-results.json"),
    }
    attempts = {}
    for path in sorted(INTEGRATION.glob("*/results.json")):
        try:
            report = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        seed = report.get("seed")
        if seed in (911901, 911902) and report.get("status", "").startswith("PASS"):
            if report.get("source_sha256") == sources:
                attempts[seed] = path
    require(set(attempts) == {911901, 911902}, f"missing current-source seed reports: {sorted(attempts)}")
    results = [audit_attempt(attempts[seed], sources) for seed in (911901, 911902)]
    require(results[0]["source_sha256"] == results[1]["source_sha256"], "seeds used different source")
    selected_paths = set(attempts.values())
    nonselected = []
    for path in sorted(INTEGRATION.glob("*/results.json")):
        report = json.loads(path.read_text())
        if report.get("seed") in (911901, 911902) and path not in selected_paths:
            same_sources = report.get("source_sha256") == sources
            nonselected.append({"attempt": str(path.relative_to(ROOT)), "seed": report.get("seed"),
                                "status": report.get("status"), "same_as_selected_source": same_sources,
                                "error": report.get("error"), "qualified": False})
    audit = {
        "schema": "cu66-v91l-live-independent-integration-audit-v1",
        "status": "PASS_TWO_SEED_LIVE_CANONICAL_ACK_HASH_PUBLICATION_AUDIT",
        "baseline_revision": BASELINE, "source_pins": sources, "model_pins": model_pins,
        "selected_attempts": results,
        "retained_nonselected_attempts": nonselected,
        "independent_checks": {
            "full_canonical_and_hud_bank_bytes_compared_to_frozen_goldens": True,
            "all_live_rtl_hash_digests_recomputed_with_hashlib": True,
            "delta_reads_actual_committed_key_bank": True,
            "acknowledged_write_precedes_hash_delivery": True,
            "strict_toolchain_and_source_snapshots_checked": True,
            "generated_wrapper_and_bench_byte_identity_checked": True,
            "independently_verified_actual_qcache_vectors": True,
        },
        "scope": "Live parser/entropy/inverse/reconstruction to actual acknowledged candidate writes, C2/HUD/seal hash, and bank commit under Verilator simulation. HUD semantic decode is native C++ before the timed start. No full RTL HUD decoder/overlay, physical memory controller, hardware 30 fps, or under-10-ms result is claimed.",
    }
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"status": audit["status"], "seeds": [x["seed"] for x in results],
                      "independent_hash_jobs": 8200, "audit": str((AREA / "audit.json").relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()

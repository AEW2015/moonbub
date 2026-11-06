#!/usr/bin/env python3
"""Independent audit for the V91k two-row chroma-cache experiment.

This verifier deliberately does not import either V91k Python model. It rebuilds
the RGB565 golden from the frozen canonical bytes, then independently walks the
external byte-read schedule and checks RTL receipts against those results.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from functools import lru_cache
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
FROZEN = ROOT / "fpga/experiments/cu66-v91k/pipeline-attempts/20261106T214341304797Z-cb9ea57e"
FROZEN_REPORT = FROZEN / "results.json"
INPUT_CANONICAL = FROZEN / "canonical_actual.tsv.gz"
INPUT_RGB = FROZEN / "vectors/rgb_goldens.tsv.gz"
EDGE_CANONICAL = AREA / "vectors/edge_actual.tsv.gz"
EDGE_RGB = AREA / "vectors/edge_rgb_goldens.tsv.gz"
WIDTH, HEIGHT, CW, CH = 720, 480, 360, 240
Y_BYTES, C_BYTES = WIDTH * HEIGHT, CW * CH
FRAME_BYTES, PIXELS = Y_BYTES + 2 * C_BYTES, WIDTH * HEIGHT
FNV_OFFSET, FNV_PRIME = 1469598103934665603, 1099511628211
MASK64 = (1 << 64) - 1
SEEDS = (911601, 911602)
EXPECTED_IDS = ("actual_001", "actual_006", "actual_043", "actual_031",
                "actual_006_varied_qcache", "structural_all_copy_zero_residual")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tsv_gz(path: Path, ncols: int) -> tuple[dict[tuple[str, ...], tuple[str, ...]], bytes]:
    compressed = path.read_bytes()
    raw = gzip.decompress(compressed)
    rows: dict[tuple[str, ...], tuple[str, ...]] = {}
    for line in raw.decode("ascii").splitlines():
        fields = tuple(line.split("\t"))
        assert len(fields) == ncols, (path, len(fields), ncols)
        key = fields[:-1]
        assert key not in rows, (path, key)
        rows[key] = fields[1:]
    return rows, raw


def read_frozen_inputs() -> tuple[dict[tuple[str, str], bytes], dict[str, bytes], dict]:
    report = json.loads(FROZEN_REPORT.read_text(encoding="utf-8"))
    assert report["schema"] == "cu66-v91k-canonical-and-rgb-rtl-v1"
    assert report["status"] == "PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY"
    canonical_sha = "03fab04d4273388cb1477c6db11c19486d7f0ad1ebc2e39b18fe6cc3508c0192"
    rgb_sha = "abe85556017a634b43711306763af93d39cbf3207b9547842edd0064c3e6547b"
    assert sha(INPUT_CANONICAL.read_bytes()) == canonical_sha
    assert sha(INPUT_RGB.read_bytes()) == rgb_sha
    canonical: dict[tuple[str, str], bytes] = {}
    raw = gzip.decompress(INPUT_CANONICAL.read_bytes())
    for line in raw.decode("ascii").splitlines():
        ident, profile, data_hex = line.split("\t")
        data = bytes.fromhex(data_hex)
        assert len(data) == FRAME_BYTES
        canonical[(ident, profile)] = data
    goldens: dict[str, bytes] = {}
    raw = gzip.decompress(INPUT_RGB.read_bytes())
    for line in raw.decode("ascii").splitlines():
        ident, data_hex = line.split("\t")
        data = bytes.fromhex(data_hex)
        assert len(data) == PIXELS * 2
        goldens[ident] = data
    assert len(canonical) == 12 and len(goldens) == 6
    assert {ident for ident, _ in canonical} == set(EXPECTED_IDS)
    assert set(goldens) == set(EXPECTED_IDS)
    return canonical, goldens, report


@lru_cache(maxsize=32)
def convert_rgb565(frame: bytes) -> bytes:
    """Recompute each output pixel from the canonical Y/Cb/Cr planes."""
    assert len(frame) == FRAME_BYTES
    yplane, cbplane, crplane = frame[:Y_BYTES], frame[Y_BYTES:Y_BYTES+C_BYTES], frame[Y_BYTES+C_BYTES:]
    result = bytearray(PIXELS * 2)
    for y in range(HEIGHT):
        cy, cy1 = y // 2, min(y // 2 + 1, CH - 1)
        for x in range(WIDTH):
            cx, cx1 = x // 2, min(x // 2 + 1, CW - 1)

            def sample(plane: bytes) -> int:
                t = plane[cy * CW + cx]
                if x & 1:
                    t = (t + plane[cy * CW + cx1] + 1) // 2
                if y & 1:
                    b = plane[cy1 * CW + cx]
                    if x & 1:
                        b = (b + plane[cy1 * CW + cx1] + 1) // 2
                    t = (t + b + 1) // 2
                return t - 128

            cb, cr = sample(cbplane), sample(crplane)
            lum = yplane[y * WIDTH + x]
            r = max(0, min(255, lum + (359 * cr + 128) // 256))
            g = max(0, min(255, lum - (88 * cb + 183 * cr + 128) // 256))
            b = max(0, min(255, lum + (454 * cb + 128) // 256))
            struct.pack_into("<H", result, (y * WIDTH + x) * 2,
                             ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))
    return bytes(result)


@lru_cache(maxsize=1)
def edge_pattern() -> bytes:
    """Recreate the separate deterministic seam fixture from its published formula."""
    yplane = bytes((37 * x + 19 * y + (x * y) % 251) % 256
                   for y in range(HEIGHT) for x in range(WIDTH))
    cbplane = bytes((11 * x + 29 * y + 17) % 256
                    for y in range(CH) for x in range(CW))
    crplane = bytes((23 * x + 7 * y + 91) % 256
                    for y in range(CH) for x in range(CW))
    return yplane + cbplane + crplane


def edge_diagnostics(frame: bytes) -> dict:
    cb = frame[Y_BYTES:Y_BYTES + C_BYTES]
    cr = frame[Y_BYTES + C_BYTES:]
    row_changes = sum(cb[238 * CW + x] != cb[239 * CW + x] for x in range(CW))
    row_changes += sum(cr[238 * CW + x] != cr[239 * CW + x] for x in range(CW))
    col_changes = sum(cb[y * CW + 358] != cb[y * CW + 359] for y in range(CH))
    col_changes += sum(cr[y * CW + 358] != cr[y * CW + 359] for y in range(CH))
    assert row_changes > 0 and col_changes > 0
    return {"different_last_two_chroma_rows": True,
            "different_last_two_chroma_columns": True,
            "differing_row_neighbor_values": row_changes,
            "differing_column_neighbor_values": col_changes}


def load_edge_inputs() -> tuple[dict, dict]:
    frame = edge_pattern()
    rgb = convert_rgb565(frame)
    assert edge_diagnostics(frame)["different_last_two_chroma_rows"]
    assert edge_diagnostics(frame)["different_last_two_chroma_columns"]
    canonical_rows = gzip.decompress(EDGE_CANONICAL.read_bytes()).decode("ascii").splitlines()
    golden_rows = gzip.decompress(EDGE_RGB.read_bytes()).decode("ascii").splitlines()
    assert len(canonical_rows) == 2 and len(golden_rows) == 1
    got = {}
    for line in canonical_rows:
        ident, profile, data_hex = line.split("\t")
        assert ident == "cache_edge_pattern" and bytes.fromhex(data_hex) == frame
        got[(ident, profile)] = frame
    assert set(got) == {( "cache_edge_pattern", "0"), ("cache_edge_pattern", "1")}
    ident, rgb_hex = golden_rows[0].split("\t")
    assert ident == "cache_edge_pattern" and bytes.fromhex(rgb_hex) == rgb
    assert sha(EDGE_CANONICAL.read_bytes()) == "e16db4767d65954a73890ffbbce323bc42a9ab078a3f82aaee7c8f3bedf17376"
    assert sha(EDGE_RGB.read_bytes()) == "bc754a20e69b7e3b303dffacd292a09799ca8e1ed6db4459f0ffb10378b99424"
    return got, {"cache_edge_pattern": rgb}


def fnv_read(h: int, address: int, value: int) -> int:
    for byte in struct.pack("<I", address) + bytes((value,)):
        h = ((h ^ byte) * FNV_PRIME) & MASK64
    return h


def fnv_bytes(data: bytes) -> int:
    h = FNV_OFFSET
    for value in data:
        h = ((h ^ value) * FNV_PRIME) & MASK64
    return h


@lru_cache(maxsize=32)
def cache_schedule(frame: bytes) -> dict:
    """Derive accepted external read address/data order and parity-bank mapping."""
    h = FNV_OFFSET
    counts = {"Y": 0, "Cb": 0, "Cr": 0}
    seen = bytearray(FRAME_BYTES)
    row_fills = []

    def read(addr: int, plane: str) -> None:
        nonlocal h
        assert 0 <= addr < FRAME_BYTES and not seen[addr], ("duplicate/out-of-range read", addr)
        seen[addr] = 1
        counts[plane] += 1
        h = fnv_read(h, addr, frame[addr])

    # Each completed row fill reads Cb then Cr, with row 0 and row 1 primed.
    def fill(row: int) -> None:
        for plane, base in (("Cb", Y_BYTES), ("Cr", Y_BYTES + C_BYTES)):
            for col in range(CW):
                slot, bank, word = row & 1, col & 1, col >> 1
                assert (slot, bank, word) == (row % 2, col % 2, col // 2)
                read(base + row * CW + col, plane)
        row_fills.append(row)
    fill(0)
    fill(1)
    for y in range(HEIGHT):
        if y >= 2 and (y & 1) == 0 and y // 2 + 1 < CH:
            fill(y // 2 + 1)
        for x in range(WIDTH):
            read(y * WIDTH + x, "Y")
    assert all(seen), "expected schedule did not cover every canonical byte exactly once"
    assert counts == {"Y": 345600, "Cb": 86400, "Cr": 86400}
    assert len(row_fills) == CH
    return {"fnv1a64": f"{h:016x}", "reads": sum(counts.values()), "reads_by_plane": counts,
            "row_fills": len(row_fills), "row_sequence": row_fills,
            "final_valid_rows": [238, 239], "final_valid_slots": [0, 1]}


@lru_cache(maxsize=1)
def lookup_schedule() -> str:
    """Hash pixel identity, top/bottom row tags, and row-valid bits per lookup."""
    h = FNV_OFFSET
    for pixel in range(PIXELS):
        top = pixel // WIDTH // 2
        bottom = min(top + 1, CH - 1)
        for byte in struct.pack("<I", pixel) + bytes((top, bottom, 3)):
            h = ((h ^ byte) * FNV_PRIME) & MASK64
    return f"{h:016x}"


@lru_cache(maxsize=32)
def uncached_schedule(frame: bytes) -> dict:
    h, counts = FNV_OFFSET, {"Y": 0, "Cb": 0, "Cr": 0}
    for y in range(HEIGHT):
        cy, cy1 = y // 2, min(y // 2 + 1, CH - 1)
        for x in range(WIDTH):
            cx, cx1 = x // 2, min(x // 2 + 1, CW - 1)
            ya = y * WIDTH + x
            h = fnv_read(h, ya, frame[ya]); counts["Y"] += 1
            for name, base in (("Cb", Y_BYTES), ("Cr", Y_BYTES + C_BYTES)):
                for row in (cy, cy1):
                    for col in (cx, cx1):
                        addr = base + row * CW + col
                        h = fnv_read(h, addr, frame[addr]); counts[name] += 1
    assert counts == {"Y": 345600, "Cb": 1382400, "Cr": 1382400}
    return {"fnv1a64": f"{h:016x}", "reads": sum(counts.values()), "reads_by_plane": counts}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def frozen_old_receipts() -> dict[int, tuple[Path, dict]]:
    summary_path = ROOT / "experiments/python-gamebub-v91k/summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["schema"] == "cu66-v91k-canonical-rgb-qualified-v1" and summary["status"] == "PASS"
    out = {}
    for seed in SEEDS:
        item = next(row for row in summary["attempts"] if row["seed"] == seed - 100)
        path = ROOT / item["path"]
        assert sha(path.read_bytes()) == item["sha256"]
        out[seed] = (path, json.loads(path.read_text(encoding="utf-8")))
    return out


def check_case_rows(attempt: Path, label: str, seed: int, expected: dict,
                    canonical: dict[tuple[str, str], bytes], goldens: dict[str, bytes]) -> dict:
    edge = label.startswith("edge-")
    cached = label.endswith("cache")
    log_path = attempt / (f"{label}.jsonl" if edge else f"simulation-{label}.jsonl")
    rows = read_jsonl(log_path)
    cases = [row for row in rows if row.get("type") == "case"]
    verdicts = [row for row in rows if row.get("type") == "verdict"]
    expected_cases = 2 if edge else 12
    expected_pixels = 691_200 if edge else 4_147_200
    assert len(cases) == expected_cases and len(verdicts) == 1, (label, len(cases), len(verdicts))
    verdict = verdicts[0]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == seed
    assert verdict["cases"] == expected_cases and verdict["pixels"] == expected_pixels
    want_reads = 3_110_400 if not cached else 518_400
    assert verdict["reads_per_frame"] == want_reads
    if cached:
        assert verdict["row_fills_per_frame"] == 240 and verdict["logical_cache_bytes"] == 1440
        required = {"abort_cb_fill_pending_drain", "warm_reset_cb_fill_pending_drain",
                    "abort_cr_fill_pending_drain", "warm_reset_cr_fill_pending_drain",
                    "abort_luma_pending_drain", "warm_reset_luma_pending_drain",
                    "abort_late_cb_fill_eviction", "warm_reset_late_cb_fill_eviction",
                    "abort_late_cr_fill_eviction", "warm_reset_late_cr_fill_eviction",
                    "abort_local_6", "warm_reset_local_6", "abort_local_7", "warm_reset_local_7",
                    "abort_held_pixel", "warm_reset_held_pixel", "wrong_epoch_cb_fill",
                    "wrong_epoch_cr_fill", "wrong_epoch_luma", "bus_error_cb_fill",
                    "bus_error_cr_fill", "bus_error_luma", "abort_last_fill_ack_same_edge",
                    "warm_reset_last_fill_ack_same_edge", "zero_epoch_rejected",
                    "start_epoch_snapshot_immutable",
                    "complete_rows_only_and_parity_ownership",
                    "registered_lookup_odd_even_edges_and_bottom_alias",
                    "clean_retry_after_cancel_and_fault"}
        assert required <= set(verdict["directed_check_names"])
        assert verdict["directed_checks"] == 29 and len(verdict["directed_check_names"]) == 29
    else:
        assert verdict["directed_checks"] == 8
    found = set()
    for row in cases:
        ident, profile = row["id"], str(row["memory_profile"])
        key = (ident, profile)
        assert key in canonical and key not in found
        found.add(key)
        item = expected[key]
        assert row["status"] == "PASS" and row["seed"] == seed
        assert row["pixels"] == 345_600
        assert row["reads"] == row["responses"] == want_reads
        assert int(row["canonical_input_hash"]) == item["canonical_fnv64"]
        assert int(row["rgb565_hash"]) == item["rgb565_fnv64"]
        assert int(row["read_schedule_hash"]) == int(item["cache" if cached else "control"]["fnv1a64"], 16)
        assert row["publication"] is False
        assert row["cycles"] > 0 and row["first_read"] > 0
        assert row["last_response"] >= row["first_read"]
        assert row["first_output"] >= row["first_read"] and row["last_output"] >= row["first_output"]
        assert row["request_stalls"] >= 0 and row["output_stalls"] >= 0
        if profile == "1":
            assert row["request_stalls"] > 0 and row["output_stalls"] > 0
        if cached:
            assert row["luma_reads"] == 345_600 and row["chroma_reads"] == 172_800
            assert row["row_fills"] == 240
            assert row["lookups"] == row["lookup_responses"] == row["cache_hits"] == 345_600
            assert int(row["lookup_hash"]) == int(item["lookup_fnv64"], 16)
            assert row["final_row_valid"] == 3 and row["final_row_tags"] == [238, 239]
        else:
            assert "lookup_hash" not in row and "row_fills" not in row
    assert found == set(canonical)
    return {"verdict": verdict, "cases": cases}


def audit_attempt(report_path: Path, canonical: dict, goldens: dict, expected: dict,
                  old_reports: dict) -> dict:
    report_path = report_path.resolve()
    attempt = report_path.parent
    report = json.loads(report_path.read_text(encoding="utf-8"))
    seed = int(report["seed"])
    assert seed in SEEDS
    assert report["schema"] == "cu66-v91k-chroma-cache-comparison-v1"
    assert report["status"] == "PASS_EXACT_REGISTERED_CHROMA_CACHE_COMPARISON"
    assert report["full_frame_publication_timestamp"] is None
    assert report["hardware_distinct_30fps_proven"] is False
    assert report["full_frame_decode_under10ms_proven"] is False
    assert report["mapped_cache_fit_proven"] is False and report["monolithic_full_frame_rtl_proven"] is False
    assert "Scheduling changes RNG consumption" in report["service_rule"]
    assert "FAST isolates deterministic schedule" in report["service_rule"]

    old_path, old_report = old_reports[seed]
    old_summary = ROOT / "experiments/python-gamebub-v91k/summary.json"
    old_audit = old_summary.with_name("audit.json")
    assert report["source_canonical_receipt"]["source_report"] == str(old_path.relative_to(ROOT))
    assert report["source_canonical_receipt"]["source_report_sha256"] == sha(old_path.read_bytes())
    assert report["source_canonical_receipt"]["source_seed"] == seed - 100
    assert report["source_canonical_receipt"]["rows"] == 12
    source_canonical = ROOT / report["source_canonical_receipt"]["path"]
    assert source_canonical == old_path.parent / old_report["canonical_actual"]["path"]
    assert sha(source_canonical.read_bytes()) == report["source_canonical_receipt"]["sha256"]
    assert report["source_canonical_receipt"]["gzip_sha256"] if "gzip_sha256" in report["source_canonical_receipt"] else True

    for table_name in ("source_sha256", "inputs_sha256"):
        for rel, digest in report[table_name].items():
            live, snapshot = ROOT / rel, attempt / ("sources" if table_name == "source_sha256" else "inputs") / rel
            if table_name == "source_sha256":
                assert live.is_file() and sha(live.read_bytes()) == digest, (rel, "live source changed")
                assert snapshot.is_file() and sha(snapshot.read_bytes()) == digest, (rel, "source snapshot mismatch")
            else:
                # Runner copies selected inputs to descriptive filenames; bind each declared
                # source digest to its current source and to the corresponding retained copy.
                assert live.is_file() and sha(live.read_bytes()) == digest, (rel, "live input changed")
        assert table_name in report

    assert report["inputs_sha256"][str(old_summary.relative_to(ROOT))] == sha(old_summary.read_bytes())
    assert report["inputs_sha256"][str(old_audit.relative_to(ROOT))] == sha(old_audit.read_bytes())
    assert report["inputs_sha256"][str(old_path.relative_to(ROOT))] == sha(old_path.read_bytes())
    assert report["inputs_sha256"][str(source_canonical.relative_to(ROOT))] == sha(source_canonical.read_bytes())
    assert report["inputs_sha256"]["experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz"] == sha(INPUT_RGB.read_bytes())

    copied = {
        "canonical_actual.tsv.gz": source_canonical,
        "rgb_goldens.tsv.gz": INPUT_RGB,
        "v91k-source-report.json": old_path,
        "v91k-summary.json": old_summary,
        "v91k-audit.json": old_audit,
        "model-results.json": AREA / "model-results.json",
        "edge_actual.tsv.gz": EDGE_CANONICAL,
        "edge_rgb_goldens.tsv.gz": EDGE_RGB,
    }
    for name, source in copied.items():
        target = attempt / "inputs" / name
        assert target.is_file() and target.read_bytes() == source.read_bytes(), (name, "retained input mismatch")
    expansions = {Path(row["path"]).name: row for row in report["input_expansions"]}
    assert set(expansions) == {"canonical_actual.tsv", "rgb_goldens.tsv", "edge_actual.tsv", "edge_rgb_goldens.tsv"}
    for name, row in expansions.items():
        compressed = attempt / row["compressed_path"]
        raw = gzip.decompress(compressed.read_bytes())
        assert sha(compressed.read_bytes()) == row["compressed_sha256"]
        assert sha(raw) == row["raw_sha256"]
        assert len(raw.splitlines()) == row["rows"]
        expected_raw = {
            "canonical_actual.tsv": gzip.decompress(INPUT_CANONICAL.read_bytes()),
            "rgb_goldens.tsv": gzip.decompress(INPUT_RGB.read_bytes()),
            "edge_actual.tsv": gzip.decompress(EDGE_CANONICAL.read_bytes()),
            "edge_rgb_goldens.tsv": gzip.decompress(EDGE_RGB.read_bytes()),
        }[name]
        assert raw == expected_raw
    assert expansions["canonical_actual.tsv"]["rows"] == 12
    assert expansions["rgb_goldens.tsv"]["rows"] == 6
    assert expansions["edge_actual.tsv"]["rows"] == 2
    assert expansions["edge_rgb_goldens.tsv"]["rows"] == 1

    # Every artifact named by the runner, including compile logs, simulation logs,
    # source/input snapshots, and compressed row provenance, must match its digest.
    for rel, digest in report["artifacts_sha256"].items():
        artifact = attempt / rel
        assert artifact.is_file() and sha(artifact.read_bytes()) == digest, (rel, "artifact hash")
    for command in report["commands"]:
        assert command["exit_code"] == 0
        if "--build" in command["argv"]:
            argv = command["argv"]
            assert "--assert" in argv and "-Wall" in argv
            assert "-Wextra -Werror" in " ".join(argv)
            assert "-j" in argv and argv[argv.index("-j") + 1] == "2"
    builds = [c for c in report["commands"] if "--build" in c["argv"]]
    assert len(builds) == 2

    control = check_case_rows(attempt, "control", seed, expected, canonical, goldens)
    cache = check_case_rows(attempt, "cache", seed, expected, canonical, goldens)
    edge_canonical, edge_goldens = load_edge_inputs()
    edge_expected = {}
    edge_frame = edge_pattern()
    edge_rgb = convert_rgb565(edge_frame)
    for edge_key in edge_canonical:
        edge_expected[edge_key] = {
            "canonical_sha256": sha(edge_frame), "canonical_fnv64": fnv_bytes(edge_frame),
            "rgb565_sha256": sha(edge_rgb), "rgb565_fnv64": fnv_bytes(edge_rgb),
            "cache": cache_schedule(edge_frame), "control": uncached_schedule(edge_frame),
            "lookup_fnv64": lookup_schedule(),
        }
    assert edge_goldens["cache_edge_pattern"] == edge_rgb
    edge_control = check_case_rows(attempt, "edge-control", seed, edge_expected, edge_canonical, edge_goldens)
    edge_cache = check_case_rows(attempt, "edge-cache", seed, edge_expected, edge_canonical, edge_goldens)
    for label, pair_count, pixel_count, read_count in (
        ("control", 12, 4_147_200, 3_110_400),
        ("cache", 12, 4_147_200, 518_400),
    ):
        verdict = report["verdicts"][label]
        assert verdict["status"] == "TEST_PASS" and verdict["seed"] == seed
        assert (verdict["cases"], verdict["pixels"], verdict["reads_per_frame"]) == (pair_count, pixel_count, read_count)
    for label, pair_count, pixel_count, read_count in (
        ("control", 2, 691_200, 3_110_400),
        ("cache", 2, 691_200, 518_400),
    ):
        verdict = report["edge_verdicts"][label]
        assert verdict["status"] == "TEST_PASS" and verdict["seed"] == seed
        assert (verdict["cases"], verdict["pixels"], verdict["reads_per_frame"]) == (pair_count, pixel_count, read_count)
    row_receipt = report["row_trace"]
    trace_path = attempt / row_receipt["path"]
    packed = trace_path.read_bytes()
    trace_raw = gzip.decompress(packed)
    assert sha(packed) == row_receipt["gzip_sha256"] and sha(trace_raw) == row_receipt["raw_sha256"]
    events = [json.loads(line) for line in trace_raw.decode("utf-8").splitlines()]
    assert len(events) == row_receipt["rows"] == 12 * 240
    per_frame: dict[tuple[str, int], list[dict]] = {}
    for event in events:
        assert event["type"] == "row_fill"
        key = (event["id"], int(event["memory_profile"]))
        per_frame.setdefault(key, []).append(event)
    assert set(per_frame) == {(ident, profile) for ident, profile_s in canonical
                              for profile in (int(profile_s),)}
    row_events = 0
    for key, frame_events in per_frame.items():
        assert len(frame_events) == 240
        assert [int(row["row"]) for row in frame_events] == list(range(240))
        assert [int(row["slot"]) for row in frame_events] == [r & 1 for r in range(240)]
        assert all(int(row["cb_acks"]) == 360 and int(row["cr_acks"]) == 360 for row in frame_events)
        assert all(int(row["epoch"]) > 0 and int(row["cycle"]) > 0 for row in frame_events)
        case_epoch = next(row["epoch"] for row in cache["cases"]
                          if (row["id"], int(row["memory_profile"])) == key)
        assert all(int(row["epoch"]) == int(case_epoch) for row in frame_events)
        assert all(int(a["cycle"]) < int(b["cycle"]) for a, b in zip(frame_events, frame_events[1:]))
        row_events += len(frame_events)

    edge_row_receipt = report["edge_row_trace"]
    edge_trace_path = attempt / edge_row_receipt["path"]
    edge_packed = edge_trace_path.read_bytes()
    edge_trace_raw = gzip.decompress(edge_packed)
    assert sha(edge_packed) == edge_row_receipt["gzip_sha256"]
    assert sha(edge_trace_raw) == edge_row_receipt["raw_sha256"]
    edge_events = [json.loads(line) for line in edge_trace_raw.decode("utf-8").splitlines()]
    assert len(edge_events) == edge_row_receipt["rows"] == 2 * 240
    edge_per_frame: dict[tuple[str, int], list[dict]] = {}
    for event in edge_events:
        assert event["type"] == "row_fill" and event["id"] == "cache_edge_pattern"
        edge_per_frame.setdefault((event["id"], int(event["memory_profile"])), []).append(event)
    assert set(edge_per_frame) == {("cache_edge_pattern", 0), ("cache_edge_pattern", 1)}
    for key, frame_events in edge_per_frame.items():
        assert len(frame_events) == 240
        assert [int(row["row"]) for row in frame_events] == list(range(240))
        assert [int(row["slot"]) for row in frame_events] == [r & 1 for r in range(240)]
        assert all(int(row["cb_acks"]) == 360 and int(row["cr_acks"]) == 360 for row in frame_events)
        assert all(int(row["epoch"]) > 0 and int(row["cycle"]) > 0 for row in frame_events)
        case_epoch = next(row["epoch"] for row in edge_cache["cases"]
                          if (row["id"], int(row["memory_profile"])) == key)
        assert all(int(row["epoch"]) == int(case_epoch) for row in frame_events)
        assert all(int(a["cycle"]) < int(b["cycle"]) for a, b in zip(frame_events, frame_events[1:]))

    # Compare measured case fences under the common declared finite service rules.
    # Different address schedules consume different numbers of RNG draws, so no
    # identical absolute stall trace is asserted.
    control_cases = {(r["id"], int(r["memory_profile"])): r for r in control["cases"]}
    cache_cases = {(r["id"], int(r["memory_profile"])): r for r in cache["cases"]}
    comparisons = []
    for key in sorted(control_cases):
        a, b = control_cases[key], cache_cases[key]
        assert a["cycles"] > 0 and b["cycles"] > 0
        comparisons.append({"id": key[0], "memory_profile": key[1],
                            "control_cycles": a["cycles"], "cache_cycles": b["cycles"],
                            "cycle_delta_cache_minus_control": b["cycles"] - a["cycles"],
                            "first_output_from_first_read_cycles": {
                                "control": a["first_output"] - a["first_read"],
                                "cache": b["first_output"] - b["first_read"]},
                            "control_stalls": {"request": a["request_stalls"], "output": a["output_stalls"]},
                            "cache_stalls": {"request": b["request_stalls"], "output": b["output_stalls"]}})
    return {
        "seed": seed,
        "attempt": str(report_path.relative_to(ROOT)),
        "results_sha256": sha(report_path.read_bytes()),
        "status": report["status"],
        "source_sha256": report["source_sha256"],
        "inputs_sha256": report["inputs_sha256"],
        "source_canonical_receipt": report["source_canonical_receipt"],
        "artifact_count": len(report["artifacts_sha256"]),
        "command_count": len(report["commands"]),
        "control_verdict": control["verdict"], "cache_verdict": cache["verdict"],
        "row_trace": {"rows": row_events, "raw_sha256": sha(trace_raw), "gzip_sha256": sha(packed)},
        "edge_control_verdict": edge_control["verdict"], "edge_cache_verdict": edge_cache["verdict"],
        "edge_row_trace": {"rows": len(edge_events), "raw_sha256": sha(edge_trace_raw), "gzip_sha256": sha(edge_packed)},
        "frame_comparisons": comparisons,
        "cache_read_reduction": {"control_per_frame": 3_110_400, "cache_per_frame": 518_400,
                                 "factor": 6},
        "directed_checks": cache["verdict"]["directed_check_names"],
        "service_rule": report["service_rule"],
        "failed_attempts_retained": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", action="append", type=Path,
                        help="attempt results.json; repeat for each seed (auto-discovery if omitted)")
    args = parser.parse_args()
    canonical, goldens, _frozen_report = read_frozen_inputs()
    expected = {}
    for (ident, profile), frame in canonical.items():
        rgb = convert_rgb565(frame)
        assert rgb == goldens[ident], (ident, profile, "independently recomputed RGB565 golden mismatch")
        expected[(ident, profile)] = {
            "canonical_sha256": sha(frame), "canonical_fnv64": fnv_bytes(frame),
            "rgb565_sha256": sha(rgb), "rgb565_fnv64": fnv_bytes(rgb),
            "cache": cache_schedule(frame), "control": uncached_schedule(frame),
            "lookup_fnv64": lookup_schedule(),
        }
    old_reports = frozen_old_receipts()
    paths = args.attempt or sorted((ROOT / "fpga/experiments/cu66-v91k-cache/comparison-attempts").glob("*/results.json"))
    passing: dict[int, list[Path]] = {seed: [] for seed in SEEDS}
    failure_reports = []
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("status") == "PASS_EXACT_REGISTERED_CHROMA_CACHE_COMPARISON":
            seed = int(report.get("seed", -1))
            if seed not in passing:
                continue
            current_sources = all((ROOT / rel).is_file() and sha((ROOT / rel).read_bytes()) == digest
                                  for rel, digest in report.get("source_sha256", {}).items())
            if current_sources:
                passing[seed].append(path)
        else:
            failure_reports.append(path)
    selected = {}
    for seed in SEEDS:
        assert passing[seed], f"no current-source passing comparison for seed {seed}"
        selected[seed] = sorted(passing[seed], key=lambda p: p.stat().st_mtime_ns)[-1]
    # Audit only the newest source-matching result for each seed. Earlier passing
    # runs remain preserved with their original status and are listed as superseded.
    audited = [audit_attempt(selected[seed], canonical, goldens, expected, old_reports) for seed in SEEDS]

    # Pin every failed attempt directory and preserve its status/error as audit evidence.
    failed_attempts = []
    for path in failure_reports:
        report = json.loads(path.read_text(encoding="utf-8"))
        attempt = path.parent
        files = sorted(p for p in attempt.rglob("*") if p.is_file())
        failed_attempts.append({"results": str(path.relative_to(ROOT)),
                                "results_sha256": sha(path.read_bytes()),
                                "status": report.get("status"), "error_class": report.get("error_class"),
                                "error": report.get("error"),
                                "retained_file_sha256": {str(p.relative_to(attempt)): sha(p.read_bytes()) for p in files}})
    superseded_attempts = []
    selected_paths = set(selected.values())
    for path in paths:
        if path in selected_paths:
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("status") != "PASS_EXACT_REGISTERED_CHROMA_CACHE_COMPARISON":
            continue
        current_sources = all((ROOT / rel).is_file() and sha((ROOT / rel).read_bytes()) == digest
                              for rel, digest in report.get("source_sha256", {}).items())
        superseded_attempts.append({
            "results": str(path.relative_to(ROOT)), "results_sha256": sha(path.read_bytes()),
            "original_status": report["status"], "seed": report.get("seed"),
            "source_sha256": report.get("source_sha256"),
            "artifacts_sha256": report.get("artifacts_sha256"),
            "superseded_reason": "newer_current_source_passing_run" if current_sources else "source_pins_no_longer_current",
        })
    final = {
        "schema": "cu66-v91k-chroma-cache-independent-audit-v1",
        "status": "PASS_CURRENT_SOURCE_BOTH_SEEDS_EXACT_CACHE_AND_CONTROL",
        "baseline_revision": "a0a60502edc348c3e6340722671bf6477a2f01c0",
        "frozen_input_receipts": {
            "source_summary_sha256": sha((ROOT / "experiments/python-gamebub-v91k/summary.json").read_bytes()),
            "source_audit_sha256": sha((ROOT / "experiments/python-gamebub-v91k/audit.json").read_bytes()),
            "canonical_gzip_sha256": sha(INPUT_CANONICAL.read_bytes()),
            "rgb_goldens_gzip_sha256": sha(INPUT_RGB.read_bytes()),
            "edge_canonical_gzip_sha256": sha(EDGE_CANONICAL.read_bytes()),
            "edge_rgb_goldens_gzip_sha256": sha(EDGE_RGB.read_bytes()),
            "model_results_sha256": sha((AREA / "model-results.json").read_bytes()),
            "canonical_input_rows": len(canonical), "rgb_golden_rows": len(goldens),
            "canonical_row_sha256": {f"{ident}/{profile}": sha(frame) for (ident, profile), frame in canonical.items()},
            "rgb565_golden_sha256": {ident: sha(rgb) for ident, rgb in goldens.items()},
        },
        "independent_expectations": {f"{ident}/{profile}": value for (ident, profile), value in expected.items()},
        "runs": audited,
        "failed_attempts": failed_attempts,
        "superseded_passing_attempts": superseded_attempts,
        "comparison_scope": "Actual canonical candidate memory to base RGB565 output. Exact pixel parity, accepted byte address/data schedules, row ownership, registered local lookup, finite service cycles and preserved failure evidence. No full publication, hardware frequency, routed memory fit, physical 30fps or under-10ms proof.",
        "cycle_comparison_caveat": "Cycle counts compare actual runs under the declared common finite service rules. The two schedules consume RNG differently, so identical absolute stall traces are not claimed.",
    }
    (AREA / "audit.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(final["status"], len(audited), "seeds", len(failed_attempts), "retained failed attempts")


if __name__ == "__main__":
    main()

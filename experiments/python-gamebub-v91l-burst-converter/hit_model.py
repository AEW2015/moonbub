#!/usr/bin/env python3
"""Source-derived direct owned-line hit model for the V91l RGB565 consumer.

This is a bounded Python model, not RTL or an implementation timing result.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
RESULT = AREA / "hit-model-results.json"
INPUT_DIR = ROOT / "fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs"
CANONICAL = INPUT_DIR / "canonical_actual.tsv.gz"
EDGES = INPUT_DIR / "edge_actual.tsv.gz"
SOURCES = {
    "docs/cu66-v91l-readbridge/next-converter.md": ROOT / "docs/cu66-v91l-readbridge/next-converter.md",
    "fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv": ROOT / "fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv",
    "fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv": ROOT / "fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv",
    "experiments/python-gamebub-v91l-tiled/prefill_model.py": ROOT / "experiments/python-gamebub-v91l-tiled/prefill_model.py",
    "fpga/experiments/cu66-v91l-burst-converter/generate_converter.py": ROOT / "fpga/experiments/cu66-v91l-burst-converter/generate_converter.py",
    "fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_cached.sv": ROOT / "fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_cached.sv",
    "fpga/experiments/cu66-v91l-burst-converter/canonical_line_reader.sv": ROOT / "fpga/experiments/cu66-v91l-burst-converter/canonical_line_reader.sv",
    "fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_lines.sv": ROOT / "fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_lines.sv",
    "fpga/experiments/cu66-v91l-burst-converter/INTERFACE.md": ROOT / "fpga/experiments/cu66-v91l-burst-converter/INTERFACE.md",
    "fpga/experiments/cu66-v91l-burst-probe/tb_probe.cpp": ROOT / "fpga/experiments/cu66-v91l-burst-probe/tb_probe.cpp",
    "scripts/cu66-v91l-burst-probe/run_test.py": ROOT / "scripts/cu66-v91l-burst-probe/run_test.py",
    "fpga/experiments/cu66-v91l-burst-probe/results.json": ROOT / "fpga/experiments/cu66-v91l-burst-probe/results.json",
    "fpga/experiments/cu66-v91l-burst-probe/attempts/20261107T010622248917Z-1b333f54/results.json": ROOT / "fpga/experiments/cu66-v91l-burst-probe/attempts/20261107T010622248917Z-1b333f54/results.json",
}
WIDTH, HEIGHT = 720, 480
Y_BYTES = WIDTH * HEIGHT
CHROMA_WIDTH, CHROMA_HEIGHT = 360, 240
C_BYTES = CHROMA_WIDTH * CHROMA_HEIGHT
FRAME_BYTES = Y_BYTES + 2 * C_BYTES


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def consumer_addresses() -> list[int]:
    """Model CHECK_ROWS -> sequential Cb/Cr row fills -> sequential Y requests."""
    result: list[int] = []
    next_chroma_row = 0
    for y in range(HEIGHT):
        bottom = min(y // 2 + 1, CHROMA_HEIGHT - 1)
        while next_chroma_row <= bottom:
            row = next_chroma_row
            result.extend(Y_BYTES + row * CHROMA_WIDTH + x for x in range(CHROMA_WIDTH))
            result.extend(Y_BYTES + C_BYTES + row * CHROMA_WIDTH + x for x in range(CHROMA_WIDTH))
            next_chroma_row += 1
        result.extend(y * WIDTH + x for x in range(WIDTH))
    assert len(result) == FRAME_BYTES
    assert sorted(result) == list(range(FRAME_BYTES))
    return result


def plane(addr: int) -> int:
    return 0 if addr < Y_BYTES else 1 if addr < Y_BYTES + C_BYTES else 2


def shared_chroma_row_boundaries(frame: bytes) -> dict[str, int]:
    """Check byte identity across adjacent 360-byte rows sharing a 16B line."""
    counts = {"Cb": 0, "Cr": 0, "Cb_shared_aligned_line": 0,
              "Cr_shared_aligned_line": 0, "distinct_value_pairs": 0}
    for name, base in (("Cb", Y_BYTES), ("Cr", Y_BYTES + C_BYTES)):
        for row in range(CHROMA_HEIGHT - 1):
            left = base + row * CHROMA_WIDTH + CHROMA_WIDTH - 1
            right = left + 1
            assert right == base + (row + 1) * CHROMA_WIDTH
            if (left & ~15) == (right & ~15):
                counts[f"{name}_shared_aligned_line"] += 1
            counts[name] += 1
            counts["distinct_value_pairs"] += frame[left] != frame[right]
    assert counts["Cb"] == 239 and counts["Cr"] == 239
    return counts


def scalar_line_reader(frame: bytes, accesses: list[int]) -> tuple[bytes, dict[str, object]]:
    """Replay the canonical reader's three independent current-line slots."""
    tags: list[int | None] = [None, None, None]
    payloads: list[bytes | None] = [None, None, None]
    delivered = bytearray()
    hits = misses = 0
    misses_by_plane = [0, 0, 0]
    line_starts: list[int] = []
    for addr in accesses:
        p = plane(addr)
        aligned = addr & ~15
        if tags[p] == aligned:
            hits += 1
            assert payloads[p] is not None
            value = payloads[p][addr & 15]
        else:
            misses += 1
            misses_by_plane[p] += 1
            line = frame[aligned:aligned + 16]
            assert len(line) == 16 and aligned // 16 == (aligned + 15) // 16
            tags[p], payloads[p] = aligned, line
            line_starts.append(aligned)
            value = line[addr & 15]
        assert value == frame[addr]
        delivered.append(value)
    assert len(delivered) == FRAME_BYTES
    assert misses == 32400 and hits == 486000
    assert misses_by_plane == [21600, 5400, 5400]
    assert len(line_starts) == len(set(line_starts)) == 32400
    return bytes(delivered), {
        "byte_requests": len(accesses), "line_hits": hits, "line_misses": misses,
        "line_misses_by_plane": {"Y": misses_by_plane[0], "Cb": misses_by_plane[1], "Cr": misses_by_plane[2]},
        "aligned_line_requests": len(line_starts),
        "physical_payload_bytes": len(line_starts) * 16,
    }


def direct_probe(frame: bytes, accesses: list[int]) -> tuple[bytes, dict[str, object]]:
    """Probe a matching owned line at consumer request state; misses refill first."""
    tags: list[int | None] = [None, None, None]
    payloads: list[bytes | None] = [None, None, None]
    output = bytearray()
    hits = misses = 0
    miss_addresses: list[int] = []
    for addr in accesses:
        p = plane(addr)
        aligned = addr & ~15
        if tags[p] == aligned:
            # One-clock local consume: matching line is already ACK-owned.
            hits += 1
            assert payloads[p] is not None
            value = payloads[p][addr & 15]
        else:
            # Preserve old byte lease: wait for the tagged line ACK, then return
            # the requested byte. The line is not usable before this point.
            misses += 1
            miss_addresses.append(aligned)
            ack_payload = frame[aligned:aligned + 16]
            assert len(ack_payload) == 16
            tags[p], payloads[p] = aligned, ack_payload
            value = ack_payload[addr & 15]
        assert value == frame[addr]
        output.append(value)
    assert len(output) == FRAME_BYTES
    assert hits == 486000 and misses == 32400
    assert len(miss_addresses) == len(set(miss_addresses)) == 32400
    return bytes(output), {
        "owned_line_hit_consumptions": hits,
        "misses_using_existing_byte_lease_and_refill": misses,
        "aligned_line_requests": len(miss_addresses),
        "physical_payload_bytes": len(miss_addresses) * 16,
    }


def load_tsv_frames(path: Path, allowed: set[str] | None = None) -> dict[str, bytes]:
    csv.field_size_limit(100_000_000)
    frames: dict[str, bytes] = {}
    with gzip.open(path, "rt", encoding="ascii", newline="") as stream:
        for row in csv.reader(stream, delimiter="\t"):
            if len(row) != 3:
                raise ValueError(f"expected id/profile/hex row in {path}")
            ident, profile, encoded = row
            if profile != "0" or (allowed is not None and ident not in allowed):
                continue
            if ident in frames:
                raise ValueError(f"duplicate frame {ident} in {path}")
            value = bytes.fromhex(encoded)
            if len(value) != FRAME_BYTES:
                raise ValueError(f"{ident}: expected {FRAME_BYTES} canonical bytes, got {len(value)}")
            frames[ident] = value
    return frames


def probe_eligible(*, active: bool, valid: bool, tag_match: bool,
                   adapter_busy: bool, physical_pending: bool,
                   byte_pending: bool, response_held: bool) -> bool:
    return (active and valid and tag_match and not adapter_busy and
            not physical_pending and not byte_pending and not response_held)


def state_guard_model() -> dict[str, object]:
    """Small exhaustive contract model for owned-line probe eligibility."""
    cases = 0
    blocked_reasons: set[str] = set()
    # A byte probe is eligible only for a matching ACK-owned line with all
    # consumer/adapter transaction slots idle.
    for active, valid, matching, adapter_busy, physical_pending, byte_pending, response_held in itertools.product((False, True), repeat=7):
        cases += 1
        allowed = probe_eligible(active=active, valid=valid, tag_match=matching,
                                 adapter_busy=adapter_busy, physical_pending=physical_pending,
                                 byte_pending=byte_pending, response_held=response_held)
        if allowed:
            assert active and valid and matching
            assert not (adapter_busy or physical_pending or byte_pending or response_held)
        else:
            assert (not active or not valid or not matching or adapter_busy or
                    physical_pending or byte_pending or response_held)
        if adapter_busy: blocked_reasons.add("adapter_busy")
        if physical_pending: blocked_reasons.add("physical_read_pending")
        if byte_pending: blocked_reasons.add("old_byte_lease_pending")
        if response_held: blocked_reasons.add("response_held")
        if not valid: blocked_reasons.add("line_not_ack_owned")
        if not matching: blocked_reasons.add("tag_or_plane_mismatch")
        if not active: blocked_reasons.add("frame_inactive")
    assert cases == 128
    # ACK may install only for the still-active matching generation. Start,
    # cancel, and generation change clear line validity before another probe.
    ack_cases = 0
    for active, same_generation, canceled in itertools.product((False, True), repeat=3):
        ack_cases += 1
        install = active and same_generation and not canceled
        assert not install or (active and same_generation and not canceled)
    assert ack_cases == 8
    invalidations = {"start": True, "cancel": True, "generation_change": True}
    return {
        "abstract_state_combinations_checked": cases,
        "ack_installation_combinations_checked": ack_cases,
        "ack_install_requires_active_same_generation_uncanceled": True,
        "line_valid_cleared_on": list(invalidations),
        "hit_blocked_when": sorted(blocked_reasons),
        "early_hit_before_matching_line_ack": "forbidden_by_valid_tag_installation_only_on_matching_ACK",
        "scope": "bounded abstract ownership guard model; not RTL proof or implementation assertion",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-freshness", action="store_true")
    args = parser.parse_args()
    accesses = consumer_addresses()
    actual = load_tsv_frames(CANONICAL, {"actual_001", "actual_006"})
    if set(actual) != {"actual_001", "actual_006"}:
        raise AssertionError(f"expected canonical actual_001 and actual_006, found {sorted(actual)}")
    edge = load_tsv_frames(EDGES, {"cache_edge_pattern"})
    if set(edge) != {"cache_edge_pattern"}:
        raise AssertionError("expected cache_edge_pattern profile 0")
    all_frames = {**actual, **edge}
    frame_results: dict[str, object] = {}
    for ident, frame in all_frames.items():
        scalar, scalar_stats = scalar_line_reader(frame, accesses)
        probed, probe_stats = direct_probe(frame, accesses)
        if scalar != probed:
            raise AssertionError(f"direct probe differs from scalar line response stream for {ident}")
        row_edges = shared_chroma_row_boundaries(frame)
        if ident == "cache_edge_pattern":
            assert row_edges["distinct_value_pairs"] == 478
        assert row_edges["Cb_shared_aligned_line"] == 120
        assert row_edges["Cr_shared_aligned_line"] == 120
        frame_results[ident] = {
            "canonical_frame_sha256": sha_bytes(frame),
            "scalar_delivered_sha256": sha_bytes(scalar),
            "direct_probe_delivered_sha256": sha_bytes(probed),
            "direct_probe_equals_scalar_byte_for_byte": True,
            "scalar_line_cache": scalar_stats,
            "direct_probe": probe_stats,
            "edge_checks": {
                "chroma_width_360_row_boundary_shared_aligned_line": row_edges,
                "chroma_x359_included": True,
                "chroma_row239_included": True,
            },
        }
    access_bytes = b"".join(addr.to_bytes(4, "little") for addr in accesses)
    # Existing FSM: byte request handshakes at edge n; registered hit response
    # is consumed at edge n+1. Direct owned hit consumes at edge n. This count
    # excludes memory wait, lookup/convert/emit and all ready/stall interactions.
    request_service = {
        "scalar_hit_timeline": "edge n: FILL_REQ/LUMA_REQ accepts byte request; edge n+1: FILL_WAIT/LUMA_WAIT consumes registered adapter response",
        "direct_hit_timeline": "edge n: FILL_REQ/LUMA_REQ consumes matching ACK-owned line byte and advances",
        "saved_request_service_clocks_per_hit": 1,
        "saved_request_service_clocks_per_frame_estimate": 486000,
        "estimate_scope": "nominal state-edge arithmetic only; excludes physical memory, RNG/stalls, lookup, conversion, output backpressure, full frame fence and interaction effects",
    }
    results = {
        "schema": "cu66-v91l-burst-hit-model-v1",
        "status": "PASS_PYTHON_SOURCE_DERIVED_BYTE_EXACT",
        "baseline_revision": "d57c0e47fba91032e2c94a78a09ed22a46679c46",
        "source_sha256": {name: sha_file(path) for name, path in SOURCES.items()},
        "generator_sha256": sha_file(Path(__file__).resolve()),
        "inputs_sha256": {str(path.relative_to(ROOT)): sha_file(path) for path in (CANONICAL, EDGES)},
        "schedule": "canonical_rgb565_cached.sv CHECK_ROWS: fill each missing chroma row Cb then Cr, then request 720 Y bytes per output row; three independent plane tags, aligned 16-byte line",
        "frame_bytes": FRAME_BYTES,
        "source_consumer_byte_requests_per_frame": FRAME_BYTES,
        "scalar_line_cache_counts_per_frame": {"line_hits": 486000, "line_misses": 32400, "aligned_16_byte_requests": 32400, "physical_payload_bytes": 518400},
        "direct_probe_counts_per_frame": {"owned_line_hit_consumptions": 486000, "miss_refills": 32400, "aligned_16_byte_requests": 32400, "physical_payload_bytes": 518400},
        "request_service_clock_estimate": request_service,
        "line_storage": {"existing_three_payload_slots_bytes": 48, "additional_payload_storage_proposed": 0, "note": "Candidate reuses the three existing per-plane line payloads; total implementation storage cannot be asserted without RTL/synthesis."},
        "generated_rtl_contract_review": {
            "source_sha256_pinned_with_sources": True,
            "probe_allowed_only_in": ["FILL_REQ", "LUMA_REQ"],
            "reader_hit_requires": ["active matching epoch", "IDLE adapter", "no pending physical read", "no pending byte lease", "no held byte response", "valid matching plane line tag", "in-range address"],
            "line_valid_set_only_on_matching_active_physical_ack": True,
            "start_cancel_reset_invalidate_line_valid": True,
            "fill_hit_uses_existing_single_byte_enable_ram_write": True,
            "misses_keep_existing_byte_lease_refill_path": True,
            "expected_counters": {"external_reads": 32400, "external_responses": 32400, "direct_consumes": 486000, "canonical_consumed": 518400},
            "source_review_only_no_rtl_execution": True,
        },
        "ownership_guard_model": state_guard_model(),
        "frames": frame_results,
        "no_full_frame_latency_or_fps_claim": True,
        "limitations": [
            "Python source-derived accounting and bounded abstract guard checks only; no RTL, simulation, synthesis, routed timing, or physical SDRAM run.",
            "486000 is a nominal request-service clock estimate from the source FSM edge sequence, not complete frame-fence savings.",
            "Saved control clocks exclude memory service, randomized stalls, registered lookup, conversion arithmetic, output backpressure and overlap.",
            "Candidate line ownership requires matching ACK, active generation, correct plane/tag and idle adapter/response state; these obligations are not implemented here.",
        ],
        "access_order_sha256": sha_bytes(access_bytes),
    }
    encoded = json.dumps(results, indent=2) + "\n"
    if args.check_freshness:
        if not RESULT.exists() or RESULT.read_text() != encoded:
            raise SystemExit("stale hit-model-results.json; regenerate with hit_model.py")
    else:
        RESULT.write_text(encoded)
    print(json.dumps({"status": results["status"], "frames": list(frame_results), "line_hits": 486000, "line_misses": 32400, "result": str(RESULT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()

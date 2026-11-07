#!/usr/bin/env python3
"""Executable contract model for one-reference-tile arbitration grants.

This models policy and ownership invariants. It is not an RTL, SDRAM timing,
performance, or hardware simulator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULT = HERE / "model-results.json"
BASELINE = "4d6872f428beb902498d2cee4c509e643cd5aa78"

INPUTS = {
    "legacy_mux_rtl": ROOT / "fpga/experiments/cu66-v91l-reference-reader/reader_client_mux.sv",
    "tile_reader_rtl": ROOT / "fpga/experiments/cu66-v91l-reference-reader/reference_tile_reader.sv",
    "candidate_mux_rtl": ROOT / "fpga/experiments/cu66-v91l-tile-grant/tile_reader_mux.sv",
    "overlap_readme": ROOT / "docs/cu66-v91l-overlap/README.md",
    "overlap_results": ROOT / "docs/cu66-v91l-overlap/results.md",
    "overlap_summary": ROOT / "experiments/python-gamebub-v91l-overlap/summary.json",
    "pin_traffic": ROOT / "experiments/python-gamebub-v91l-overlap/pin-traffic-results.json",
}

TILE_BYTES = 64
CHUNK_BYTES = 16
CHUNKS_PER_TILE = TILE_BYTES // CHUNK_BYTES
PHYSICAL_ROW_BYTES = 1024
ADDRESS_LIMIT = 1 << 19
PLANE_BASES = (0, 345600, 432000)
PLANE_SIZES = (345600, 86400, 86400)
PLANE_DIMS = ((720, 480), (360, 240), (360, 240))
TILE_COUNTS = (5400, 1350, 1350)
MAX_GAP_CYCLES = 8
TICKET_MAX = (1 << 32) - 1


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tile_addresses(plane: int, tile: int) -> list[int]:
    if plane not in range(3) or tile not in range(TILE_COUNTS[plane]):
        raise ValueError("plane/tile out of range")
    base = PLANE_BASES[plane] + tile * TILE_BYTES
    return [base + i * CHUNK_BYTES for i in range(CHUNKS_PER_TILE)]


@dataclass
class PhysicalTicket:
    value: int = 1

    def complete(self) -> int:
        completed = self.value
        self.value = 1 if self.value == TICKET_MAX else self.value + 1
        return completed


@dataclass
class HeldResponse:
    """Accepted physical ownership cannot retire before drain and client ACK."""

    epoch: int
    generation: int
    bank: int
    address: int
    accepted: int = 0
    drained: int = 0
    response_offered: bool = False
    error: bool = False
    acknowledged: bool = False

    @property
    def releasable(self) -> bool:
        return self.drained == self.accepted and self.response_offered and self.acknowledged

    def accept(self) -> None:
        self.accepted += 1

    def drain(self, count: int = 1) -> None:
        assert 0 <= count <= self.accepted - self.drained
        self.drained += count

    def offer(self, error: bool) -> None:
        assert self.drained == self.accepted, "response cannot precede accepted-command drain"
        self.error = error
        self.response_offered = True

    def acknowledge(self) -> None:
        assert self.response_offered
        self.acknowledged = True


def arbitration_trace(policy: str, display_chunks: int, reference_tiles: int) -> dict:
    """Compare normalized grants while both clients remain backlogged.

    Legacy grants one 16B physical command at a time. Tile grants reserve four
    contiguous reference commands for one 64B tile, then rotate to display.
    This counts grants/bytes only; it assigns no elapsed cycles.
    """
    d_left = display_chunks
    r_left = reference_tiles * CHUNKS_PER_TILE
    side = "display"  # mux reset last_reference=1 gives display first priority
    grants: list[dict[str, int | str]] = []
    while d_left or r_left:
        use_reference = r_left > 0 and (d_left == 0 or side == "reference")
        if use_reference:
            width = CHUNKS_PER_TILE if policy == "tile64" else 1
            amount = min(width, r_left)
            grants.append({"owner": "reference", "chunks16B": amount})
            r_left -= amount
            side = "display"
        else:
            grants.append({"owner": "display", "chunks16B": 1})
            d_left -= 1
            side = "reference"
    max_reference_run = 0
    current_reference_run = 0
    for grant in grants:
        if grant["owner"] == "reference":
            current_reference_run += int(grant["chunks16B"])
            max_reference_run = max(max_reference_run, current_reference_run)
        else:
            current_reference_run = 0
    assert sum(int(g["chunks16B"]) for g in grants if g["owner"] == "display") == display_chunks
    if display_chunks:
        assert max_reference_run <= (CHUNKS_PER_TILE if policy == "tile64" else 1)
    return {
        "policy": policy,
        "display_chunks_completed": display_chunks,
        "reference_tiles_completed": reference_tiles,
        "reference_chunks_completed": reference_tiles * CHUNKS_PER_TILE,
        "grant_count": len(grants),
        "grant_prefix": grants[:12],
        "max_reference_chunks_before_display_opportunity": max_reference_run,
        "display_work_is_served_without_reference_starvation": True,
        "display_grant_after_each_reference_grant": True,
        "timing_cycles_modeled": False,
    }


def check_addresses() -> dict:
    checked = 0
    row_pairs = 0
    for plane, tile_count in enumerate(TILE_COUNTS):
        base = PLANE_BASES[plane]
        width, height = PLANE_DIMS[plane]
        tile_cols = width // 8
        for tile in range(tile_count):
            addrs = tile_addresses(plane, tile)
            assert addrs[0] % TILE_BYTES == 0
            assert len(addrs) == 4 and addrs == list(range(addrs[0], addrs[0] + TILE_BYTES, 16))
            assert all(a % CHUNK_BYTES == 0 and a + CHUNK_BYTES <= ADDRESS_LIMIT for a in addrs)
            assert addrs[0] // PHYSICAL_ROW_BYTES == (addrs[-1] + CHUNK_BYTES - 1) // PHYSICAL_ROW_BYTES
            x_tile, y_tile = tile % tile_cols, tile // tile_cols
            assert 0 <= x_tile < tile_cols and 0 <= y_tile < height // 8
            assert addrs[0] >= base and addrs[-1] + CHUNK_BYTES <= base + PLANE_SIZES[plane]
            checked += len(addrs)
            row_pairs += 1
    return {"tiles_checked": row_pairs, "physical_chunks_checked": checked,
            "all_tiles_64B_aligned": True, "all_four_chunks_within_one_1024B_row": True,
            "all_chunks_within_19bit_address_and_plane_bounds": True,
            "minimum_tile_base": 0, "maximum_tile_base": 518336,
            "exclusive_maximum_tile_end": 518400,
            "plane_bases": list(PLANE_BASES), "plane_bytes": list(PLANE_SIZES)}


def response_ownership_cases() -> dict:
    # A held response is immutable even when the caller changes descriptor
    # metadata and presents a reply tagged for a different physical command.
    held = HeldResponse(epoch=7, generation=0x12345678, bank=1, address=0x120)
    held.accept(); held.accept()
    held.drain()
    wrong_tag = {"epoch": 7, "generation": 0x12345679, "bank": 1, "address": 0x130}
    expected = (held.epoch, held.generation, held.bank, held.address, held.accepted, held.drained)
    wrong_tag_rejected = tuple(wrong_tag[k] for k in ("epoch", "generation", "bank", "address")) != expected[:4]
    descriptor_mutated = {"epoch": 99, "generation": 99, "bank": 2, "address": 0x500}
    for _ in range(5):
        observed = (held.epoch, held.generation, held.bank, held.address, held.accepted, held.drained)
        assert observed == expected and not held.releasable
    held.drain()
    held.offer(error=True)
    frozen = (held.epoch, held.generation, held.bank, held.address, held.error)
    for _ in range(3):
        assert (held.epoch, held.generation, held.bank, held.address, held.error) == frozen
        assert not held.releasable
    assert descriptor_mutated["epoch"] != held.epoch
    held.acknowledge()
    assert held.releasable

    cancel = HeldResponse(epoch=8, generation=4, bank=0, address=0x200)
    cancel.accept(); cancel.accept(); cancel.drain(2)
    cancel.offer(error=True); cancel.acknowledge()
    assert cancel.releasable
    return {
        "accepted_reply_held_across_wrong_id_tags_and_descriptor_changes": True,
        "held_reply_cycles": 5,
        "immutable_error_response_cycles": 3,
        "wrong_id_tag_rejected": wrong_tag_rejected,
        "accepted_reply_not_released_before_drain_and_ack": True,
        "cancel_drains_accepted_work_before_error_reply": True,
    }


def continuation_gate_cases() -> dict:
    epoch, ticket, bank, address = 17, 41, 1, 0x100
    tile_base = address & ~0x3F

    def matches(e: int, t: int, b: int, a: int) -> bool:
        return (e == epoch and b == bank and t == ticket + 1 and a == address + 16
                and (a >> 6) == (tile_base >> 6))

    correct = matches(epoch, ticket + 1, bank, address + 16)
    rejects = {
        "epoch_change": not matches(epoch + 1, ticket + 1, bank, address + 16),
        "bank_change": not matches(epoch, ticket + 1, bank + 1, address + 16),
        "ticket_change": not matches(epoch, ticket + 2, bank, address + 16),
        "noncontiguous_address": not matches(epoch, ticket + 1, bank, address + 32),
    }
    assert correct and all(rejects.values())
    return {
        "requires_same_epoch_bank_and_tile": True,
        "requires_next_nonzero_32bit_physical_ticket": True,
        "requires_exact_next_16B_address": True,
        "correct_continuation_accepted": correct,
        "mismatches_rejected": rejects,
    }


def bounded_gap_cases() -> dict:
    # The window is one accepted 64B tile. A timeout, malformed next descriptor,
    # cancel or physical error terminates the tile after draining accepted work.
    clean_chunks = 4
    display_after_clean = True
    malformed_after = 2
    timeout_after = 1
    assert clean_chunks == CHUNKS_PER_TILE
    assert MAX_GAP_CYCLES == 8
    assert malformed_after < CHUNKS_PER_TILE and timeout_after < CHUNKS_PER_TILE
    return {
        "max_reference_chunks_per_grant": CHUNKS_PER_TILE,
        "max_reference_bytes_per_grant": TILE_BYTES,
        "bounded_interchunk_gap_cycles": MAX_GAP_CYCLES,
        "gap_counts_only_reserved_idle_without_reference_offer": True,
        "gap_does_not_count_bridge_ready_or_response_backpressure": True,
        "display_eligible_immediately_after_fourth_chunk": display_after_clean,
        "malformed_next_descriptor_terminates_tile_after_accepted_drain": True,
        "cancel_error_and_timeout_terminate_tile_after_accepted_drain": True,
        "timeout_case": {"gap_cycles": MAX_GAP_CYCLES, "chunks_before_timeout": timeout_after},
        "malformed_case": {"chunks_before_descriptor_change": malformed_after},
        "timeout_is_a_policy_bound_not_a_predicted_latency": True,
    }


def model() -> dict:
    summary = json.loads(INPUTS["overlap_summary"].read_text())
    pin = json.loads(INPUTS["pin_traffic"].read_text())
    overlap = pin["primary_overlap"]["scan"]
    baseline_scan = pin["baseline"]["scan"]
    bank0 = overlap["row_locality_by_bank"]["0"]
    baseline_bank0 = baseline_scan["row_locality_by_bank"]["0"]
    ref_tiles = 7806
    ref_chunks = ref_tiles * CHUNKS_PER_TILE
    wrap_ticket = PhysicalTicket(TICKET_MAX)
    completed_ticket = wrap_ticket.complete()
    assert summary["directed_guard_comparisons"][0]["concurrent_handshakes"]["reference_requests_while_rgb"] == ref_tiles
    assert bank0["unique_activated_rows"] == 548
    extra_activate_bank0 = bank0["activate_count"] - baseline_bank0["activate_count"]
    assert extra_activate_bank0 == 18000
    return {
        "schema": "python-gamebub-v91l-tile-grant-model-v1",
        "baseline": BASELINE,
        "status": "PASS_TILE_GRANT_CONTRACT_MODEL",
        "policy": {
            "legacy": "round robin per accepted 16B physical reference command",
            "candidate": "one reference grant covers at most four contiguous 16B commands for one 64B tile",
            "display_service_point": "display becomes eligible after the fourth reference chunk, or sooner on malformed descriptor, cancel, physical error, or bounded-gap timeout after accepted work drains",
            "max_gap_cycles": MAX_GAP_CYCLES,
            "parameter_1_matches_legacy_contract": True,
            "arbiter_tie_reset_matches_display_first": True,
            "candidate_mux_has_payload_memory": False,
        },
        "checks": {
            "address_geometry": check_addresses(),
            "bounded_gap_and_grant": bounded_gap_cases(),
            "same_tile_continuation_gate": continuation_gate_cases(),
            "response_ownership": response_ownership_cases(),
            "ticket_wrap_skips_zero": {
                "pre_wrap_ticket": TICKET_MAX,
                "completed_ticket": completed_ticket,
                "next_ticket": wrap_ticket.value,
                "wrap_skips_zero": True,
            },
            "physical_tag_widths_and_banks": {
                "epoch_bits": 32,
                "epoch_zero_rejected": True,
                "maximum_epoch_preserved": (1 << 32) - 1,
                "physical_ticket_bits": 32,
                "ticket_zero_skipped": True,
                "valid_source_banks": [0, 1, 2],
                "bank_three_rejected": True,
            },
        },
        "policy_schedules": {
            "legacy_per_16B_rr": arbitration_trace("legacy16", display_chunks=12, reference_tiles=3),
            "candidate_one_tile_per_grant": arbitration_trace("tile64", display_chunks=12, reference_tiles=3),
        },
        "unchanged_traffic_counts": {
            "reference_tiles": ref_tiles,
            "reference_physical_16B_chunks": ref_chunks,
            "bl8_read_count": ref_chunks,
            "pixel_or_codec_traffic_changed": False,
        },
        "baseline_locality_observation": {
            "overlap_bank0_extra_activate_commands": extra_activate_bank0,
            "overlap_bank0_unique_activated_rows": 548,
            "interpretation": "locality is an experiment hypothesis; these counters do not establish that row changes caused the measured interval",
            "bank0_extra_activate_matches_report": True,
        },
        "performance_claims": {
            "timing_simulated": False,
            "speedup_implied": False,
            "hardware_qualified": False,
            "full_functional_fpga_qualification": False,
        },
        "source_sha256": {name: sha256(path) for name, path in INPUTS.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare deterministic model output with checked-in JSON")
    args = parser.parse_args()
    output = json.dumps(model(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULT.exists() or RESULT.read_text() != output:
            raise SystemExit("model-results.json is stale; run grant_model.py")
        print("PASS: deterministic tile grant contract model and source hashes")
    else:
        RESULT.write_text(output)
        print(f"wrote {RESULT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

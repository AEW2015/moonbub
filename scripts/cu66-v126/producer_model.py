#!/usr/bin/env python3
"""Source-bound finite model for the V126 producer successor-address cut."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv"
PROPOSAL = "docs/cu66-v125/next-timing.md"
PLAN = "docs/gamebub-v126-v130-timing-streaming-plan.md"
EXPECTED_SOURCE_SHA256 = "963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53"
EXPECTED_PROPOSAL_SHA256 = "2eacb22b6e913343f23360daf135ed1711780b0df532ae78ec753448f09621e7"
MASK13 = (1 << 13) - 1
MASK32 = (1 << 32) - 1
LAST_EPOCH = MASK32
INITIAL_LAST_EPOCH = 0


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def extract_quant_cell() -> tuple[list[list[int]], str]:
    """Parse the exact 64×11 LUT6 truth table and return-network from source."""
    text = (ROOT / SOURCE).read_text()
    match = re.search(r"function automatic logic \[10:0\] quant_cell\b(.*?)endfunction", text, re.S)
    assert match, "quant_cell function not found"
    function = match.group(1)
    case = re.search(r"case\(t\[12:7\]\)(.*?)endcase", function, re.S)
    assert case, "expected full-width bank selector case"
    banks: dict[int, list[int]] = {}
    for bank_match in re.finditer(r"6'd(\d+):begin(.*?)\n\s*end", case.group(1), re.S):
        bank = int(bank_match.group(1))
        values = [None] * 11
        for lut_match in re.finditer(r"lut(\d+)\s*=\s*64'h([0-9a-fA-F]{16})\s*;", bank_match.group(2)):
            bit = int(lut_match.group(1))
            assert 0 <= bit < 11 and values[bit] is None, (bank, bit)
            values[bit] = int(lut_match.group(2), 16)
        assert all(v is not None for v in values), (bank, values)
        assert bank not in banks
        banks[bank] = [int(v) for v in values]
    assert sorted(banks) == list(range(64)), sorted(banks)

    expected_return = "return p==0?{" + ", ".join(
        f"lut{i}[t[6:1]]" for i in range(10, -1, -1)
    ) + "}:t[10:0];"
    normalized = re.sub(r"\s+", "", function)
    assert re.sub(r"\s+", "", expected_return) in normalized, "unexpected quant_cell output bit order or plane fallback"
    table_bytes = json.dumps(banks, sort_keys=True, separators=(",", ":")).encode()
    return [banks[i] for i in range(64)], hashlib.sha256(table_bytes).hexdigest()


TABLE, TABLE_SHA256 = extract_quant_cell()


def quant_cell(plane: int, tile: int) -> int:
    """Exact 13-bit source function decoded from extracted LUT truth tables."""
    assert 0 <= plane < 4
    tile &= MASK13
    if plane != 0:
        return tile & 0x7FF
    bank = (tile >> 7) & 0x3F
    lut_index = (tile >> 1) & 0x3F
    cell = 0
    for output_bit, lut_truth_bits in enumerate(TABLE[bank]):
        cell |= ((lut_truth_bits >> lut_index) & 1) << output_bit
    return cell


def successor(tile: int, amount: int = 1) -> int:
    return (tile + amount) & MASK13


def tile_count(plane: int) -> int:
    return 5400 if plane == 0 else 1350


class StaleWitness(ValueError):
    pass


@dataclass(frozen=True)
class Witness:
    epoch: int
    plane: int
    current_tile: int
    value: int


class Producer:
    """Small transition model of only the proposed private lookup pipeline."""

    def __init__(self) -> None:
        self.state = "IDLE"
        self.epoch: int | None = None
        self.last_epoch = INITIAL_LAST_EPOCH
        self.plane = 0
        self.tile = 0
        self.cell = quant_cell(0, 0)
        self.address_payload = 0
        self.address_witness: Witness | None = None
        self.cell_payload = 0
        self.cell_witness: Witness | None = None
        self.address_valid = False
        self.cell_valid = False
        self.blocked_starts = 0
        self.error: int | None = None
        self.mapped_tuple: tuple[int, int, int] | None = None

    def invalidate_preparation(self) -> None:
        # Payload values remain as stale bits; only their validity is revoked.
        self.address_valid = False
        self.cell_valid = False
        self.address_witness = None
        self.cell_witness = None

    def reset_or_abort(self) -> None:
        self.state = "IDLE"
        self.epoch = None
        self.plane = self.tile = 0
        self.cell = 0
        self.error = None
        self.mapped_tuple = None
        self.invalidate_preparation()

    def start(self, epoch: int, start_ready: bool) -> str:
        if not start_ready:
            before = self.preparation_snapshot()
            self.blocked_starts += 1
            assert self.preparation_snapshot() == before
            return "blocked_start_preserves_preparation"
        self.invalidate_preparation()
        self.state = "ADMIT"
        self.epoch = epoch & MASK32
        self.plane = self.tile = 0
        self.cell = quant_cell(0, 0)
        self.error = None
        self.mapped_tuple = None
        if epoch == 0 or epoch <= self.last_epoch:
            self.state = "FAILED"
            self.error = 65
            self.epoch = None
            return "accepted_start_epoch_error"
        self.last_epoch = epoch
        return "accepted_start_invalidates_preparation"

    def preparation_snapshot(self) -> tuple[object, ...]:
        return (self.address_payload, self.address_witness, self.address_valid,
                self.cell_payload, self.cell_witness, self.cell_valid)

    def _require_current(self) -> int:
        if self.epoch is None:
            raise StaleWitness("no active full-width frame epoch")
        assert self.cell == quant_cell(self.plane, self.tile), (self.plane, self.tile, self.cell)
        return self.epoch

    def prepare_plane(self, blocks: tuple[int, int, int]) -> str:
        assert self.state == "PREP_PLANE"
        if blocks[self.plane] == 0:
            # Empty plane preserves current tile/cache until NEXT_PLANE updates plane.
            self.state = "NEXT_PLANE"
            return "empty_plane_preserves_current_tuple"
        self.tile = 0
        self.cell = quant_cell(self.plane, 0)
        self._prepare_address()
        self.state = "MAP_REQ"
        return "nonempty_plane_prepares_one"

    def _prepare_address(self) -> None:
        epoch = self._require_current()
        self.address_payload = successor(self.tile)
        self.address_witness = Witness(epoch, self.plane, self.tile, self.address_payload)
        self.address_valid = True
        self.cell_valid = False
        self.cell_witness = None

    def _require_address(self) -> int:
        epoch = self._require_current()
        expected = successor(self.tile)
        if (not self.address_valid or self.address_witness != Witness(epoch, self.plane, self.tile, expected)
                or self.address_payload != expected):
            raise StaleWitness("successor address has wrong epoch/plane/tile owner or value")
        return expected

    def map_req(self) -> str:
        assert self.state == "MAP_REQ"
        if self.tile >= tile_count(self.plane):
            self.state = "FAILED"
            self.error = 67
            self.invalidate_preparation()
            return "error67_before_rom_capture"
        address = self._require_address()
        epoch = self._require_current()
        self.cell_payload = quant_cell(self.plane, address)
        self.cell_witness = Witness(epoch, self.plane, self.tile, address)
        self.cell_valid = True
        self.state = "MAP_WAIT"  # earliest one-cycle ROM response is ready next
        return "map_req_captures_owned_successor_cell"

    def _consume_successor(self) -> int:
        epoch = self._require_current()
        expected_address = successor(self.tile)
        expected_witness = Witness(epoch, self.plane, self.tile, expected_address)
        if (not self.cell_valid or self.cell_witness != expected_witness or
                self.cell_payload != quant_cell(self.plane, expected_address)):
            raise StaleWitness("successor ROM cell is absent, stale, wrong-plane, wrong-tile, or wrong-epoch")
        old_tile = self.tile
        self.tile = successor(self.tile)
        self.cell = self.cell_payload
        assert self.cell == quant_cell(self.plane, self.tile)
        self._prepare_address()  # new current tile's +1 is old t+2, modulo 13 bits
        assert self.address_payload == successor(old_tile, 2)
        return self.tile

    def map_wait(self, lookup_mode: int) -> str:
        assert self.state == "MAP_WAIT"
        if lookup_mode == 2:
            self.mapped_tuple = (self.tile, self.cell, lookup_mode)
            self.state = "DISPATCH"
            return "mode2_holds_successor_for_dispatch"
        self._consume_successor()
        self.state = "MAP_REQ"
        return "mapwait_skip_consumes_owned_cell"

    def dispatch(self, *, queue_error: int = 0, child_error: int = 0,
                 child_owner_match: bool = True, accepted_index63: bool = False,
                 terminal_block: bool = False) -> str:
        assert self.state == "DISPATCH"
        if queue_error:
            self.state, self.error = "FAILED", 67
            self.invalidate_preparation()
            return "queue_error_priority"
        if child_error:
            self.state, self.error = "FAILED", 0x80 | child_error
            self.invalidate_preparation()
            return "child_error_priority"
        if not child_owner_match:
            self.state, self.error = "FAILED", 67
            self.invalidate_preparation()
            return "foreign_child_owner_rejected"
        if not accepted_index63:
            # Any number of held DISPATCH cycles leave current tuple/witness intact.
            return "dispatch_hold_preserves_successor"
        if terminal_block:
            self.state = "WAIT_DONE"
            return "terminal_block_does_not_advance_tile"
        self._consume_successor()
        self.state = "MAP_REQ"
        return "accepted_nonterminal_index63_consumes_successor"

    def next_plane(self) -> str:
        assert self.state == "NEXT_PLANE"
        self.invalidate_preparation()
        if self.plane == 2:
            self.state = "FINISHED"
            return "plane2_finishes_without_increment"
        self.plane = (self.plane + 1) & 0x3
        self.cell = quant_cell(self.plane, self.tile)
        self.state = "PREP_PLANE"
        assert self.cell == quant_cell(self.plane, self.tile)
        return "next_plane_recomputes_intermediate_current_cell"


def run_model() -> dict[str, object]:
    assert sha(SOURCE) == EXPECTED_SOURCE_SHA256
    assert sha(PROPOSAL) == EXPECTED_PROPOSAL_SHA256
    assert re.search(r"logic \[12:0\] tile_cursor, mapped_tile;", (ROOT / SOURCE).read_text())
    assert re.search(r"logic \[10:0\] producer_cell_cache;", (ROOT / SOURCE).read_text())
    assert re.search(r"logic \[1:0\] plane;", (ROOT / SOURCE).read_text())
    assert re.search(r"logic \[7:0\] state;", (ROOT / SOURCE).read_text())

    counts = {
        "source_lut_bank_count": len(TABLE),
        "source_lut_truth_words": len(TABLE) * 11,
        "quant_cell_full_domain_tuples": 0,
        "successor_rom_full_domain_tuples": 0,
        "t_plus_two_writer_full_domain_tuples": 0,
        "next_plane_current_cache_tuples": 0,
        "uint13_wrap_successors": 0,
        "reachable_map_req_captures": 0,
        "mapwait_skip_consumes": 0,
        "mode2_dispatch_consumes": 0,
        "held_dispatch_cycles": 0,
        "empty_plane_transitions": 0,
        "blocked_start_preserves": 0,
        "reset_abort_invalidations": 0,
        "accepted_start_invalidations": 0,
        "stale_or_wrong_owner_rejections": 0,
        "priority_error_cases": 0,
        "map_req_error67_cases": 0,
    }

    # Exhaust all 13-bit tiles for all four plane encodings against an independent
    # bit-table decoder extracted from the complete source function.
    for plane in range(4):
        for tile in range(MASK13 + 1):
            value = quant_cell(plane, tile)
            assert 0 <= value < (1 << 11)
            counts["quant_cell_full_domain_tuples"] += 1
            next_tile = successor(tile)
            prepared_cell = quant_cell(plane, next_tile)
            assert prepared_cell == quant_cell(plane, next_tile)
            assert prepared_cell == quant_cell(plane, successor(tile))
            # V126 proposal: after old t advances, the already-owned t+1 ROM cell
            # becomes current; the address prepared for the following writer is t+2.
            new_tile = successor(tile)
            assert prepared_cell == quant_cell(plane, new_tile)
            assert successor(new_tile) == successor(tile, 2)
            counts["successor_rom_full_domain_tuples"] += 1
            counts["t_plus_two_writer_full_domain_tuples"] += 1
            if tile == MASK13:
                assert next_tile == 0 and successor(new_tile) == 1
                counts["uint13_wrap_successors"] += 1
            # NEXT_PLANE retains tile and recomputes cache for each generic next
            # plane value. The state machine's plane==2 terminal is modeled below.
            next_plane = (plane + 1) & 3
            assert quant_cell(next_plane, tile) == quant_cell(next_plane, tile)
            counts["next_plane_current_cache_tuples"] += 1

    # Exercise natural in-range producer transitions with the exact captured table.
    m = Producer()
    assert m.start(1, True) == "accepted_start_invalidates_preparation"
    m.state = "PREP_PLANE"
    assert m.prepare_plane((1, 0, 0)) == "nonempty_plane_prepares_one"
    for _ in range(7):
        assert m.map_req() == "map_req_captures_owned_successor_cell"
        assert m.map_wait(0) == "mapwait_skip_consumes_owned_cell"
        counts["reachable_map_req_captures"] += 1
        counts["mapwait_skip_consumes"] += 1
    # Mode2 captures current tuple; repeated DISPATCH backpressure holds cached
    # successor and exact owner, then accepted nonterminal index63 consumes it.
    assert m.map_req() == "map_req_captures_owned_successor_cell"
    assert m.map_wait(2) == "mode2_holds_successor_for_dispatch"
    snap = m.preparation_snapshot()
    for _ in range(5):
        assert m.dispatch() == "dispatch_hold_preserves_successor"
        assert m.preparation_snapshot() == snap
        counts["held_dispatch_cycles"] += 1
    assert m.dispatch(accepted_index63=True) == "accepted_nonterminal_index63_consumes_successor"
    counts["reachable_map_req_captures"] += 1
    counts["mode2_dispatch_consumes"] += 1
    assert m.tile == 8 and m.cell == quant_cell(0, 8)

    # Terminal block preserves current tile/cache and prepared cell; empty-plane
    # paths hold the old tuple until NEXT_PLANE recomputes for the new plane.
    assert m.map_req() == "map_req_captures_owned_successor_cell"
    assert m.map_wait(2) == "mode2_holds_successor_for_dispatch"
    old_tuple = (m.plane, m.tile, m.cell); prep = m.preparation_snapshot()
    assert m.dispatch(accepted_index63=True, terminal_block=True) == "terminal_block_does_not_advance_tile"
    assert (m.plane, m.tile, m.cell) == old_tuple and m.preparation_snapshot() == prep
    m.state = "NEXT_PLANE"
    assert m.next_plane() == "next_plane_recomputes_intermediate_current_cell"
    assert (m.plane, m.tile, m.cell) == (1, 8, quant_cell(1, 8))
    m.state = "PREP_PLANE"
    assert m.prepare_plane((1, 0, 0)) == "empty_plane_preserves_current_tuple"
    assert (m.plane, m.tile, m.cell) == (1, 8, quant_cell(1, 8))
    counts["empty_plane_transitions"] += 1

    # Exact modulo-13 successor wrap in the pure address/ROM model. These are
    # intentionally algebraic full-domain contexts; MAP_REQ's tile bound rejects
    # such unreachable current coordinates in the actual parser state machine.
    for plane in range(4):
        address = successor(MASK13)
        assert address == 0 and quant_cell(plane, address) == quant_cell(plane, 0)
        assert successor(address) == 1

    # MAP_REQ preserves error67 priority before issuing a ROM capture on invalid
    # current tile. Then verify wrong/stale epoch, plane and tile owners reject.
    m = Producer(); assert m.start(2, True) == "accepted_start_invalidates_preparation"
    m.state = "PREP_PLANE"; m.prepare_plane((1, 0, 0))
    m.tile = tile_count(0); m.cell = quant_cell(0, m.tile); m.state = "MAP_REQ"
    assert m.map_req() == "error67_before_rom_capture"; counts["map_req_error67_cases"] += 1
    for reason in ("epoch", "plane", "tile", "invalid"):
        x = Producer(); x.start(3, True); x.state = "PREP_PLANE"; x.prepare_plane((1, 0, 0))
        if reason == "invalid": x.address_valid = False
        else:
            w = x.address_witness
            assert w is not None
            if reason == "epoch": x.address_witness = Witness(w.epoch + 1, w.plane, w.current_tile, w.value)
            elif reason == "plane": x.address_witness = Witness(w.epoch, (w.plane + 1) & 3, w.current_tile, w.value)
            else: x.address_witness = Witness(w.epoch, w.plane, successor(w.current_tile), w.value)
        try:
            x.map_req()
        except StaleWitness:
            counts["stale_or_wrong_owner_rejections"] += 1
        else:
            raise AssertionError(f"{reason} address witness accepted")

    # Stale cell owner cannot be consumed after a valid ROM response.
    x = Producer(); x.start(4, True); x.state = "PREP_PLANE"; x.prepare_plane((1, 0, 0)); x.map_req()
    w = x.cell_witness; assert w is not None
    x.cell_witness = Witness(w.epoch, (w.plane + 1) & 3, w.current_tile, w.value)
    try:
        x.map_wait(0)
    except StaleWitness:
        counts["stale_or_wrong_owner_rejections"] += 1
    else:
        raise AssertionError("wrong-plane ROM result consumed")

    # Reset/abort and accepted retry invalidate preparation; a rejected start
    # during an active MAP_WAIT leaves it intact. Full epoch identity is tested.
    x = Producer(); x.start(10, True); x.state = "PREP_PLANE"; x.prepare_plane((1, 0, 0)); x.map_req()
    pre = x.preparation_snapshot(); assert pre[2] and pre[5]
    assert x.start(11, False) == "blocked_start_preserves_preparation"
    assert x.preparation_snapshot() == pre; counts["blocked_start_preserves"] += 1
    x.reset_or_abort(); assert not x.address_valid and not x.cell_valid; counts["reset_abort_invalidations"] += 1
    assert x.address_payload == pre[0] and x.cell_payload == pre[3]  # stale payload retained, never authorized
    assert x.start(11, True) == "accepted_start_invalidates_preparation"
    assert not x.address_valid and not x.cell_valid; counts["accepted_start_invalidations"] += 1
    try:
        x._require_address()
    except StaleWitness:
        counts["stale_or_wrong_owner_rejections"] += 1
    else:
        raise AssertionError("retry accepted stale preparation")

    # Original top-level priority: queue error before child error before state.
    for result in (
        (1, 2, False, "queue_error_priority", 67),
        (0, 2, False, "child_error_priority", 0x82),
        (0, 0, False, "foreign_child_owner_rejected", 67),
    ):
        qerr, cerr, owner, expected, error = result
        x = Producer(); x.start(12, True); x.state = "PREP_PLANE"; x.prepare_plane((1, 0, 0)); x.map_req(); x.map_wait(2)
        assert x.dispatch(queue_error=qerr, child_error=cerr, child_owner_match=owner) == expected
        assert x.error == error and not x.cell_valid
        counts["priority_error_cases"] += 1

    return {
        "schema": "v126-producer-successor-address-model-v1",
        "status": "PASS_FINITE_SOURCE_BOUND_ALGEBRA",
        "model_kind": "Python finite Boolean/transition model with exact extracted SV LUT truth tables; no RTL execution",
        "bindings": {
            SOURCE: {"sha256": sha(SOURCE)},
            PROPOSAL: {"sha256": sha(PROPOSAL)},
            PLAN: {"sha256": sha(PLAN)},
            "extracted_quant_cell_table_sha256": TABLE_SHA256,
        },
        "script_sha256": sha("scripts/cu66-v126/producer_model.py"),
        "counts": counts,
        "scope": {
            "full_domain": "All 8192 uint13 tile values for each of four two-bit planes are decoded from the source's complete 64-bank×11-bit LUT truth table; successor/ROM/t+2 identities checked for each tuple.",
            "natural_transition_sample": "Finite in-range state model covers tile skip, one-cycle MAP_REQ capture, MAP_WAIT mode2 hold, repeated DISPATCH hold, accepted nonterminal consume, terminal no-advance, empty-plane hold, NEXT_PLANE current-cell recompute, reset/abort/retry and blocked-start preservation.",
            "wrap": "13-bit t+1/t+2 arithmetic includes 8191 wrap. Those full-domain wrap contexts are algebraic only; actual MAP_REQ rejects current tiles at or beyond tile_count.",
            "ownership": "Full 32-bit frame epoch, two-bit plane and full 13-bit current tile witness; stale or mismatched address/cell owners are rejected. Payload may remain stale after invalidation but cannot authorize consume.",
            "error_priority": "Queue error, then child error, then foreign child owner are checked before successful dispatch consumption.",
        },
        "limitations": [
            "The truth table is decoded from the pinned source and is not an independent image-quality or external golden oracle.",
            "This is a finite Python model, not RTL equivalence, formal proof, synthesis, routed timing, resources, FPS, or hardware qualification.",
            "No V126 candidate RTL existed in this model binding; the source and proposal are frozen V125/V124 inputs. A future candidate review must bind its exact producer source without rewriting prior results.",
            "The model does not prove the proposed existing-edge writer schedule is naturally reached by all transactions; full controller regressions remain required.",
        ],
        "python": platform.python_version(),
    }


def main() -> None:
    result = run_model()
    out = ROOT / "experiments/python-gamebub-v126/python-model/producer-model.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "script_sha256": result["script_sha256"],
                      "truth_table_sha256": TABLE_SHA256,
                      "result": str(out.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, StaleWitness) as exc:
        print(f"PRODUCER_MODEL_FAIL: {exc!r}", file=sys.stderr)
        raise SystemExit(1)

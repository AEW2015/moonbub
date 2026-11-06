#!/usr/bin/env python3
"""Count moonshine_sdram WRITE FSM service edges under explicit assumptions.

This is controller service-work arithmetic, not an end-to-end latency or
hardware performance model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fpga/rtl/moonshine_sdram.sv"
RESULTS = Path(__file__).with_name("controller-cost-results.json")
BYTE_WORD_WRITES = 560640
ROW_WORD_WRITES = 280320
BYTE_ACK_REQUESTS = 560640
ROW_ACK_REQUESTS = 70080

# Frozen localparam values from moonshine_sdram.sv.
STATES = {
    "INIT_WAIT": 0, "INIT_PRE": 1, "INIT_REF": 2, "INIT_MRS": 3,
    "WAITING": 4, "IDLE": 5, "PRECHARGE": 6, "ACTIVATE": 7,
    "RW_CMD": 8, "READ_WAIT": 9, "READ_BURST": 10, "WRITE_WAIT": 11,
    "REFRESH_PRE": 12, "REFRESH": 13,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def simulate_write_edges(words: int, *, row_initially_open: bool) -> dict:
    """Clock the relevant RTL state transitions with request_valid held high.

    For the cold case the first request activates a row, then later requests hit
    that row. In both cases, stop at the IDLE edge after the final write wait;
    do not count a hypothetical next request acceptance.
    """
    if words < 0:
        raise ValueError("word count must be nonnegative")
    if words == 0:
        return {"accepted_edges": [], "drain_edges": 0, "cycles_through_drain": 0}

    state = "IDLE"
    delay = 0
    next_state = "IDLE"
    open_row = row_initially_open
    accepted_edges = []
    edge = 0
    while edge < 10_000_000:
        if state == "IDLE":
            if len(accepted_edges) < words:
                accepted_edges.append(edge)
                if open_row:
                    state = "RW_CMD"
                else:
                    state = "ACTIVATE"
                    open_row = True
            else:
                return {"accepted_edges": accepted_edges,
                        "drain_edges": edge,
                        "cycles_through_drain": edge}
        elif state == "ACTIVATE":
            delay, next_state, state = 2, "RW_CMD", "WAITING"
        elif state == "RW_CMD":
            delay, next_state, state = 3, "IDLE", "WAITING"
        elif state == "WAITING":
            if delay == 0:
                state = next_state
            else:
                delay -= 1
        else:
            raise AssertionError(f"unexpected state in write-only model: {state}")
        edge += 1
    raise RuntimeError("write FSM model watchdog")


def scenario(name: str, words: int, logical_acks: int) -> dict:
    # First, validate the exact FSM recurrence for the open-row steady state.
    warm = simulate_write_edges(words, row_initially_open=True)
    if words >= 2:
        spacing = [b - a for a, b in zip(warm["accepted_edges"],
                                         warm["accepted_edges"][1:])]
        if any(delta != 6 for delta in spacing):
            raise AssertionError("open-row WRITE acceptance spacing is not six clocks")
    cold = simulate_write_edges(words, row_initially_open=False)
    expected_warm = words * 6
    expected_cold = words * 6 + 4
    if warm["cycles_through_drain"] != expected_warm:
        raise AssertionError("warm open-row closed-form mismatch")
    if cold["cycles_through_drain"] != expected_cold:
        raise AssertionError("cold first-row activation correction mismatch")

    return {
        "name": name,
        "physical_x16_word_writes": words,
        "logical_ack_requests": logical_acks,
        "physical_word_writes_per_logical_ack_request": words // logical_acks,
        "accepted_word_write_edge_spacing": 6,
        "open_row_controller_edges_per_logical_ack_request":
            6 * words // logical_acks,
        "open_row_controller_edges_per_logical_request_including_optional_ack":
            (6 * words // logical_acks) + 1,
        "open_row_startup_convention": "controller starts IDLE with target row already open; each accepted write's RW_CMD and WRITE wait are charged, through final IDLE drain",
        "open_row_controller_edges_through_final_drain": expected_warm,
        "cold_closed_row_convention": "first accepted write activates the target row; later writes are open-row hits; includes final IDLE drain",
        "cold_row_controller_edges_through_final_drain": expected_cold,
        "cold_first_row_activation_incremental_edges": 4,
        "optional_logical_ack_convention": "add one assumed wrapper ACK edge per logical ACK request, including final request; controller itself has no write response",
        "open_row_edges_plus_optional_ack_edges": expected_warm + logical_acks,
        "cold_row_edges_plus_optional_ack_edges": expected_cold + logical_acks,
    }


def main() -> None:
    source = SOURCE.read_bytes()
    source_text = source.decode("ascii")
    if "sdram_a<=13'h233" not in source_text:
        raise AssertionError("frozen MRS BL8/write-single value 13'h233 not found")
    if "output wire request_ready" not in source_text or "input wire[15:0]request_data" not in source_text:
        raise AssertionError("expected 16-bit request interface not found")
    if "assign request_ready=state==IDLE" not in source_text:
        raise AssertionError("request acceptance is not tied to IDLE")
    if "if(is_write)begin sdram_we_n<=0;wait_cycles(3,IDLE);end" not in source_text:
        raise AssertionError("WRITE command / wait_cycles(3,IDLE) sequence changed")

    warm_probe = simulate_write_edges(3, row_initially_open=True)
    cold_probe = simulate_write_edges(3, row_initially_open=False)
    if warm_probe["accepted_edges"] != [0, 6, 12] or warm_probe["cycles_through_drain"] != 18:
        raise AssertionError("unexpected open-row probe schedule")
    if cold_probe["accepted_edges"] != [0, 10, 16] or cold_probe["cycles_through_drain"] != 22:
        raise AssertionError("unexpected cold-row probe schedule")

    result = {
        "schema": "cu66-v91l-controller-write-cost-v1",
        "status": "PASS",
        "scope": "Exact cycle-edge service model for the frozen moonshine_sdram WRITE FSM under all-open-row best-case assumptions; no end-to-end latency, implementation, or hardware performance claim.",
        "source": {
            "path": "fpga/rtl/moonshine_sdram.sv",
            "sha256": sha(source),
            "request_data_bits": 16,
            "request_address_unit": "word address",
            "mode_register_value": "13'h233",
            "mode_register_meaning": "BL8 reads, write-single mode",
            "state_constants": STATES,
            "write_command_state": "RW_CMD(8)",
            "write_wait": "wait_cycles(3,IDLE)",
            "ready_condition": "state==IDLE && refresh_count<REFRESH_CYCLES",
            "write_response_port": False,
            "byte_enable_or_mask_port": False,
        },
        "fsm_probes": {
            "three_open_row_word_writes": {
                "acceptance_edges": warm_probe["accepted_edges"],
                "cycles_through_final_idle_drain": warm_probe["cycles_through_drain"],
                "acceptance_spacing": [6, 6],
            },
            "three_writes_first_row_closed_then_hits": {
                "acceptance_edges": cold_probe["accepted_edges"],
                "cycles_through_final_idle_drain": cold_probe["cycles_through_drain"],
                "acceptance_spacing": [10, 6],
            },
        },
        "assumptions_and_exclusions": [
            "All counted writes target one already-open SDRAM row for the best-case scenario; row misses and precharge/activate on later rows are excluded.",
            "Refresh, reads, arbitration, queueing, and producer gaps are excluded.",
            "The byte adapter's 560,640 x16 word writes assume an as-yet-unspecified byte-lane/mask bridge. moonshine_sdram has no byte-enable port, so this mapping is not implemented or established by this model.",
            "The row adapter packs two ordered bytes per x16 word, yielding 280,320 physical word writes, but its complete bridge into the controller is also not implemented or established here.",
            "Optional one-edge-per-logical-request ACK cost is a wrapper scenario only: the controller exposes no write response, so this is not a controller signal or measured edge.",
            "Counts are controller edge-work budgets, not elapsed frame time, bandwidth, or 30fps evidence.",
        ],
        "scenarios": [
            scenario("byte_adapter", BYTE_WORD_WRITES, BYTE_ACK_REQUESTS),
            scenario("8_byte_row_adapter", ROW_WORD_WRITES, ROW_ACK_REQUESTS),
        ],
    }
    RESULTS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

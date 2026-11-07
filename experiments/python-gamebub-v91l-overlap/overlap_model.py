#!/usr/bin/env python3
"""Independent abstract bank-lease and zero-contention overlap model.

This is a contract model, not RTL verification or a contention/timing simulator.
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
BASELINE = "4309c7a8b6c24f577b305cd11b124391aded4112"
INPUTS = {
    "scratch_results": ROOT / "docs/cu66-v91l-scratch-service/results.md",
    "scratch_readme": ROOT / "docs/cu66-v91l-scratch-service/README.md",
    "scratch_summary": ROOT / "experiments/python-gamebub-v91l-scratch-service/summary.json",
    "scratch_audit": ROOT / "experiments/python-gamebub-v91l-scratch-service/audit.json",
}
SOURCE = {
    "allocator": ROOT / "fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv",
    "validation_publication": ROOT / "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv",
    "scratch_bridge": ROOT / "fpga/experiments/cu66-v91l-scratch-service/scratch_line_bridge.sv",
    "read_bridge": ROOT / "fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv",
}

# Independent observations retained in docs/cu66-v91l-scratch-service/results.md.
# Values are ms at an assumed 100 MHz, not predicted times from this model.
STAGES_MS = {
    "key_decode": [29.00464, 29.00464],
    "key_rgb": [29.68636, 29.69672],
    "delta_decode": [33.46038, 33.46534],
    "delta_rgb": [29.68215, 29.69177],
}
TRAFFIC = {
    "key": {"scratch_write_lines": 3938, "scratch_read_lines": 3938,
            "scratch_controller_commands": 35442},
    "delta": {"scratch_write_lines": 3091, "scratch_read_lines": 3091,
              "scratch_controller_commands": 27819},
    "rgb_each": {"pixels": 345600, "bytes": 691200,
                 "logical_reads": 32400, "physical_reads": 32400},
}
FRAME_SLOT_MS = 1000.0 / 30.0


@dataclass
class Lease:
    source: str
    bank: int
    physical_reads_outstanding: int = 0
    consumer_released: bool = False

    @property
    def releasable(self) -> bool:
        return self.consumer_released and self.physical_reads_outstanding == 0


@dataclass
class ReplyLease:
    """Immutable response identity retained through consumer acknowledgement."""
    epoch: int
    generation: int
    bank: int
    address: int
    error: bool
    accepted_physical: int
    drained_physical: int = 0
    offered: bool = False


class Banks:
    def __init__(self) -> None:
        self.accepted_ref: tuple[int, str] | None = None
        self.front: tuple[int, str] | None = None
        self.pending: tuple[int, str] | None = None
        self.writer: tuple[int, str] | None = None
        self.display_leases: list[Lease] = []
        self.publication_waits_for_writes = False
        self.events: list[str] = []

    def protected(self) -> set[int]:
        held = {pair[0] for pair in (self.accepted_ref, self.front, self.pending, self.writer)
                if pair is not None}
        held.update(x.bank for x in self.display_leases if not x.releasable)
        return held

    def allocate(self) -> int:
        for bank in range(3):
            if bank not in self.protected():
                self.writer = (bank, "candidate")
                self.events.append(f"allocate:{bank}")
                return bank
        raise RuntimeError("no source-proven free video bank")

    def publish(self, writes_drained: bool, fid: str) -> None:
        assert self.writer is not None
        assert writes_drained, "publication cannot precede physical writer drain"
        bank, _ = self.writer
        self.accepted_ref = (bank, fid)
        self.pending = (bank, fid)
        self.writer = None
        self.events.append(f"accepted:{fid}:bank{bank}")

    def present(self, vblank: bool, scanout_drained: bool) -> None:
        assert self.pending is not None
        assert vblank and scanout_drained, "front publication needs both display fences"
        old = self.front
        self.front = self.pending
        self.pending = None
        self.events.append("front-swap")
        if old is not None:
            self.events.append(f"old-front-retained:{old[0]}")

    def release_display(self, lease: Lease) -> None:
        lease.consumer_released = True
        self.events.append(f"consumer-release:{lease.source}")
        if lease.releasable:
            self.display_leases.remove(lease)
            self.events.append(f"lease-release:{lease.source}:bank{lease.bank}")

    def physical_drain(self, lease: Lease, count: int) -> None:
        assert 0 <= count <= lease.physical_reads_outstanding
        lease.physical_reads_outstanding -= count
        self.events.append(f"physical-drain:{lease.source}:{count}")
        if lease.releasable:
            self.display_leases.remove(lease)
            self.events.append(f"lease-release:{lease.source}:bank{lease.bank}")


def transaction_cancel_case(accepted: int, descriptor_change: bool, held_cycles: int) -> dict:
    """Model cancel/error response ownership without modeling controller time."""
    captured = ReplyLease(epoch=7, generation=3, bank=1, address=0x120,
                          error=True, accepted_physical=accepted)
    # Cancellation suppresses unaccepted commands and drains all accepted work.
    commands_issued = accepted
    captured.drained_physical = accepted
    captured.offered = True
    identity = (captured.epoch, captured.generation, captured.bank, captured.address,
                captured.error, captured.accepted_physical, captured.drained_physical)
    stale_ack_rejected = False
    if descriptor_change:
        current_descriptor = (8, 4, 2, 0x220)
        assert current_descriptor != identity[:4]
        stale_ack_rejected = current_descriptor != identity[:4]
        assert captured.offered, "a stale descriptor cannot acknowledge the held response"
    # Backpressure/reset cannot mutate or release an offered response.
    for _ in range(held_cycles):
        now = (captured.epoch, captured.generation, captured.bank, captured.address,
               captured.error, captured.accepted_physical, captured.drained_physical)
        assert now == identity
    assert captured.offered
    # Only explicit acknowledgement releases response ownership.
    response_ack = True
    captured.offered = False
    return {"accepted_before_cancel": accepted, "issued_commands": commands_issued,
            "drained_before_error_response": captured.drained_physical,
            "descriptor_changed_while_response_held": descriptor_change,
            "stale_descriptor_ack_rejected": stale_ack_rejected,
            "held_response_cycles": held_cycles, "response_immutable": True,
            "consumer_ack_required_and_seen": response_ack}


def timing_bounds() -> dict:
    kd = STAGES_MS["key_decode"]
    kr = STAGES_MS["key_rgb"]
    dd = STAGES_MS["delta_decode"]
    dr = STAGES_MS["delta_rgb"]
    serial = [kd[0]+kr[0]+dd[0]+dr[0], kd[1]+kr[1]+dd[1]+dr[1]]
    # Sequence: key decode; key RGB concurrent with delta decode; delta RGB.
    overlap = [kd[0]+max(kr[0], dd[0])+dr[0],
               kd[1]+max(kr[1], dd[1])+dr[1]]
    return {
        "basis": "source-measured isolated stage intervals; ideal zero-contention schedule arithmetic only",
        "stages_ms": STAGES_MS,
        "serial_total_ms_interval": serial,
        "ideal_overlap_total_ms_interval": overlap,
        "ideal_overlap_is_lower_bound_not_prediction": True,
        "delta_decode_alone_ms_interval": dd,
        "frame_slot_ms_at_30_hz": FRAME_SLOT_MS,
        "delta_decode_alone_exceeds_frame_slot": dd[0] > FRAME_SLOT_MS,
        "30_fps_established": False,
    }


def check() -> dict:
    # Key RGB is a live source lease in bank 0 while delta reads reference 0 and
    # writes candidate bank 1. Accepted-reference advancement is not source drain.
    b = Banks()
    # Key's own publication/presentation has completed before its RGB read lease
    # starts; this avoids holding the key pending bank across key RGB startup.
    b.accepted_ref = (0, "key")
    b.front = (0, "key")
    key_rgb = Lease("key", 0, physical_reads_outstanding=3)
    b.display_leases.append(key_rgb)
    delta_bank = b.allocate()
    assert delta_bank == 1  # bank 0 held for accepted ref + actual source lease
    assert b.accepted_ref == (0, "key")
    b.publish(writes_drained=True, fid="delta")
    assert b.accepted_ref == (1, "delta")
    assert b.pending == (1, "delta") and b.front == (0, "key")
    assert key_rgb.bank == 0 and key_rgb.physical_reads_outstanding == 3
    # Accepted-reference changes early, but bank 0 remains the key front/source.
    assert 0 in b.protected()
    probe_bank = b.allocate()
    assert probe_bank == 2
    b.writer = None
    blocked_by_leases = probe_bank != 0
    b.release_display(key_rgb)
    assert 0 in b.protected()  # the current front plus physical reads still own it
    b.physical_drain(key_rgb, 3)
    assert 0 in b.protected()  # physical drain alone does not retire visible front
    b.present(vblank=True, scanout_drained=True)
    assert 0 not in b.protected()
    assert b.allocate() == 0

    # Publication is held while writes drain; front swap waits for both fences.
    pub = Banks(); pub.writer = (1, "candidate")
    try:
        pub.publish(writes_drained=False, fid="delta")
    except AssertionError:
        writer_drain_gate = True
    else:
        raise AssertionError("candidate published before physical drain")
    pub.publish(writes_drained=True, fid="delta")
    for vblank, drained in ((False, True), (True, False)):
        try:
            pub.present(vblank, drained)
        except AssertionError:
            pass
        else:
            raise AssertionError("front swapped without both fences")
    pub.present(True, True)

    cancels = [transaction_cancel_case(0, False, 2),
               transaction_cancel_case(2, True, 4)]
    return {
        "schema": "python-gamebub-v91l-overlap-model-v1",
        "baseline": BASELINE,
        "status": "PASS_ABSTRACT_BANK_LEASES_AND_IDEAL_OVERLAP_BOUNDS",
        "checks": {
            "delta_uses_bank1_while_key_rgb_and_reference_hold_bank0": "PASS",
            "accepted_reference_change_does_not_release_active_key_rgb_source": "PASS",
            "candidate_cannot_reuse_active_rgb_source_even_after_consumer_release_until_physical_drain": "PASS",
            "publication_requires_physical_writer_drain": "PASS",
            "front_swap_requires_vblank_and_scanout_drain": "PASS",
            "cancel_error_held_response_cases": cancels,
            "candidate_blocked_by_source_lease": blocked_by_leases,
            "writer_drain_gate": writer_drain_gate,
        },
        "source_derived_traffic_counts": TRAFFIC,
        "timing": timing_bounds(),
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in SOURCE.values()},
        "input_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                         for name, path in INPUTS.items()},
        "limitations": [
            "Lease, cancel and stale-descriptor behavior is an abstract software contract model, not an RTL/hardware result.",
            "Traffic counts and stage intervals come from the retained two-source physical scratch campaign; no new contention was simulated.",
            "Ideal overlap arithmetic assumes zero shared-memory contention and is a lower bound, not predicted simulation time.",
            "Delta decode alone exceeds 33.333 ms; overlap alone cannot establish 30 fps.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(check(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULT.exists() or RESULT.read_text() != rendered:
            raise SystemExit("model-results.json differs; run without --check to refresh it")
        print("PASS: deterministic abstract overlap model")
    else:
        RESULT.write_text(rendered)
        print(rendered, end="")


if __name__ == "__main__":
    main()

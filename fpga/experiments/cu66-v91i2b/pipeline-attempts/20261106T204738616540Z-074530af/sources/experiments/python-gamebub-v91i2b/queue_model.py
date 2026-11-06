#!/usr/bin/env python3
"""Bounded abstract V91i2b registered-read refill queue ownership model.

This is a Python port model, not an RTL proof or a hardware performance model.
It consumes already-pinned packet/span bytes and checks byte/epoch ownership
under child backpressure. It does not decode BR88 or produce new vectors.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "experiments/python-gamebub-v91i2/vectors"
OUT = Path(__file__).resolve().parent / "queue-results.json"
DEPTH = 2


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Refill:
    """Two byte slots plus one registered response reservation (total <= 2)."""

    def __init__(self, payload: bytes, base: int, frame_epoch: int,
                 child_epoch: int, mode: int):
        assert mode in (0, 1)
        self.payload, self.base, self.frame_epoch = payload, base, frame_epoch
        self.child_epoch, self.mode = child_epoch, mode
        self.queue: list[dict | None] = [None] * DEPTH
        self.head = self.tail = self.count = 0
        self.pending: dict | None = None
        self.issued = self.sent = self.cycles = 0
        self.out: list[dict] = []
        self.max_owners = self.max_queued = self.max_pending = 0
        self.stall_cycles = self.full_cycles = self.simultaneous = 0
        self.request_cycles = self.response_cycles = self.pop_cycles = 0
        self.max_head_hold = 0
        self._held_head: dict | None = None
        self._held_cycles = 0
        self.phase = "REQ"  # mode-0 REQ/WAIT/SEND controller
        self.waiting: dict | None = None
        self.send: dict | None = None

    def _assert_state(self):
        assert 0 <= self.count <= DEPTH
        assert self.count + (self.pending is not None) <= DEPTH
        assert self.issued <= len(self.payload)
        assert self.sent <= self.issued
        assert sum(x is not None for x in self.queue) == self.count
        if self.count:
            head = self.queue[self.head]
            assert head is not None
            assert head["addr"] == self.base + self.sent
            assert head["frame_epoch"] == self.frame_epoch
            assert head["child_epoch"] == self.child_epoch

    def cycle(self, child_ready: bool, action: str = "run") -> bool:
        """Apply one rising edge; action is run, cancel, or reset.

        Return True if the chunk drained on this edge. Reset/cancel invalidate
        local pending and queued ownership. They do not model external ACKs.
        """
        assert action in ("run", "cancel", "reset", "failure")
        self.cycles += 1
        if action in ("cancel", "reset", "failure"):
            self.queue = [None] * DEPTH
            self.head = self.tail = self.count = 0
            self.pending = self.waiting = self.send = None
            self.phase = "REQ"
            self._held_head = None
            self._held_cycles = 0
            self.cancelled = True
            self.failed = action == "failure"
            self._assert_state()
            return False
        if getattr(self, "cancelled", False):
            return False

        if self.mode == 1:
            pop = self.count > 0 and child_ready
            old_pending = self.pending
            push = old_pending is not None
            if self.count + int(self.pending is not None) == DEPTH:
                self.full_cycles += 1
            if self.count and not child_ready:
                self.stall_cycles += 1
                head = self.queue[self.head]
                if self._held_head is None:
                    self._held_head = dict(head)
                    self._held_cycles = 1
                else:
                    assert head == self._held_head, "valid head changed while child stalled"
                    self._held_cycles += 1
                    self.max_head_hold = max(self.max_head_hold, self._held_cycles)
            else:
                self._held_head = None
                self._held_cycles = 0

            # Reserve before issuing. A same-edge pop grants one credit;
            # response push consumes the old pending owner's reserved credit.
            issue = (self.issued < len(self.payload) and
                     self.count + int(self.pending is not None) - int(pop) < DEPTH)
            if push:
                assert old_pending["frame_epoch"] == self.frame_epoch
                assert old_pending["child_epoch"] == self.child_epoch
                assert old_pending["addr"] == self.base + self.sent + self.count
                assert old_pending["addr"] < self.base + len(self.payload)
                self.queue[self.tail] = old_pending
                self.tail = (self.tail + 1) % DEPTH
                self.response_cycles += 1
            if pop:
                popped = self.queue[self.head]
                assert popped is not None
                self.queue[self.head] = None
                self.head = (self.head + 1) % DEPTH
                self.sent += 1
                self.out.append(popped)
                self.pop_cycles += 1
            if issue:
                addr = self.base + self.issued
                assert addr < self.base + len(self.payload), "overread"
                self.pending = {"addr": addr, "byte": self.payload[self.issued],
                                "last": self.issued == len(self.payload) - 1,
                                "frame_epoch": self.frame_epoch,
                                "child_epoch": self.child_epoch}
                self.issued += 1
                self.request_cycles += 1
            else:
                self.pending = None
            if pop and push:
                self.simultaneous += 1
            self.count += int(push) - int(pop)
            # Pointer updates plus the operations above model atomic ring updates.
            self.max_queued = max(self.max_queued, self.count)
            self.max_pending = max(self.max_pending, int(self.pending is not None))
            self.max_owners = max(self.max_owners, self.count + int(self.pending is not None))
        else:
            # Frozen abstract control: REQ captures one address, WAIT accepts
            # its one-edge response, SEND holds the byte through child stall.
            if self.phase == "REQ" and self.issued < len(self.payload):
                self.waiting = {"addr": self.base + self.issued,
                                "byte": self.payload[self.issued],
                                "last": self.issued == len(self.payload) - 1,
                                "frame_epoch": self.frame_epoch,
                                "child_epoch": self.child_epoch}
                self.issued += 1
                self.phase = "WAIT"
                self.request_cycles += 1
            elif self.phase == "WAIT":
                assert self.waiting is not None
                self.send = self.waiting
                self.waiting = None
                self.phase = "SEND"
                self.response_cycles += 1
            elif self.phase == "SEND":
                if child_ready:
                    assert self.send is not None
                    self.out.append(self.send)
                    self.send = None
                    self.sent += 1
                    self.phase = "REQ"
                    self.pop_cycles += 1
                else:
                    self.stall_cycles += 1
            self.max_owners = max(self.max_owners,
                                  int(self.waiting is not None) + int(self.send is not None))

        self._assert_state()
        return (self.sent == len(self.payload) and self.count == 0 and
                self.pending is None and self.send is None and self.waiting is None)


def expected_records(payload: bytes, base: int, frame_epoch: int,
                     child_epoch: int) -> list[dict]:
    return [{"addr": base + i, "byte": b, "last": i == len(payload) - 1,
             "frame_epoch": frame_epoch, "child_epoch": child_epoch}
            for i, b in enumerate(payload)]


def run(payload: bytes, base: int, frame_epoch: int, child_epoch: int,
        mode: int, ready_fn, action_fn=lambda cycle: "run") -> dict:
    m = Refill(payload, base, frame_epoch, child_epoch, mode)
    bound = len(payload) * 8 + 64
    completed = False
    for c in range(bound):
        if m.cycle(bool(ready_fn(c)), action_fn(c)):
            completed = True
            break
        if getattr(m, "cancelled", False):
            break
    assert completed or getattr(m, "cancelled", False), "bounded trace did not terminate"
    if completed:
        assert m.out == expected_records(payload, base, frame_epoch, child_epoch)
        assert m.sent == m.issued == len(payload)
        assert all(row["last"] == (i == len(payload) - 1) for i, row in enumerate(m.out))
    return {"completed": completed, "cycles": m.cycles, "sent": m.sent,
            "issued": m.issued, "max_total_owners": m.max_owners,
            "max_fifo_occupancy": m.max_queued, "max_pending_owner": m.max_pending,
            "stall_cycles": m.stall_cycles, "full_owner_cycles": m.full_cycles,
            "simultaneous_pop_push": m.simultaneous,
            "requests": m.request_cycles, "responses": m.response_cycles,
            "pops": m.pop_cycles,
            "output_sha256": sha(bytes(r["byte"] for r in m.out)) if completed else None,
            "cancelled": getattr(m, "cancelled", False)}


def read_vectors():
    manifest = json.loads((VECTORS / "manifest.json").read_text())
    tsv = VECTORS / "cases.tsv"
    assert sha(tsv.read_bytes()) == manifest["tsv"]["sha256"]
    by_id = {case["id"]: case for case in manifest["cases"]}
    cases = {}
    csv.field_size_limit(sys.maxsize)
    with tsv.open(newline="") as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row:
                continue
            ident = row[0]
            meta = by_id[ident]
            packet = bytes.fromhex(row[2])
            assert len(packet) == meta["packet_bytes"] and sha(packet) == meta["packet_sha256"]
            spans = []
            for s in meta["spans"]:
                payload = packet[s["offset"]:s["offset"] + s["length"]]
                assert len(payload) == s["length"] and sha(payload) == s["sha256"]
                spans.append({"axis": s["axis"], "chunk": s["chunk"],
                              "offset": s["offset"], "length": s["length"],
                              "bytes": payload, "sha256": s["sha256"]})
            cases[ident] = {"meta": meta, "spans": spans}
    assert set(cases) == set(by_id) and len(cases) == 11
    return manifest, cases


def ready_schedule(case: str, axis: int):
    # Force an initial full queue, then repeatable short stalls. This schedule
    # is synthetic backpressure, not a measured memory or child service rate.
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(case)) + axis * 17
    def ready(cycle):
        if cycle < 7:
            return False
        return ((cycle * 13 + seed) % 11) not in (0, 1, 2)
    return ready


def exhaustive_small():
    traces = 0
    worst_owners = 0
    for n in range(0, 5):
        payload = bytes((0x31 + 29 * i) & 255 for i in range(n))
        for ready_bits in itertools.product((False, True), repeat=8):
            schedule = lambda c, rb=ready_bits: rb[c] if c < len(rb) else True
            for mode in (0, 1):
                result = run(payload, 37, 9, 4, mode, schedule)
                assert result["completed"] and result["sent"] == n
                assert result["max_total_owners"] <= (2 if mode else 1)
                if mode:
                    assert result["max_fifo_occupancy"] <= 2
                    assert result["max_total_owners"] <= 2
                worst_owners = max(worst_owners, result["max_total_owners"])
                traces += 1
    return {"trace_count": traces, "payload_lengths": [0, 1, 2, 3, 4],
            "ready_bits_per_trace": 8, "modes": [0, 1],
            "max_total_owners_seen": worst_owners}


def directed_ownership():
    # Fill both reserved slots, hold the head, then do a full pop+push+issue.
    payload = bytes([0xA1, 0xB2, 0xC3, 0xD4])
    m = Refill(payload, 100, 22, 7, 1)
    m.cycle(False)  # issue address 100
    m.cycle(False)  # push 100, issue 101
    m.cycle(False)  # push 101, now full and held
    assert m.count == 2 and m.pending is None
    before = dict(m.queue[m.head])
    m.cycle(False)
    assert m.queue[m.head] == before
    m.cycle(True)  # pop 100, then refill and reserve next address
    for _ in range(24):
        if m.cycle(True):
            break
    assert m.out == expected_records(payload, 100, 22, 7)
    assert m.simultaneous > 0 and m.max_owners == 2

    cancellations = []
    for cancel_after in (1, 2, 3):
        c = Refill(bytes([1, 2, 3]), 200, 31, 8, 1)
        for _ in range(cancel_after):
            c.cycle(False)
        owned_before = c.count + int(c.pending is not None)
        c.cycle(False, "cancel")
        assert c.count == 0 and c.pending is None and c.sent == 0
        # A replacement starts with a fresh epoch and cannot inherit old owners.
        replacement = run(bytes([9, 8]), 300, 32, 9, 1, lambda _: True)
        assert replacement["completed"] and replacement["sent"] == 2
        cancellations.append({"cancel_cycle": cancel_after + 1,
                              "owners_invalidated": owned_before,
                              "replacement_epoch": 32, "replacement_child_epoch": 9})
    r = Refill(bytes([5, 6]), 400, 41, 10, 1)
    r.cycle(False)
    r.cycle(False, "reset")
    assert r.count == 0 and r.pending is None
    f = Refill(bytes([7, 8]), 500, 51, 11, 1)
    f.cycle(False)
    f.cycle(False, "failure")
    assert f.count == 0 and f.pending is None and f.failed
    return {"full_queue_stall_head_stable": True,
            "simultaneous_pop_push_issue_ordered": True,
            "cancel_reset_and_failure_clear_local_owners": True,
            "replacement_epochs_reject_old_local_ownership": True,
            "cancellation_positions": cancellations}


def main():
    _, cases = read_vectors()
    case_rows = []
    for ident, data in cases.items():
        meta = data["meta"]
        # Early rejects and zero-job frames issue no refill reads.
        admitted = bool(meta["all_br88"] and meta["expected_error"] == 0 and data["spans"])
        span_rows = []
        if admitted:
            for span in data["spans"]:
                pair = {}
                for mode in (0, 1):
                    result = run(span["bytes"], span["offset"], meta["fid"],
                                 span["axis"] * 256 + span["chunk"] + 1, mode,
                                 ready_schedule(ident, span["axis"]))
                    assert result["completed"] and result["output_sha256"] == span["sha256"]
                    pair[f"mode{mode}"] = result
                assert pair["mode0"]["sent"] == pair["mode1"]["sent"] == span["length"]
                span_rows.append({"axis": span["axis"], "chunk": span["chunk"],
                                  "address": span["offset"], "bytes": span["length"],
                                  "source_sha256": span["sha256"], "modes": pair})
        case_rows.append({"id": ident, "packet_bytes": meta["packet_bytes"],
                          "expected_error": meta["expected_error"],
                          "all_br88": meta["all_br88"], "admitted_refill": admitted,
                          "spans": span_rows,
                          "read_requests": sum(s["length"] for s in data["spans"]) if admitted else 0,
                          "emitted_bytes": sum(s["length"] for s in data["spans"]) if admitted else 0})
    admitted_spans = [s for c in case_rows for s in c["spans"]]
    totals = {}
    for mode in (0, 1):
        mr = [s["modes"][f"mode{mode}"] for s in admitted_spans]
        totals[f"mode{mode}"] = {
            "bytes_requested": sum(x["requests"] for x in mr),
            "bytes_responded": sum(x["responses"] for x in mr),
            "bytes_emitted": sum(x["pops"] for x in mr),
            "cycles": sum(x["cycles"] for x in mr),
            "child_stall_cycles": sum(x["stall_cycles"] for x in mr),
            "full_owner_cycles": sum(x["full_owner_cycles"] for x in mr),
            "peak_total_owners": max((x["max_total_owners"] for x in mr), default=0),
            "peak_fifo_occupancy": max((x["max_fifo_occupancy"] for x in mr), default=0),
            "simultaneous_pop_push": sum(x["simultaneous_pop_push"] for x in mr),
        }
    vectors = VECTORS
    result = {
        "schema": "v91i2b-byte-queue-ownership-model-v1",
        "status": "PASS",
        "scope": ["Independent abstract Python port model; not RTL proof or hardware performance.",
                  "Reuses pinned V91i2 vectors and exact span bytes; no entropy codec or new frame goldens.",
                  "Mode 0 abstracts frozen REQ/WAIT/SEND; mode 1 models two FIFO byte slots plus one registered-response owner with total reservation <=2.",
                  "One-edge response, no bypass, exact address/frame epoch/child epoch/last ownership; child ready schedule is deterministic synthetic backpressure.",
                  "Cancellation/reset clear modeled local queue and response ownership; external accepted scratch ACK ownership is outside this byte refill model."],
        "pins": {"manifest_sha256": sha((vectors / "manifest.json").read_bytes()),
                 "cases_tsv_sha256": sha((vectors / "cases.tsv").read_bytes()),
                 "case_count": len(cases)},
        "protocol": {"mode0": "frozen REQ/WAIT/SEND byte service", "mode1_fifo_slots": 2,
                     "mode1_registered_pending_slots": 1, "mode1_total_owners_bound": 2,
                     "response_latency_edges": 1, "bypass": False,
                     "issue_rule": "issued < chunk_length and count + pending - pop < 2",
                     "pop_rule": "count > 0 and child_ready",
                     "push_rule": "old pending response, after address and epoch verification"},
        "case_rows": case_rows,
        "totals": totals,
        "exhaustive_small_traces": exhaustive_small(),
        "directed": directed_ownership(),
        "claims": {"exact_output_bytes_checked": True, "exact_addresses_checked": True,
                   "exact_last_position_checked": True, "frame_and_child_epochs_checked": True,
                   "queue_head_stable_while_stalled": True, "overread_checked": True,
                   "request_response_pop_conservation_checked": True,
                   "hardware_performance_claim": False, "rtl_proof_claim": False},
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS", result["pins"]["case_count"], "cases",
          len(admitted_spans), "admitted spans",
          result["exhaustive_small_traces"]["trace_count"], "symbolic traces")


if __name__ == "__main__":
    main()

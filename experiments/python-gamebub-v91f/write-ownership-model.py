#!/usr/bin/env python3
"""Abstract two-line write ownership model for the V91f overlap contract.

This models ownership events, not RTL states, cycle timing, or performance.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "experiments/python-gamebub-v91f/write-ownership-results.json"


@dataclass(frozen=True)
class Line:
    epoch: int
    address: int
    tag: int
    kind: str = "data"  # data or descriptor


@dataclass(frozen=True)
class State:
    epoch: int = 1
    active: bool = True
    failed: bool = False
    assembler: Line | None = None
    slot: Line | None = None  # offered or accepted; immutable while owned
    accepted: bool = False
    slot_valid: bool = False  # local request-valid; may clear while physical owner drains
    committed: tuple[Line, ...] = ()
    next_data_address: int = 0
    seal_requested: bool = False
    descriptors_enqueued: int = 0
    descriptors_acked: int = 0
    sealed: bool = False
    read_started: bool = False
    cancelled: bool = False
    stale_acks: int = 0


def invariant(s: State) -> None:
    owned = int(s.assembler is not None) + int(s.slot is not None)
    assert owned <= 2, "more than two 16-byte payload owners"
    assert not s.accepted or s.slot is not None, "accepted request has no immutable physical owner"
    assert s.slot is not None or not s.slot_valid, "valid offered slot has no payload owner"
    assert not s.sealed or (not s.active and s.seal_requested and s.descriptors_acked == 2 and not s.failed), "early or failed publication barrier"
    assert not s.read_started or s.sealed, "read before successful seal"
    ordered = [(x.epoch, x.address) for x in s.committed]
    assert ordered == sorted(ordered) and len(ordered) == len(set(ordered)), "commit order/uniqueness"
    if s.slot is not None and s.accepted:
        assert not any((x.epoch, x.address) == (s.slot.epoch, s.slot.address)
                       for x in s.committed), "accepted write committed before ACK"


def transitions(s: State):
    """Yield (event, next_state); ineligible events are absent, not simulated as FSM states."""
    # Fill the second line owner with one complete immutable payload.
    if s.active and not s.failed and s.assembler is None and s.next_data_address < 2:
        n = s.next_data_address
        line = Line(s.epoch, n * 16, 100 + n)
        yield f"enqueue_data(addr={line.address},tag={line.tag})", replace(
            s, assembler=line, next_data_address=n + 1
        )
    # Transfer assembler ownership into the single write slot; the external
    # request remains merely offered until an explicit acceptance event.
    if s.active and not s.failed and s.slot is None and s.assembler is not None:
        yield "offer_assembler", replace(s, slot=s.assembler, assembler=None, accepted=False, slot_valid=True)
    if s.active and not s.failed and s.slot is not None and s.slot_valid and not s.accepted:
        yield "accept_request", replace(s, accepted=True)
    # Wrong-epoch responses are observable errors but cannot retire ownership.
    if s.slot is not None and s.accepted:
        yield "ack_wrong_epoch", replace(s, failed=True, assembler=None, slot_valid=False,
                                     stale_acks=s.stale_acks + 1)
        line = s.slot
        rest = replace(s, slot=None, accepted=False, slot_valid=False, committed=s.committed + (line,))
        if line.kind == "descriptor":
            rest = replace(rest, descriptors_acked=rest.descriptors_acked + 1)
        yield "ack_match_ok", rest
        if s.active and not s.failed and s.assembler is not None:
            combined = replace(s, slot=s.assembler, assembler=None, accepted=False,
                               committed=s.committed + (line,))
            if line.kind == "descriptor":
                combined = replace(combined, descriptors_acked=combined.descriptors_acked + 1)
            combined = replace(combined, slot_valid=True)
            yield "ack_match_ok_and_enqueue", combined
        yield "ack_match_error", replace(s, slot=None, accepted=False, slot_valid=False,
                                           assembler=None, failed=True)
    # Abort/reset drops only local, not externally accepted, ownership.
    if s.active or s.failed:
        if s.slot is None or not s.accepted:
            yield "abort_or_reset", replace(s, active=False, failed=False, assembler=None, slot=None,
                                             accepted=False, slot_valid=False, cancelled=True)
        else:
            yield "abort_or_reset", replace(s, active=False, failed=False, assembler=None, slot_valid=False, cancelled=True)
    # A replacement can start only after an accepted old request drains.
    if not s.active and not s.failed and s.slot is None and not s.accepted and not s.slot_valid:
        yield "replace_epoch", replace(s, epoch=s.epoch + 1, active=True, assembler=None,
                                         slot=None, accepted=False, next_data_address=0,
                                         seal_requested=False, descriptors_enqueued=0, descriptors_acked=0,
                                         sealed=False, slot_valid=False, read_started=False, cancelled=False)
    # The input seal request follows all data ACKs. Its accepted side effect is
    # represented by two sequential, physically acknowledged descriptor writes.
    if (s.active and not s.failed and not s.seal_requested and s.slot is None
            and s.assembler is None and s.next_data_address == 2
            and len([x for x in s.committed if x.epoch == s.epoch and x.kind == "data"]) == 2):
        yield "seal_request", replace(s, seal_requested=True)
    if (s.active and not s.failed and s.seal_requested and s.descriptors_enqueued < 2
            and s.slot is None and s.assembler is None):
        n = s.descriptors_enqueued
        desc = Line(s.epoch, 32 + n * 16, 900 + s.epoch * 2 + n, "descriptor")
        yield f"enqueue_descriptor(index={n},addr={desc.address})", replace(
            s, assembler=desc, descriptors_enqueued=n + 1)
    if (s.active and not s.failed and s.seal_requested and s.descriptors_enqueued == 2
            and s.descriptors_acked == 2 and s.slot is None and s.assembler is None):
        yield "sealed_publication_barrier", replace(s, active=False, sealed=True)
    # A stale abort from an older transaction is ignored without changing any owner.
    if s.epoch > 1:
        yield "stale_abort(prior_epoch)", s
    if s.sealed and not s.read_started:
        yield "read", replace(s, read_started=True)


def check_transition(before: State, event: str, after: State) -> None:
    invariant(after)
    if before.slot is not None and event not in {"ack_match_ok", "ack_match_error", "ack_match_ok_and_enqueue"} \
            and not (event == "abort_or_reset" and not before.accepted):
        assert after.slot == before.slot, "offered/accepted request payload or address changed while owned"
    if event.startswith("enqueue_data"):
        assert after.assembler is not None
        assert after.assembler.address == before.next_data_address * 16
    if event.startswith("enqueue_descriptor"):
        current = [x for x in before.committed if x.epoch == before.epoch]
        data = [x for x in current if x.kind == "data"]
        descriptors = [x for x in current if x.kind == "descriptor"]
        index = int(event.split("index=")[1].split(",")[0])
        assert len(data) == 2 and len(descriptors) == index
    if event == "accept_request":
        assert before.slot == after.slot and after.slot is not None
    if event == "offer_assembler":
        assert after.slot == before.assembler and after.slot_valid and not after.accepted
    if event == "ack_match_ok_and_enqueue":
        assert before.accepted and before.slot is not None and before.assembler is not None
        assert after.slot == before.assembler and after.assembler is None and not after.accepted
        assert after.committed == before.committed + (before.slot,)
    if event == "ack_wrong_epoch":
        assert before.slot == after.slot and before.accepted == after.accepted
        assert after.assembler is None and not after.slot_valid
    if event == "stale_abort(prior_epoch)":
        assert before.epoch > 1 and after == before
    if event == "abort_or_reset" and before.accepted:
        assert after.slot == before.slot and after.accepted and not after.slot_valid
    if event.startswith("replace_epoch"):
        assert before.slot is None and not before.accepted
    if event == "seal_request":
        assert before.next_data_address == 2 and before.slot is None and before.assembler is None
    if event == "sealed_publication_barrier":
        assert before.seal_requested and before.descriptors_acked == 2 and before.slot is None and before.assembler is None
    if event == "read":
        assert before.sealed


def exhaustive(max_depth: int = 20) -> dict:
    start = State()
    queue = deque([(start, ())])
    seen = {start: 0}
    transitions_checked = 0
    event_coverage: set[str] = set()
    shortest: dict[str, list[str]] = {}
    while queue:
        state, trace = queue.popleft()
        if len(trace) >= max_depth:
            continue
        for event, nxt in transitions(state):
            check_transition(state, event, nxt)
            transitions_checked += 1
            event_coverage.add(event.split("(")[0])
            if nxt.stale_acks and "ack_wrong_epoch" not in shortest:
                shortest["ack_wrong_epoch"] = list(trace + (event,))
            depth = len(trace) + 1
            if nxt not in seen or depth < seen[nxt]:
                seen[nxt] = depth
                queue.append((nxt, trace + (event,)))
    required = {"enqueue_data", "offer_assembler", "accept_request", "ack_wrong_epoch",
                "ack_match_ok", "ack_match_ok_and_enqueue", "ack_match_error", "abort_or_reset", "replace_epoch",
                "enqueue_descriptor", "seal_request", "sealed_publication_barrier", "stale_abort", "read"}
    assert required <= event_coverage, f"missing bounded event coverage: {required-event_coverage}"
    return {"max_depth": max_depth, "unique_states": len(seen),
            "transitions_checked": transitions_checked,
            "event_coverage": sorted(event_coverage),
            "shortest_stale_response_trace": shortest["ack_wrong_epoch"]}


def seeded_scenario(seed: int = 910436, steps: int = 2500) -> dict:
    """Long reproducible event walk; prefers making progress, injects stale replies/abort."""
    rng = random.Random(seed)
    s = State()
    counts: dict[str, int] = {}
    max_owners = 0
    for _ in range(steps):
        options = [(e, n) for e, n in transitions(s) if not e.startswith("stale_abort")]
        if not options:
            # Restart after a successful sealed/read transaction as a replacement epoch.
            s = replace(s, active=False, sealed=False, read_started=False,
                        seal_requested=False, descriptors_acked=0, descriptors_enqueued=0,
                        slot_valid=False, next_data_address=2, failed=False, slot=None, accepted=False,
                        assembler=None)
            options = [(e, n) for e, n in transitions(s) if not e.startswith("stale_abort")]
            if not options:
                break
        # Favor forward work while retaining a stable seeded mix of abort/error races.
        weights = [8 if e.split("(")[0] in {"enqueue_data", "offer_assembler",
                   "accept_request", "ack_match_ok", "enqueue_descriptor", "seal_request",
                   "sealed_publication_barrier", "read",
                   "replace_epoch"} else 1 for e, _ in options]
        event, nxt = rng.choices(options, weights=weights, k=1)[0]
        check_transition(s, event, nxt)
        counts[event.split("(")[0]] = counts.get(event.split("(")[0], 0) + 1
        s = nxt
        max_owners = max(max_owners, int(s.assembler is not None) + int(s.slot is not None))
    return {"seed": seed, "requested_steps": steps, "events_executed": sum(counts.values()),
            "event_counts": dict(sorted(counts.items())), "max_payload_owners": max_owners}


def directed_checks() -> dict:
    s = State()
    trace: list[str] = []
    wanted = ["enqueue_data", "offer_assembler", "accept_request", "enqueue_data",
              "abort_or_reset", "ack_wrong_epoch", "ack_match_ok", "abort_or_reset", "replace_epoch"]
    for prefix in wanted:
        match = next(((e, n) for e, n in transitions(s) if e.split("(")[0] == prefix), None)
        assert match is not None, f"directed event unavailable: {prefix}"
        event, nxt = match
        check_transition(s, event, nxt)
        trace.append(event)
        s = nxt
        if prefix == "abort_or_reset" and s.slot is not None:
            assert s.accepted and s.assembler is None
            assert not any(e.startswith("replace_epoch") for e, _ in transitions(s))
        if prefix == "ack_wrong_epoch":
            assert s.slot is not None and s.accepted
    assert s.active and s.epoch == 2 and s.slot is None
    stale, after_stale = next((e, n) for e, n in transitions(s) if e.startswith("stale_abort"))
    check_transition(s, stale, after_stale)
    t = State()
    race_trace: list[str] = []
    for prefix in ["enqueue_data", "offer_assembler", "accept_request", "enqueue_data"]:
        event, t = next((e, n) for e, n in transitions(t) if e.split("(")[0] == prefix)
        race_trace.append(event)
    assert not any(e == "seal_request" for e, _ in transitions(t)), "seal was offered while request pending"
    combined, t = next((e, n) for e, n in transitions(t) if e == "ack_match_ok_and_enqueue")
    check_transition(State(epoch=1, next_data_address=2, slot=Line(1, 0, 100),
                           accepted=True, assembler=Line(1, 16, 101)), combined, t)
    race_trace.append(combined)
    assert t.slot == Line(1, 16, 101) and t.committed == (Line(1, 0, 100),)
    stale_state = State(epoch=1, next_data_address=2, slot=Line(1, 0, 100),
                        accepted=True, slot_valid=True, assembler=Line(1, 16, 101))
    stale_event, stale_next = next((e, n) for e, n in transitions(stale_state)
                                   if e == "ack_wrong_epoch")
    check_transition(stale_state, stale_event, stale_next)
    assert stale_next.slot == stale_state.slot and stale_next.accepted
    assert not stale_next.slot_valid and stale_next.assembler is None
    u = State()
    for prefix in ["enqueue_data", "offer_assembler", "accept_request", "enqueue_data"]:
        event, u = next((e, n) for e, n in transitions(u) if e.split("(")[0] == prefix)
    err, u = next((e, n) for e, n in transitions(u) if e == "ack_match_error")
    check_transition(State(epoch=1, next_data_address=2, slot=Line(1, 0, 100),
                           accepted=True, assembler=Line(1, 16, 101)), err, u)
    assert u.slot is None and u.assembler is None and u.failed
    assert not any(e == "ack_match_ok_and_enqueue" for e, _ in transitions(
        State(epoch=1, failed=True, next_data_address=2, slot=Line(1, 0, 100),
              accepted=True, assembler=Line(1, 16, 101))))
    return {"checks": 10, "trace": trace, "ack_enqueue_race_trace": race_trace,
            "confirmed": ["second line fills while first accepted", "abort cancels assembler but retains accepted owner",
                          "wrong-epoch response clears local owners but cannot retire physical owner",
                          "replacement waits for matching ACK",
                          "matching ACK can retire old slot and transfer next assembled line atomically",
                          "error ACK has priority and cancels assembler ownership",
                          "seal request is unavailable while a data write is pending",
                          "stale abort from prior epoch leaves replacement untouched"]}


def main() -> None:
    exhaustive_result = exhaustive()
    scenario = seeded_scenario()
    directed = directed_checks()
    source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {"schema": "v91f-write-ownership-results-v1",
              "model_scope": "abstract two-data/two-descriptor ownership; seal_request maps input seal handshake and sealed_publication_barrier maps descriptor-ACK/read fence; producer-side semantic-failure cause omitted; not RTL/performance/hardware proof",
              "source_sha256": source_sha256,
              "exhaustive": exhaustive_result,
              "directed_checks": directed,
              "seeded_scenario": scenario,
              "invariants": ["at most two 16-byte payload owners", "offered/accepted slot payload immutable",
                             "accepted physical owner retires only on matching ACK, even when local slot_valid is clear",
                             "successful ACK may atomically transfer the next assembled line",
                             "wrong-epoch ACK clears local slot-valid/assembler but cannot retire pending physical owner",
                             "error ACK clears unaccepted local ownership",
                             "abort/reset preserves accepted physical owner while clearing local slot_valid",
                             "stale prior-epoch abort is ignored", "commits follow increasing line address",
                             "input seal request follows data ACKs and final barrier follows both descriptor ACKs",
                             "read follows final sealed/publication barrier"]}
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

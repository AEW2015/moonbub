#!/usr/bin/env python3
"""Bounded abstract ownership checks for the V91g read-prefetch contract.

This explores ownership events, not RTL states, cycles, timing, or performance.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "experiments/python-gamebub-v91g/prefetch-ownership-results.json"
SEED = 910437


@dataclass(frozen=True)
class Snapshot:
    epoch: int
    segment: int
    address: int
    tag: int


@dataclass(frozen=True)
class CacheLine:
    epoch: int
    segment: int
    address: int
    tag: int


@dataclass(frozen=True)
class State:
    epoch: int = 1
    segment: int = 0
    sealed: bool = False
    segment_cache: CacheLine = CacheLine(1, 0, 0, 100)
    cache_consumed: bool = False
    dense_value: int = 100
    dense_hold: bool = False
    offered: Snapshot | None = None
    physical_owner: Snapshot | None = None
    local_valid: bool = False
    failed: bool = False
    cancelled: bool = False
    done: bool = False
    wrong_responses: int = 0
    error_responses: int = 0
    fills: int = 0


def invariant(s: State) -> None:
    assert not (s.offered is not None and s.physical_owner is not None), "one external read at a time"
    assert s.offered is not None or s.physical_owner is not None or not s.local_valid, "local fill intent needs an offer or owner"
    if s.offered is not None:
        assert s.local_valid, "offered request lost local valid before acceptance"
    assert s.segment in (0, 1), "bounded segment identifier"
    assert s.segment_cache.address in (0, 16), "bounded line address"
    assert s.dense_value >= 0
    if s.done:
        assert s.sealed and not s.failed and not s.cancelled and not s.dense_hold
        assert s.offered is None and s.physical_owner is None and not s.local_valid
    assert s.segment_cache.epoch == s.epoch, "cache bank belongs to current epoch"
    if s.failed or s.cancelled:
        assert not s.local_valid, "failed/cancelled prefetch must not be locally fillable"


def transitions(s: State):
    """Yield eligible abstract event and resulting state."""
    if s.done:
        return
    # A sealed transaction permits one next-line read offer. Snapshot includes
    # all identity fields and is immutable through ready-low and acceptance.
    target_addr = s.segment_cache.address + 16
    if (s.sealed and not s.failed and not s.cancelled and not s.done and s.cache_consumed
            and s.offered is None and s.physical_owner is None and target_addr <= 16):
        snap = Snapshot(s.epoch, s.segment, target_addr, 200 + s.epoch + s.segment)
        yield "offer_prefetch", replace(s, offered=snap, local_valid=True)
    if s.offered is not None and s.physical_owner is None and s.local_valid:
        yield "accept_read", replace(s, physical_owner=s.offered, offered=None)
    # A wrong-epoch response cannot retire the physical owner. A matching
    # error ACK below is a physical completion fence but never fills data.
    if s.physical_owner is not None:
        yield "response_wrong_epoch", replace(s, local_valid=False, failed=True,
                                                 wrong_responses=s.wrong_responses + 1)
        # A matching error ACK ends physical ownership but never fills data.
        yield "ack_match_error", replace(s, physical_owner=None, local_valid=False,
                                            failed=True, error_responses=s.error_responses + 1)
        if s.dense_hold:
            yield "ack_error_priority_over_output", replace(
                s, physical_owner=None, local_valid=False, failed=True,
                error_responses=s.error_responses + 1
            )
        owner = s.physical_owner
        if not s.failed and not s.cancelled and s.local_valid and (owner.epoch, owner.segment, owner.address) == (
            s.epoch, s.segment, target_addr
        ):
            line = CacheLine(owner.epoch, owner.segment, owner.address, owner.tag)
            yield "ack_match_fill", replace(s, physical_owner=None, local_valid=False,
                                               segment_cache=line, cache_consumed=False,
                                               fills=s.fills + 1)
        else:
            yield "ack_match_drain", replace(s, physical_owner=None, local_valid=False)
        if s.dense_hold and s.local_valid and not s.failed and not s.cancelled:
            line = CacheLine(owner.epoch, owner.segment, owner.address, owner.tag)
            yield "ack_during_dense_hold", replace(s, physical_owner=None, local_valid=False,
                                                        segment_cache=line, cache_consumed=False,
                                                        fills=s.fills + 1)
    # Cancel/abort drops unaccepted local work. Accepted requests keep the
    # physical owner alive and block replacement until matching drain ACK.
    if not s.cancelled and not s.failed:
        if s.physical_owner is None:
            yield "abort_reset_unaccepted", replace(s, offered=None, local_valid=False,
                                                       cancelled=True, dense_hold=False)
        else:
            yield "abort_reset_accepted", replace(s, offered=None, local_valid=False,
                                                     cancelled=True, dense_hold=False)
    # Dense output is a separately latched scalar/tile payload. The existing
    # segment cache may be replaced only after its old line is consumed.
    if not s.cache_consumed and not s.failed and not s.cancelled:
        yield "consume_segment_cache", replace(s, cache_consumed=True)
    if not s.dense_hold and not s.failed and not s.cancelled:
        yield "dense_hold", replace(s, dense_value=s.dense_value, dense_hold=True)
    if s.dense_hold:
        yield "dense_release", replace(s, dense_hold=False)
    if (s.sealed and not s.failed and not s.cancelled and not s.dense_hold
            and s.offered is None and s.physical_owner is None and not s.done):
        yield "dense_complete", replace(s, done=True)
    # A response may arrive concurrently with an output hold. It writes the
    # existing segment cache after consumption; output remains independently
    # pinned to dense_value.
    # (Combined event is emitted above as ack_during_dense_hold.)
    # Model bank replacement as an event offered by a caller. It is eligible
    # only after any accepted physical owner has drained and local work is gone.
    if (s.physical_owner is None and s.offered is None and not s.local_valid and not s.dense_hold
            and (s.cancelled or s.failed)):
        next_epoch = s.epoch + 1
        next_segment = 1 - s.segment
        yield "replace_bank", replace(s, epoch=next_epoch, segment=next_segment,
                                        segment_cache=CacheLine(next_epoch, next_segment, 0, 300 + next_segment),
                                        cache_consumed=False, dense_value=300 + next_segment,
                                        dense_hold=False, sealed=False, failed=False, cancelled=False, done=False)
    # Seal is an explicit prerequisite event, ordered before every prefetch.
    if not s.sealed and not s.failed and not s.cancelled:
        yield "seal_before_prefetch", replace(s, sealed=True)


def check_transition(before: State, event: str, after: State) -> None:
    invariant(after)
    if before.dense_hold and event not in {"dense_release", "abort_reset_unaccepted", "abort_reset_accepted"}:
        assert after.dense_value == before.dense_value, "dense output changed while held"
    if before.offered is not None and event != "accept_read" and event != "abort_reset_unaccepted":
        assert after.offered == before.offered, "offered request snapshot changed before acceptance"
    if before.physical_owner is not None and event not in {
        "ack_match_fill", "ack_match_drain", "ack_during_dense_hold", "ack_match_error",
        "ack_error_priority_over_output", "replace_bank"
    }:
        assert after.physical_owner == before.physical_owner, "physical owner changed before matching drain"
    if event == "offer_prefetch":
        assert before.sealed and after.offered is not None
        assert before.cache_consumed
        assert (after.offered.epoch, after.offered.segment, after.offered.address) == (
            before.epoch, before.segment, before.segment_cache.address + 16
        )
    if event == "accept_read":
        assert before.offered == after.physical_owner and after.offered is None
    if event in {"response_wrong_epoch", "abort_reset_accepted"}:
        assert after.physical_owner == before.physical_owner and not after.local_valid
    if event == "ack_match_error":
        assert before.physical_owner is not None and after.physical_owner is None and after.failed
    if event == "ack_error_priority_over_output":
        assert before.dense_hold and after.dense_hold and after.dense_value == before.dense_value
        assert after.physical_owner is None and after.failed and after.segment_cache == before.segment_cache
    if event == "ack_during_dense_hold":
        assert before.dense_hold and after.dense_hold
        assert after.dense_value == before.dense_value
        assert after.segment_cache == CacheLine(before.physical_owner.epoch, before.physical_owner.segment,
                                                 before.physical_owner.address, before.physical_owner.tag)
        assert after.cache_consumed is False
    if event == "ack_match_fill":
        assert before.physical_owner is not None and before.local_valid
        assert after.segment_cache.tag == before.physical_owner.tag and not after.cache_consumed
    if event == "replace_bank":
        assert before.physical_owner is None and before.offered is None and not before.local_valid
    if event == "consume_segment_cache":
        assert after.cache_consumed
    if event == "dense_complete":
        assert before.offered is None and before.physical_owner is None and not before.dense_hold
    if event == "seal_before_prefetch":
        assert before.offered is None and before.physical_owner is None
    if not before.sealed:
        assert event != "offer_prefetch", "prefetch cannot be offered before seal"
    if event == "offer_prefetch":
        assert before.sealed, "prefetch offer before seal"


def bounded_bfs(max_depth: int = 11) -> dict:
    start = State()
    queue = deque([(start, ())])
    seen = {start: 0}
    checked = 0
    events: set[str] = set()
    shortest: dict[str, list[str]] = {}
    while queue:
        state, trace = queue.popleft()
        if len(trace) >= max_depth:
            continue
        for event, nxt in transitions(state):
            check_transition(state, event, nxt)
            checked += 1
            events.add(event)
            depth = len(trace) + 1
            if event not in shortest:
                shortest[event] = list(trace + (event,))
            if nxt not in seen or depth < seen[nxt]:
                seen[nxt] = depth
                queue.append((nxt, trace + (event,)))
    required = {"seal_before_prefetch", "offer_prefetch", "accept_read", "ack_match_fill",
                "ack_match_drain", "ack_match_error", "ack_error_priority_over_output", "response_wrong_epoch",
                "abort_reset_unaccepted", "abort_reset_accepted", "dense_hold",
                "ack_during_dense_hold", "consume_segment_cache", "replace_bank", "dense_complete"}
    assert required <= events, f"bounded event coverage missing {sorted(required - events)}"
    return {"max_depth": max_depth, "unique_states": len(seen), "transitions_checked": checked,
            "event_coverage": sorted(events), "shortest_event_traces": shortest}


def run_trace(prefixes: list[str], start: State | None = None) -> tuple[State, list[str]]:
    state = start or State()
    trace: list[str] = []
    for prefix in prefixes:
        choices = [(event, nxt) for event, nxt in transitions(state) if event == prefix]
        assert choices, f"directed event unavailable: {prefix}"
        event, nxt = choices[0]
        check_transition(state, event, nxt)
        trace.append(event)
        state = nxt
    return state, trace


def directed_checks() -> dict:
    initial = State()
    assert not any(event == "offer_prefetch" for event, _ in transitions(initial)), "offer before seal"
    terminal, _ = run_trace(["seal_before_prefetch", "dense_complete"])
    assert terminal.done and terminal.offered is None and terminal.physical_owner is None and not terminal.failed
    assert not list(transitions(terminal)), "done state must be terminal"

    # Offer remains stable through a ready-low observation and acceptance.
    state, trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch"])
    snapshot = state.offered
    check_transition(state, "ready_low_observe", state)
    assert state.offered == snapshot
    state, rest = run_trace(["accept_read", "dense_hold", "ack_during_dense_hold"], state)
    trace.extend(["ready_low_observe"] + rest)
    assert state.dense_value == 100 and state.segment_cache.tag == snapshot.tag
    assert state.physical_owner is None
    state, rest = run_trace(["dense_release"], state)
    trace.extend(rest)
    assert state.segment_cache.tag == snapshot.tag

    # A matching error ACK fails logical fill closed and retires physical
    # ownership. A wrong-epoch response leaves the owner for matching drain.
    error_state, error_trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch", "accept_read", "ack_match_error"])
    assert error_state.failed and error_state.physical_owner is None and not error_state.local_valid
    assert error_state.segment_cache.tag == 100
    priority, priority_trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch",
                                           "accept_read", "dense_hold", "ack_error_priority_over_output"])
    assert priority.failed and priority.dense_hold and priority.segment_cache.tag == 100

    wrong, wrong_trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch", "accept_read", "response_wrong_epoch"])
    assert wrong.physical_owner is not None and wrong.failed
    wrong, rest = run_trace(["ack_match_drain"], wrong)
    wrong_trace.extend(rest)

    # Abort of an unaccepted offer drops only local ownership; accepted abort
    # retains the external hazard until matching drain.
    unaccepted, abort_trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch", "abort_reset_unaccepted"])
    assert unaccepted.offered is None and unaccepted.physical_owner is None
    accepted, accepted_trace = run_trace(["seal_before_prefetch", "consume_segment_cache", "offer_prefetch", "accept_read", "abort_reset_accepted"])
    assert accepted.physical_owner is not None and accepted.cancelled
    assert not any(e == "replace_bank" for e, _ in transitions(accepted))
    accepted, rest = run_trace(["ack_match_drain", "replace_bank"], accepted)
    accepted_trace.extend(rest)

    # Replacement is blocked while an accepted request remains, then becomes
    # eligible only after its matching drain.
    blocked = State(sealed=True, cache_consumed=True, offered=Snapshot(1, 0, 16, 201), local_valid=True)
    assert not any(e == "replace_bank" for e, _ in transitions(blocked))
    return {"checks": ["offer_snapshot_stable_ready_low", "one_accepted_external_read",
                        "ack_during_dense_hold_preserves_output", "consumed_segment_cache_replacement",
                        "ack_error_priority_suppresses_output_advance", "wrong_epoch_fails_closed_until_matching_drain",
                        "matching_error_ack_retires_owner_without_fill",
                        "abort_drops_unaccepted_local_work", "abort_retains_accepted_hazard",
                        "replacement_bank_blocked_until_drain", "seal_precedes_prefetch"],
            "traces": {"dense_hold_ack": trace, "matching_error_ack": error_trace,
                       "error_priority": priority_trace,
                       "wrong_epoch_drain": wrong_trace, "unaccepted_abort": abort_trace,
                       "accepted_abort_drain_replace": accepted_trace}}


def seeded_walk(seed: int = SEED, steps: int = 3000) -> dict:
    rng = random.Random(seed)
    state = State()
    counts: dict[str, int] = {}
    peak = 0
    terminal_restarts = 0
    for _ in range(steps):
        choices = list(transitions(state))
        if not choices:
            terminal_restarts += 1
            next_epoch = state.epoch + 1
            state = State(epoch=next_epoch, segment_cache=CacheLine(next_epoch, 0, 0, 100))
            continue
        event, nxt = rng.choice(choices)
        check_transition(state, event, nxt)
        counts[event] = counts.get(event, 0) + 1
        state = nxt
        peak = max(peak, int(state.offered is not None) + int(state.physical_owner is not None))
    return {"seed": seed, "requested_steps": steps,
            "events_executed": sum(counts.values()), "terminal_restarts": terminal_restarts,
            "event_counts": dict(sorted(counts.items())), "peak_read_owners": peak}


def main() -> None:
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = {"model": "abstract_read_prefetch_ownership", "source_sha256": source_sha,
              "scope": "bounded ownership-event simulation; not RTL proof, cycle model, or performance model",
              "bfs": bounded_bfs(), "directed": directed_checks(), "seeded": seeded_walk()}
    RESULT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"source_sha256": source_sha, "bfs_states": report["bfs"]["unique_states"],
                      "bfs_transitions": report["bfs"]["transitions_checked"],
                      "seeded_requested_steps": report["seeded"]["requested_steps"],
                      "seeded_events_executed": report["seeded"]["events_executed"],
                      "result": str(RESULT)}, indent=2))


if __name__ == "__main__":
    main()

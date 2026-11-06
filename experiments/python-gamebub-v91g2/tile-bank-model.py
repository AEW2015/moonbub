#!/usr/bin/env python3
"""Bounded abstract ownership checks for V91g2's two tile banks.

Events describe ownership changes, not RTL states, cycles, or performance.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "experiments/python-gamebub-v91g2/tile-bank-results.json"
SEED = 910438
BLOCKS = 3
SCALARS = 3
PREP_UNITS = 2


@dataclass(frozen=True)
class Bank:
    phase: str = "EMPTY"  # EMPTY, PREPARING, READY; READY also owns emitted data.
    epoch: int = -1
    block: int = -1
    prep: int = 0
    payload: int = -1


EMPTY = Bank()


@dataclass(frozen=True)
class ReadOwner:
    bank: int
    epoch: int
    block: int
    request: int


@dataclass(frozen=True)
class State:
    epoch: int = 1
    banks: tuple[Bank, Bank] = (Bank("PREPARING", 1, 0, 0, 100), EMPTY)
    next_block: int = 1
    emit_block: int = 0
    emit_bank: int = 0
    emit_index: int = 0
    output_held: bool = False
    held_value: int = -1
    physical: ReadOwner | None = None
    read_needed: bool = True
    failed: bool = False
    cancelled: bool = False
    done: bool = False
    accepted_outputs: int = 0
    epoch_outputs: int = 0
    discarded_responses: int = 0
    error_acks: int = 0


def has_owners(s: State) -> int:
    return sum(b.phase != "EMPTY" for b in s.banks)


def invariant(s: State) -> None:
    assert len(s.banks) == 2
    assert has_owners(s) <= 2, "at most two bank owners, including preparation"
    assert sum(b.phase == "PREPARING" for b in s.banks) <= 1, "one producer preparation owner"
    owners = [(b.epoch, b.block) for b in s.banks if b.phase != "EMPTY"]
    assert len(owners) == len(set(owners)), "two banks cannot own the same block"
    assert 0 <= s.emit_block <= BLOCKS
    assert 0 <= s.emit_index < SCALARS
    if s.output_held:
        b = s.banks[s.emit_bank]
        assert b.phase == "READY" and b.block == s.emit_block
        assert b.epoch == s.epoch
        assert s.held_value == b.payload * 100 + s.emit_index
    if s.physical is not None:
        p = s.physical
        assert p.bank in (0, 1) and p.epoch >= 0
        # Local cancellation may clear the bank, but its physical bus owner is
        # separate and continues to reserve that bank against replacement.
    if s.done:
        assert s.emit_block == BLOCKS and s.physical is None
        assert not any(b.phase != "EMPTY" for b in s.banks)
        assert not s.output_held and not s.failed and not s.cancelled
        assert s.epoch_outputs == BLOCKS * SCALARS
    if not s.failed and not s.cancelled:
        assert all(b.epoch == s.epoch for b in s.banks if b.phase != "EMPTY")
    if s.failed or s.cancelled:
        assert not s.output_held
    if s.emit_block < BLOCKS and not s.failed and not s.cancelled:
        b = s.banks[s.emit_bank]
        assert b.phase == "EMPTY" or (b.phase in {"PREPARING", "READY"}
                                        and b.block == s.emit_block)


def clear_banks(s: State) -> tuple[Bank, Bank]:
    return (EMPTY, EMPTY)


def transitions(s: State):
    if s.done:
        return

    # Start preparation only in an EMPTY bank. A physical request that was
    # accepted for that bank keeps it unavailable even after local clear.
    if (not s.failed and not s.cancelled and s.next_block < BLOCKS
            and not any(b.phase == "PREPARING" for b in s.banks)):
        for idx, bank in enumerate(s.banks):
            if idx != s.next_block % 2:
                continue
            reserved = s.physical is not None and s.physical.bank == idx
            if bank.phase == "EMPTY" and not reserved:
                payload = 100 + s.epoch * 10 + s.next_block
                bs = list(s.banks)
                bs[idx] = Bank("PREPARING", s.epoch, s.next_block, 0, payload)
                yield "start_prepare", replace(s, banks=tuple(bs), next_block=s.next_block + 1,
                                                 read_needed=True)

    if not s.failed and not s.cancelled and s.physical is None and s.read_needed:
        prep = next(((i, b) for i, b in enumerate(s.banks) if b.phase == "PREPARING"), None)
        if prep is not None:
            i, b = prep
            yield "accept_external_read", replace(
                s, physical=ReadOwner(i, b.epoch, b.block, 1000 + b.epoch * 10 + b.block),
                read_needed=True)

    if s.physical is not None:
        p = s.physical
        # Wrong epoch/error does not become a successful local fill. The
        # former retains the physical owner; the latter retires it.
        yield "response_wrong_epoch", replace(s, banks=clear_banks(s), failed=True,
                                                  cancelled=False, output_held=False,
                                                  held_value=-1,
                                                  discarded_responses=s.discarded_responses + 1)
        yield "ack_match_error", replace(s, physical=None, failed=True,
                                            banks=clear_banks(s),
                                            cancelled=False, output_held=False, held_value=-1,
                                            error_acks=s.error_acks + 1)
        matching_bank = s.banks[p.bank]
        if (not s.failed and not s.cancelled and p.epoch == s.epoch
                and matching_bank.phase == "PREPARING"
                and (matching_bank.epoch, matching_bank.block) == (p.epoch, p.block)):
            yield "ack_match_ok", replace(s, physical=None, read_needed=False)
        if (s.failed or s.cancelled or matching_bank.phase != "PREPARING"
                or (matching_bank.epoch, matching_bank.block) != (p.epoch, p.block)):
            yield "ack_match_drain", replace(s, physical=None, read_needed=False)

    if not s.failed and not s.cancelled:
        for idx, b in enumerate(s.banks):
            if (b.phase == "PREPARING" and b.prep >= PREP_UNITS
                    and not (s.physical is not None and s.physical.bank == idx)):
                bs = list(s.banks)
                bs[idx] = replace(b, phase="READY")
                yield "prepare_complete", replace(s, banks=tuple(bs))

    if not s.failed and not s.cancelled and not s.output_held and s.emit_block < BLOCKS:
        b = s.banks[s.emit_bank]
        if b.phase == "READY" and b.block == s.emit_block:
            val = b.payload * 100 + s.emit_index
            yield "hold_output", replace(s, output_held=True, held_value=val)

    if s.output_held:
        # Backpressure leaves both held scalar and emitting bank immutable.
        yield "stall_output", s
        # Error priority: if a matching error ACK and output transfer coincide,
        # no scalar advances. (The physical request may name the other bank.)
        if s.physical is not None:
            yield "ack_error_priority_over_output", replace(
                s, physical=None, failed=True, banks=clear_banks(s),
                output_held=False, held_value=-1,
                error_acks=s.error_acks + 1)
        if s.emit_index + 1 < SCALARS:
            yield "accept_output", replace(s, emit_index=s.emit_index + 1,
                                              output_held=False, held_value=-1,
                                              accepted_outputs=s.accepted_outputs + 1,
                                              epoch_outputs=s.epoch_outputs + 1)
        else:
            # This event is the explicit same-edge ordering point: accept the
            # consumer's last scalar, release its bank, then publish any other
            # bank whose preparation completes on this edge. The producer can
            # reuse the released bank only in a later transition.
            other = 1 - s.emit_bank
            bs = list(s.banks)
            bs[s.emit_bank] = EMPTY
            if (bs[other].phase == "PREPARING" and bs[other].prep >= PREP_UNITS
                    and not (s.physical is not None and s.physical.bank == other)):
                bs[other] = replace(bs[other], phase="READY")
                event = "accept_last_and_prepare_complete"
            else:
                event = "accept_last_output"
            new_block = s.emit_block + 1
            new_emit_bank = other
            if new_block == BLOCKS:
                # Completion is fenced by physical ACK drain and every local
                # bank owner, not merely the final scalar transfer.
                yield event, replace(s, banks=tuple(bs), emit_block=new_block,
                                     emit_index=0, output_held=False, held_value=-1,
                                     accepted_outputs=s.accepted_outputs + 1,
                                     epoch_outputs=s.epoch_outputs + 1)
            else:
                # Keep the current output cursor at the next block. The next
                # output cannot be held until that block is READY.
                yield event, replace(s, banks=tuple(bs), emit_block=new_block,
                                     emit_bank=new_emit_bank, emit_index=0,
                                     output_held=False, held_value=-1,
                                     accepted_outputs=s.accepted_outputs + 1,
                                     epoch_outputs=s.epoch_outputs + 1)

    # Abstract producer progress is separate from output hold. It writes only
    # its PREPARING bank; the bank being emitted is immutable.
    if not s.failed and not s.cancelled:
        for idx, b in enumerate(s.banks):
            if b.phase == "PREPARING" and b.prep < PREP_UNITS and s.physical is None:
                # Progress cannot cross the external-read fence for this tile.
                if not s.read_needed:
                    yield "prepare_progress", replace(s, banks=tuple(
                        replace(x, prep=x.prep + 1) if j == idx else x
                        for j, x in enumerate(s.banks)))

    # Abort/reset invalidates local work and advances the logical epoch. An
    # accepted request remains a separate, immutable physical owner.
    if not s.cancelled and not s.done:
        yield "cancel_reset", replace(s, epoch=s.epoch + 1, banks=clear_banks(s),
                                        next_block=0, emit_block=0, emit_bank=0,
                                        emit_index=0, output_held=False, held_value=-1,
                                        read_needed=False, cancelled=True, failed=False,
                                        epoch_outputs=0)

    # A failed/cancelled transaction may be replaced only after the accepted
    # external owner has drained. Restart begins a fresh epoch and tile zero.
    if s.physical is None and s.cancelled and not s.output_held:
        payload = 100 + s.epoch * 10
        yield "restart_after_drain", replace(
            s, banks=(Bank("PREPARING", s.epoch, 0, 0, payload), EMPTY),
            next_block=1, emit_block=0, emit_bank=0, emit_index=0,
            output_held=False, held_value=-1, read_needed=True,
            failed=False, cancelled=False, done=False, epoch_outputs=0)

    if (s.emit_block == BLOCKS and s.physical is None
            and not any(b.phase != "EMPTY" for b in s.banks)
            and not s.output_held and not s.failed and not s.cancelled):
        yield "final_done_after_drain", replace(s, done=True)


def check_transition(before: State, event: str, after: State) -> None:
    invariant(after)
    consumer_or_invalidation = {"accept_output", "accept_last_output",
                                "accept_last_and_prepare_complete", "cancel_reset",
                                "response_wrong_epoch", "ack_match_error",
                                "ack_error_priority_over_output"}
    if before.output_held and event not in consumer_or_invalidation:
        assert after.held_value == before.held_value, "held scalar changed under output backpressure"
        assert after.banks[before.emit_bank] == before.banks[before.emit_bank], \
            "producer changed bank while its scalar was held"
    if before.physical is not None and event not in {
        "ack_match_ok", "ack_match_error", "ack_match_drain", "ack_error_priority_over_output",
        "cancel_reset", "response_wrong_epoch", "restart_after_drain"
    }:
        assert after.physical == before.physical, "accepted physical read owner was erased"
    if event == "response_wrong_epoch":
        assert after.physical == before.physical and after.failed
    if event in {"ack_match_error", "ack_error_priority_over_output"}:
        assert after.physical is None and after.failed
        assert after.accepted_outputs == before.accepted_outputs
        assert not any(b.phase != "EMPTY" for b in after.banks)
    if event == "ack_match_ok":
        assert before.physical is not None and after.physical is None
        assert after.banks[before.physical.bank].phase == "PREPARING"
    if event == "ack_match_drain":
        assert before.physical is not None and after.physical is None
    if event == "accept_last_and_prepare_complete":
        assert before.output_held and before.emit_index == SCALARS - 1
        assert after.banks[before.emit_bank].phase == "EMPTY"
        assert after.banks[1 - before.emit_bank].phase == "READY"
    if event == "accept_last_output":
        assert before.output_held and before.emit_index == SCALARS - 1
        assert after.banks[before.emit_bank].phase == "EMPTY"
    if event == "restart_after_drain":
        assert before.physical is None
    if event == "final_done_after_drain":
        assert after.done and after.physical is None and has_owners(after) == 0


def bounded_bfs(max_depth: int = 36) -> dict:
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
            shortest.setdefault(event, list(trace + (event,)))
            if nxt not in seen or depth < seen[nxt]:
                seen[nxt] = depth
                queue.append((nxt, trace + (event,)))
    required = {"start_prepare", "accept_external_read", "ack_match_ok", "prepare_complete",
                "hold_output", "stall_output", "accept_output", "accept_last_output",
                "accept_last_and_prepare_complete", "response_wrong_epoch", "ack_match_error",
                "ack_error_priority_over_output", "ack_match_drain", "cancel_reset", "restart_after_drain",
                "final_done_after_drain"}
    assert required <= events, f"bounded event coverage missing {sorted(required - events)}"
    return {"max_depth": max_depth, "unique_states": len(seen),
            "transitions_checked": checked, "event_coverage": sorted(events),
            "shortest_event_traces": shortest}


def run_trace(events: list[str], start: State | None = None) -> tuple[State, list[str]]:
    s = start or State()
    trace = []
    for wanted in events:
        choices = [(name, nxt) for name, nxt in transitions(s) if name == wanted]
        assert choices, f"directed event unavailable: {wanted}"
        name, nxt = choices[0]
        check_transition(s, name, nxt)
        trace.append(name)
        s = nxt
    return s, trace


def directed_checks() -> dict:
    checks = {}
    # Stable output and producer writes in the other bank while it is held.
    s, _ = run_trace(["accept_external_read", "ack_match_ok", "prepare_progress",
                      "prepare_progress", "prepare_complete", "hold_output"])
    held = s.held_value
    s, _ = run_trace(["start_prepare", "accept_external_read", "ack_match_ok",
                      "prepare_progress", "prepare_progress", "stall_output"], s)
    assert s.held_value == held and s.banks[0].phase == "READY"
    assert s.banks[1].phase == "PREPARING" and s.banks[1].prep == PREP_UNITS
    checks["held_output_immutable"] = True

    # Prepare block 1 in bank 1 while block 0 remains owned. Its preparation
    # completes on the same abstract edge as block 0's last output transfer.
    s, _ = run_trace(["accept_external_read", "ack_match_ok", "prepare_progress",
                      "prepare_progress", "prepare_complete", "start_prepare",
                      "accept_external_read", "ack_match_ok", "prepare_progress",
                      "prepare_progress", "hold_output", "accept_output",
                      "hold_output", "accept_output", "hold_output",
                      "accept_last_and_prepare_complete"])
    assert s.banks[0].phase == "EMPTY" and s.banks[1].phase == "READY"
    checks["last_scalar_prepare_handoff"] = True
    # Bank 0 can be reused only on a later event, after last-scalar release.
    s, _ = run_trace(["start_prepare"], s)
    assert s.banks[0].phase == "PREPARING"
    checks["reuse_after_handoff"] = True

    # Error ACK while output is held has priority and does not advance output.
    err, _ = run_trace(["accept_external_read", "ack_match_ok", "prepare_progress",
                        "prepare_progress", "prepare_complete", "start_prepare",
                        "accept_external_read", "hold_output"])
    err, _ = run_trace(["ack_error_priority_over_output"], err)
    assert err.failed and err.emit_index == 0 and err.accepted_outputs == 0
    checks["matching_error_priority"] = True

    # Wrong epoch clears local transaction state but retains immutable physical
    # ownership. Cancel/restart remains blocked until matching drain ACK; the
    # small model's matching ACK after failure is represented as cancel/reset
    # followed by physical drain in the seeded/BFS campaign.
    wrong = State()
    wrong, _ = run_trace(["accept_external_read", "response_wrong_epoch"], wrong)
    assert wrong.physical is not None and wrong.failed and not any(
        b.phase != "EMPTY" for b in wrong.banks)
    wrong, _ = run_trace(["cancel_reset"], wrong)
    assert wrong.physical is not None and wrong.cancelled
    wrong, _ = run_trace(["ack_match_drain", "restart_after_drain"], wrong)
    assert wrong.physical is None and not wrong.cancelled and wrong.banks[0].phase == "PREPARING"
    checks["wrong_epoch_retains_physical_owner"] = True
    return {"directed_checks": checks}


def seeded_walk(seed: int = SEED, steps: int = 5000) -> dict:
    rng = random.Random(seed)
    s = State()
    counts: dict[str, int] = {}
    restarts = 0
    actual_events = 0
    for _ in range(steps):
        choices = list(transitions(s))
        if not choices:
            epoch = s.epoch + 1
            s = State(epoch=epoch, banks=(Bank("PREPARING", epoch, 0, 0,
                                               100 + epoch * 10), EMPTY))
            restarts += 1
            choices = list(transitions(s))
        event, nxt = rng.choice(choices)
        check_transition(s, event, nxt)
        s = nxt
        counts[event] = counts.get(event, 0) + 1
        actual_events += 1
        if s.done:
            epoch = s.epoch + 1
            s = State(epoch=epoch, banks=(Bank("PREPARING", epoch, 0, 0,
                                               100 + epoch * 10), EMPTY))
            restarts += 1
    return {"seed": seed, "requested_steps": steps, "actual_events": actual_events,
            "terminal_restarts": restarts, "event_counts": dict(sorted(counts.items()))}


def main() -> None:
    src = Path(__file__).read_bytes()
    result = {
        "schema": "cu66-v91g2-two-tile-bank-model-v1",
        "status": "PASS_BOUNDED_ABSTRACT_OWNERSHIP_CHECKS",
        "scope": {
            "kind": "abstract_ownership_model",
            "banks": 2, "blocks": BLOCKS, "abstract_scalars_per_block": SCALARS,
            "abstract_prepare_units": PREP_UNITS,
            "actual_rtl_scalars_per_block": 64,
            "accepted_output_counter": "cumulative_across_epochs",
            "rtl_equivalence_claimed": False,
            "cycle_accurate": False,
            "performance_evidence": False,
            "description": "Abstract ownership-event reference; not RTL, a formal proof, or performance evidence."
        },
        "source_sha256": hashlib.sha256(src).hexdigest(),
        "bounded_bfs": bounded_bfs(),
        **directed_checks(),
        "seeded_walk": seeded_walk(),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "source_sha256": result["source_sha256"],
                      "unique_states": result["bounded_bfs"]["unique_states"],
                      "transitions_checked": result["bounded_bfs"]["transitions_checked"],
                      "seeded_actual_events": result["seeded_walk"]["actual_events"],
                      "seeded_restarts": result["seeded_walk"]["terminal_restarts"]}, indent=2))


if __name__ == "__main__":
    main()

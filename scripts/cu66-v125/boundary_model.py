#!/usr/bin/env python3
"""Finite algebra check for incremental hidden and tile-terminal predicates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
MASK = (1 << 32) - 1
V125 = "fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv"
V122 = "fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv"
EXPECTED = {
    V125: "2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb",
    V122: "54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf",
}
HIDDEN = {
    0: ((633, 651), (723, 741), (993, 1011), (1083, 1101),
        (4071, 4110), (4161, 4200), (4251, 4290), (4431, 4460),
        (4521, 4550)),
    1: ((1046, 1064),),
    2: ((1046, 1064),),
    3: ((1046, 1064),),
}


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def hidden(plane: int, tile: int) -> bool:
    tile &= MASK
    return any(lo <= tile <= hi for lo, hi in HIDDEN[plane])


def enter(plane: int, tile: int) -> bool:
    tile &= MASK
    return any(tile == lo - 1 for lo, _ in HIDDEN[plane])


def leave(plane: int, tile: int) -> bool:
    tile &= MASK
    return any(tile == hi for _, hi in HIDDEN[plane])


def tile_count(plane: int) -> int:
    return 5400 if plane == 0 else 1350


def recurrence_authorized(owner: tuple[int, int, int], epoch: int,
                          plane: int, tile: int, next_plane: int,
                          next_tile: int) -> bool:
    return (owner == (epoch, plane, tile & MASK) and next_plane == plane and
            next_tile == ((tile + 1) & MASK))


def main() -> None:
    for path, expected in EXPECTED.items():
        actual = digest(path)
        if actual != expected:
            raise SystemExit(f"pinned source changed: {path}: {actual}")

    counts = {
        "planes": 4,
        "hidden_range_count": sum(map(len, HIDDEN.values())),
        "range_boundary_transitions": 0,
        "high_bit_transitions": 0,
        "uint32_wrap_transitions": 0,
        "deterministic_random_transitions": 0,
        "tile_terminal_cases": 0,
        "same_plane_unit_steps": 0,
        "invalid_owner_or_transition_fallback_cases": 0,
        "stale_or_wrong_hidden_witness_rejections": 0,
    }

    # Check every range edge and its immediate neighbors. For each current tile t,
    # the recurrence must predict the exact full-function value at uint32(t+1).
    boundary_tiles = set()
    for ranges in HIDDEN.values():
        for lo, hi in ranges:
            boundary_tiles.update((lo - 2, lo - 1, lo, hi - 1, hi, hi + 1))
    for p in range(4):
        for t in sorted(boundary_tiles):
            old = hidden(p, t)
            expected = hidden(p, (t + 1) & MASK)
            predicted = enter(p, t) or (old and not leave(p, t))
            assert predicted == expected, (p, t, old, predicted, expected)
            counts["range_boundary_transitions"] += 1

    # Include high-bit/no-range values and uint32 wrap, as well as every boundary
    # transition. Random sampling is deterministic and bounded.
    high_tiles = {0x7FFFFFFF, 0x80000000, 0x80000001, 0xFFFFFFFD,
                  0xFFFFFFFE, 0xFFFFFFFF}
    for p in range(4):
        for t in sorted(high_tiles):
            predicted = enter(p, t) or (hidden(p, t) and not leave(p, t))
            assert predicted == hidden(p, (t + 1) & MASK)
            counts["high_bit_transitions"] += 1
            if t == MASK:
                counts["uint32_wrap_transitions"] += 1
        # A fixed seed makes this a repeatable algebra sample, not a proof over
        # every uint32 coordinate.
        rng = random.Random(0xB0A1D + p)
        for _ in range(25_000):
            t = rng.getrandbits(32)
            predicted = enter(p, t) or (hidden(p, t) and not leave(p, t))
            assert predicted == hidden(p, (t + 1) & MASK), (p, t)
            counts["deterministic_random_transitions"] += 1

    # The terminal recurrence is restricted to an owned same-plane unit step:
    # (t+1 mod 2^32)==tile_count(p) iff t==tile_count(p)-1.
    terminal_tiles = {0, 1, MASK - 1, MASK}
    for p in range(4):
        n = tile_count(p)
        terminal_tiles.update((n - 2, n - 1, n, n + 1))
        for t in sorted(terminal_tiles):
            successor = (t + 1) & MASK
            direct = successor == n
            predicted = t == n - 1
            assert direct == predicted, (p, t, successor, n)
            counts["tile_terminal_cases"] += 1
            counts["same_plane_unit_steps"] += 1

    # Owner discipline: cached H is valid only for the exact epoch/plane/tile
    # key. A jump, plane change, or stale key takes the direct full-function path.
    epoch = 71
    for p in range(4):
        for t in sorted(boundary_tiles | high_tiles):
            owner = (epoch, p, t & MASK)
            assert recurrence_authorized(owner, epoch, p, t, p, (t + 1) & MASK)
            candidates = (
                (epoch, p, t, p, (t + 2) & MASK),
                (epoch, p, t, (p + 1) & 3, (t + 1) & MASK),
                (epoch + 1, p, t, p, (t + 1) & MASK),
                (epoch, (p + 1) & 3, t, (p + 1) & 3, (t + 1) & MASK),
            )
            for old_epoch, old_plane, old_tile, next_plane, next_tile in candidates:
                candidate_owner = (epoch, p, t & MASK)
                assert not recurrence_authorized(candidate_owner, old_epoch,
                                                 old_plane, old_tile,
                                                 next_plane, next_tile)
                _ = hidden(next_plane, next_tile)  # direct fallback oracle
                counts["invalid_owner_or_transition_fallback_cases"] += 1
            stale_owner = ((epoch + 1, p, t & MASK))
            assert not recurrence_authorized(stale_owner, epoch, p, t, p,
                                             (t + 1) & MASK)
            counts["stale_or_wrong_hidden_witness_rejections"] += 1

    result = {
        "schema": "v125-incremental-boundary-algebra-v1",
        "status": "PASS_FINITE_ALGEBRA_MODEL",
        "model_kind": "standard-library Python Boolean algebra; no RTL or synthesis",
        "script_sha256": digest("scripts/cu66-v125/boundary_model.py"),
        "sources": {p: {"sha256": digest(p)} for p in EXPECTED},
        "counts": counts,
        "claims": {
            "hidden_recurrence": "For same-plane uint32 unit steps, H(p,t+1)=ENTER(p,t) OR (H(p,t) AND NOT EXIT(p,t)); ENTER uses each inclusive lower bound minus one and EXIT uses each inclusive upper bound.",
            "terminal_recurrence": "For same-plane uint32 unit steps, terminal(t+1) equals (t == tile_count(p)-1), with tile_count 5400 for plane 0 and 1350 otherwise.",
            "ownership": "The recurrence is authorized only by an exact same-plane, same-epoch (model token), unit-step witness. Jumps, plane changes, and stale/wrong owners use direct full-function evaluation.",
        },
        "limitations": [
            "Finite boundary and deterministic-random checks do not exhaust all 2^32 tiles.",
            "The recurrence is an optional algebraic candidate and is not implemented by the current V125 RTL.",
            "Synthesis may already refactor the existing full predicate; only a later routed experiment can establish timing or resource effects.",
            "No FPGA timing, resources, FPS, or hardware qualification is measured.",
        ],
        "python": platform.python_version(),
    }
    result_path = ROOT / "experiments/python-gamebub-v125/boundary-model/results.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "counts": counts,
                      "script_sha256": digest("scripts/cu66-v125/boundary_model.py"),
                      "result": str(result_path.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"BOUNDARY_MODEL_FAIL: {exc!r}", file=sys.stderr)
        raise SystemExit(1)

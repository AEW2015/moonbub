#!/usr/bin/env python3
"""Independent finite algebraic check of sparse-position rank comparison."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v123/python-model"
OUT = AREA / "rank-model.json"
V119 = ROOT / "fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv"
ORACLE = ROOT / "scripts/cu66-v91c/build_vectors.py"
SEED = 123_091_119
U32 = (1 << 32) - 1
U16 = (1 << 16) - 1


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def v119_rank(raster: int) -> int:
    """Literal algorithmic shape from frozen V119 zigzag(); independent Python."""
    rank = 0
    found = 0
    for diagonal in range(15):
        for step in range(8):
            row = step if diagonal % 2 else 7 - step
            col = diagonal - row
            if 0 <= col < 8:
                if row * 8 + col == raster:
                    found = rank
                rank += 1
    return found


def oracle_order() -> tuple[int, ...]:
    """Independent V91c packet-oracle ordering formula; returns scan order."""
    return tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                   i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))


ORACLE_ORDER = oracle_order()
ORACLE_RANKS = tuple(ORACLE_ORDER.index(i) for i in range(64))
V119_RANKS = tuple(v119_rank(i) for i in range(64))
THRESHOLD_MASKS = tuple((1 << (rank + 1)) - 1 for rank in range(64))


def old_sparse_le(block: int, raster: int, previous: int) -> bool:
    return block * 64 + V119_RANKS[raster] <= previous


def proposed_sparse_le(block: int, raster: int, previous: int) -> bool:
    """High-bits/block compare plus rank-threshold-mask membership."""
    rank = ORACLE_RANKS[raster]
    if previous >> 22:
        return True  # every 16-bit block/rank candidate is below 2**22
    previous_block = (previous >> 6) & U16
    if block < previous_block:
        return True
    if block > previous_block:
        return False
    previous_rank = previous & 0x3F
    return bool(THRESHOLD_MASKS[previous_rank] & (1 << rank))


def band_matches(band: int, raster: int, ranks: tuple[int, ...]) -> bool:
    rank = ranks[raster]
    if band == 1:
        return 1 <= rank < 6
    if band == 2:
        return 6 <= rank < 21
    if band == 3:
        return rank >= 21
    return raster == 0


def input_bad(context: dict, use_proposed: bool) -> bool:
    phase = context["phase"]
    raw = context["raw"]
    block, raster = context["block"], context["raster"]
    value = context["value"]
    position = block * 64 + (raster if raw else (ORACLE_RANKS[raster] if phase != 0 else 0))
    bad = (context["coef_epoch"] != context["active_epoch"] or
           context["coef_band"] != (phase & 3) or
           block >= context["blocks"] or
           value < -2048 or value > 2048 or
           context["written"] >= context["counts"][phase & 3])
    if raw:
        return bad or position != context["written"]
    if phase == 0:
        return bad or raster != 0 or block != context["written"]
    format_bad = not band_matches(context["coef_band"], raster, ORACLE_RANKS) or value == 0
    if context["previous_valid"]:
        le = (proposed_sparse_le(block, raster, context["previous_position"])
              if use_proposed else old_sparse_le(block, raster, context["previous_position"]))
        format_bad = format_bad or le
    return bad or format_bad


def gate_error(context: dict, bad: bool) -> int:
    """V119 INGEST fault selection: context gates event; epoch fault wins."""
    if (context["reset"] or context["cancel"] or context["response_failure"] or
            not context["ingest_state"] or not context["coef_valid"] or not bad):
        return 0
    return 2 if context["coef_epoch"] != context["active_epoch"] else 3


def base_context(phase: int, raw: bool) -> dict:
    band = phase & 3
    block, raster = 2, 3
    if not raw and phase == 0:
        block, raster = 2, 0
        written = block
    elif not raw:
        raster = next(i for i in range(64) if band_matches(band, i, ORACLE_RANKS))
        written = 0
    else:
        written = block * 64 + raster
    return {"phase": phase, "raw": raw, "block": block, "raster": raster, "value": 17,
            "coef_epoch": 7, "active_epoch": 7, "coef_band": band, "blocks": 65536,
            "written": written, "counts": [100, 100, 100, 100], "previous_valid": False,
            "previous_position": 0, "reset": False, "cancel": False,
            "response_failure": False, "ingest_state": True, "coef_valid": True}


def compare(context: dict) -> None:
    old = input_bad(context, False)
    new = input_bad(context, True)
    assert old == new, (context, old, new)
    assert gate_error(context, old) == gate_error(context, new)


def run() -> dict:
    assert len(set(ORACLE_ORDER)) == len(ORACLE_ORDER) == 64
    assert set(ORACLE_ORDER) == set(range(64))
    assert V119_RANKS == ORACLE_RANKS, "independent rank table differs from V119 scratch mapping"
    table_bytes = bytes(ORACLE_RANKS)
    table_sha = sha(table_bytes)
    source_hashes = {str(V119.relative_to(ROOT)): sha(V119.read_bytes()),
                     str(ORACLE.relative_to(ROOT)): sha(ORACLE.read_bytes())}

    all_indices = 0
    for raster in range(64):
        assert V119_RANKS[raster] == ORACLE_RANKS[raster]
        assert ORACLE_ORDER[ORACLE_RANKS[raster]] == raster
        all_indices += 1

    # Sweep all ranks at representative 16-bit block-word boundaries and
    # compare previous-position equality plus adjacent full-32 values.
    block_values = (0, 1, 2, 0x7FFE, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF)
    block_cases = 0
    for block in block_values:
        for raster in range(64):
            candidate = block * 64 + V119_RANKS[raster]
            for previous in (max(0, candidate - 1), candidate, min(U32, candidate + 1)):
                assert old_sparse_le(block, raster, previous) == proposed_sparse_le(block, raster, previous)
                block_cases += 1

    # Include all 10 high bits, full32 extrema and equality boundaries.
    previous_values = {0, 1, (1 << 22) - 1, 1 << 22, (1 << 22) + 1, U32}
    for high in range(1, 1 << 10):
        previous_values.add((high << 22) | (high * 37 & ((1 << 22) - 1)))
    high_cases = 0
    for block in block_values:
        for raster in (0, 1, 31, 63):
            candidate = block * 64 + V119_RANKS[raster]
            for previous in (max(0, candidate - 1), candidate, min(U32, candidate + 1), *previous_values):
                assert old_sparse_le(block, raster, previous) == proposed_sparse_le(block, raster, previous)
                high_cases += 1

    rng = random.Random(SEED)
    random_cases = 100_000
    for _ in range(random_cases):
        block, raster, previous = rng.getrandbits(16), rng.randrange(64), rng.getrandbits(32)
        assert old_sparse_le(block, raster, previous) == proposed_sparse_le(block, raster, previous)

    # All 8 phase encodings, raw/sparse mode, explicit malformed-format
    # examples, and every Boolean gating combination for error application.
    scenario_names = ("valid", "epoch_error_priority", "band_mismatch", "block_oob",
                      "value_low", "value_high", "count_exhausted", "format_error",
                      "zero_value", "previous_equal", "previous_lower", "previous_high")
    phase_raw_contexts = gating_contexts = error_priority_cases = 0
    gate_names = ("reset", "cancel", "response_failure", "ingest_state", "coef_valid")
    for phase in range(8):
        for raw in (False, True):
            for scenario in scenario_names:
                c = base_context(phase, raw)
                if scenario == "epoch_error_priority":
                    c["coef_epoch"] = 6; c["coef_band"] = (phase + 1) & 3
                elif scenario == "band_mismatch": c["coef_band"] = (phase + 1) & 3
                elif scenario == "block_oob": c["block"] = c["blocks"]
                elif scenario == "value_low": c["value"] = -2049
                elif scenario == "value_high": c["value"] = 2049
                elif scenario == "count_exhausted": c["written"] = c["counts"][phase & 3]
                elif scenario == "format_error":
                    if raw: c["written"] ^= 1
                    elif phase == 0: c["raster"] = 1
                    else: c["raster"] = next(i for i in range(64) if not band_matches(phase & 3, i, ORACLE_RANKS))
                elif scenario == "zero_value": c["value"] = 0
                elif scenario in ("previous_equal", "previous_lower", "previous_high") and not raw and phase != 0:
                    candidate = c["block"] * 64 + ORACLE_RANKS[c["raster"]]
                    c["previous_valid"] = True
                    c["previous_position"] = candidate if scenario == "previous_equal" else max(0, candidate - 1) if scenario == "previous_lower" else U32
                # Other modes ignore previous_position; leave an explicitly high value too.
                for gate_bits in range(1 << len(gate_names)):
                    g = dict(c)
                    for bit, name in enumerate(gate_names):
                        g[name] = bool(gate_bits & (1 << bit))
                    compare(g)
                    gating_contexts += 1
                    if scenario == "epoch_error_priority":
                        assert gate_error(g, input_bad(g, True)) in (0, 2)
                        if not any(g[n] for n in ("reset", "cancel", "response_failure")) and g["ingest_state"] and g["coef_valid"]:
                            assert gate_error(g, True) == 2
                        error_priority_cases += 1
                    phase_raw_contexts += 1

    result = {
        "schema": "v123-independent-spatial-rank-model-v1", "status": "PASS",
        "classification": "finite algebraic model only; no RTL compilation, timing, throughput, or hardware claim",
        "inputs": {"frozen_V119_scratch": {"path": str(V119.relative_to(ROOT)), "sha256": source_hashes[str(V119.relative_to(ROOT))]},
                   "independent_V91c_oracle_source": {"path": str(ORACLE.relative_to(ROOT)), "sha256": source_hashes[str(ORACLE.relative_to(ROOT))]},
                   "model_script": {"path": "scripts/cu66-v123/rank_model.py", "sha256": sha(Path(__file__).read_bytes())}},
        "rank_table": {"entries": 64, "raster_to_rank": list(ORACLE_RANKS), "scan_order": list(ORACLE_ORDER),
                       "independent_table_sha256": table_sha,
                       "checksum_encoding": "64 raster-to-rank bytes in raster index order",
                       "v119_function_matches_independent_oracle": True},
        "tested": {"all_64_indices": all_indices, "16bit_block_boundary_comparisons": block_cases,
                   "full32_previous_highbit_and_equality_cases": high_cases,
                   "deterministic_random_full32_comparisons": random_cases, "random_seed": SEED,
                   "phase_raw_context_scenarios": phase_raw_contexts,
                   "boolean_gate_contexts": gating_contexts, "error_priority_contexts": error_priority_cases,
                   "scenarios": list(scenario_names)},
        "equivalence_claim_scope": "For tested finite inputs, (block<<6)+rank <= full32 previous_position equals highbits/block compare plus 64-entry threshold-mask membership; original input_bad gating, phase/raw branches, and epoch-before-format error priority agree in the enumerated examples.",
        "not_tested": ["exhaustive 2^32 previous_position by 2^16 block combinations", "RTL semantics/synthesis/timing", "system throughput or saved cycles", "physical hardware behavior"]
    }
    AREA.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))

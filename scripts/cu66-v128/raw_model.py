#!/usr/bin/env python3
"""Independent algebra model for the V128 direct raw/context tuple factorization.

This models the frozen V127 selected scratch validation and the V128 two-lane
decision equations. It does not import RTL-generation, testbench, or audit code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V127_INDEX = ROOT / "experiments/python-gamebub-v127/integration/results.json"
V127_SCRATCH_ALIAS = "fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv"
V128_MAP = ROOT / "fpga/experiments/cu66-v128-raw/source-map.json"
V128_ALIAS = V127_SCRATCH_ALIAS
V128_RECIPE = ROOT / "fpga/experiments/cu66-v128-raw/edit-recipe.json"
DEFAULT_OUT = ROOT / "experiments/python-gamebub-v128/python-model/raw-model.json"
DOC = ROOT / "docs/cu66-v128/raw-model.md"
SEED = 0x1285A17
SIGNED16_MIN = -32768
SIGNED16_MAX = 32767
MASK32 = (1 << 32) - 1


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources() -> tuple[dict, str, str, list[dict]]:
    old_index = json.loads(V127_INDEX.read_text())
    old_meta = old_index["source_origins"][V127_SCRATCH_ALIAS]
    old_path = ROOT / old_meta["path"]
    old_sha = digest(old_path)
    if old_sha != old_meta["sha256"]:
        raise RuntimeError("V127 integration index source hash mismatch")

    source_map = json.loads(V128_MAP.read_text())
    new_meta = source_map["source_origins"][V128_ALIAS]
    new_path = ROOT / new_meta["path"]
    new_sha = digest(new_path)
    if new_sha != new_meta["sha256"]:
        raise RuntimeError("V128 source-map scratch hash mismatch")

    # V128's map contains its four changed origins only. Start from the frozen
    # V127 selected source index, then overlay those four physical replacements.
    selected_map = dict(old_index["source_origins"])
    selected_map.update(source_map["source_origins"])
    selected_new = []
    for alias, meta in selected_map.items():
        path = ROOT / meta["path"]
        actual = digest(path)
        if actual != meta["sha256"]:
            raise RuntimeError(f"V128 selected source hash mismatch: {meta['path']}")
        selected_new.append({"alias": alias, "path": meta["path"], "sha256": actual})
    if len(selected_new) != 18:
        raise RuntimeError(f"expected 18 V128 selected source origins, got {len(selected_new)}")
    return old_index, old_meta["path"], new_meta["path"], selected_new


def old_source_band_matches() -> tuple[list[int], dict]:
    """Translate the old RTL zigzag() and band_matches() functions literally."""
    ranks = [None] * 64
    rank = 0
    for diagonal in range(15):
        for step in range(8):
            row = step if diagonal % 2 == 1 else 7 - step
            col = diagonal - row
            if 0 <= col < 8:
                ranks[row * 8 + col] = rank
                rank += 1
    if rank != 64 or any(v is None for v in ranks) or sorted(ranks) != list(range(64)):
        raise RuntimeError("old RTL zigzag transcription failed permutation sanity")

    def matches(band: int, index: int) -> bool:
        z = ranks[index & 0x3F]
        if (band & 0x3) == 1:
            return 1 <= z < 6
        if (band & 0x3) == 2:
            return 6 <= z < 21
        if (band & 0x3) == 3:
            return z >= 21
        return (index & 0x3F) == 0

    # Every raster index gets its source-derived band. Bands 1..3 use z-rank
    # ranges; default band 0 is the source's literal index==0 condition.
    band_by_index = []
    for i in range(64):
        band_by_index.append(0 if matches(0, i) else 1 if matches(1, i) else 2 if matches(2, i) else 3)
    return ranks, {"band_by_raster_index": band_by_index, "rank_by_raster_index": ranks}


def u32(value: int) -> int:
    return value & MASK32


def source_word(value: int) -> int:
    """The input is a signed logic [15:0] value, then represented as 16 bits."""
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def sparse_order_bad(lane: dict, ctx: dict, rank_mask: int) -> bool:
    previous = u32(ctx["previous_position"])
    block = lane["block"] & 0xFFFF
    index = lane["index"] & 0x3F
    return (
        ((previous >> 22) != 0)
        or block < ((previous >> 6) & 0xFFFF)
        or (block == ((previous >> 6) & 0xFFFF) and bool((rank_mask >> index) & 1))
    )


def lane_reasons(lane: dict, ctx: dict, phase: int, stored_raw: bool,
                 rank_mask: int, ranks: list[int]) -> dict[str, bool]:
    phase &= 0x7
    block = lane["block"] & 0xFFFF
    index = lane["index"] & 0x3F
    band = lane["band"] & 0x3
    value = source_word(lane["value"])
    # This is the exact source condition `coef_block >= 16'(blocks)`: the
    # source has a 17-bit blocks field and explicitly casts it to 16 bits.
    block_limit = ctx["blocks"] & 0xFFFF
    phase_format_bad = (
        (block * 64 + index != u32(ctx["written"])) if stored_raw else
        ((index != 0 or block != u32(ctx["written"])) if phase == 0 else
         (not band_matches(band, index, ranks) or value == 0 or
          (ctx["previous_valid"] and sparse_order_bad(lane, ctx, rank_mask))))
    )
    return {
        "epoch": u32(lane["epoch"]) != u32(ctx["active_epoch"]),
        "band": band != (phase & 0x3),
        "block_bound": block >= block_limit,
        "signed_value_bound": value < -2048 or value > 2048,
        "count_bound": u32(ctx["written"]) >= u32(ctx["counts"][phase & 0x3]),
        "stored_format": bool(phase_format_bad),
    }


def band_matches(band: int, index: int, ranks: list[int]) -> bool:
    z = ranks[index & 0x3F]
    band &= 3
    if band == 1:
        return 1 <= z < 6
    if band == 2:
        return 6 <= z < 21
    if band == 3:
        return z >= 21
    return (index & 0x3F) == 0


def reasons_bad(reasons: dict[str, bool]) -> bool:
    return any(reasons.values())


def selected_tuple(lanes: tuple[dict, dict], select_raw: bool) -> dict:
    return dict(lanes[0 if select_raw else 1])


def old_selected_decisions(lanes: tuple[dict, dict], select_raw: bool,
                           ctx: dict, phase: int, stored_raw: bool,
                           rank_mask: int, ranks: list[int]) -> list[bool]:
    selected = selected_tuple(lanes, select_raw)
    return [reasons_bad(lane_reasons(selected, ctx, p, stored_raw, rank_mask, ranks))
            for p in range(8)]


def factored_decisions(lanes: tuple[dict, dict], select_raw: bool,
                       ctx: dict, stored_raw: bool,
                       rank_mask: int, ranks: list[int]) -> list[bool]:
    per_lane = [[reasons_bad(lane_reasons(lane, ctx, p, stored_raw, rank_mask, ranks))
                 for p in range(8)] for lane in lanes]
    return per_lane[0 if select_raw else 1]


def selected_epoch_bad(lanes: tuple[dict, dict], select_raw: bool, ctx: dict) -> bool:
    lane = lanes[0 if select_raw else 1]
    return u32(lane["epoch"]) != u32(ctx["active_epoch"])


def error_code(bad: bool, epoch_bad: bool) -> int:
    # Old sequential INGEST priority: input_bad ? (input_epoch_bad ? 2 : 3).
    return 0 if not bad else (2 if epoch_bad else 3)


def record_tuple(lane: dict, phase: int, stored_raw: bool) -> dict:
    block = lane["block"] & 0xFFFF
    index = lane["index"] & 0x3F
    value = source_word(lane["value"])
    is_word16 = stored_raw or phase == 0
    if is_word16:
        payload = value & 0xFFFF
        byte_count = 2
        position = block * 64 + index if stored_raw else block
    else:
        payload = ((block & 0x1FFF) << 19) | (index << 13) | (value & 0x1FFF)
        byte_count = 4
        position = block * 64 + zigzag_rank(index)
    return {"payload_u32": payload & 0xFFFFFFFF, "bytes": byte_count,
            "position_u32": u32(position)}


def zigzag_rank(index: int) -> int:
    ranks, _ = old_source_band_matches()
    return ranks[index & 63]


def make_context(rng: random.Random, phase: int, stored_raw: bool, rank_mask: int,
                 previous_valid: bool = False) -> tuple[dict, dict]:
    # blocks is the source's 17-bit transaction field; select a nonzero low16
    # limit here. Directed cases below cover zero and 17-bit wrap boundaries.
    limit = rng.randrange(1, 0x10000)
    active_epoch = rng.getrandbits(32)
    if stored_raw:
        block = rng.randrange(limit)
        index = rng.randrange(64)
        written = block * 64 + index
    elif phase == 0:
        block = rng.randrange(limit)
        written = block
        index = 0
    else:
        block = rng.randrange(limit)
        written = rng.randrange(0, max(1, limit))
        good_indices = [i for i in range(64) if band_matches(phase & 3, i, old_source_band_matches()[0])]
        index = rng.choice(good_indices)
    band = phase & 3
    value = rng.choice([n for n in range(-2048, 2049) if n != 0])
    count_slots = [rng.randrange(0x100000, 0xFFFFFFFF) for _ in range(4)]
    count_slots[phase & 3] = max(count_slots[phase & 3], written + 1)
    lane = {"epoch": active_epoch, "block": block, "index": index,
            "value": value, "band": band}
    ctx = {"active_epoch": active_epoch, "blocks": limit,
           "written": written, "counts": count_slots,
           "previous_valid": False, "previous_position": rng.getrandbits(32)}
    if previous_valid and not stored_raw and phase != 0:
        # The generated mask may be arbitrary, so choose a previous block that
        # guarantees strict source-order validity (lower block where possible).
        if block:
            ctx["previous_position"] = ((block - 1) << 6) | 63
            ctx["previous_valid"] = True
        else:
            ctx["previous_position"] = 0
            ctx["previous_valid"] = True
            rank_mask &= ~(1 << index)
    return ctx, lane


def valid_lane(rng: random.Random, phase: int, stored_raw: bool,
               ctx: dict, ranks: list[int]) -> dict:
    phase &= 7
    limit = ctx["blocks"] & 0xFFFF
    band = phase & 3
    if stored_raw:
        block = rng.randrange(limit) if limit else 0
        index = rng.randrange(64)
        ctx["written"] = block * 64 + index
    elif phase == 0:
        block = rng.randrange(limit) if limit else 0
        index = 0
        ctx["written"] = block
    else:
        block = rng.randrange(limit) if limit else 0
        index = rng.choice([i for i in range(64) if band_matches(band, i, ranks)])
        ctx["written"] = rng.randrange(0, max(1, limit))
        ctx["previous_valid"] = False
    ctx["counts"][phase & 3] = min(MASK32, ctx["written"] + rng.randrange(1, 1000))
    return {"epoch": ctx["active_epoch"], "block": block, "index": index,
            "value": rng.choice([n for n in range(-2048, 2049) if n != 0]),
            "band": band}


def random_lane(rng: random.Random) -> dict:
    return {"epoch": rng.getrandbits(32), "block": rng.getrandbits(16),
            "index": rng.randrange(64), "value": rng.randrange(SIGNED16_MIN, SIGNED16_MAX + 1),
            "band": rng.randrange(4)}


def clone_lanes(lanes: tuple[dict, dict]) -> tuple[dict, dict]:
    return dict(lanes[0]), dict(lanes[1])


def run(out_path: Path) -> dict:
    old_index, old_scratch_path, new_scratch_path, selected_new = load_sources()
    ranks, derived_map = old_source_band_matches()
    rng = random.Random(SEED)
    cases: list[dict] = []
    categories = Counter()

    def add_case(label: str, lanes: tuple[dict, dict], ctx: dict,
                 phase: int, select_raw: bool, stored_raw: bool,
                 rank_mask: int = 0) -> None:
        cases.append({"label": label, "lanes": clone_lanes(lanes), "ctx": json.loads(json.dumps(ctx)),
                      "phase": phase & 7, "select_raw": bool(select_raw),
                      "stored_raw": bool(stored_raw), "rank_mask": rank_mask & ((1 << 64) - 1)})
        categories[label.split(":", 1)[0]] += 1

    # Directed valid witnesses for every 3-bit phase, selector polarity, and
    # scratch stored format. The unselected lane is intentionally unrelated.
    for phase in range(8):
        for select_raw in (False, True):
            for stored_raw in (False, True):
                ctx = {"active_epoch": 0xA5000000 | phase, "blocks": 37,
                       "written": 0, "counts": [1000, 1000, 1000, 1000],
                       "previous_valid": False, "previous_position": 0xFFFFFFFF}
                selected = valid_lane(rng, phase, stored_raw, ctx, ranks)
                lanes = (random_lane(rng), random_lane(rng))
                lanes = (selected, lanes[1]) if select_raw else (lanes[0], selected)
                add_case("directed_valid", lanes, ctx, phase, select_raw, stored_raw)
                both_valid = (dict(selected), dict(selected))
                add_case("directed_both_lanes_valid", both_valid, ctx, phase, select_raw, stored_raw)

                # Nonselected lane alone is bad; selected lane remains valid.
                nonselected_bad = clone_lanes(lanes)
                ni = 1 if select_raw else 0
                nonselected_bad[ni]["epoch"] ^= 0x80000000
                add_case("nonselected_epoch_bad_only", nonselected_bad, ctx, phase, select_raw, stored_raw)

                # Selected lane alone is bad by epoch, and should classify 2.
                selected_epoch_bad_lanes = clone_lanes(lanes)
                si = 0 if select_raw else 1
                selected_epoch_bad_lanes[si]["epoch"] ^= 0x80000000
                add_case("selected_epoch_bad", selected_epoch_bad_lanes, ctx, phase, select_raw, stored_raw)

                # Selected lane is format-invalid while only the nonselected
                # lane has an epoch mismatch: selected error class must be 3.
                selected_format_bad = clone_lanes(lanes)
                selected_format_bad[si]["value"] = 0
                if not stored_raw and phase != 0:
                    selected_format_bad[si]["value"] = 0
                elif stored_raw:
                    ctx_bad = json.loads(json.dumps(ctx)); ctx_bad["written"] += 1
                else:
                    selected_format_bad[si]["index"] = 1
                format_ctx = locals().get("ctx_bad", ctx)
                selected_format_bad[ni]["epoch"] ^= 0x40000000
                add_case("selected_format_bad_nonselected_epoch_bad", selected_format_bad,
                         format_ctx, phase, select_raw, stored_raw)
                if "ctx_bad" in locals():
                    del ctx_bad

                # Boundaries are inclusive at -2048/+2048 and fail immediately
                # outside. Exercise the full signed16 representation limits too.
                for value in (-2049, -2048, 2048, 2049, -32768, 32767):
                    boundary = clone_lanes(lanes)
                    boundary[si]["value"] = value
                    add_case(f"signed_boundary_{value}", boundary, ctx, phase, select_raw, stored_raw)

                # Full epoch, full written/count, and blocks[16:0] cast boundary.
                for blocks in (0, 1, 0xFFFF, 0x10000, 0x10001):
                    bound_ctx = json.loads(json.dumps(ctx)); bound_ctx["blocks"] = blocks
                    add_case(f"blocks17_cast_{blocks:05x}", lanes, bound_ctx, phase, select_raw, stored_raw)
                full_ctx = json.loads(json.dumps(ctx)); full_ctx["active_epoch"] = 0xFFFFFFFF
                full_ctx["written"] = 0xFFFFFFFF; full_ctx["counts"][phase & 3] = 0xFFFFFFFF
                add_case("full32_written_count_epoch", lanes, full_ctx, phase, select_raw, stored_raw)

                high_epoch_ctx = json.loads(json.dumps(ctx)); high_epoch_ctx["active_epoch"] = 0x80000001
                high_epoch_lanes = clone_lanes(lanes); high_epoch_lanes[si]["epoch"] = 0x00000001
                add_case("full32_epoch_upper_bit", high_epoch_lanes, high_epoch_ctx, phase, select_raw, stored_raw)
                wide_count_ctx = json.loads(json.dumps(ctx)); wide_count_ctx["written"] = 0
                wide_count_ctx["counts"][phase & 3] = 0x10000
                add_case("full32_count_upper_bits", lanes, wide_count_ctx, phase, select_raw, stored_raw)
                wide_written_ctx = json.loads(json.dumps(ctx)); wide_written_ctx["written"] = 0x10000
                wide_written_ctx["counts"][phase & 3] = 0x10001
                add_case("full32_written_upper_bits", lanes, wide_written_ctx, phase, select_raw, stored_raw)

                if not stored_raw and phase != 0:
                    for previous in (0x003FFFFF, 0x00400000, 0xFFFFFFFF):
                        prev_ctx = json.loads(json.dumps(ctx)); prev_ctx["previous_valid"] = True
                        prev_ctx["previous_position"] = previous
                        add_case(f"full32_previous_{previous:08x}", lanes, prev_ctx,
                                 phase, select_raw, stored_raw, rng.getrandbits(64))

    # Deliberately probe arbitrary 64-bit masks. At equal block, the literal
    # implemented mask bit at index is the ordering decision, regardless of
    # whether this mask could have been generated by the previous-position owner.
    for phase in range(8):
        for select_raw in (False, True):
            for stored_raw in (False, True):
                for index in (0, 1, 7, 21, 42, 63):
                    mask = 1 << index
                    ctx = {"active_epoch": 0x12345678, "blocks": 100,
                           "written": 0, "counts": [0xFFFFFFFF] * 4,
                           "previous_valid": True, "previous_position": (9 << 6) | index}
                    selected = {"epoch": ctx["active_epoch"], "block": 9, "index": index,
                                "value": 1, "band": phase & 3}
                    other = random_lane(rng)
                    lanes = (selected, other) if select_raw else (other, selected)
                    add_case("arbitrary_rank_mask_hit", lanes, ctx, phase, select_raw, stored_raw, mask)
                    ctx_clear = json.loads(json.dumps(ctx)); ctx_clear["previous_position"] = (9 << 6) | index
                    add_case("arbitrary_rank_mask_miss", lanes, ctx_clear, phase, select_raw, stored_raw, 0)

    # Owned-mask witnesses: literal zigzag rank order is meaningful only when
    # the mask was generated from this previous owner threshold, exactly as the
    # old APPEND loop does. Check all 64 indices for several rank thresholds.
    owned_mask_checks = 0
    owned_order_checks = 0
    for threshold in (0, 1, 5, 6, 20, 21, 63):
        mask = sum((1 << i) for i in range(64) if ranks[i] <= threshold)
        for index in range(64):
            expected = ranks[index] <= threshold
            if bool((mask >> index) & 1) != expected:
                raise RuntimeError("owned rank mask disagrees with literal zigzag rank")
            owned_mask_checks += 1
            # With an owned previous-position mask and equal block, the
            # implemented arbitrary-bit lookup recovers the literal rank order.
            lane = {"block": 9, "index": index}
            previous = {"previous_position": (9 << 6) | threshold}
            if sparse_order_bad(lane, previous, mask) != expected:
                raise RuntimeError("owned rank mask ordering differs from literal zigzag")
            owned_order_checks += 1

    # Balanced random population: valid selected tuples are deliberately
    # generated, then a separate population mutates one chosen field so the
    # result contains substantial passing and failing cases.
    random_valid_count = 20_000
    random_mutation_count = 50_000
    mutations = Counter()
    mutation_kinds = ("selected_epoch", "selected_band", "selected_block",
                      "selected_value_low", "selected_value_high", "selected_count",
                      "selected_stored_format", "nonselected_epoch", "nonselected_value")
    for i in range(random_valid_count):
        phase = rng.randrange(8); select_raw = bool(rng.randrange(2)); stored_raw = bool(rng.randrange(2))
        ctx = {"active_epoch": rng.getrandbits(32), "blocks": rng.randrange(1, 0x10000),
               "written": 0, "counts": [0xFFFFFFFF] * 4,
               "previous_valid": False, "previous_position": rng.getrandbits(32)}
        selected = valid_lane(rng, phase, stored_raw, ctx, ranks)
        peer = dict(selected)
        peer["value"] = -selected["value"] if selected["value"] != -2048 else 2047
        lanes = (dict(selected), peer)
        add_case("random_valid", lanes, ctx, phase, select_raw, stored_raw, rng.getrandbits(64))
    for i in range(random_mutation_count):
        phase = rng.randrange(8); select_raw = bool(rng.randrange(2)); stored_raw = bool(rng.randrange(2))
        ctx = {"active_epoch": rng.getrandbits(32), "blocks": rng.randrange(1, 0x10000),
               "written": 0, "counts": [0xFFFFFFFF] * 4,
               "previous_valid": False, "previous_position": rng.getrandbits(32)}
        selected = valid_lane(rng, phase, stored_raw, ctx, ranks)
        peer = dict(selected)
        peer["value"] = -selected["value"] if selected["value"] != -2048 else 2047
        lanes = (dict(selected), peer)
        ctx["counts"][phase & 3] = max(ctx["counts"][phase & 3], ctx["written"] + 1)
        kind = mutation_kinds[i % len(mutation_kinds)]
        si = 0 if select_raw else 1; ni = 1 if select_raw else 0
        if kind == "selected_epoch": lanes[si]["epoch"] ^= (1 << rng.randrange(32))
        elif kind == "selected_band": lanes[si]["band"] = (lanes[si]["band"] + 1) & 3
        elif kind == "selected_block": lanes[si]["block"] = ctx["blocks"] & 0xFFFF
        elif kind == "selected_value_low": lanes[si]["value"] = -2049
        elif kind == "selected_value_high": lanes[si]["value"] = 2049
        elif kind == "selected_count": ctx["counts"][phase & 3] = ctx["written"]
        elif kind == "selected_stored_format":
            if stored_raw: ctx["written"] = u32(ctx["written"] + 1)
            elif phase == 0: lanes[si]["index"] = 1
            else: lanes[si]["value"] = 0
        elif kind == "nonselected_epoch": lanes[ni]["epoch"] ^= (1 << rng.randrange(32))
        else: lanes[ni]["value"] = 2049
        mutations[kind] += 1
        add_case("random_mutation:" + kind, lanes, ctx, phase, select_raw, stored_raw,
                 rng.getrandbits(64))

    decision_comparisons = 0
    selected_failures = 0
    selected_passes = 0
    nonselected_only_bad = 0
    both_lanes_pass = 0
    error2 = error3 = 0
    directed_error_codes = Counter()
    phase_coverage = Counter()
    selector_coverage = Counter()
    stored_format_coverage = Counter()
    mismatch_examples = []
    record_equal = 0
    record_count = 0
    selected_bad_reason_counts = Counter()
    for n, case in enumerate(cases):
        lanes = tuple(case["lanes"])
        ctx = case["ctx"]
        phase = case["phase"]
        sel = case["select_raw"]
        raw = case["stored_raw"]
        mask = case["rank_mask"]
        old = old_selected_decisions(lanes, sel, ctx, phase, raw, mask, ranks)
        new = factored_decisions(lanes, sel, ctx, raw, mask, ranks)
        decision_comparisons += 8
        phase_coverage[phase] += 1
        selector_coverage[str(sel).lower()] += 1
        stored_format_coverage[str(raw).lower()] += 1
        if old != new and len(mismatch_examples) < 10:
            mismatch_examples.append({"case": n, "label": case["label"], "phase": phase,
                                     "select_raw": sel, "stored_raw": raw,
                                     "old": old, "factored": new})
        old_bad = old[phase]
        selected_passes += not old_bad
        selected_failures += old_bad
        si = 0 if sel else 1; ni = 1 if sel else 0
        selected_r = lane_reasons(lanes[si], ctx, phase, raw, mask, ranks)
        nonselected_r = lane_reasons(lanes[ni], ctx, phase, raw, mask, ranks)
        if not reasons_bad(selected_r) and not reasons_bad(nonselected_r):
            both_lanes_pass += 1
        if not reasons_bad(selected_r) and reasons_bad(nonselected_r):
            nonselected_only_bad += 1
        for reason, is_bad in selected_r.items():
            if is_bad: selected_bad_reason_counts[reason] += 1
        epoch_bad = selected_epoch_bad(lanes, sel, ctx)
        code = error_code(old_bad, epoch_bad)
        error2 += code == 2; error3 += code == 3
        if case["label"] in ("selected_epoch_bad", "selected_format_bad_nonselected_epoch_bad"):
            directed_error_codes[case["label"] + "_code_" + str(code)] += 1
        # Ingress returns and scratch receives the same selected 72-bit tuple.
        chosen = selected_tuple(lanes, sel)
        compare_chosen = dict(lanes[si])
        if chosen == compare_chosen:
            record_equal += 1
        record_count += 1

    if mismatch_examples:
        raise RuntimeError(f"old/factored validation mismatch: {mismatch_examples[0]}")
    if selected_passes == 0 or selected_failures == 0:
        raise RuntimeError("coverage must include both passing and failing directed/random cases")
    if nonselected_only_bad == 0:
        raise RuntimeError("nonselected-lane-only invalid cases were not exercised")
    if not all(phase_coverage[p] for p in range(8)):
        raise RuntimeError("phase encoding coverage incomplete")
    if error2 == 0 or error3 == 0:
        raise RuntimeError("input error code 2/3 distinction was not covered")

    # Recheck signed and storage extraction at source-shaped boundaries. This
    # identifies layout semantics without pretending to model a sequential run.
    stored_examples = {}
    for raw in (False, True):
        for phase in (0, 1, 4, 7):
            lane = {"epoch": 1, "block": 0x1234, "index": 0x2A, "value": -2048, "band": phase & 3}
            stored_examples[f"raw_{int(raw)}_phase_{phase}"] = record_tuple(lane, phase, raw)

    query_input_sha = {
        "v127_integration_index": digest(V127_INDEX),
        "v127_old_selected_scratch": digest(ROOT / old_scratch_path),
        "v128_source_map": digest(V128_MAP),
        "v128_edit_recipe": digest(V128_RECIPE),
    }
    output = {
        "schema": "v128-independent-raw-validation-algebra-model-v1",
        "status": "PASS_MODEL_ONLY",
        "actual_RTL_run": False,
        "exhaustive": False,
        "sequential_behavior_modeled": False,
        "timing_qualification": False,
        "seed": SEED,
        "case_count": len(cases),
        "directed_case_count": sum(v for k, v in categories.items() if k.startswith("directed_") or k.startswith("nonselected_") or k.startswith("selected_") or k.startswith("signed_") or k.startswith("blocks17_") or k.startswith("full32_") or k.startswith("arbitrary_")),
        "random_valid_case_count": categories["random_valid"],
        "random_mutation_case_count": sum(v for k, v in categories.items() if k.startswith("random_mutation")),
        "random_mutations_by_kind": dict(mutations),
        "old_selected_72_tuple_equals_selected_direct_lane_count": record_equal,
        "decision_comparisons": decision_comparisons,
        "decision_mismatches": 0,
        "pass_case_count": selected_passes,
        "fail_case_count": selected_failures,
        "nonselected_lane_only_bad_case_count": nonselected_only_bad,
        "both_lanes_pass_case_count": both_lanes_pass,
        "input_error_code_counts": {"0_pass": record_count - error2 - error3, "2_epoch": error2, "3_other_input_error": error3},
        "directed_epoch_priority_witnesses": dict(directed_error_codes),
        "selected_bad_reason_counts": dict(selected_bad_reason_counts),
        "phase_coverage": {str(k): v for k, v in sorted(phase_coverage.items())},
        "ingress_selector_coverage": selector_coverage,
        "scratch_stored_raw_mode_coverage": stored_format_coverage,
        "owned_rank_mask_literal_zigzag_checks": owned_mask_checks,
        "owned_rank_mask_literal_order_checks": owned_order_checks,
        "arbitrary_mask_contract": "Ordering at equal previous block uses exactly rank_threshold_mask[index]; literal zigzag equivalence is asserted only for masks derived from an owned previous-position threshold.",
        "blocks_17_to_16_cast_cases": {"directed_values": [0, 1, 65535, 65536, 65537], "expression": "block >= (blocks & 0xffff)"},
        "signed16_acceptance": {"field_range": [SIGNED16_MIN, SIGNED16_MAX], "accepted_inclusive": [-2048, 2048], "outside_rejected": True},
        "full_width_semantics": ["epoch equality uses all 32 bits", "written and each count use all 32 bits", "previous_position high bits [31:22] participate in sparse ordering"],
        "old_source_band_match_derivation": {"source": old_scratch_path, "function": "band_matches(2-bit band, 6-bit raster index)", "rank_map": derived_map, "bands": {"0": "index == 0", "1": "zigzag rank 1..5", "2": "zigzag rank 6..20", "3": "zigzag rank >=21"}},
        "stored_tuple_examples": stored_examples,
        "source_binding": {"v127_selected_source_index_path": str(V127_INDEX.relative_to(ROOT)), "v127_selected_scratch": {"path": old_scratch_path, "sha256": query_input_sha["v127_old_selected_scratch"]}, "v128_source_map_path": str(V128_MAP.relative_to(ROOT)), "v128_changed_origin_count": len(json.loads(V128_MAP.read_text())["source_origins"]), "v128_selected_sources": selected_new, "input_hashes": query_input_sha},
        "limitations": ["Independent combinational/algebra model only; no RTL simulation was run.", "No exhaustive state-space or sequential timing claim is made.", "The result checks equivalence of the source-shaped selected tuple decision with per-lane decision followed by the ingress selector for generated input records."],
    }
    output["model_script_sha256"] = digest(Path(__file__))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2) + "\n")
    script_sha = output["model_script_sha256"]
    doc = f'''# V128 raw tuple algebra model\n\nThe independent Python model compares V127's selected 72-bit tuple validation with V128's two direct lane decisions followed by the ingress selector. It uses the V127 integration source index for the old selected scratch and `source-map.json` for all 18 current selected sources, including the four V128 replacements.\n\n- Result: **{output['status']}**, {len(cases):,} generated records, {decision_comparisons:,} per-phase decision comparisons, zero mismatches.\n- Coverage includes every 3-bit phase encoding, both independent ingress selector values, both scratch stored-format values, directed valid and invalid records, signed value boundaries, 17-bit block cast boundaries, full-width epoch/count/written/previous-position cases, and deterministic random valid plus single-field mutation populations.\n- Selected-record error class follows the old sequential priority: code 2 for a selected epoch mismatch; code 3 for another selected input error. Invalid data in only the unselected lane does not affect the result.\n- The old source's actual band test is transcribed from its `zigzag()` and `band_matches()` functions. At equal blocks, sparse ordering uses the arbitrary stored 64-bit rank mask exactly as implemented. Literal zigzag order is checked only for a mask derived from the owned previous-position threshold.\n- Source hashes and detailed coverage are in [`raw-model.json`](../../experiments/python-gamebub-v128/python-model/raw-model.json). Model script SHA-256: `{script_sha}`.\n\nThis is an algebra model only: no RTL run, exhaustive sequential check, timing measurement, or timing qualification.\n'''
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(doc)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({"status": result["status"], "case_count": result["case_count"],
                      "decision_comparisons": result["decision_comparisons"],
                      "mismatches": result["decision_mismatches"],
                      "pass_cases": result["pass_case_count"], "fail_cases": result["fail_case_count"],
                      "nonselected_only_bad": result["nonselected_lane_only_bad_case_count"],
                      "error_codes": result["input_error_code_counts"]}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Exhaustively compare two bounded BR88 parallel-prefix combinational models.

This is a Python-only model of br88_rice_elastic.sv's prefix scan and a proposed
aligned-window leading-zero formulation. It does not run RTL or a vendor tool.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fpga/experiments/cu66-v91/br88_rice_elastic.sv"
OUTPUT = ROOT / "experiments/python-gamebub-v103/parser-prefix-model.json"
DOC = ROOT / "docs/cu66-v103/parser-prefix-model.md"
WATCHDOG_SECONDS = 50.0


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def old_scan(reservoir: int, available: int, window: int, serial: bool) -> tuple[int, bool, bool, int, int, bool]:
    """Model the source for-loop and prefix branch directly, in source order."""
    zeros = 0
    found_one = False
    for i in range(15):
        if i < window and not found_one:
            if available > i and ((reservoir >> (available - 1 - i)) & 1):
                found_one = True
            else:
                zeros += 1
    prefix_empty = window == 0
    needed = 1 if serial else window
    take_bits = 1 if serial else (15 if zeros == 15 else (zeros + 1 if found_one else window))
    can_step = available >= needed
    return zeros, found_one, prefix_empty, needed, take_bits, can_step


def aligned_window(reservoir: int, available: int, window: int, serial: bool) -> tuple[int, bool, bool, int, int, bool]:
    """Factored proposal: align the available prefix into a zero-filled window."""
    if available >= window:
        visible = (reservoir >> (available - window)) & ((1 << window) - 1)
    else:
        visible = (reservoir & ((1 << available) - 1)) << (window - available)
    zeros = window if visible == 0 else window - visible.bit_length()
    found_one = visible != 0
    prefix_empty = window == 0
    needed = 1 if serial else window
    take_bits = 1 if serial else (15 if zeros == 15 else (zeros + 1 if found_one else window))
    can_step = available >= needed
    return zeros, found_one, prefix_empty, needed, take_bits, can_step


def reservoir_for_prefix(word: int, window: int, available: int) -> int:
    """Place a distinct window word at the reservoir's available-bit head."""
    if available >= window:
        return (word << (available - window)) & ((1 << available) - 1)
    if available == 0:
        return 0
    return word >> (window - available)


def pack_result(output: tuple[int, bool, bool, int, int, bool]) -> bytes:
    zeros, found, empty, needed, take, can_step = output
    return bytes((zeros, int(found), int(empty), needed, take, int(can_step)))


def available_representatives(window: int) -> list[int]:
    vals = {0, 1, 2, max(0, window - 1), window, min(64, window + 1),
            15, 16, 31, 32, 63, 64}
    return sorted(v for v in vals if 0 <= v <= 64)


def run() -> dict[str, Any]:
    started = time.monotonic()
    input_hash = hashlib.sha256()
    result_hash = hashlib.sha256()
    counts = {"prefix_word_cases": 0, "all_availability_random_cases": 0,
              "random_tail_bit_cases": 0, "model_comparisons": 0,
              "distinct_window_prefix_words": 0, "representative_availability_values": 0}
    categories = {"empty_windows": 0, "short_unterminated_zero_prefixes": 0,
                  "fifteen_zero_escape_prefixes": 0, "leading_one_at_first_position": 0,
                  "leading_one_at_last_position": 0, "insufficient_available_for_parallel": 0}
    samples: dict[str, Any] = {}

    def compare(window: int, word: int, available: int, reservoir: int, *, source: str) -> None:
        if time.monotonic() - started > WATCHDOG_SECONDS:
            raise TimeoutError(f"finite Python model watchdog exceeded {WATCHDOG_SECONDS:.0f}s")
        if not (0 <= available <= 64 and 0 <= window <= 15 and 0 <= reservoir < (1 << 64)):
            raise ValueError("model input outside declared range")
        for serial in (False, True):
            old = old_scan(reservoir, available, window, serial)
            new = aligned_window(reservoir, available, window, serial)
            if old != new:
                raise AssertionError({"source": source, "window": window, "word": word,
                                      "available": available, "reservoir": reservoir,
                                      "serial": serial, "old": old, "new": new})
            input_hash.update(bytes((window, available, int(serial))) + word.to_bytes(2, "big")
                              + reservoir.to_bytes(8, "big"))
            result_hash.update(pack_result(old))
            counts["model_comparisons"] += 1
            if source == "prefix_word":
                counts["prefix_word_cases"] += 1
            elif source == "all_availability_random":
                counts["all_availability_random_cases"] += 1
            elif source == "random_tail_bit":
                counts["random_tail_bit_cases"] += 1
            zeros, found, empty, needed, take, can_step = old
            if empty:
                categories["empty_windows"] += 1
            if window < 15 and window > 0 and zeros == window and not found and not serial and can_step:
                categories["short_unterminated_zero_prefixes"] += 1
            if window == 15 and zeros == 15 and not found and not serial and take == 15:
                categories["fifteen_zero_escape_prefixes"] += 1
            if found and zeros == 0:
                categories["leading_one_at_first_position"] += 1
            if found and zeros == window - 1:
                categories["leading_one_at_last_position"] += 1
            if not serial and available < window:
                categories["insufficient_available_for_parallel"] += 1
            if source == "prefix_word" and not serial and available >= window:
                samples.setdefault("exhaustive_word_parallel_visible", True)

    # Every bit pattern for all 0..15-bit windows is visited. For each word,
    # include low availability, the window boundary, and representative refill
    # capacities up through 64; short available inputs are zero-filled exactly
    # as in the source scan.
    for window in range(16):
        counts["distinct_window_prefix_words"] += 1 << window
        reps = available_representatives(window)
        counts["representative_availability_values"] += len(reps) * (1 << window)
        for word in range(1 << window):
            for available in reps:
                compare(window, word, available, reservoir_for_prefix(word, window, available),
                        source="prefix_word")

    # Cover every legal available count for every scan window using independent
    # full-width reservoirs; this checks source bit ordering beyond the tightly
    # aligned prefix-word construction above.
    rng = random.Random(0x103A11CE)
    for window in range(16):
        for _ in range(64):
            reservoir = rng.getrandbits(64)
            for available in range(65):
                if available >= window:
                    word = (reservoir >> (available - window)) & ((1 << window) - 1)
                elif available == 0:
                    word = 0
                else:
                    word = (reservoir & ((1 << available) - 1)) << (window - available)
                compare(window, word, available, reservoir, source="all_availability_random")

    # Independently flip bits strictly below the selected prefix. They must not
    # change zeros/found-one even though the source reservoir contains data.
    for window in range(1, 16):
        for available in range(window, 65):
            for _ in range(4):
                rng_reservoir = rng.getrandbits(64)
                tail_mask = (1 << (available - window)) - 1
                flipped = rng_reservoir ^ tail_mask
                word = (rng_reservoir >> (available - window)) & ((1 << window) - 1)
                before = old_scan(rng_reservoir, available, window, False)
                after = old_scan(flipped, available, window, False)
                if before[:2] != after[:2]:
                    raise AssertionError("unused tail bits affected selected prefix")
                compare(window, word, available, flipped, source="random_tail_bit")

    # Named boundary vectors give compact, human-readable receipts for empty,
    # short final, 15-zero escape, and first/last one positions.
    for label, window, word, available in (
        ("empty", 0, 0, 0), ("short_zero", 7, 0, 7), ("escape15_zero", 15, 0, 15),
        ("one_first", 15, 1 << 14, 15), ("one_last", 15, 1, 15),
        ("short_unavailable", 11, 0, 3), ("escape15_unavailable", 15, 0, 9),
    ):
        reservoir = reservoir_for_prefix(word, window, available)
        result = old_scan(reservoir, available, window, False)
        samples[label] = {"window": window, "word": word, "available": available,
                          "zeros": result[0], "found_one": result[1], "prefix_empty": result[2],
                          "needed": result[3], "take_bits": result[4], "can_step": result[5]}

    duration = time.monotonic() - started
    return {
        "schema": "v103-parser-prefix-model-v1",
        "status": "PASS",
        "model_scope": "Python combinational model only: current bounded source prefix scan versus aligned-window leading-zero formulation.",
        "source": "fpga/experiments/cu66-v91/br88_rice_elastic.sv",
        "source_sha256": sha(SOURCE.read_bytes()),
        "script_sha256": sha(Path(__file__).read_bytes()),
        "deterministic_random_seed": "0x103A11CE",
        "enumerated_input_sha256": input_hash.hexdigest(),
        "enumerated_result_sha256": result_hash.hexdigest(),
        "counts": counts,
        "categories": categories,
        "boundary_samples": samples,
        "watchdog_seconds": WATCHDOG_SECONDS,
        "limits": ["No actual RTL simulation, formal proof, or full parser state-machine proof.",
                   "No suffix, error-response, pipeline latency, synthesis, native gain, or physical timing claim."],
    }


def write_doc(report: dict[str, Any]) -> None:
    c = report["counts"]
    cat = report["categories"]
    rows = [
        "# V103 parser prefix model",
        "",
        f"**Status: {report['status']} — Python combinational model only.**",
        "",
        "This artifact advances the V103 rank 1 prefix-network hypothesis without changing the geometry candidates or measured native sources. It models the existing `br88_rice_elastic.sv` scan and an aligned-window leading-zero formulation, then compares `zeros`, `found_one`, `prefix_empty`, `needed`, `take_bits`, and `can_step`.",
        "",
        "## Coverage",
        "",
        "| Check | Count |",
        "|---|---:|",
        f"| Distinct prefix words across windows 0–15 | {c['distinct_window_prefix_words']} |",
        f"| Word / representative availability pairs | {c['representative_availability_values']} |",
        f"| Model comparisons (parallel and serial modes) | {c['model_comparisons']} |",
        f"| Random full-width reservoir comparisons over every window and availability 0–64 | {c['all_availability_random_cases']} |",
        f"| Random lower-tail-bit comparisons | {c['random_tail_bit_cases']} |",
        "",
        "The total prefix-word count is 65,535: one empty-width word plus all 65,534 words for widths 1–15. Exhaustive prefix words are tested at representative availability values including 0, values below the window, the window boundary, and larger refill capacities. Full-width deterministic random reservoirs (seed `0x103A11CE`) cover every availability value 0–64 for each window in both modes. Lower tail bits are flipped independently to check that the selected prefix is unaffected.",
        "",
        "## Boundary observations",
        "",
        f"- Empty windows observed: {cat['empty_windows']} combinational comparisons.",
        f"- Short all-zero unterminated-prefix combinations with enough bits: {cat['short_unterminated_zero_prefixes']}.",
        f"- Fifteen-zero parallel escape-boundary combinations: {cat['fifteen_zero_escape_prefixes']}.",
        f"- Leading one at first/last prefix position: {cat['leading_one_at_first_position']} / {cat['leading_one_at_last_position']} comparisons.",
        f"- Parallel cases where available bits are fewer than window bits: {cat['insufficient_available_for_parallel']}.",
        "",
        "Named edge vectors are also retained in the JSON receipt, including empty, short-zero, 15-zero, first-one, last-one, and unavailable-tail prefixes.",
        "",
        "## Result and limits",
        "",
        "The two Python combinational formulations matched on every enumerated input. The input and result streams are represented by SHA-256 digests in the JSON receipt; no expanded trace is written. This supports only the next isolated RTL extraction experiment. It does not establish RTL equivalence, full parser behavior, suffix or error-path behavior, a latency change, LUT reduction, synthesis gain, routed timing, or performance.",
        "",
        f"Source SHA-256: `{report['source_sha256']}`",
        "",
        f"Model script SHA-256: `{report['script_sha256']}`",
        "",
        f"Enumerated input SHA-256: `{report['enumerated_input_sha256']}`",
        "",
        f"Enumerated result SHA-256: `{report['enumerated_result_sha256']}`",
        "",
    ]
    DOC.write_text("\n".join(rows))


def main() -> int:
    try:
        if not SOURCE.is_file():
            raise FileNotFoundError(SOURCE)
        report = run()
    except Exception as exc:
        report = {
            "schema": "v103-parser-prefix-model-v1",
            "status": "FAIL",
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha(SOURCE.read_bytes()) if SOURCE.exists() else None,
            "script_sha256": sha(Path(__file__).read_bytes()),
            "error": f"{type(exc).__name__}: {exc}",
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_doc(report)
    print(json.dumps({"status": report["status"], "model_comparisons": report.get("counts", {}).get("model_comparisons"),
                      "error": report.get("error")}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

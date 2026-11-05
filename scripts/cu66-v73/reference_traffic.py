#!/usr/bin/env python3
"""Synthetic all-tiles reference-read/cache traffic model for the CU66 v73 study.

This is a deterministic Python standard-library model, not RTL or a live CU66
request trace. Run from any directory; JSON goes to stdout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "fpga/experiments/cu66-v70/memory/memory_map.hpp"
BASELINE_PINS = ROOT / "fpga/experiments/cu66-v73/baseline-sources.json"
BASE = 0x080000
PLANES = (("Y", 90, 360, 0), ("U", 45, 180, 172800), ("V", 45, 180, 216000))
TILE_BYTES = 64
BL8_WORDS = 8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RRCache:
    """N-entry round-robin replacement cache, tagged by physical BL8 address."""
    def __init__(self, ways: int):
        self.ways = ways
        self.tags: list[int | None] = [None] * ways
        self.next_victim = 0

    def access(self, tag: int) -> bool:
        if tag in self.tags:
            return True
        self.tags[self.next_victim] = tag
        self.next_victim = (self.next_victim + 1) % self.ways
        return False


def row_start(plane_base: int, pitch: int, width: int, tile_index: int, row: int) -> int:
    return plane_base + (tile_index // width) * 8 * pitch + (tile_index % width) * 4 + row * pitch


def simulate(ways: int, wide_rows: bool) -> dict:
    cache = RRCache(ways)
    fields = ("tile_requests", "row_requests", "word_requests", "useful_words",
              "cache_misses", "read_bursts", "read_beats", "wire_bytes",
              "useful_bytes", "overfetch_bytes")
    out = {**{key: 0 for key in fields}, "per_plane": {}}
    for name, width, pitch, offset in PLANES:
        totals = {key: 0 for key in fields}
        for idx in range(width * (60 if name == "Y" else 30)):
            totals["tile_requests"] += 1
            for row in range(8):
                addr = row_start(BASE + offset, pitch, width, idx, row)
                assert addr & 7 in (0, 4), (name, idx, row, hex(addr))
                # Each row contributes the four logical x16 words in the selected half.
                selected = tuple(addr + k for k in range(4))
                assert selected == tuple(range(addr, addr + 4))
                assert (selected[0] & 7) in (0, 4) and (selected[-1] & 7) in (3, 7)
                end = BASE + offset + (60 if name == "Y" else 30) * 8 * pitch
                assert selected[0] >= BASE + offset and selected[-1] < end
                totals["row_requests"] += 1
                reqs = selected if not wide_rows else (addr,)
                # word_requests counts API calls: scalar-word calls in v72,
                # four-word row calls in v73. useful_words is logical payload.
                totals["word_requests"] += len(reqs)
                totals["useful_words"] += 4
                for req_addr in reqs:
                    hit = cache.access(req_addr >> 3)
                    if not hit:
                        totals["cache_misses"] += 1
                        totals["read_bursts"] += 1
        totals["read_beats"] = totals["read_bursts"] * BL8_WORDS
        totals["wire_bytes"] = totals["read_beats"] * 2
        totals["useful_bytes"] = totals["useful_words"] * 2
        totals["overfetch_bytes"] = totals["wire_bytes"] - totals["useful_bytes"]
        out["per_plane"][name] = totals
        for key in totals:
            if key in out and key != "per_plane":
                out[key] += totals[key]
    out["cache_entries"] = ways
    out["request_shape"] = "four_word_row" if wide_rows else "scalar_word"
    out["word_requests_semantics"] = "API calls (scalar word calls in v72; four-word row calls in v73)"
    out["physical_read_beat_semantics"] = "8 x16 beats per BL8 read burst; 2 wire bytes per beat"
    return out


def adjacent_pair_check() -> dict:
    # Two adjacent luma tiles, first row only: shared BL8s survive with 8 entries.
    row_addrs = [row_start(BASE, 360, 90, idx, 0) for idx in (0, 1)]
    results = {}
    for ways in (1, 8):
        cache = RRCache(ways)
        misses = hits = 0
        for addr in row_addrs:
            if cache.access(addr >> 3): misses += 1
            else: hits += 1
        results[str(ways)] = {"misses": misses, "hits": hits}
    assert results["1"] == {"misses": 1, "hits": 1}
    assert results["8"] == {"misses": 1, "hits": 1}
    # Compare the v73 wide-row 8-entry cache with v72 scalar words/1-entry.
    full = {}
    for ways in (1, 8):
        cache = RRCache(ways)
        misses = hits = 0
        for idx in (0, 1):
            for row in range(8):
                addr = row_start(BASE, 360, 90, idx, row)
                reqs = (addr,) if ways == 8 else tuple(addr + word for word in range(4))
                for req_addr in reqs:
                    if cache.access(req_addr >> 3): hits += 1
                    else: misses += 1
        full[str(ways)] = {"misses": misses, "hits": hits}
    assert full["1"] == {"misses": 16, "hits": 48}
    assert full["8"] == {"misses": 8, "hits": 8}
    return {"one_row_per_tile": results, "full_adjacent_tile_pair": full}


def main() -> None:
    # Ensure the stated canonical mapping is still the source of this model's base.
    map_text = MAP.read_text(encoding="utf-8")
    assert "CANONICAL0_BASE=0x080000" in map_text
    # Odd chroma pitch must alternate selected-half placement on successive rows.
    chroma_halves = [row_start(BASE + 172800, 180, 45, 0, r) & 7 for r in range(8)]
    assert chroma_halves == [0, 4] * 4
    report = {
        "schema": "cu66-v73-reference-traffic-v1",
        "scope": "synthetic raster-order all-tiles traffic; not actual CU66 P-request set, FPS, or live-target proof",
        "mapping": {"base_word": BASE, "Y_offset_words": 0, "U_offset_words": 172800,
                    "V_offset_words": 216000, "Y_tiles": 5400, "U_tiles": 1350,
                    "V_tiles": 1350, "total_tiles": 8100, "Y_pitch_words": 360,
                    "chroma_pitch_words": 180, "selected_words_per_row": 4,
                    "bl8_words": 8, "bl8_tag": "address >> 3"},
        "placement_checks": {"chroma_row_lowbits": chroma_halves,
                             "valid_halves": [0, 4], "out_of_bounds": False},
        "self_check": adjacent_pair_check(),
        "v72_scalar_cache1": simulate(1, False),
        "v73_rowwide_cache8": simulate(8, True),
        "source_sha256": {**json.loads(BASELINE_PINS.read_text(encoding="utf-8"))["source_sha256"],
                          "scripts/cu66-v73/reference_traffic.py": sha256(Path(__file__))},
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

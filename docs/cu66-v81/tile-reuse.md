# V81 exact tile reuse screen

This is a native-only equality screen over the 457 immutable native decoder
fixtures: four independent histories (cohorts 0–3), one walkthrough family.
For each accepted frame, the screen compares each canonical 8×8 tile with the
same tile in the immediately previous accepted frame in that history. The
first source in a history has no predecessor. The corpus contains 20 key
sources and 437 delta sources; keys are measured separately and excluded from
the hypothetical write-elision counts.

## Delta-source results

The table gives per-source medians across delta sources in each cohort. Each
row has 294 identical hidden tiles (fixed canonical-128 regions), shown
separately from visible tiles. The total includes both visible and hidden
tiles.

| Cohort | Delta sources | Median identical visible tiles | Median identical hidden tiles | Median identical total tiles |
|---:|---:|---:|---:|---:|
| 0 | 114 | 4,483.5 | 294 | 4,777.5 |
| 1 | 114 | 4,296 | 294 | 4,590 |
| 2 | 114 | 7,228 | 294 | 7,522 |
| 3 | 95 | 3,408 | 294 | 3,702 |

Across the 437 deltas, 2,345,125 tiles were exactly equal to the immediately
previous accepted frame. If each such tile were represented by a reusable
reference, this would correspond to 9,380,500 hypothetical canonical BL8
writes avoided: four 128-bit writes per 512-bit tile. The baseline count is
14,806,800 canonical BL8 writes across all 457 sources. These are arithmetic
what-if counts, not measured memory traffic or savings.

The 294 hidden tiles per frame remain a separate fixed-128 category. They are
included in equality totals, but key sources are ineligible for elision. The
native decoder still checks the full canonical SHA, packet hash, HUD digest,
and display digest. The screen changes no RTL or protocol and implements no
tile map, aliasing, allocation/refcounts, or scanout-coherence handling. It
does not price metadata, indirection, or reference traffic; these costs could
reduce or erase any benefit. It claims no reduction in entropy, arithmetic,
reads, or authentication work, no latency savings, and no proof of 30 fps or
strict under-10-ms latency.

## Reproduction and retained evidence

From the repository root, the analyzer has no CLI options and runs a fresh
native screen with:

```sh
python3 scripts/cu66-v81/analyze_tile_reuse.py
```

The retained attempt documented here is
[`results.json`](../../fpga/experiments/cu66-v81/tile-reuse/attempt-20261106T042021082509Z-1b67892f/results.json)
with per-source masks and counts in
[`frames.json`](../../fpga/experiments/cu66-v81/tile-reuse/attempt-20261106T042021082509Z-1b67892f/frames.json).
The native comparison implementation is
[`tile_reuse.cpp`](../../fpga/experiments/cu66-v81/tile-reuse/tile_reuse.cpp);
the report retains the exact build/run commands, logs, source hashes, and
source snapshot. Re-running the analyzer creates a new attempt directory.

# Exact RGB565 UI payload reuse at 720×480

This standalone Python experiment reuses unchanged HUD-region work even while
the full game background changes. `ui_cache.PatchCache(max_entries=4)` plugs into
the frozen `hybrid.select_frame(..., patch_encoder=cache)` callback. It retains at
most four LRU entries keyed by canvas geometry, declared rectangle and patch
policy. Every invocation converts the current source rectangle to RGB565 and
compares every word. A hit returns the immutable prior full HP01/HR01 payload.
RGB888 changes within one RGB565 word correctly remain eligible for reuse.

The frozen selector still decodes/validates each patch, checks the complete frame
cap, assembles HG01 and enforces observed work budgets. Full packets still cross
the link and undergo receiver decoding; patches never enter the immutable YUV
prediction anchor. This changes host work, not packet size, reference rules,
rendered words or a negotiated codec profile.

On a hit, details report zero **current** encoder candidates and no current
encoding attempts. Any retained candidate history is separately labeled
`reused_candidate_details`; its historical timings are not current paid work.
Current conversion, comparison, metadata/copy work, normal validation and assembly
remain inside measured selector wall time. Misses pay their extra word conversion
and copy in addition to actual HP01/all-HR01 candidate encoding.

Six tests cover byte-identical output, current-word mutation, background changes,
RGB888 changes within the same RGB565 words, canvas/rectangle/policy separation,
four-entry eviction, cap fallback/base rejection and budget expiry with paid
lookup/validation. No existing codec files are modified.

## Paired selector results

| Source | Hits / patch attempts | Hits while full source changed | Mean selector, frozen → cached |
| --- | ---: | ---: | ---: |
| Combat, 60 native IDs | 213 / 240 | 109 | 5.78 → 1.68 ms |
| Second, 60 native IDs | 9 / 240 | 9 | 8.60 → 8.64 ms |
| Combat, 8 held-out keys | 26 / 32 | 14 | 6.05 → 2.01 ms |
| Second, 8 held-out keys | 0 / 32 | 0 | 8.70 → 8.83 ms |
| Synthetic moving background/static UI | 44 / 48 | 44 | 6.38 → 0.95 ms |
| Synthetic moving background/changing UI | 0 / 48 | 0 | 6.37 → 6.54 ms |

All **160 complete HG01 pairs are byte-identical**, including every selected
patch byte. Independently decoded output matches and all 21,120 selected RGB565
words per frame remain exact. All packets fit 49,152 bytes. There are 292 hits
among 640 attempts, including 176 hits while the complete source image changed.
The combat selector improves 70.9%; the second sample has a 0.45% overhead. The
synthetic static-UI control has 12 distinct full source images and an 85.1%
selector improvement; its changing-UI counterpart demonstrates the miss cost.
These are whole selector timings, not complete encoder/decoder or frame periods.

Common actual GM01 preparation is shared by the two selectors and excluded from
these selector clocks, along with source capture/BOX resize and independent
correctness decoding/hashes. AB/BA selector order alternates each source ID; host
load is uncontrolled. Native footage is related precompressed 25/29.88 fps and
contains repeated images; the primary 120 native IDs contain 32+60 distinct RGB
images. The two eight-key held-out sets contain four/eight distinct images.
Configured rectangles are not verified real game HUD locations.

The largest reported persistent cache is **51,286 bytes** (exact rectangle words
plus full encoded payloads). Counts exclude Python object/history metadata,
temporary conversion/validation arrays and transient old/new overlap during
replacement. This is not a process-peak or physical target memory measurement.
There are no raw source-frame, transform or reference-image copies in this cache.

**The 16-case parent finite execution results do not include this UI cache.**
The later [credit-window study](../python-game-credit-window-study/README.md)
integrates it in both credit arms. This benchmark remains a separate selector-only
comparison. No
native sender mode, ESP32/FPGA implementation, physical memory service or sustained
hardware 30 fps is proved. Keep the 720×480 coded/720×405 active native target.

Run with the study virtual environment from this directory:

```sh
python -m unittest -v test_ui_cache.py
python verify.py                    # read-only retained checks
python benchmark.py > run.log 2>&1   # regenerate; requires external source media
```

`results.json` pins 14 executed source files plus source-media manifests. Every
row retains full packet hashes, patch sizes, selected regions, exact-word checks,
current/historical candidate accounting and paired wall costs.

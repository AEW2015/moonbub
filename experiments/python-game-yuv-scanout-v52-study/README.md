# V52 one-line RGB565 scanout from exact YUV420 and HUD inputs

This prototype emits one RGB565 output line directly from immutable 8-bit
YUV420 planes, then overlays the exact four opaque RGB565 HUD patches. It keeps
the frozen horizontal-then-vertical chroma averaging, color arithmetic,
clamping and HUD behavior. It does not materialize a full RGB565 frame.

## Exact scanout replay

The campaign processes 96 actual decoded CS38 frames, the first 24 frames from
each of four v40 cohorts. It emits 46,080 lines, 33,177,600 exact RGB565 words
and 2,027,520 exact HUD words. The scanout implementation matches the frozen
full-frame composition on every output word; the YUV and HUD inputs remain
caller-owned read-only arrays. Four scanout tests and three memory-budget tests
pass. Independent replay confirms the display words, HUD overlays, source pins
and no retained full RGB frame.

The scanout path keeps two raw chroma rows per plane and one output line. Its
logical native input-plus-output line storage is 3,600 bytes: Y/chroma row data
plus one RGB565 output line. That figure excludes host NumPy temporaries, the
42,240-byte four-patch HUD input, reference planes, packet input and other
receiver state. The implementation uses additional host intermediates; their
allocation was not measured as a target layout. This is a line-generation
prototype, not a complete local-memory fit.

Mean scanout plus assertion/hash time is 23.481 ms per frame. It excludes decode
and input conversion, and includes checks; this is not a paired uninstrumented
scanout timing or evidence of physical frame rate. A YUV scanout interface could
benefit any decoder that produces compatible YUV planes; the benefit is not
exclusive to this codec.

## Declared bus traffic model

`memory_budget.py` compares materializing a complete RGB565 image with scanning
YUV420 and composing HUD words at scanout. Both paths charge shared YUV reference
reads and normalized writes, compressed-packet staging write/read, and HUD update
writes. Under nominal 30-fps decode, 60-fps scanout and one reference tap, the
modeled YUV path reduces traffic by 45.3888 MB/s in each cohort. The first cohort
example is 111.6712 MB/s for RGB565 materialization versus 66.2824 MB/s for
YUV420 scanout.

These are scenario estimates from 720×480 geometry and the average selected
complete-packet sizes of the 96 prefixes. The matrix also varies reference taps
and evaluates a 16-bit 50/100-MHz bus with assumed 25/50/75% efficiency and a
20% reserve margin. Those bus rates, efficiencies, margin and 30/60 rates are
assumptions, not measured sustained traffic, controller service or verified
panel timing. The triple-buffer totals in `memory-budget.json` are storage
arithmetic, not proof of bank ownership, porting, fences or physical-part fit.

The traffic model excludes CRC/SHA, retries, metadata, DMA copies and cache
traffic. It charges shared HUD and compressed-packet traffic; placing HUD in
separate SRAM/BRAM would alter arbitration but is not implemented here. No RTL,
memory controller, panel timing or firmware is changed.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_memory_budget
/home/lori/gamebub-streaming-prototype/.venv/bin/python memory_budget.py --check
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

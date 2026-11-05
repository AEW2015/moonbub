# V51/V52 evidence audit

Audited the V51 fault-recovery result and verifier, plus the V52 scanout results,
tests, independent replay and declared memory-budget model. Counts agree with
the retained outputs; both are software/model evidence with explicit hardware
and transport limits.

## V51 fault recovery

V51 contains 24 deterministic cases: six fault plans across each of four source
cohorts. The 33 frame IDs per cohort are reused across the six plans, yielding
132 distinct source IDs rather than 24 independent long videos. The aggregate
is 804 actions: 800 calls to the V48 receiver, 588 accepted packets, 212
rejections and four drops. Every case recovers on key frame 24 and accepts
through frame 32. Independent V43 replay confirms each accepted output and
reference/HUD display hash, and verifies that rejected states remain unchanged.
No encoding runs during verification.

These are stored-packet software traces. There is no actual network, socket,
serial transport, keyframe request, elapsed recovery-time measurement, FPGA
fence, ESP32 reset path or panel recovery. Periodic-key recovery in this harness
does not establish real transport or physical display recovery.

## V52 YUV scanout

The scanout replay covers 96 actual decoded CS38 frames (first 24 per four v40
cohorts), 46,080 lines, 33,177,600 exact RGB565 words and 2,027,520 exact HUD
words from 49,766,400 YUV input bytes. Four color/scanout tests and three
memory-budget tests pass; independent replay confirms all pixels and HUD words
and no retained full RGB frame. The
model reads immutable uint8 YUV input/reference planes, caches at most two raw
chroma rows per plane and emits a single output line. It preserves the exact
chroma and color arithmetic. Such a YUV scanout path could serve any compatible
YUV decoder, not only this custom codec.

The stated 3,600-byte native input-plus-output line storage excludes host
intermediates, the 42,240-byte HUD patches and caller-owned reference/input
banks. The 23.481-ms scanout-plus-checks figure is instrumented line generation;
it excludes decoding and input conversion and is not an uninstrumented panel
scanout timing.

`memory_budget.py --check` passes. Its nominal 30-fps decode / 60-fps scanout
scenario estimates a 45.3888-MB/s traffic reduction for YUV scanout versus full
RGB565 materialization. Both paths charge shared HUD and compressed-stage bus
traffic. The scenario uses 720×480 geometry and assumed 16-bit 50/100-MHz bus
rates, 25/50/75% efficiencies and 20% reserve margin. These are not measured
controller bandwidth or verified panel timing. It excludes CRC/SHA, retry,
metadata, DMA-copy and cache traffic. Buffer totals and 3,600-byte line storage
are logical budgets, not BRAM or physical memory-fit proofs.

Neither study establishes physical 30-fps performance, a BRAM fit, verified
panel timing or deployed receiver recovery.

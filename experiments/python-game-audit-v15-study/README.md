# Python Game v15 evidence audit

Stdlib-only read-only audit workspace for the unified codec, UI, and finite streaming studies. Target: 720x480 canvas, 720x405 active image, 30 fps. Codec, UI, all-features stream, and cadence-gate artifacts are independently audited and hash-pinned.

## Unified UI plugin

The UI result has 6 cases and 160 paired frame IDs (128 distinct input hashes). Across both selector variants, 1,280 rectangle attempts were recorded, or 640 per variant; 292 were cache hits, including 176 on changed whole-source hashes. All selected original RGB565 words and unselected base words match exactly. Cache-on and cache-off selections and display RGB565 hashes agree. No selected item exceeds its declared budget, and all framed patch lengths include the four-byte prefix. The selector/parser regression log records 8 passing tests.

The 32,768-byte budget covers the UI section and its four-byte prefixes only; it excludes AR02 base frame, wrapper/envelope, transport, and wire bytes. It is not a whole-frame cap or FPS measurement. UI timing includes paired selector work and separately timed section parsing/application; it excludes source capture, base RGB generation, and validation metrics. Exact selection applies to original RGB565 UI patch words, while unselected words are preserved from the declared base RGB565 frame. This does not establish YUV-reference updates or FPGA fit. The native inputs are precompressed 25/29.88 fps clips alongside synthetic controls, not live 30 fps capture.

The changing-noise case rejects its fourth priority rectangle after paying candidate work. It selects 15,360 of 21,120 requested pixels and uses 30,816 of 32,768 section bytes.

## Unified codec

The codec artifact has 328 source IDs and 1,020 profile decisions across same-input GM, exact, prune-4, and UI profiles. All 1,002 admitted packets fit the 49,152-byte cap; every complete packet size equals its recorded inner, envelope, and UI patch byte components. All 18 rejected candidates record paid preparation work and exceed the cap. Every decision records one analysis and three forward calls, and profiles preserve identical frame IDs and input hashes per scene.

Exact mode has zero same-reference YUV error against GM; prune-4 remains within four YUV levels. Protected GM words and selected original RGB565 UI words have zero recorded mismatches. The companion exact-reference analysis is hash-linked to the result and analyzer and confirms matching source IDs/hashes, base/display RGB hashes, selected reference IDs/tags, and quality metrics for 300 native base IDs; it includes 45 stored canonical YUV tag observations. Across admitted UI rows, selected source coverage totals 1,584,000 words; coverage can vary by cap admission.

For the 180-frame held-out native scene, mean complete packet bytes are 8,803.23 for GM, 8,727.29 for exact, and 7,650.80 for prune-4. Pruning adds encoder work and is bounded against quantized GM at the same current reference, not original source or a different reference history. Exact mode is lossless relative to corresponding quantized GM output in this comparison; it is not source-lossless. These are measured host timings on related precompressed 25/29.88 fps material, not live 30 fps or physical hardware results.

## Finite all-features stream

The 14 cases contain 1,248 capture events, 1,154 prepared packets, and 1,152 decoded commits; the sum of measured Python wall time is 124.85 seconds. All packet size fields match the complete AR02 composition and fit the cap. The outer route CRC binds to the receiver frame ID and AF02 body-CRC binding; stored reference ID/tag pairs match receiver banks, and decode read pins are present. Every case drains sender slots, encoder pending work, ingress buffers, receiver readers, and decoder work. Observed peaks are 3 sender slots, 2 ingress slots, 3 framebuffer roles, and 2 of the allowed 4 feedback descriptors.

Both promotion fault cases expire safely: a lost promotion ACK leaves the sender on the prior acknowledged tag and subsequent frames use the safe fallback; conflicting promotion statuses expire the staged ACK. Work records retain positive measured duration for all performed stages, including feedback parsing and expiry. The current stream regression log has 11 passing tests, including the two-ingress overload/NACK case; its independent verifier reports pass.

On the 180-frame held-out stream, GM+UI records 175 strict / 178 eventual presentations, exact+UI 169 / 172, prune-4+UI 126 / 129, and exact+UI refresh-30 155 / 157. The one-second diagnostic rate can show 31 IDs/s during backlog/window phase; it is not a sustained input rate. These are finite schedule outcomes under declared 8 Mb/s forward/reverse links, 160 Mb/s QSPI service, 10 ms feedback latency, and 60 Hz vblank. They do not show live capture, shared native CPU execution, or physical hardware throughput.

Every decoded UI frame selects 21,120 exact source RGB565 words with zero recorded mismatch. This is display-side UI selection; YUV reference/tag state remains separate. Matched ID sets and histories are retained per pair. UI coverage, quality, payload bytes, and presentation counts must be read together; no earlier-study gain is added or multiplied, and the direct baseline is not framed as a UI FPS comparison.

## Fixed cadence-gate result

The gate study has 9 cases and 540 events, including a new 60-ID validation window. Its PTS run from 120000 through 144000, strictly after the earlier window's 119600 end; all 60 new image hashes are distinct and none overlap the earlier window. The 0.90 threshold was fixed before the new window. The gate samples 64 coefficient blocks per plane after GM quantization and enables exact SR only if all three sampled planes have at least 90% zero/DC-only blocks. It does not estimate uncoded SR size.

All 174 gate evaluations were ineligible. They cost 18.63 ms total, about 0.107 ms each. On the new window, GM-only, unconditional exact, and gated each decode 58 frames and report 55 strict / 58 eventual presentations; the exact control emits SR on 3 frames while the gate emits none. Their mean complete packet sizes are 21,716.21, 21,711.02, and 21,716.21 bytes respectively. The gate adds screening cost without selecting SR in these samples. Across all three windows, separate matched exact controls identify 79 actual SR byte wins totaling 19,400 inner bytes on matching reference and GM-length IDs. Those are wins measured in the controls; they do not provide payload sizes for SR candidates skipped by the gate. The untimed matched-control analysis hash-checks against the result and analyzer, and both `verify.log` and the analysis check report pass. The evidence supports keeping this as a negative causal-gate experiment and using plain GM+UI for these clips.

The cadence suite records 15 passing tests, 32 source pins, and stable external media hashes. Its measured Python service and declared virtual link schedules remain distinct. This finite, precompressed-source experiment does not show 30 distinct physical captures/s or hardware throughput.

`audit.py` reads retained artifacts only; it does not rerun study benchmarks. Artifact presence alone is not finalized evidence. Run the audit guards with the project Python interpreter using `python -m unittest -v test_audit.py` from this directory. v14 evidence remains read-only. Detailed cases, portable source pins, and before/after external media hashes are retained in `audit-run.log`. Current audited source pins are 16 for UI, 21 for codec, 25 for stream, and 32 for cadence gate; all match. All four input artifacts and the v15 audit guards pass.

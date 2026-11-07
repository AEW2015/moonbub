# V99 RC1 hardware/software development handoff

Use the frozen [profile](../../experiments/python-gamebub-v99/profile.json),
[qualification](../../experiments/python-gamebub-v99/qualification.json) and
[inventory](../../experiments/python-gamebub-v99/inventory.json) together.
Their evidence is software/native. Existing source and interface hashes are
audited boundaries, not a claim that the production JPEG top implements CS88.

## Receiver and packet contract

Implement the restricted CS88 profile, not the native receiver's full grammar:

- 720×480, zero motion, block size 32, all BR88 chunks, chunk block cap 65,536.
- Key mode method 0; P mode method 3; QM87 full run method 2 or accepted
  inherited-map method 6. Uniform scale 16/code 1 is the frozen default.
- At most 49,152 logical bytes per complete packet including CRC. Keep logical
  length separate from DMA alignment padding. Never admit an oversized packet
  because the diagnostic native receiver permits a 2-MiB research envelope.
- Preserve the actual C2 content root, words-only HUD hash and frame seal.
  CU66's geometry/rectangles/HUD hash is a different preimage, not a substitute.
- COPY reads only the exact accepted reference. Candidate writes remain
  provisional until all parsing/reconstruction/HUD/content/seal checks and
  actual write ACKs finish. Presentation additionally waits for vblank and
  scanout drain. Cancellation retains ownership until old accepted work drains.

CS88 carries generation and reference identities, not an epoch field. Bind
transport epoch/core generation and negotiated capability explicitly in the
adapter. No existing MB97 research profile ID currently means CS88, and the
active MSV1/JPEG path must reject custom payloads. The fallback remains its
separate supported image/profile until coexistence or switching is implemented
and tested. Do not infer simultaneous fit from historical JPEG utilization.

## Golden material

The selected CS88 index and RTL-facing index identify immutable reports under
`experiments/python-gamebub-v99/cs88/`. q16 chains contain four full causal
30-frame histories with source hashes and exact packet, coefficient, canonical,
HUD, RGB565, root and seal hashes. The new video is
`mass-effect-legendary-combat-20s-q16`, chain07.

The `rtl-facing-index.json` selects that new source's key 0 and P1 plus a late
CRC fixture. Gzip TSVs include signed dequant/residual goldens and a pinned
testbench contract. Run those through the actual receiver pipeline first;
exporting vectors and native decoding did not perform that RTL run. Retain
strict transcripts, terminal assertions and source/vector hashes. Add further
scenes and keys before broadening any qualification claim.

The separate direct sender's 32-frame synthetic control covers keys 0/30 and
P31→30. Its actual native ACKs check the cross-key root/reference/cache behavior.
It is functional coverage, not unique gameplay or physical cadence coverage.

## Parallel implementation work

| Owner | Concrete next work | Acceptance evidence |
|---|---|---|
| Native Sunshine sender | Port fixed-color conversion, forward transform/quantization, exact HUD selection, BR88 and C2 into one native process. Remove Python loops and helper IPC; keep the slow reference available. | Byte-for-byte q16 packet equality on all 120 goldens, exact native pixels, cross-key/cap/recovery checks, and measured RGB-to-packet tails including actual capture/resize as separately identified costs. Never splice packets from separately predicted q8/q16 histories. |
| ESP32/transport | Add an opt-in negotiated CS88 capability and bounded active UDP/QSPI worker. Probe real core identity/generation and preserve credit/ACK ownership, logical DMA length and backpressure. | Real target CPU/heap/DMA/pbuf/stack telemetry with UI/input/audio and Wi-Fi/QSPI simultaneously active; loss, duplicate, timeout, reset and stale-completion recovery. Opaque forwarding alone is not decode/publication. |
| FPGA functional integration | Join actual packet/BR88 arrivals to dequant/IDCT, reference reconstruction, actual HUD semantics, C2 validation, accepted publication and safe scanout. | Run the new goldens and malformed/retry cases without predecoded canonical replay or host-supplied authoritative HUD receipts substituting for target work. Reconcile all read/write/drain/publication counters. |
| FPGA memory and V100 baseline | Freeze exact part/top/XDC/tool/device support; inventory packet, coefficient, table, HUD, C2, reference, candidate and display memories and all ports. | Explicit finite map, refresh/turnaround/display arbitration, write-drain ownership and whole-device RAM/DSP/LUT/clock reports. Route supported components where possible; list incomplete top-level endpoints. |
| Verification/system | Extend original held-out captures and real service schedules; maintain strict source/packet/pixel identities. | 1,800 distinct source identities over 60 s, then 18,000 over 600 s at 30 Hz on target, bounded queues and zero underruns. Separately measure complete packet-to-validated-publication decoding strictly below 10 ms. |

The current direct sender's new-combat median is 269.74 ms, with 221.60 ms in
Python HUD work. Those values identify host work to replace; they are not
target FPGA/ESP32 costs. Native CU66 CPU timings also do not price selected
CS88 hardware. Likewise the retained V91l FAST validation-only result is
1,290,445 simulated cycles: at an assumed 100 MHz that alone exceeds a
1,000,000-cycle/10-ms budget, before complete decoder/display work. Its
physical clock is unqualified. C2 scheduling/parallelism and the complete
timing fence therefore need actual implementation evidence, rather than
adding isolated component speed estimates.

## Overflow and support limits

The new source's q8 frame25 is 49,654 bytes in CS88. Its native diagnostic
history advances through that frame; dropping it from a deployed stream would
invalidate later references. A production sender must re-encode from the
actual accepted state, reset to a supported key/profile, or negotiate the JPEG
fallback. Fixed q16 passed these short samples but has no universal cap proof
and no active automatic fallback implementation. Quantizer/feature changes
need new complete causal goldens and measured quality; do not label them a
representation-only change.

Physical board identity, current Artix device installation, complete candidate
fit and routed frequency remain pending. The source-backed JPEG target is
`xc7a100tcsg324-1`; its old resource report is a baseline for that image and
does not establish this candidate's budget or fit.

# Next receiver candidate: bounded continuous correctness first

Design proposal, November 7, 2026. Not an implemented firmware release or a new network contract. Keep V43/V027 and original DYN1 pair as the control. Candidate numbering follows source creation/build, not this document.

Implementation update: the first finite three-frame step is now V44, built/packaged and offline-qualified with unchanged V027; see the [current hardware handoff](V44-V027-HARDWARE-HANDOFF-20261107.md). It explicitly uses bounded3-v2, not silent continuous reinterpretation of DYN1/v1. The broader reusable continuous-session/recovery architecture below remains future work.

## Smallest useful implementation

Refactor the two-frame diagnostic into a reusable single-frame transaction plus a bounded sequence coordinator. Start with one in-flight frame and a finite explicitly configured sequence, rather than unbounded buffering or pipelining. Preserve the current full-readback mode for this first correctness candidate. It will be slow; that is acceptable for the lifecycle gate and is not a performance acceptance result.

The per-frame transaction must preserve current identity, staging CRC, native HUD ticket/tag, actual AUX drain, native software commit acknowledgment, and observed presentation checks. Return success only after real presentation; no retained endpoint may be reused on an unclassified error. The coordinator owns the same HUD endpoint/maintenance guard across successful frames, and reports bounded aggregate counters plus a fixed-size recent-event ring rather than allocating arrays proportional to video length.

## Actual V43 assumptions to replace

- `network_driver.rs`: `for index in 0..2`, `[u64;2]` stage arrays, cumulative counter expectations based on `index+1`, and final `frames:2`.
- `network_usb.rs`: fixed two-frame readiness/result messages and unconditional final hold after any mutated trial. Normal finite completion remains an explicit hold until a tested stop/ownership protocol exists; failure retains quarantine/drain semantics.
- `network_io.rs`: current one-peer/same-session, strictly increasing frame admission and duplicate presentation reply behavior must remain explicit. It does not by itself provide session restart, negotiated limits or KEY recovery after a failed admitted frame.
- Native endpoint/reference state and FPGA bank/generation reuse require real multi-frame evidence; a staging-only stress test cannot establish them.

First keep the production `run` two-frame API as the control and introduce a distinct sequence entry point. Validate finite frame limits before side effects. Choose the maximum by bounded counters/deadlines and test generation/command-sequence exhaustion. Do not silently reinterpret the existing uploader or DYN1 v1 as continuous-capable. Publish profile/version selection and matching host behavior before a network trial.

## Instrumentation to add before optimizing

Use receiver-local timestamps around these exact stages, with compact output after the transaction:

1. First validated frame header; final chunk received; final FPGA staging acknowledgment; seal complete.
2. Admission command completion; first valid HUD request snapshot. This separates decoder/request readiness wait from later service.
3. HU extraction start/end, bytes and command21 count. V43 currently retrieves four bytes per checked command; report command/lock waits separately before selecting an aperture/burst change.
4. Native HUD computation start/end and arena/live/peak/reserve diagnostics.
5. HUD write, actual readback, native acknowledgment/drain, software commit ACK and observed presentation, retaining the existing distinctions.

Per-lock/QSPI events must be bounded or summarized. Include trace overflow/loss counts and phase ownership on errors. CPU time and wall-clock enclosing stages can overlap other hardware work; avoid adding nested durations twice.

## Required offline progression

1. Keep existing original-pair and failure tests passing against unchanged V43.
2. Exercise the new coordinator with actual native HUD plus realistic fake-bus completion/failure semantics. Verify more than two *distinct valid dependent frames*, repeated bank/generation turnover, missing commit/presentation replies, identity mismatch and reset/recovery boundaries.
3. Replay the same real packets against exact system RTL. Pair or component tests are controls, not substitutes for this gate.
4. Target-build the new candidate with effective SRAM/stack accounting and a uniquely preserved release. Only then schedule an original-pair control and short multi-frame hardware window.

If the Windows encoder/source is unavailable, retain this as a documented dependency. Historical retained CU66 sequences can qualify plumbing and feature coverage, but cannot be presented as the requested two-minute Mass Effect source.

Performance work follows the [measured V43 stage attribution](V43-STAGE-ATTRIBUTION-20261107.md). Native HUD CPU is already hundreds of milliseconds on the physical ESP32; removing diagnostic readback and changing frame-loop bounds alone will not deliver 20 or 30 fps.

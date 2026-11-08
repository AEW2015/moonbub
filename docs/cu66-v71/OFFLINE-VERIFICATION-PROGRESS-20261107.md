# Continuous CU66: first offline verification pass

November 7, 2026, America/Denver. Three parallel workstreams executed the first verification pass from the [active plan](CUSTOM-CODEC-STREAMING-PLAN-20261107.md). No hardware programming, device reset or network transmission was performed. No new continuous firmware or FPGA image is claimed ready.

## Executed evidence

- Receiver: **46 host tests passed**, importing actual production V43 Rust modules and native HUD implementation. Driver tests use modeled FPGA MMIO; framing tests use the production parser. New staging tests cover 10,000 successful drained generations and 2,000 abort/integrity-failure generations. This does not prove continuous native HUD/reference/FPGA operation or target stack safety.
- Encoder/reference: fresh Python software-reference replay passed **12 retained frames across four histories**, checking canonical YUV, native tags, HUD words and composed display hashes. All **457 retained packets** passed hash/length/outer-CRC/capacity checks (largest 44,016 bytes); two pure serializer/validation tests passed. These are historical corpus frames, not the user's requested two-minute source. A separate audit of retained native qualification results also ran; fresh replay and historical audit are distinct.
- FPGA retained evidence: revalidated all **78 frozen V027 inputs**, exact selected BIT and synthesized bulk export bindings. Re-compared the retained V023 fast/slow canonical pair and composed raster against the oracle with zero mismatches, including borders. This is retained-evidence revalidation, not a new V027 complete-system replay.
- FPGA fresh RTL: both one-bank and two-bank V027 frozen row-unit runs **passed**, each exercising two frames, 1,036,816 qualified bytes and 16,204 tiles, randomized output backpressure, abort/reset/invalid input and reference/control/payload/RAM-write-authority comparisons. These are actual newly executed row-unit simulations, not complete decoder/network/physical SDRAM or performance acceptance tests.
- Physical performance analysis: [recomputed retained V43 stages](V43-STAGE-ATTRIBUTION-20261107.md). Native HUD CPU took 319.753/210.758 ms, nested within stored-to-presentation totals 1913.495/1443.366 ms. Significant pre-HUD service remains unattributed. No new performance measurement was taken.

## Evidence and reproduction

All small harnesses, logs, commands and machine-readable results are under `C:/moon/maintenance/streaming-verification-20261107`:

- `receiver/receiver-report.md`, `run_checks.py`, `execution.json`, `source-hashes.json` and actual test logs.
- `encoder-readiness.md`, serializer/reference/audit logs and reference output JSON. Its report records dependencies and commands.
- `fpga-replay-report.md`, `fpga-recheck-result.json` and `fpga-rows-fresh` execution/source bindings.
- `profile_retained_v43.py` and `v43-stage-attribution.json`.

Source/image identities are retained in the reports; test passes must not be transferred to a future modified candidate without revalidation. The Python reference dependency was installed in an isolated `C:/moon/tools/venvs/cu66-verify` environment; the global Python environment was not modified.

## Next implementation priorities

1. Bind the retained third Mass Effect-family packet (`mass-effect-10000` frame2/ref1, 13,708 bytes) after the exact original pair into the next continuous/system test. It freshly passed the software reference, but integrated FPGA compatibility still needs verification. In parallel generate a new short sequence through an isolated output-only adapter around the existing causal research encoder, explicitly enforcing zero-motion/arithmetic dispatch5/6. Confirm Windows encoder capability and the requested full source there; do not substitute historical media without labeling it.
2. Implement the [bounded continuous receiver candidate](CONTINUOUS-RECEIVER-NEXT-CANDIDATE-20261107.md): single-frame transaction/coordinator, one frame in flight, bounded reports, real reference/bank reuse and explicit lifecycle/recovery. Original pair remains the control.
3. Add stage markers for decoder/HUD-request wait, stable snapshot, allocation, per-word HU extraction and native CPU. Select subsequent burst/CPU/offload optimization from those measurements.
4. Bind the continuous candidate and real short sequence into exact V027 full-system replay. Retain canonical/HUD/raster comparisons; model QSPI/CPU service separately from correctness-only native callbacks.
5. Require these candidate gates before the original-pair control and short multi-frame physical trial. The full two-minute clip and 30 fps acceptance remain later milestones; existing component passes are insufficient to start them.

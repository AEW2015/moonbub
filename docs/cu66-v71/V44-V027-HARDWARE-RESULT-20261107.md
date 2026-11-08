# V44 / V027 bounded-three physical result: PASS

November 7, 2026, America/Denver. [Structured receiver/host evidence](V44-V027-HARDWARE-RESULT-20261107.json). Exact source/package selection is in the [hardware handoff](V44-V027-HARDWARE-HANDOFF-20261107.md).

The original KEY0/P1 pair and distinct dependent P2 completed one physical network invocation: **3 accepted /3 presented /0 rejected /0 LCD underruns**, with **63,360 HUD words actually written and read back equal**. Receiver elapsed time was **9.582711 seconds**, including network wait/upload/staging and diagnostic service. Windows confirmed matching status2 replies for all three identities, exit0, no timeout/status3 error and no whole-run retry. This is a finite correctness trial, not a streaming FPS result or the requested120-second clip.

Session15632681948135564100, `192.168.0.47:59273 -> 192.168.0.157:5535`, explicit `dy71-bounded3-v2`. Packet sizes were24,758 /18,873 /13,708 bytes, references none /0 /1. The held game scene and HUD are visible in the direct-camera snapshot; glare/white balance are not calibrated and the snapshot does not prove continuous motion.

## Installed identities and memory

- Queried installed ELF: `f92e3df64a104657957e0d9c86e7a1b79d4f07e2febb5f6fb40a6dd11da76110`; app-only UF2 `e2f5a90143015cefeea367158f957638de4eeac4bdc3838eb49077a70952c903`.
- Existing unchanged V027: DONE1/USERCODE4459373f, BIT SHA`9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`.
- CPU-only original-pair HUD and expected allocation-exception checks passed before volatile JTAG programming.
- Before Wi-Fi:175,872 free /77,824 largest. Receiver ready after Wi-Fi:117,600 free /37,888 largest. The original98,304 native arena ceiling and8,192 per-allocation physical reserve were retained; the three-frame trial completed without guard refusal.
- Post-result read-only query:74,944 free /19,456 largest; USB task stack-low3212. The **network worker's** stack-low, native minimum free and target arena peak were lost from the USB export and remain unknown. USB-task stack is not a substitute for the network-worker stack measurement.
- A fresh post-result identity/uptime query remained on the same exact ELF with advancing uptime; no reboot was recorded in the captured trial. The inherited diagnostic variant text still saysV43, so use the exact ELF identity, not that stale label.

## Retained receiver-local timings

| Interval | KEY0 | P1 |
|---|---:|---:|
| HU extraction from staged packet |1018.254ms|666.042ms|
| Command21 reads |3102|2031|
| Native HUD CPU |303.409ms|209.555ms|
| HUD writes |280.182ms|283.073ms|
| Actual HUD readback |272.904ms|275.887ms|
| Completely stored to observed presentation |1892.191ms|Unknown|

All differences use the same receiver clock. Native CPU lies inside the broader admission-to-HUD interval. Do not subtract Windows and receiver clocks or call these timings FPGA-only decode latency. HU extraction alone is a demonstrated large cost of the current scalar diagnostic path; removing only pixel readback would leave extraction and native CPU far above a33.333ms frame budget.

## Export limitation

Short individual log records did not prevent loss when21records were emitted in a burst. Raw USB text truncates after P1's HUD write/readback line, merging a partial P1-final line and a P2-extract fragment. P1 final and all complete P2 stage records, arena/IO/health summaries and the explicit final lease message are missing. The corruption/loss point inside the logging/USB path was not instrumented; do not assert a particular overflow count or attribute it to video packet loss. Complete success/word-count summaries plus independently matching host replies establish the bounded result despite missing detailed telemetry.

Raw evidence, transfer/programming preconditions, exact DONE receipt, camera images, sender receipt and frozen USB capture are at `C:/moon/dev/evidence/v44-v027-network-20261107-run01`. Initial USB open raced Windows enumeration; it failed with0captured bytes. The second recorder opened successfully without resetting the device, captured read-only exact identity, and ended cleanly after the post-result query. Raw capture hash is in the structured result.

## Next development, before another hardware run

1. Fix report export as a bounded **paced or paged retained snapshot**, with record indices/counts and explicit export-loss reporting. Test burst capacity as well as individual line size. Preserve progress on errors rather than inventing missing values.
2. Investigate avoiding redundant scalar command21 HU reads: the validated incoming packet already contains these bytes. A bounded ingress HU cache may reuse the same HC70 input-buffer budget, provided whole-frame/staging integrity, exact HU offset/length/ticket/tag and reference identity are checked before native use. This is a proposal requiring actual-source failure tests and memory/lifetime revalidation, not an implemented fast path. It may avoid a new FPGA build for this first service-cost reduction.
3. Native CPU and HUD transfer costs still need measured optimization. Extend finite/lifecycle/KEY-recovery coverage and produce actual new content through the Windows encoder before attempting the120-second stream. A configured30fps sender does not resolve these measured costs.

Sender is stopped; final endpoint/maintenance lease remains held by design. USB recorder was stopped after preserving results. Do not repeat, force-release ownership or switch FPGA images underneath the retained native endpoint; another test requires the qualified reset/reconfiguration workflow.

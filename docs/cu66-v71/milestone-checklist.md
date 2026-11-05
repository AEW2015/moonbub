# CU66 v71 milestone checklist

Status: the v71 prototype and its stated simulation campaign are complete;
physical throughput and latency gates remain open. This checklist preserves the v69/v70
comparison baseline; passing a functional simulation does not close cadence,
latency, target-fit, or physical-hardware gates.

## Frozen evidence inputs

- [x] Run `python3 scripts/cu66-v71/verify_baseline.py`; retain its PASS line
      alongside the v71 evidence. It verifies frozen v69 and v70 bundles,
      v70 reviewed-source pins, and the additional manifests/verifier pins.
- [x] Record source revision, tool versions, commands, seeds, fixture identity,
      and hashes for each new result. Keep all new v71 outputs under
      `fpga/experiments/cu66-v71/` and documentation under `docs/cu66-v71/`.
- [ ] Preserve the functional reconstruction scope separately: exact packet,
      canonical YUV/tag, HUD semantic/readback, RGB565 raster, memory ownership,
      recovery, and malformed-input assertions. A simulator PASS means these
      modeled assertions passed for its stated inputs and model only.

## Sustained presentation: 30 distinct new frames/s

- [ ] Demonstrate 1,800 distinct chronological source frames, without looping
      the retained 457-frame set, at the declared 30 fps arrival cadence.
- [ ] Demonstrate a separate ten-minute physical run whose distinct new complete
      presentations average at least 30 fps over predefined fixed observation
      windows, with bounded age/backlog and no unexplained drops or unexpected
      normal-load LCD underruns. Define window length, warm-up/drain, arrival
      jitter tolerance, and deadline policy before the run; do not require 30
      presentations in every arbitrary wall-clock sliding second unless that
      stricter policy is explicitly chosen and justified.
- [ ] Count frame IDs through source, attempt, accept, commit, and complete
      presentation. Repeated panel refreshes, buffer flips, or repeated-content
      stress frames are not new source frames. State warm-up, observation, and
      drain windows and retain failed attempts.
- [ ] Exercise live transport, CPU/HUD service, concurrent memory clients,
      refresh, actual LCD scanout, and achieved device clock. Report presentation
      spacing against the native panel's 65.0755 Hz quantized cadence (541 × 834
      pixels per raster at the declared pixel clock), frame age, and missed
      deadlines. State how the 30 fps input cadence maps to panel refreshes and
      which fixed-window deadline tolerance applies. Functional simulation or average FPS alone cannot prove this
      physical sustained-throughput gate.

## Validated decode latency: strict observed maximum <10 ms

- [ ] For every supported valid frame in the predefined campaign, measure from
      complete packet availability in immutable staging through integrity-checked
      canonical YUV and exact HUD being stored, required writes drained, and the
      frame becoming validated-ready. Include post-staging admission/queue wait,
      framing/profile/reference/CRC checks, entropy/reconstruction/hash work,
      HUD semantic processing and transfer, and actual CPU and memory service.
- [ ] Require the observed campaign maximum to be strictly below 10 ms; report
      p50/p95/p99/max, all failed/late/rejected/recovery attempts, and resource
      work. Report queue wait separately while retaining it in the headline
      interval. Keep RGB composition, vblank wait, scanout, and capture-to-visible
      as separately measured costs.
- [ ] Bind timestamps to generation/frame IDs: source capture, packet complete,
      admission, packet validated, base tag, HUD semantic/transfer, writes drained,
      validated-ready, RGB-ready, commit, and first/last correct visible pixel.
      Synchronize clock domains or report cross-device clock uncertainty.
- [ ] Do not infer target latency from native CPU execution or RTL simulation:
      simulated time omits deployed processor execution and physical memory,
      transport, clock, and panel behavior unless explicitly modeled and then
      measured on target. A finite observed maximum is campaign evidence, not a
      universal worst-case execution-time proof.

## v70 evidence and v71 focus

V70's full command model preserved exact output but did not meet clean cadence:
its P-frame strip transaction modeled about 230 ms at a 10 ns memory period and
recorded 11,762 LCD underruns across its unequal-duration run. The model used
conservative single writes; it did not implement true write bursts. The v71 work
implements an elastic burst LCD port, four-line auxiliary cache and finite-grace
scheduler. The final key/P command-model run has zero underruns; its P
transaction takes 260.19 ms and does not establish 30 fps. Physical tests and the
larger fixed-arrival campaign remain open. They do not alone prove 30 fps or <10 ms.

- [ ] Show functional equivalence and ownership/abort correctness under the new
      LCD burst path and four-line cache, including concurrent canonical, HUD,
      painter, and scanout traffic.
- [ ] Measure command counts, per-client wait/service tails, line deadlines,
      cache behavior, and underruns under fixed, reproducible schedules. Normalize
      comparisons to equivalent inputs and observation windows.
- [ ] If adding burst writes later, specify accepted-beat completion, masks,
      alignment, partial bursts, abort/drain, and cache invalidation explicitly;
      compare against the frozen scalar-write control.
- [ ] Keep target implementation/CDC/timing and board measurements as explicit
      gates. Native CPU and simulation evidence cannot establish FPGA fit/Fmax,
      ESP32 service under deployed load, electrical SDRAM behavior, LCD-visible
      correctness, or physical ten-minute cadence.

## Evidence audit

Run `python3 scripts/cu66-v71/verify_evidence.py` after all qualified results
are present. It checks source and command-log hashes, terminal PASS markers,
expected memory/display/control/full-strip/comparison counts, and the declared
simulation scope. Intentional starvation/fault probes remain counted as
coverage probes; their expected underruns/errors do not change the normal-run
verdict. This is an integrity and count audit only. It cannot establish
physical throughput, target timing/resource fit, or board behavior.

Earlier system iterations are retained under
`fpga/experiments/cu66-v71/system/initial-buffered/` and
`fpga/experiments/cu66-v71/system/elastic-before-grace/`. Each manifest and ZIP
preserve the exact sources, logs, and result hashes. Both are explicitly
superseded: the buffered version had weaker raster counting and underruns; the
elastic-before-grace version missed adversarial request-gap/bank-conflict line
deadlines. The evidence verifier checks these archives internally, while
checking current source pins only against the rerun final results.

# Read-only DY71 service and lookahead review

This review selects no implementation change. The base owner, memory map, scheduler and PHY remain frozen. Numeric inputs and source hashes are retained in `architecture-performance-review-v001.json` and the line-88 trace proof.

## What the retained evidence establishes

The cache contains **two physical Y groups per context**, not one: current plus one future 8-column group. Group parity selects one half of `y_mem[127:0]`. Y6 therefore aliases Y4's half. Y4 cannot be overwritten while its last generated line still reads that half. The last Y4 line, physical 79/coded 39, offers its final LCD word at cycle 3,261,630; safe reuse follows that memory edge, not a guessed physical-panel-80 timestamp.

C3 starts earlier at cycle 3,261,229. One `f_active` job owns both Cb and Cr phases until the complete chroma group is available. It does not reconsider Y selection at each BL8 boundary: BL8-level priority is FRONT versus PREPARE, not Y versus Cb versus Cr. PREPARE is inactive throughout this first failure window. The current source therefore explains why freeing Y4's bank does not immediately let Y6 run.

The measured sequence is Cb3 at 3,261,229, Cr3 at 3,266,897, then Y6 at 3,272,579. Y6 is finally usable at line-88 admission, cycle 3,282,171. Line 88's active deadline is 3,279,773; final line fill is offered at 3,282,657. Y is unavailable at the deadline while both chroma/halo readiness predicates are true. The observed fill is approximately 28.84 µs late.

An important constraint is that **C3 is needed before Y6**: coded line 47/physical 87 requires the next chroma group's first column for bilinear interpolation, whereas Y6 begins at coded line 48/physical 88. Moving an entire Y6 job ahead of unfinished C3 can merely move the miss to line 87. Current page order is compatible with those immediate deadlines; a simplistic Y-always-first rule is not established as a fix.

## Demand versus available lead

The native test uses a 34.058 ns pixel period and 541 clocks per line: **18.425378 µs per line**, 147.403 µs per eight lines and 294.806 µs per sixteen. Panel scan rate is approximately 65.076 Hz, independent of the intended rate of new video frames.

| Work | BL8 commands | Measured window |
|---|---:|---:|
| One Y group, 8 × 480 bytes | 240 | Y4 96.65 µs; Y5 114.89 µs; Y6 95.92 µs |
| One Cb group, 8 × 240 bytes | 120 | Cb3 56.68 µs |
| One Cr group, 8 × 240 bytes | 120 | Cr3 56.82 µs |
| Two Y groups plus a Cb/Cr pair | 720 | Y4 + Y5 + C3: 325.04 µs |
| Available sixteen-line scan interval | — | 294.806 µs |

Page-start differences include any handoff/hazard gap; they are not independently isolated controller service times. Nevertheless, the retained local sequence already takes about 30.23 µs more than its sixteen-line cadence. More buffer lead may absorb a transient deficit, but cannot establish sustained capacity if the same excess repeats.

The Y6 job receives only 71.94 µs of start-to-deadline budget but needs approximately 95.92 µs to readiness. Early Y-bank reuse plus arbitrary preemption does not make both Y6 and C3 deadlines feasible at unchanged measured service times: the remaining combined work after Y4 release exceeds the remaining combined deadline window. A fix must advance useful work, reduce service cost, or both.

The steady scan requires 45 canonical BL8 reads per active canvas line, or 32,400 per raster. At this panel clock that is about 2.108 million commands/s, before new-context HUD reads. A full 30-fps dependent-frame budget can additionally contain 972,000 canonical reference reads, 972,000 canonical writes and **633,600 scalar masked-HUD-write commands/s**, plus 79,200 HUD cache-read commands/s. These are worst/full-copy design budgets, not a measured 30-fps workload. Scalar HUD writes are especially inefficient: each useful x16 word occupies a masked BL8 command. Raw SDRAM byte bandwidth alone therefore understates command/activation overhead.

## Feasible candidates and their costs

| Candidate | Potential benefit | Bound or cost |
|---|---|---|
| Third Y group per context | Allows current plus two future groups, avoiding Y6/Y4 alias earlier | About 7,680 useful bytes total, 8 KiB padded, provisionally +2 RAMB36. Needs a third tag/valid bank, changed bank selection and **extended lookahead**; RAM alone with current current+next selection does nothing. No new synthesis/fit proof exists. |
| Four Y groups per context | Two-bit group selection retains power-of-two addressing and provides deeper lookahead | About 16 KiB padded extra total, provisionally +4 RAMB36. Read mux/fanout and owner hazard/tag logic need timing and reset/abort proof. Does not cure a sustained service deficit. |
| Resumable/chunked front jobs with deadline selection | Reconsiders Y/C urgency after bounded BL8 or tile chunks instead of an entire Cb+Cr page | Little payload RAM; extra retained job progress/identity, counters and arbitration stages. Must preserve partial-page invalidity, exact generation ownership, abort drain and reader hazards. Preempting C3 for an entire Y6 is not sufficient in this window. |
| More backend LCD quota | May reduce FRONT service delay under reference/candidate work | At equal command cost, 2:1→3:1 raises LCD share 12.5%; the entire 325.04 µs window would ideally become 288.92 µs, inside 294.806 µs. This could improve cadence but nominal background grant share falls 25%; at 4:1 it falls 40%. These are sensitivities, not predictions: queue bubbles, row reuse and earlier C completion change both demand and Y start time. Background decode becomes slower unless total efficiency improves. |
| Tile-sized row-local batches | Four BL8 operations match one physical 64-byte tile; could reduce repeated ACT/PRE when FRONT and reference reads share a bank | Requires measured row-locality evidence and bounded fairness/abort proofs. This changes scheduler granularity and is not selected. It may be preferable to granting more individual bursts if it improves total rather than only LCD throughput. |

The RAM estimates include both cache contexts and assume inference comparable to the current unreset synchronous arrays; they are not synthesized resource results. Current cache/color evidence uses 41 RAMB36 before full-system integration. Whole-design fit and routed timing are still required. Extra chroma capacity or extra LCD line buffers could also extend lead, but would add separate read-port/CDC/tag ownership changes and are not the first proposed experiment.

For clarity, scaling only the measured Y6 service gives approximately 85.3 µs at ideal 3:1 share or 79.9 µs at 4:1, both above its original 71.94 µs start-to-deadline window. That fixed-start calculation is **not a proof that quota cannot work**, because accelerating the preceding C job advances Y6's start too. The whole-window calculation and the competing background-throughput cost must be considered together.

## Inference still to test

Actual P reference reads use the same accepted canonical bank as FRONT scanout. Reference traversal is tile-row-major while scanout pages traverse tile columns. Their alternating physical rows can incur ACT/PRE traffic not exercised by candidate-only writes in another bank. The agent's matched reference-read/candidate-write component now reproduces Y-unavailable misses independently of the decoder, but its final source-bound results must be used before drawing a causal conclusion. This supports a service/locality investigation; it does not yet prove same-bank row thrashing is dominant.

## One next cause experiment

After the matched reference-copy baseline finishes, run a **diagnostic bank-locality A/B** with no PHY, map or scheduler change. Keep FRONT canonical0/HUD0, candidate1/HUD1, reference tile order, copy dependency and all clocks/model parameters unchanged. Preload the identical independent native reference in canonical2, then change only reference-read source bank0→bank2. Check every returned tile and candidate write against the same oracle. This is a diagnostic mirrored-reference fixture, not a valid codec lease transition or hardware release profile.

Compare first missing line, Y/C start-to-ready times, line admission/fill slack, reference-copy progress, LCD request wait and ACT/PRE counts normalized per completed work. A strong benefit from separation would justify a later row-local batching/service experiment. Little benefit would point toward aggregate service demand and insufficient lookahead instead. Keep all failures and source hashes. **No fix is chosen by this review.**

# Custom codec: continuous playback and Mass Effect replay

Updated November 7, 2026 (America/Denver). This is the active next-development plan after the V43/V027 original KEY/P hardware pass. The earlier [implementation plan](IMPLEMENTATION-PLAN.md) remains the architecture/history reference. This document does not arm hardware or authorize a Windows sender to start.

## Goal and current boundary

Replay the user's same 120-second Mass Effect Legendary Edition Combat clip, offset zero, without looping, using CU66 through the DY71 decoder. Keep the approved 720x480 canvas with 720x405 content at (0,37), no side padding, 37 top and 38 bottom rows. Verify how CU66 preprocessing and HUD composition preserve this placement before assuming JPEG settings carry over. The prior margin13 setting belongs to the JPEG setup; query the custom image's actual placement controls rather than assuming that register/setting applies.

First qualify continuous correct playback at a measured sustainable rate. The target remains 30 unique complete presentations/s; a configured sender rate, accepted packet count or repeated image does not satisfy it. The prior 20 fps/Q30/5 Mbps recipe is a JPEG reference, not a CU66 quality or bitrate contract. Define CU66 quality/rate controls from its actual encoder and golden decoder; do not label them Q30 without a defined mapping.

## Verified baseline and remaining unknowns

- V43 release-v002 ELF SHA-256: `efd0a8650853f8d996dd22bfa4fb33d0d1b4da8678f453cb8304ac9579880fb9`.
- V027 BIT SHA-256: `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`; DONE1/USERCODE `4459373f` verified in the completed trial. Routed setup +0.019 ns, hold +0.012 ns, pulse +2.000 ns; 55,412/55,412 nets routed, zero routing/DRC errors.
- Original network KEY0/P1 passed: 2 accepted, 2 presented, zero rejects/underruns, all 42,240 HUD words actually read back and compared. Windows matched both status-2 presentation replies and exited 0.
- Pair elapsed time was 6.782169 seconds, with 58,078 QSPI attempts, versus V42/V023's 35.050912 seconds and 392,927 attempts. This is diagnostic end-to-end elapsed time, not decode-only latency or sustained FPS.
- Source evidence: `C:/moon/dev/evidence/v43-v027-network-20261107-run01`; current-state record: `C:/moon/dev/evidence/CURRENT-CUSTOM-CODEC-HARDWARE.json`. Hardware was not re-queried after the microSD backup; do not infer present readiness or that the volatile V027 image survived a power cycle.
- V43 receives exactly two network frames, then retains the final endpoint/lease. It is not a continuous player. DYN1 port 5535 is a bounded lab transport, separate from JPEG/MSV1 port 5533 and AV v1 port 5534.
- Last coordinated Windows baseline was offline CU66 qualification plus the pinned `cbbd85fda` fixture uploader. A general video encoder and continuous sender are not established by that result. Inspect the current Windows branch before claiming either exists or is absent today.
- Earlier V42 native HUD preparation alone measured 304,230/209,963 microseconds for KEY/P. Re-measure V43 stages: bulk QSPI improvements alone do not establish that CPU work can meet a video frame budget.
- Retained V43 timestamps have now been [attributed without a new hardware run](V43-STAGE-ATTRIBUTION-20261107.md): completely stored-to-presentation was 1913.495/1443.366 ms; nested native HUD CPU was 319.753/210.758 ms. HUD writes took 284.791/286.447 ms and readback 271.855/276.288 ms. Admission-to-HUD still contains 1028.559/664.936 ms of unattributed non-CPU work; instrument HUD-request wait and HU extraction separately before choosing an FPGA/QSPI fix.

## Work packages

### 1. Freeze host/receiver compatibility and generate a short real sequence

Windows owner: inspect `gamebub/cu66-v70-windows-20261105` and report its current commit, actual encoder support, profile and dependencies. Receiver owner: bind the V43/V027 payload parser, staging/CSR/HBU ABI and accepted feature subset to exact source hashes.

Use the unchanged Mass Effect source SHA-256 `fb01977e41e649bfb9fd53d1ee0e6db436127fb86e4b3b7ec303158e0568aff5`; Windows must recheck the source file and at least 120 seconds of available video. Export a short chronological KEY/P sequence first, with exact source-frame indices, preparation, encoder settings, reference IDs, packet lengths/CRCs and decoded reference hashes. Compare every generated frame with the software reference. Exercise scene changes and a deliberately broken dependency.

Do not silently substitute retained fixtures, resize/crop differently, loop the clip or switch quality. The existing complete CU66 packet limit is 49,152 bytes; select and test an explicit oversize policy before transmission. Any re-encoding must use the encoder's accepted reconstruction for subsequent references. Never truncate packets or skip a referenced frame and continue its dependent chain.

Gate: a reproducible multi-frame sequence within the exact decoder feature/capacity limits, with matching reconstruction/HUD output and explicit placement. This can proceed offline in parallel with packages 2 and 3.

### 2. ESP32 continuous receiver and lifecycle

Create a new candidate; preserve the exact V43 rollback. Generalize the fixed two-frame driver/report arrays into bounded reusable state. Retain one explicit owner, finite staging/queues, checked allocation, sender/session binding, generation/reference identity and integrity checks. Keep radio receive and UI/control work responsive during decode/HUD/QSPI service; account for stack plus largest contiguous heap allocation.

Publish a versioned continuous lab contract before changing the sender: limits, credits, admission versus stored-prefix versus actual presentation replies, duplicate/retry behavior, reference eligibility, loss/timeout handling, session reset/STOP and maximum in-flight work. Preserve DYN1 v1 as the original pair control; negotiate or explicitly select a new version/profile if semantics change. Do not infer readiness from an ingress ACK.

On loss or a failed dependent frame, reject dependent continuation and require a defined new-KEY recovery. Drain accepted hardware work before recycling buffers or changing ownership. Define paired reset/reconfiguration for unrecoverable faults; do not force-release a live native lease. Test session restart, stale/reordered/duplicate packets, missing final chunks, lost replies, oversize packets, error cleanup and long bounded reuse.

Gate: host fault/recovery tests and target build with effective SRAM/stack accounting; controlled multi-frame physical correctness without allocation growth, reboot or illegal reuse.

### 3. Attribute and reduce frame service cost

Measure locally on the receiver: packet completion, admission, native HUD computation, staging/QSPI bytes and transactions, lock/credit waits, HUD transfer/readback, FPGA completion/drain, commit and presentation. Retain bounded failure history and trace-loss counters; use compact summaries outside hot paths. Match Windows records by session/frame/reference/capture identity, never by subtracting independent monotonic clocks.

Keep the full-readback diagnostic as a correctness mode and control. Develop a separately identified playback mode that avoids per-word diagnostic polling/readback only after documenting its replacement integrity/completion checks. Retain selected sampling/full-check runs and corruption detection; do not report unchecked memory as verified. Measure native CPU HUD work before choosing algorithm/SIMD/implementation acceleration or moving work into FPGA logic.

Gate: stage distributions and worst observed waits on varied real frames, including simultaneous ingress, decoder/HUD activity and scanout. Select each optimization from measured cost; neither QSPI nor FPGA backpressure is assumed to be dominant.

### 4. FPGA baseline and conditional changes

Use the qualified V027 as the first functional control. Audit continuous generation/reference turnover, staging bounds, repeated HUD updates, frame-boundary presentation, reset and error drain in the exact system simulation. Add long multi-frame/reference tests with memory latency, backpressure and failure injection; retain native output equality and LCD safety checks.

If measured bottlenecks require RTL changes, create an isolated successor. Candidate areas are HUD offload, packet/HUD burst service, reference-read overlap/cache service and bounded arbitration; none is selected merely from old model results. Preserve the qualified SDRAM PHY, clocks, LCD timing and pin budgets until evidence justifies changing them.

Every new BIT requires exact-source functional evidence, final positive routed setup/hold/pulse, full routing, zero unwaived DRC errors, reset/CDC/native-image audits and hashes. Simulation throughput, routed timing and physical unique presentation rate remain separate evidence. V027's small positive margins do not establish a robust 30 fps operating point.

### 5. Offline verification before the next hardware candidate

Run actual encoder output through the production receiver code and exact candidate RTL wherever practical. A simplified model or callback is useful for fault injection but must not stand in for the implementation whose correctness or speed is claimed. Existing historical tests remain controls; bind new results to the new candidate.

| Check | Required evidence and pass condition |
|---|---|
| Mass Effect encoding and software reference | Source SHA, offset zero/no loop, frame indices, canvas/placement, encoder/profile settings and reference chain recorded. All packets fit the agreed 49,152-byte limit or follow the tested oversize policy. Every generated frame decodes with expected canonical/HUD results; unsupported features and broken dependencies fail explicitly. |
| ESP32 continuous lifecycle | Exercise thousands of frames through the actual reusable receiver/driver state. Allocation accounting, queue capacity and ownership stay bounded; no stale references, buffer reuse before drain, leaked lease or cumulative memory growth. Include generation/session rollover boundaries supported by the contract. |
| Network and protocol faults | Deterministic missing, duplicate, reordered, truncated and corrupted chunks; lost stored/presentation replies; sender restart, timeout, oversize input and missing final chunk. Assert precise reply/state transitions, idempotent retries, no corrupt presentation and defined KEY/session recovery. Retain seed and first-failure history. |
| Exact FPGA system reconstruction | Replay actual encoded frames through staging, parsing/decoder, native HUD service, SDRAM and presentation using the candidate's exact source binding. Compare canonical reconstruction and composed scanout with the software oracle under the defined color/rounding rules. Check placement, reference-bank turnover and frame-boundary presentation, rather than only completion counters. |
| Concurrent service and backpressure | Exercise ingress, HUD, reference reads and LCD scanout with declared clock ratios, realistic QSPI/CPU service delays and SDRAM latency/refresh/turnaround behavior. Cover maximum allowed backpressure, credit/lock waits and failure drain. Record queue peaks, mutually exclusive stall bins, completion latency and unique-presentation intervals; fail on overflow, deadlock, starvation or missed declared display guarantees. |
| Firmware SRAM, stack and memory correctness | Inspect effective generated SDK configuration, ELF map/static SRAM, task-stack allocations, bounded native arena and largest contiguous-allocation requirements. Exercise worst-case packets and error cleanup with host sanitizers where supported. Review target-only paths and explicit margins. Static analysis and host runs do not prove ESP32 scheduling or stack safety; target high-water/heap checks remain mandatory. |
| Final FPGA implementation, if RTL changes | Exact final routed checkpoint/BIT binding; strictly positive setup/hold/pulse, complete routes, zero unwaived DRC errors, reset/CDC/native-image checks and final image hashes. Functional behavioral or synthesized simulation does not replace routed timing. Preserve any timing-model or post-route simulation gaps explicitly. |

#### Execution order and useful parallel work

1. Generate a short, varied Mass Effect KEY/P sequence and establish its independent software-reference results. While Windows prepares this, the receiver owner can implement bounded lifecycle/fault tests and the FPGA owner can prepare exact-system replay. Use the original pair only as the initial control, not a substitute for real moving frames.
2. Run the actual continuous receiver against those packets, including fault/recovery cases. Use a virtual clock or modeled service for logic tests; report that model separately from real CPU timing.
3. Run the short sequence through complete RTL with realistic memory and HUD-service assumptions. A zero-time native C callback cannot establish ESP32 HUD throughput. Add boundary/backpressure tests and compare actual output, not merely accepted/completed counts.
4. Replay the entire two-minute encoded sequence through the software receiver. Select difficult RTL segments by measured packet size, scene changes, reference dependency length, HUD cost and stalls. Include long generation/bank reuse coverage. Full-clip RTL simulation is optional if its cost is excessive; record exactly which frames and conditions were simulated and which were not.
5. Profile each candidate, select the next optimization from measured evidence, then rerun affected correctness/recovery tests. Re-run full FPGA implementation gates only for a changed FPGA candidate; retain V027's existing qualified implementation evidence when the FPGA is unchanged.
6. Assemble the hardware-candidate report below. Do not declare a gate passed merely because its harness exists or a process launched successfully.

#### Hardware-candidate report

Keep one indexed report under `C:/moon` containing exact repository commits plus dirty-source manifests, tool/config versions, contract/profile, fixtures and source hashes, app ELF/BIN/UF2 and selected BIT hashes, reproducible commands, exit codes, pass/fail summaries and explicit skipped/unknown coverage. Separate these evidence classes:

- Software correctness and software encoding performance.
- RTL functionality and simulated throughput, with CPU/QSPI/memory assumptions.
- Routed FPGA timing/implementation checks.
- Physical playback and runtime results, populated only after the hardware trial.

Include stage distributions and worst waits, buffer/arena bounds, reference/HUD/scanout comparisons, fault recovery, trace-loss counts and any open failure. Preserve full diagnostic readback as a control. If playback mode omits readback, state exactly which integrity/completion checks remain and do not carry over the diagnostic's verified-word claim.

The first physical trial should answer whether the exact offline-qualified sequence reconstructs and presents correctly on the device with healthy memory and useful stage timing. Offline checks cannot establish RF delivery, physical SDRAM margin, ESP32 scheduler/stack behavior or visible LCD quality. Those are explicit hardware checks, not inferred offline passes. A known failing correctness, lifecycle or image-timing gate blocks that candidate; an unmeasured physical property is the purpose of a controlled trial.

### 6. Hardware ladder to the two-minute replay

1. Reconfirm physical boot, exact app ELF, FPGA hash/DONE/USERCODE/ABI, actual IP/filter, ownership, heap/stack and intended mode. Preserve rollback; no installation or start based solely on this plan.
2. With fresh candidate identities, run the original KEY/P control and independently check presentation and natural colors.
3. Run a short distinct multi-frame Mass Effect sequence at a conservative measured rate. Require matching references/reconstruction, presentation replies, stable placement and bounded memory. Include a controlled recovery trial separately.
4. Run 10 seconds of the actual clip. Choose cadence from measured service capacity; increase only after ingress and presentation remain healthy. Record configured, complete-sent, admitted, decoded and unique-presented rates separately.
5. Run the full 120 seconds, offset zero/no looping, video-only. Predeclare rate/quality/profile, source hash/preparation, fresh IDs/session, baseline counters and recording coverage through STOP. Freeze/export receiver history afterward; reconcile all sends, rejects, missing outcomes, queue/core errors, reference recovery, visible freezes and STOP/ownership restoration.
6. Add independently sequenced controls, then audio, with explicit compatible AV ownership and coexistence tests. Existing JPEG/AV success does not prove coexistence with the custom native owner.

Do not start a long run if encoding support, receiver continuous lifecycle or measured cadence is still missing. A slower correct custom replay is an intermediate milestone, not a 20/30 fps acceptance result.

## Immediate deliverables and coordination

Latest physical milestone: [V48 local12 hardware PASS](V48-LOCAL12-HARDWARE-RESULT-20261107.md):12accepted/12presented,253,440HUDwords verified, zero rejects/underruns/native allocation failures. V48 preserves V47's native decoder and V027, adds local serial control/WinUSB descriptors, and uses the local`.33`sender. Both checksummed exports match. This is a bounded correctness result, not30fps or the full120-second clip; changed host/control layout prevents isolated allocation-order attribution.

Current work: qualify fully automatic software recovery and protected app-only vendor updates, then longer distinct sequences and measured decoder/QSPI improvements. See [V48 bootstrap](V48-SELFTEST-BOOTSTRAP-20261107.md). The first software reboot occurred and was independently verified after a host COM-open race; preserve that failure and qualify the corrected controller separately. No true battery-level cold cycle is claimed.

Update: the corrected controller subsequently completed a physical software-reboot qualification, including bounded COM-open wait and exact post-reboot ELF. Software DFU enumerates as a separate noncomposite root node lacking a driver; a narrowly scoped signed in-box WinUSB binding is prepared, pending one-time administrative approval. No vendor-client flash erase/write has been attempted. Offline [V49 and V50 candidates](V49-V50-OFFLINE-CANDIDATES-20261108.md) now pass target-build/package checks and await safe updater access; keep their native changes separate for comparison.

Previous candidate: [V47 allocation-order hardware handoff](V47-HARDWARE-HANDOFF-20261107.md), with [change/test plan](V47-HUD-ORDER-PLAN-20261107.md). Its direct network attempt had expired sender/receiver windows and never exercised the codec; V48 subsequently ran the decoder successfully locally. This candidate improves some synthetic heap layouts but is not a universal fragmentation cure; no V027/wire/cap/reserve change.

Current physical result: [V46 cold CPU12 passed](V46-CPU12-HARDWARE-RESULT-20261107.md), then [V46 network cached12 located frame3's failed11,520-byte malloc](V46-V027-CACHED12-FAILURE-20261107.md):35,284total free but7,680largest internal block. The wrapper identifies Prepare opcode1/native reply4; FPGA passive samples show3accepted/3presented/0rejected/0underruns. Keep the failed endpoint quarantined until coordinated update; no V027 rebuild is indicated by this immediate cause. V45's similar failure had no allocator detail, so its exact cause remains unproven.

Previous physical result: [V45 cached3 passed](V45-V027-CACHED3-RESULT-20261107.md), then [cached12 stopped at frame3 with generic native Hud failure](V45-V027-CACHED12-FAILURE-20261107.md). Host and receiver agreed on three presentations and a stored-but-failed fourth frame; frames4–11 were withheld.

V46 diagnostic build, target compilation, packaging, independent review and bounded physical checks are now recorded in its handoff/result reports. It retains the actual native opcode/reply/payload checks, allocator failure context and failure-only passive FPGA status, plus a separate cold CPU-only twelve-frame HUD probe. V027, sequence-v3 and all decode/admission/reserve/ownership rules stayed unchanged. The cold probe cannot reproduce network-time fragmentation. Do not advance to long-video or performance testing until a bounded candidate fixes and verifies the network-time allocation failure.

Previous candidate design: [V45 ingress cache, reliable telemetry and longer bounded host sequence](V45-INGRESS-CACHE-PLAN-20261107.md). This is ESP32+host work with unchanged V027; exact source-bound cached-system replay and physical runtime qualification remain distinct gates.

Earlier physical milestone: [V44/V027 three-frame end-to-end PASS](V44-V027-HARDWARE-RESULT-20261107.md). All three host presentation replies match3receiver presentations and63,360 actual HUD comparisons. This does not qualify continuous playback. V45 subsequently passed cached3 with complete paced telemetry; cached12's native failure is the current gate.

Execution has begun: see the [first offline verification results and remaining gates](OFFLINE-VERIFICATION-PROGRESS-20261107.md). The [next continuous receiver candidate design](CONTINUOUS-RECEIVER-NEXT-CANDIDATE-20261107.md) defines the bounded correctness-first implementation; it is not an installed or built release.

The first bounded implementation is now built and packaged as V44, using unchanged V027. See the [exact three-frame hardware handoff](V44-V027-HARDWARE-HANDOFF-20261107.md): final-source host/native/socket, complete selected-system replay, ELF SRAM/configuration and production UF2 parser gates passed. This is ready for a coordinated three-frame physical correctness/stage-timing test; it does not implement the120-second stream, continuous session recovery or30fps. A native prediction-copy fix restores the original98,304-byte arena cap while keeping physical guards unchanged. Current hardware identity/IP/memory must be checked after installation.

- Windows: current branch/commit capability report, short Mass Effect CU66 sequence and software-reference results, then a version-matched continuous uploader.
- ESP32: new continuous candidate, contract, failure/reuse tests and stage timing; exact V43 retained as the two-frame control.
- FPGA: V027 continuous-system audit/simulation and measured change proposal; rebuild only for a selected change or failed gate.
- Integration: offline verification matrix and exact candidate report first, then the next coordinated hardware window starting with the original pair and short sequence. No current START, IP readiness or test ETA is asserted.

All new source, tools, evidence and fast build outputs stay beneath `C:/moon`. Preserve one exact JPEG/build50 recovery backup and the current custom control; clean superseded generated builds as milestones complete.

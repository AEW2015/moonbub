# CU66 v70: ESP32 and FPGA implementation plan

> Active next-development plan (November 7): [continuous CU66 playback and the two-minute Mass Effect replay](CUSTOM-CODEC-STREAMING-PLAN-20261107.md). V43/V027 has now passed the original network KEY/P pair; continuous streaming and 30 fps remain unqualified. The dated baseline below is retained as architecture/history, not current hardware readiness.

Date: November 5, 2026, America/Denver. Status: proposed implementation; no
CU66 board image, target firmware or 30 fps result is established by this plan.

Source: [v70 hardware handoff](https://github.com/AEW2015/moonbub/blob/fcc02c58d46f96a26790ce02826a0bf937c2478b/docs/cu66-v70/hardware-handoff.md),
[milestone definitions](https://github.com/AEW2015/moonbub/blob/fcc02c58d46f96a26790ce02826a0bf937c2478b/docs/cu66-v70/plan.md),
and [diagnostics](https://github.com/AEW2015/moonbub/blob/fcc02c58d46f96a26790ce02826a0bf937c2478b/docs/cu66-v70/diagnostics.md).
Pin integration to commit `fcc02c58d46f96a26790ce02826a0bf937c2478b`.

## Direction and acceptance

Preserve CU66 payloads, decoded quality, 720×480 coded resolution, canonical
reference identity and exact HUD semantics. First deliver sustainable **30
unique, complete presentations/s**. Then retain that throughput while reducing
the observed maximum validated-decoding latency to **strictly below 10 ms**.
Audio and independently sequenced controller coexistence follow the video gate.

The immediate bottleneck is memory service and presentation. Prioritize BL8
scanout, bounded arbitration, burst writes and the ESP32 HUD feasibility port.
Do not begin by adding inverse-transform lanes or raising the memory clock.

Retain the existing JPEG/AV implementation as a selectable compatibility path.
CU66 is a new integration, not a replacement image that can be deployed by
copying the study top. The current CP23 fixed-ROM image work is a separate
qualification track; its success would not establish CU66 support.

## Starting evidence and compatibility boundaries

V70 has functional reconstruction and transactional tests, but its integrated
command-model cadence fails. The eight-row painter's modeled P transaction
takes about 230 ms under its declared schedule; that includes composition and
contention and is not decode-only latency or a measured FPGA result. Its host
HUD endpoint has no measured ESP32 CPU cost. Existing tests must be retained
as controls, with their original source and model assumptions.

The local SDR2 tests establish a selected physical memory operating point, not
full-system throughput. Four complete memory passes had zero comparison errors;
the metrics image measured about 93.91 MB/s aggregate useful sequential read+write
traffic. This is neither a concurrent-system ceiling nor a 30 fps qualification.
The slow/max full-top post-route simulation remains incomplete; preserve and
investigate that gap independently of functional and physical evidence.

**Do not deploy v70's physical SDRAM controller unchanged.** Its conservative
backend has MRS 0x233, single writes, read-wait 5, a 279° assumption and negedge
retiming. The local qualified SDR2 backend uses MRS 0x033, BL8 writes,
read-wait4,274.5° and posedge retiming. Preserve the qualified clock/pin/I/O
constraints and validate an explicit adapter. Do not mechanically change a
wait constant in the v70 source and treat old simulation results as proof.

## Work packages and gates

### A. Freeze the integration contracts and establish target fit

1. Create an isolated integration checkout/candidate. Preserve the v70 study,
   its failure evidence, current running builds, and unrelated working trees.
2. Record exact source/fixture hashes, tool versions, board revision, fitted
   part, memory map and selected timing profile. Generate map constants shared
   by firmware, RTL and tests; initially use only the implemented 32 MiB chip.
3. Freeze network/session admission separately from internal HUD framing:
   - CU66 complete packet length is 1..49,152 bytes. Reject oversized packets
     before allocation/start; do not inherit JPEG's 262,144-byte maximum.
   - The internal HC70/HR70 ABI has a 32-byte LE header, up to 49,152 payload
     bytes, and a 4-byte IEEE CRC over header+payload (49,188 bytes maximum
     complete control frame). Keep generation/frame/
     reference identity, opcode, length and reserved-field checks.
   - Decide and document CU66 transport magic/version, port, fragmentation,
     checksums, reference recovery/key requests and admission/feedback meaning
     with the Windows agent. HC70 is not a UDP-video protocol. Do not silently
     reinterpret MSV1 JPEG payloads or advertise an unimplemented capability.
4. Run exact-device leaf/OOC synthesis early on `xc7a100tcsg324-1`, followed
   by the full board wrapper. Report LUT/FF/BRAM/DSP use, RAM ports, inferred
   storage, clocks and CDC. The remote study's missing-device limitation does
   not apply to the installed local target tools.

Exit: versioned interface/map document, immutable vectors and target resource
baseline. Network implementation waits for the agreed contract; RTL/firmware
component work can proceed meanwhile.

### B. Instrument the memory service and validated-ready boundary

Add per-client accepted/completed operations, outstanding counts, service wait
max/distribution, arbitration blocking, cache hit/miss/eviction, queue peaks,
ACT/PRE/RD/WR/REF, turnaround and refresh deferral. Separate LCD, painter, HUD,
reference, candidate and compressed-staging costs. Keep response ownership
through backpressure; queue acceptance is not memory completion.

Add generation/frame-bound packet-complete, admission, packet-validated,
base-tag, HUD CPU/transfer/readback, writes-drained, validated-ready, RGB-ready,
commit and qualified presentation events. Existing arrival is admission, not
packet completion. Add coherent snapshot/latch semantics and full live stage;
the compact two-bit stage and eight-entry event ring are insufficient alone.
Retain first faults, event overwrites, trace loss and every attempted outcome.

Exit: reproducible baseline under fixed arrivals and concurrent scanout/refresh,
with reconciled per-client time and traffic. No subtraction of unrelated clocks.

### C. Integrate the qualified memory backend and remove scanout starvation

Affected study paths: `memory/cu70_memory_system.sv`, `cu70_word_bridge.sv`,
`cu70_tile_memory.sv`, `display/cu70_scanout.sv`, `cu70_lcd_lines.sv`, and the
aux-client arbitration in `system/cu70_system.sv`.

1. Bridge the study APIs to the qualified BL8 controller, preserving response
   generation, frame, bank, plane, tile and request sequence ownership.
2. Implement dedicated BL8 LCD line prefetch and bounded service reservations.
   A 480-word line needs 60 aligned BL8 reads rather than 480 scalar roundtrips.
   Derive the actual request-to-active deadline from the selected board timing
   and two-buffer schedule; the study line period is about18.43µs. Include
   refresh, row misses, turnarounds and maximum non-preemptible grants.
3. Give readers independent response buffers and reader-specific caches or a
   measured associative alternative. A stalled HUD/painter response must not
   hold the entire arbiter. Preserve selective alias invalidation, including
   queued reads and write completion ordering.
4. Add abort-safe BL8 strip, HUD and canonical writers. A canonical tile row
   contains four x16words: combine only within owned allocations or mask the
   remaining beats. Define partial/odd-byte masks, row boundaries, flush,
   accepted-beat accounting, completion and drain explicitly.

Exit: exact canonical/HUD/RGB readback and intact guards with scanout+refresh
active; no normal-load LCD underruns; bounded per-client latency. Exercise
every partial/abort beat boundary, stalled response, alias, refresh overlap,
reset recovery and row/bank transition. Use the datasheet-correct model and
routed I/O terms; preserve original v70 models as historical controls.

### D. Select the presentation architecture from measured workloads

Keep the RGB565/eight-row strip path as the exact-output control. In parallel,
prototype direct transposed-YUV scanout with bounded line caches and exact
color/HUD conversion. The study estimates122.91 MB/s useful traffic for its
copy path versus69.56 MB/s for direct YUV, excluding important overheads. Those
figures motivate the experiment; they do not prove either architecture fits.

Compare identical fixed arrivals, observation windows, content and display
timing. Include all ingress/reference/HUD/scanout traffic, command overhead,
overfetch, refresh, diagnostics and failed attempts. Prefer the RGB control
only if measured concurrent service has sustainable30 fps capacity and useful
deadline margin. Otherwise select direct YUV after these gates:

- Exact native rounding, chroma interpolation, HUD and complete480×800 rasters.
- Canonical hash order independent of transposed storage layout.
- Reference and scanout leases both prevent premature bank reuse.
- Bounded line-cache size, worst-case refill time and target BRAM/DSP fit.
- Zero normal-load black replacement lines or mixed-generation pixels.

After selecting the path, overlap decode and provisional conversion/writes
where dependencies permit. Keep all provisional pixels private until parser,
base/HUD integrity and memory fences permit the single global commit.

### E. Port the processor endpoint to bounded ESP32 firmware

1. Port the actual native HUD semantics and HC70/HR70 compatibility vectors;
   remove unbounded vectors/copies and account for exceptions/temporary memory.
   Stream bounded chunks and incremental CRC/hash rather than holding complete
   request and response copies. Keep radio/UI operations off blocking paths.
2. Use bounded DMA/QSPI buffers and immutable FPGA packet staging. Start the
   owner only after outer ingress completeness/integrity checks and staging
   writes drain. Record packet-complete when immutable staging is available;
   do not move it past admission or CU66 semantic/base/HUD validation. Recycle
   the allocation only after every tagged read/operation drains.
3. Measure peak live allocations, largest free block, task stack high-water,
   CPU service, lock wait, transfer time and Wi-Fi/UI/AV coexistence. Two HUD
   caches alone are 94,720 bytes; adding two maximum HC70 wire buffers would
   exceed 193 kB before these other costs. Desktop execution is not fit evidence.
4. Budget actual QSPI service: HUD write+functional readback is 84,480 bytes/frame,
   or 2.5344 MB/s at30 fps. Maximum compressed ingress adds 1.47456 MB/s. The combined
   useful demand for this maximum-packet-size workload is at least 4.009 MB/s
   before framing/retries/diagnostics/AV; smaller packets reduce ingress traffic.
   Benchmark that mixed workload, DMA gaps and lock contention on this board.
5. Keep independent controller sequencing and audio workers bounded. Charge
   their contention during coexistence tests; video ACK is not decoder-ready.

Exit: all retained HUD histories and malformed/control vectors pass on the
ported endpoint; measured SRAM/CPU/stack/QSPI budgets fit without UI starvation
or reboot. If they do not, explicitly repartition HUD work/storage and repeat
the exact-output checks before enlarging firmware or advertising CU66.

### F. Preserve publication and recovery semantics end to end

The FPGA root owner is authoritative. Require matching generation/frame/
reference ID for processor mutations and candidate reads. Check response
header echoes and status-body identity separately; a retry response must not
substitute state belonging to another transaction. Require
all parser/base/HUD/write-drain conditions before commit. Compute HUD integrity
from actual functional readback, not a count of 21,120 transferred words alone.

Before commit: hold accepted reference/HUD/front state, stop new work, and
drain already accepted operations before releasing banks. After commit: retain
the irreversible decision and retry matching idempotent COMMIT until processor
reconciliation; timeout must not roll it back. Use STATUS to resolve a lost
PREPARE reply instead of blindly preparing again. Reject stale completions.

Retain the RGB or YUV front descriptor until its matching presentation ACK;
vblank alone does not release it. RESET requires confirmed adapter and both
clock-domain quiescence plus a fresh generation. Clearing diagnostics does
not authorize reset, cancellation or allocation reuse.

Exit: wire-to-owner tests cover corrupted/fragmented messages, lost/duplicate
ACKs, delayed descriptors, dependency loss, abort during every transfer phase,
timeout/drain and coordinated reset without partial publication or deadlock.

### G. Timing closure, local hardware and coordinated network acceptance

1. Build the selected complete board design with exact source/asset hashes.
   Require positive routed setup/hold/pulse slack, zero failing routes, DRC
   acceptance, complete timing coverage and reviewed CDC/reset crossings.
   Retain I/O budgets and clocks; no blanket false paths or relaxed constraints.
2. Repair measured logic paths with registered handshakes, balanced reductions,
   local enable replication and bounded fanout as appropriate. Pipeline only
   with exact latency/backpressure tests. Preserve BRAM inference; reset
   ownership/control rather than bulk data, with explicit soft-reset flushing.
   Re-check timing after integrating memory, display and firmware interfaces.
3. Generate a hashed BIT and app-only firmware package. Preserve exact installed
   image/ELF metadata and recovery artifacts. Use volatile JTAG first; fresh
   USB identity/DONE and camera coverage must precede claims about playback.
4. Local loader/BIST: memory+guards; bars/edges/motion; actual CU66 key and
   dependent P; canonical/HUD/framebuffer readback; presentation identity;
   malformed/abort/lost-ACK/reset recovery. No network required for this gate.
5. Coordinate a fresh Windows test window and agreed CU66 contract. Start
   low-rate exact fixtures, then fixed 5/15/20/25/30 fps replays. Advance only
   after complete outcome/counter reconciliation and explained failures.
6. Qualify 1,800 distinct chronological source frames, then a ten-minute physical
   30 fps campaign. Preserve source/attempted/accepted/committed/presented IDs,
   packet logs, diagnostics, camera coverage and STOP/restoration evidence.
   Predeclare warm-up/drain windows, bounded age/backlog and panel-quantized
   deadline policy. Duplicated scans, buffer flips and ingress ACKs do not count.
7. Repeat with audio and independently sequenced controls. Then pursue the
   strict observed-maximum validated-decoding target below10 ms without losing
   the throughput/correctness gates. Include post-staging queues and HUD CPU,
   transfer, validation and drain; report composition/vblank/scanout separately.

Exit: 30 unique complete presentations/s over the declared physical campaign,
bounded age/backlog and no unexplained loss or normal-load LCD underruns.
Report all failures and p50/p95/p99/max. A low-rate diagnostic hardware PASS
is not this release gate; neither is a simulation or native encoding benchmark.

## Parallel execution and dependencies

| Owner | Work that can start in parallel | Integration boundary |
|---|---|---|
| Root/integrator | Contracts, owner/recovery, resource baseline, final system tests | Owns interfaces, capability advertisement and release verdict |
| FPGA memory agent | BL8 adapter, LCD scheduling, cache/response isolation | Must retain generation/drain identity and selected PHY constraints |
| FPGA display agent | Strip control and direct-YUV prototype | Exact pixels, reference leases, line deadlines and RAM-port budget |
| ESP32 agent | Bounded HUD endpoint, staging, QSPI/CPU/SRAM measurements | HC70/HR70 vectors and irreversible owner/commit reconciliation |
| Luna agent | Source/vector hashes, register docs, counts and evidence packaging | Independent scope/count checks; no relabeling failed runs |

With four available concurrent slots, root plus memory/display/firmware can
run first; reuse a finished slot for Luna audits. Avoid simultaneous large
Vivado implementations that exhaust this machine. Serialize all programming
and serial ownership. No agent may alter shared interfaces without root review.

Dependency order: A+B → C/E in parallel, D prototype alongside C → architecture
decision and F integration → G. Run exact-device synthesis early, not only
after all features are written. Keep both correctness and timing failures
visible while measuring the next single change.

## Immediate next development slice

### Measured updates on November 6

The implementation is now split between a local correctness candidate and a
direct-YUV throughput prototype. Keep these verdicts separate:

| Measured cause | Implemented successor | Remaining gate |
|---|---|---|
| Original v70 storage inferred 209,508 FFs and did not fit | Per-bank synchronous canonical BRAM and pipelined painter BRAM; first complete shell uses 29,059 LUTs and 27,814 FFs | Final successor resource and routed reports |
| Entropy configuration modulo formed a 70-level path | Bounded 17-step remainder; arithmetic v4 separates product, clamp, boundary, probability update and parameter validation | Whole-board routed setup/hold; leaf setup is +0.544 ns |
| Dequantizer combined coefficient selection and DSP multiply | Registered selection/product/store, 7,081 exact golden tiles and 78 cancellation/replay checks | Whole-board routed setup/hold; leaf setup is +2.906 ns |
| Long reset-distribution paths remain after arithmetic fixes | Compare same-cycle final-stage FF replication with an isolated combinational BUFG experiment | Exact leaf/driver/control-set audit and routed result; no blanket reset false paths |
| Complete codec activity still causes LCD underruns | Direct-YUV cache, color pipeline and descriptor owner; physical canonical tiles use four full BL8 operations | Actual SDRAM/LCD raster, ownership/commit integration and complete clean-generation cadence |

The entropy timing repair costs approximately 49.45% more cycles in the same
1,371-fixture entropy campaign. It is a setup repair, not a throughput win.
The whole key/P/P successor remains exact but has 2,599 LCD underruns in its
short actual-pin-model replay. Do not promote its descriptor acknowledgments
to complete clean presentations. Profile the full stages before choosing
context overlap or a shorter arithmetic schedule.

The reset BUFG experiment finished with WNS -0.249 ns versus -0.113 ns for its
unchanged parent candidate, so it is not selected. A global buffer is a measured
option, not an automatic cure. Regional FF copies must retain the original
INIT, primitive, clock, CE, D, asynchronous PRE and same-cycle behavior; preserve
strong D setup/hold checks and audit every moved primitive leaf. Temporary
mixed control sets during an ECO are not evidence of a legal final placement.

For the morning, preserve build50 for the separately coordinated 25 fps test.
The selected successor app is now sealed **v36**, with explicit local USB `G`
for CU71 and `Y` for incompatible DY71. The direct profile is identified by
magic `44593731`, ABI `00010000` and capabilities `0f`; it does not reinterpret
CU71's RGB slot. First use still requires an app-only update and a separately
qualified, exact-profile BIT. V35 remains an immutable prior artifact and
must reject DY71. CU66 network capability remains false.

Current completion sequence (November 6):

1. Retain build50/v32 for the separately coordinated morning 25 fps test.
2. Complete report-only full-board DY71 implementation with the proven grouped
   memory scheduler, SYNCsafe LCD crossing, bounded tile/index arithmetic,
   lookahead SHA and structural CSR read-address split. Do not relax clocks,
   SDRAM hold or board I/O budgets. Bind exact source and legal CDC endpoints.
3. Replay the actual sealed v36/native KEY/P worker against that selected
   SYNCsafe/math/split-control CSR and checked SDRAM pin model. Keep numeric
   CSR, physical QSPI wire tests and physical playback evidence separate.
4. Resolve each measured routed critical path; require positive setup, hold,
   pulse, complete routing, no DRC errors, reviewed CDC/exception coverage and
   frozen functional proofs before generating and hashing a BIT.
5. After the baseline test, perform the known physical app-only update step,
   check the installed ELF identity, and run the W exception probe plus one
   explicit local G or Y fixture with USB/camera/counters and build50 rollback.
6. Keep the 30 fps gate closed until clean unique presentation is measured.
   The grouped direct three-frame replay has no underruns but a 46.10029 ms
   second presentation interval. Profile arithmetic, reference traffic and
   bounded scheduler idle time before changing another parameter.

1. Freeze the pinned sources and generated map/contracts; reproduce the
  457-frame and 28-negative controls without modifying their archived results.
2. Start local exact-device resource/OOC checks and the ESP32 allocation/CPU
   feasibility port in parallel.
3. Build the qualified BL8 bridge plus dedicated LCD prefetch and instrument
   worst service deadlines; prototype direct-YUV with the RGB strip oracle.
4. Review measured budgets before selecting the complete board architecture.
   Do not promise a CU66 hardware-test date until fit, memory service and
   firmware feasibility gates have execution evidence.

Deliver source-pinned commands, reports, failed attempts, source/constraint/
fixture hashes, firmware ELF/BIN/UF2 metadata and the actual BIT. Keep functional,
timing, physical playback, throughput and latency verdicts separate. The
GameBub and Vivado evidence-handoff skills apply to build/recovery and packaging;
neither replaces independent functional or physical verification.

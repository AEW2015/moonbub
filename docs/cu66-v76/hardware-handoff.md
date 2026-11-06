# CU66 V76 — warm-frame limits and direct-YUV service candidate

V76 measures the frozen V75 design under warm, phase-controlled scanout and
prototypes the memory/cache organization needed to remove the RGB composition
pass. It does **not** change production RTL or produce a bitstream.

The sustained **30 distinct source-fps** and **strict maximum validated decode
below 10 ms** goals remain unproven. The new warm burst-HUD measurements are
**28.16892–30.36680 ms validated** and **86.60411–89.20155 ms per transaction**.
The earlier V75 bootstrap P measurement, 16.98661 ms validated / 75.86986 ms per
transaction, does not generalize to an already active front.

There is useful forward progress: a dedicated display-port, bounded early-read
schedule meets all 90 original strip deadlines under the tested paced memory
load. Its cache liveness model requires **29,184 data bytes**, plus hardware
staging/control/output buffers. This qualifies a service/cache hypothesis for
RTL development, not a working direct-YUV display or a 30-fps system.

## Goals and timing contract

See [milestones.md](milestones.md) for exact measurement boundaries. Primary
validated latency is immutable ingress-complete → validated-ready, retaining
queue, actual memory drains and validation. FPGA admission is also recorded.
Composition/commit events and an actual qualified front switch/full correct
raster remain separate. Kernel-only or first-black-border timings do not close
the validated-frame or input-to-photon gates.

The predefined **1,800-source modeled run is 60 seconds** at 30 fps. A ten-minute
physical proof requires **18,000 distinct sources** after declared warm-up, with
live ESP32/processor/display service and all failures retained. None of those
sustained campaigns is replaced by the short V76 tests. The 33.333…-ms transaction
threshold is a serial service-budget test for the current single-candidate
implementation; future overlapped pipelines also need initiation-interval and
queue/output-throughput qualification.

## Warm full-system replay

Each trial produces a real key and P source through the actual packet/qmap/base,
reference memory, native semantic HUD endpoint, painter and LCD path. The P is
admitted at an exact absolute cycle **20,000,000 + offset**, after nine complete
correct warm rasters of the first source. Offsets are 0, 384,171, 768,342 and
1,152,513 memory clocks. Actual request handshake timestamp, panel x/y/active
state and front generation match across scalar/burst pairs. No deadline is slid
to a later convenient admission.

| Warm P interval, four phases | Scalar HUD | Burst HUD |
|---|---:|---:|
| Validated interval | 36.20444–40.28688 ms | **28.16892–30.36680 ms** |
| Composition | 58.32003–59.23407 ms | **58.36391–59.16383 ms** |
| Complete transaction | 95.43920–98.60760 ms | **86.60411–89.20155 ms** |

All **eight trials × two sources** pass independent canonical hash/plane,
complete portrait RGB565 and live LCD order/generation checks. Every trial
has two distinct correctly presented sources, zero LCD underruns and zero
mismatching black lines. Processor COMMIT acknowledgment loss is reconciled
without a second global commit. Predicted references come from prior RTL-produced
SDRAM; the oracle does not feed golden reference pixels to the decoder.

All eight P cases fail both modeled performance thresholds. Even an optimistic
perfect overlap of the measured decode and composition stages leaves the slower
stage above 33.333 ms. Thus overlap alone, with the existing composition work,
is insufficient in this experiment. The finite observed maximum is not a formal
worst-case latency proof.

The model assumes 100 MHz and zero simulation time for native CPU HUD execution,
readback hashing and control. Live ESP32 Wi-Fi/QSPI is absent. These omissions
remain open system work; the warm values cannot be promoted to target latency.
See [phase evidence and exact timestamps](phases.md).

## Actual-controller strip service

The independent trace maps the 720×480 coded image to 90 native eight-row strips.
It includes exact parity-dependent chroma neighbors and actual packed HUD block
addresses. Software cache schedules retain 720 YUV lines and 192 HUD lines,
16 bytes per line, cold at panel start. The trace contains **35,040 BL8 requests /
280,320 checked x16 words / 560,640 physical bytes**, including all 2,640 HUD
blocks. Static profile SAFE maps supply 7,806 ordered nonhidden reference tile
IDs; background release times are synthetic, not timed live packet decoding.

Source data is initialized through actual physical writes, outside measurement.
The benchmark then uses the unchanged V74 bridge/memory adapters and V72
controller/checked SDRAM command model. Every returned word is checked. Paced
background releases use **243,000 canonical upload tiles/s** and **234,180
reference tiles/s**, corresponding to 8,100 / 7,806 tiles at 30 fps. Upload uses
bank 1, while reference reads share the displayed immutable bank 0. All released
jobs are counted; measurement-end backlog is reported and drained.

The minimal producer route has no extra inserted issue bubbles. P1 wrapper
acceptance can precede internal arbitration; its one-cycle acceptance gap does
not imply contention-free service. The dedicated display route exposes the
actual direct acceptance wait. Original strip cache-ready deadlines are
147.403024 µs apart.

| Continuous request route / background | Maximum service | Original deadlines missed |
|---|---:|---:|
| P1 auxiliary / none | 124.60 µs | 0 / 90 |
| Dedicated display / none | 118.94 µs | 0 / 90 |
| P1 auxiliary / paced shared-front references | 224.67 µs | 90 / 90 |
| Dedicated display / paced shared-front references | 150.48 µs | **1 / 90** |
| P1 auxiliary / saturation | 259.44 µs | 90 / 90 |
| Dedicated display / saturation | 149.99 µs | **1 / 90** |

The paced display-port miss is approximately **3.08 µs**; the saturation miss is
approximately **2.59 µs**. These failures remain in the final base evidence.
The corresponding tAC 2/7-ns results agree. An extra producer-gap control costs
another clock per request and is retained separately. The near-deadline case
also has an Icarus crosscheck. Finite functional PASS and deadline PASS/FAIL are
separate verdicts. See [service setup, counts and cross-simulation](service.md).

## Early schedule and corrected cache lifetime

A separate schedule moves strip `i` request release from `i*P` to
`max(0,i-1)*P`, retaining original cache-ready deadline `(i+1)*P`.
The dedicated display route meets **all 90 original deadlines** with paced
shared-front background at both tAC corners. P1 still misses all 90. The largest
individual display service interval is 153.97 µs; that can exceed P because the
request starts early and still completes before its original absolute deadline.
No result is rescued by changing or dropping a deadline.

A whole cached strip must be ready **before consumption starts**. The timeline
therefore includes one initial period of prefill, with consumer `i` starting at
`(i+1)*P`. Under the early schedule a current strip, a next ready strip and an
additional filling strip may coexist. A two-live-strip cache proof is insufficient.

The independent structured Python model proves the tested data/address liveness
for three Y columns, three chroma columns per plane and four HUD block columns
per rectangle: **29,184 bytes**. A 19,968-byte two-live-strip model remains valid
for its narrower case but does not justify the early schedule. Negative probes
with too few Y, chroma or HUD slots expose overwritten live data. Each of the
one-/two-/three-live-strip models checks **345,600 active RGB565 pixels** and
matches every per-strip miss set in the independent LRU trace.

This replaces the earlier tentative two-live-strip memory estimate. It is a
cache-consumer timeline correction, not a change to the measured service result.
[Structured architecture and model](direct-yuv-architecture.md) gives the slot
mapping, explicit hazards, initial prefill requirement and physical implementation
gates. The service benchmark has no RTL cache or pixel consumer; the Python
model has no cycle-accurate BRAM ports, compute, clock crossing or source switches.
Their combination is a candidate architecture, not integrated timing proof.

## What is ready for the next RTL iteration

Implement the structured three-live-strip cache and streamed fill on the dedicated
display path, with a native pixel pipeline and explicit generation leases. Keep
full-word synchronous reads and real port schedules, measure unpack/compute/fill
overlap, and compare every pixel and deadline against the native oracle. A
128-bit snapshot unpacked for eight extra clocks is not the same service as
writing one incoming streamed word per clock.

Bind descriptors to source ID, generation and canonical bank. Drain accepted
old-front reads and honor the qualified vblank switch before releasing that bank.
The RGB-copy flow could release canonical storage earlier; direct scanout cannot
inherit that ownership assumption. Test stale responses, aborts, pending
switches, source changes, invalid cache tags and shared reference/front traffic.

Then repeat multiple full panel periods, including border/vblank intervals,
cache invalidation and actual source arrivals. The current service replay is one
cold panel trace, not steady-state or sustained 30-fps proof; its synthetic
paced clients omit entropy decode, CPU and transport. Controller command
queueing/coalescing and ownership-safe scheduling remain candidates for reducing
validated decode toward 10 ms. Profile accepted service, waits and compute with
proper overlap accounting; do not subtract independently overlapping counters
as if they were a complete critical-path decomposition.

Retain the 457-frame and 1,800-distinct-source modeled gates, then exact-device
fit/route/CDC, live processor/ESP32 service and the 18,000-source physical goal.
The frozen V75 exact-part preflight remains **UNAVAILABLE_EXACT_PART**; V76 has
no new production top or new target implementation result.

## Reproduction and integrity

```sh
python3 scripts/cu66-v76/verify_baseline.py
python3 scripts/cu66-v76/run_phases.py
python3 scripts/cu66-v76/generate_service_trace.py
python3 scripts/cu66-v76/run_service.py
python3 fpga/experiments/cu66-v76/service/run_crosscheck.py
python3 fpga/experiments/cu66-v76/service/run_lookahead.py
python3 scripts/cu66-v76/structured_cache.py
python3 scripts/cu66-v76/analyze_milestones.py
python3 scripts/cu66-v76/verify_evidence.py
python3 scripts/cu66-v76/bundle_manifest.py
```

Use the recorded containers and mounted paths, one build job and bounded runtime
workers. The service document supplies the separate Icarus command. Baseline
verification preserves every V69–V75 manifest and the V75 parent ancestry.
Recorded source/log/trace hashes and internally hashed superseded archives make
functional results and their measurement boundaries reviewable. Package integrity
is a separate gate from correctness, deadlines and hardware qualification.

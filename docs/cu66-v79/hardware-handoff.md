# V79 hardware-development handoff

## Scope and goals

The integrated hardware remains the frozen V78 decoder, guarded HUD transfer,
canonical-bank ownership, direct cache/converter and native LCD pipeline. V79
changes its testbench and measurements. It also adds a **separate two-slot
reference-prefetch RTL experiment**, which is not connected to that system.

The target remains sustained 30 distinct game-source frames per second through
ESP32 → FPGA → display, followed by a strict maximum ingress-complete → validated
FPGA decode interval below 10 ms. Preserve coded 720×480 and native 480×800
portrait output. A serial processor-ACK budget, panel repeat or isolated cache
test does not establish either whole-system goal.

V79 uses parallel agents for monitor/RTL development, an independent memory
study/review, and Luna evidence auditing. Root coordinates immutable campaigns,
paired comparison, finite queue budgets and integration reporting.

## What the hardened system bench checks

Every model evaluation observes display error pulses, the memory-error counter
and underruns, including packet-release waits, admission waits, canonical
verification and final display drain. A failed observation records its phase
and timestamp and fails the run. No severity is downgraded to obtain a PASS.

Every processor COMMIT ACK starts a per-generation full-raster obligation with a
100-ms functional liveness bound. Completing a raster removes only that identity's
obligation. A retry/repeat cannot restart its timer, and an already completed
raster is not rearmed if ACK is delayed. This conservative liveness bound is
**not** a permitted gameplay-latency threshold. The final observation window is
at least the same 3,500,000 clocks as V78 and extends if obligations remain.

The input model declares the complete finite release schedule before running.
It samples released-but-unadmitted, admitted-but-unacknowledged and total owned
source counts throughout admission stalls. Original ingress timestamps do not
slide when the decoder falls behind. Waiting and active packet storage are
reported separately; this is a modeled endpoint, not an ESP32-capacity proof.

Each actual source still passes independent full canonical plane/hash checks,
actual HUD write/readback/hash fences and complete ordered native-raster checks.
The decoder's reference pixels come from prior RTL-produced SDRAM. No expected
reference, predecoded canonical frame or per-source reset feeds the system.

The new eight disjoint tick bins partition BASE_RUN versus other stages, tile
adapter busy versus idle, and HUD adapter busy versus idle. Sixteen stage bins
also partition each transaction exactly. These describe occupancy and overlap;
they are not a critical-path decomposition or a recoverable-gain measurement.

## Qualified artifacts and result boundaries

The nine observer self-tests use synthetic observation snapshots. They check
error pulses during release/readiness/tail phases, memory-error and underrun
counters, expired/fulfilled raster obligations and finite queue growth. They
test the checker; **they are not injected physical hardware failures**.

The paired four-source actual-system smoke matches **184 original V78 fields**,
including complete transaction timing, first-presentation milestones and the
original final summary. Only CPU wall-time observations differ. The production
RTL and behavioral timing are unchanged by the added verification. Both runs
use the same original modeled clocks and fixture schedule.

The extended campaign requests four independent histories, with **119, 119,
119 and 100 sources**. Each independent process resets once at its history
boundary and then runs continuously. Identity is `(cohort,generation,frame ID)`;
source IDs can repeat across independent histories. The total is 457 history
samples, not a single 457-source continuous stream and not a replacement for
the 1,800-distinct-source/60-second sustained gate.

The frozen fixture catalog identifies the cohorts as `mass-effect-10000`,
`mass-effect-4500`, `mass-effect-1600` and `mass-effect-combat`, respectively.
They are from the same walkthrough family, not four independent games or new
captures. The [V69 fixture audit](../cu66-v69/fixture-audit.md) records provenance.

The command manifest and `system/cohort*/results.json` preserve every requested
history and failure. `analysis.json` derives validated latency, source cadence,
presentation latency, queue delay and occupancy from retained results. It does
not combine independent histories into a fictional continuous output rate.

All four complete histories pass: **457/457 sources**, each with an exact full
canonical image/tag and at least one complete correct native raster. The runs
check **381,694,375 native pixels**, including repeats and partial final rasters,
with zero black/mismatching lines, display errors, memory errors or underruns.
All queues drain and every raster obligation completes. The four-worker campaign
took about **33.1 minutes wall time**, separate from modeled FPGA time.

| Frozen history | Sources | Validated min–max | Median validated | Serial ACK budget passes | Finite display cadence |
|---|---:|---:|---:|---:|---:|
| mass-effect-10000 | 119 | 14.09–30.82 ms | 28.56 ms | 119/119 | 29.879 fps |
| mass-effect-4500 | 119 | 19.55–49.81 ms | 31.02 ms | 82/119 | 29.879 fps |
| mass-effect-1600 | 119 | 12.41–28.98 ms | 25.19 ms | 119/119 | 29.879 fps |
| mass-effect-combat | 100 | 21.63–78.72 ms | 57.43 ms | 1/100 | 29.826 fps |

The primary intervals retain queue time from the original immutable packet
release. The combat history's actual transaction service is **21.63–39.77 ms**;
its maximum release-to-admission delay is **45.39 ms**. The 4500 history has up
to **16.48 ms** of queue delay. None is relabeled a fresh start to improve the
latency result. Across the full histories, **321/457** serial ACK budgets pass,
**136/457 fail**, and **0/457** validated intervals meet strict under-10-ms.

Finite cadence uses N−1 intervals between first complete-raster starts, excluding
initial loading and final drain. Native refresh quantization and queued repeats
remain included. These are correctness and diagnostic results, not sustained
30-fps or a physical latency proof. The min/max covers the tested corpus, not
a formal worst-case bound.

## Packet queue and ESP32 boundary

`queue_budget.py` uses actual immutable fixture lengths and recorded release,
admission and ACK events. It retains both waiting packets and the active packet
through processor ACK. Equal-cycle releases precede admission and ACK for a
conservative peak. The script compares derived packet-count maxima with the
live observer and records byte peaks and illustrative reservation checks.
It also charges a fixed **48-KiB (49,152-byte) slot per owned packet** separately;
actual payload-byte peaks do not prove that a firmware pool of fixed slots fits.

| History | Peak owned packets, including active | Peak actual packet bytes | Fixed 48-KiB pool reservation |
|---|---:|---:|---:|
| mass-effect-10000 | 1 | 27,047 | 48 KiB |
| mass-effect-4500 | 2 | 76,740 | 96 KiB |
| mass-effect-1600 | 1 | 16,233 | 48 KiB |
| mass-effect-combat | 3 | 129,481 | 144 KiB |

The combat payload-only peak fits the illustrative 128-KiB number, but its
three fixed slots require **147,456 bytes**, so a 128-KiB fixed pool fails that
reservation check. Neither result includes the other firmware/transport
allocations below. No packet is dropped or timer restarted to fit a budget.

Those byte reservations exclude Wi-Fi/lwIP, DMA copies, QSPI descriptors,
application/GUI buffers, stack/heap, fragmentation and execution cost. They are
not measured free SRAM, allocated firmware pools or a validated ESP32 transport
model. An over-budget modeled history must be reported as a capacity concern;
it does not justify silently dropping sources or restarting latency timers.

## Python memory-study conclusion

The frozen V78 delta path transfers **1,102,464 non-display bytes per frame**:
canonical/HUD writes, stored references and HUD readback. Its ideal x16 bus
beat floor is 5.51232 ms at assumed 100 MHz. The frozen single-outstanding
controller's row-hit accept-to-next-accept state costs imply **9.63480 ms of
idealized non-display command service**, excluding display, refresh, row changes,
bridge gaps and codec work. This is conditional service analysis, not measured
validated latency or a target-clock proof.

The Python study exactly replays 17 retained measured strip-service schedules
and evaluates 33 **uncalibrated** bounded dependency scenarios. Numerical
counterfactual differences are not claimed speedups. Their sensitivity to
display phase and bridge gaps argues for measured small prototypes, rather
than assuming deeper queues will deliver 10 ms. See [memory-study.md](memory-study.md).

The separate [physical layout study](layout-study.md) evaluates six mappings and
96 synthetic service schedules. All mappings restore the same actual 518,400-byte
YUV fixture exactly, with injective addresses and checked padding/bank/HUD bounds.
Grouped layouts add 31,488–38,656 allocation bytes without changing logical wire
traffic. There is no universal service winner: 8×2 and 4×4 favor different declared
interleavings, while improving display-only row hits can worsen reference reads.
Do not change the default layout on that basis. The new plane offsets/spans also
require versioned adaptation of every physical-address producer and allowlist;
unused space before HUD is not permission to use the old guards unchanged.

## Separate reference-prefetch experiment

The standalone module and bench are specified in [prefetch.md](prefetch.md).
Two generation/bank/plane/tile-tagged 64-byte reference slots provide bounded
lookahead with one physical BL8 request outstanding. Full tiles become visible
only after all four eight-word fills. Slot retirement, held lookup responses,
unused hidden references and abort/drain preserve explicit ownership.

The all-tile walker avoids assuming future qmap decisions are available. It
reads 294 extra hidden tiles per delta: **18,816 bytes / 1,176 BL8 requests**.
The Python study reserves 320 logical bytes for two reference/candidate/metadata
slots, including candidate staging outside the standalone reference cache.
That is neither implemented BRAM utilization nor target fit.

The reference bank differs from the candidate-write bank. Future integration
must authenticate and translate retirement identity, retain immutable reference
leases, and adapt all write-completion consumers. The frozen receiver's write-
completion ready/valid behavior cannot be retrofitted by simply adding a
response FIFO or wiring a new backpressure signal. Keep that change isolated
and repeat the complete history/raster regression afterward.

The standalone test's synthetic memory is not the physical SDRAM controller,
and it is not an integrated decoder or a whole-system throughput experiment.
Its ownership/correctness results cannot be promoted to an under-10-ms gain.

## Reproduction and next milestone

Use the retained Python runners and exact command manifests. The system runner
builds once with `-j1`, hashes the binary and all input/source files, then permits
read-only `--skip-build` runs. Parallel jobs share that immutable executable;
they never run concurrent builds in its output directory. All model runtimes
have both simulated progress bounds and in-container/host wall-time limits.

```sh
python3 scripts/cu66-v79/verify_baseline.py
python3 scripts/cu66-v79/run_monitor.py
python3 scripts/cu66-v79/run_system.py --cohort 0 --frames 4 --mode fixed30 --tac 2
python3 scripts/cu66-v79/run_campaign.py --workers 4
python3 scripts/cu66-v79/compare_v78.py --new fpga/experiments/cu66-v79/system/cohort0-frames4-fixed30-tac2/results.json
python3 scripts/cu66-v79/analyze_system.py
python3 scripts/cu66-v79/queue_budget.py
python3 scripts/cu66-v79/memory_budget.py --check
python3 scripts/cu66-v79/run_prefetch.py
python3 scripts/cu66-v79/verify_evidence.py
python3 scripts/cu66-v79/bundle_manifest.py
```

Successful evidence is immutable: the runner requires archiving an existing
result/build identity before rebuilding or repeating into the same directory.
For a new reproduction, use a disposable workspace and move its retained V79
runtime-result directories and `system/build-tac2.json` to an archive outside
the active V79 tree before running the commands. Keep the published package
unchanged. A fresh checkout includes the retained results, so checking out alone
does not bypass the overwrite guards. The replay generates new evidence and
needs its own audit/manifest; CPU wall times and executable hashes may differ.

Next, capture per-tile request/response/ready timestamps and qualify the two-slot
prototype through the actual memory/controller and decoder interfaces under
matched arrivals and display phases. Measure command grouping/bridge overhead
as well as prefetch; 9.63-ms idealized non-display service leaves little room
for a strict 10-ms validated target on the current controller.

Fatal cache/scanout recovery, real HUD CPU cost, live ESP32 Wi-Fi/QSPI, exact-part
fit/route/CDC and physical testing remain open. The integrated campaign still
uses assumed clocks and zero simulated native CPU cost. Complete the 60-second
modeled sustained gate before the 600-second physical 30-fps goal, then retain
that throughput while requiring every validated interval to be strictly below
10 ms. No new bitstream or hardware performance is established by this package.

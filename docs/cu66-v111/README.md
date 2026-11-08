# V111: header timing preparation and executable harness baseline

Implementation branch: `study/gamebub-v111-harness-timing-20261108`.
Starting revision: `08e91145e0fc103c81d0b383338cfa70970ec399`.
This is the first execution step of the
[V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md).
**V111 is partial: the functional baselines passed, but timing remains open.**
All three planned native routes finished. The header cut regressed at both
measured clocks and is not selected as a standalone timing improvement. The
frozen V110 Count control remains the better 100-MHz diagnostic source; it
also fails timing. No source is promoted as 100/125-MHz qualified.

## Executed changes and evidence

The [header timing cut](header.md) prepares the four-length predicate in three
private stages during existing header fetches. It adds 169 reset-free payload
bits without adding a public cycle. CRC, basic-header, length-sum and raw-mode
failure priorities stay on their original edge. Malformed raw packets retain
their original partial metadata writes, including invalid-cycle public views.
An independent wide consuming assertion checks the prepared predicate.

Both focused seeds passed 76 complete packets, 36 cancellation/retry checks and
754,644 golden coefficients each. Added coverage includes 5,896 synthetic
header rows, 17 real received-header cases and read/header cancellation tests
per seed. Six original stale-response assertion rejections passed in total.
The first C++ fixture-formatting failure remains recorded. No DUT assertion or
expected value was weakened. The [independent focused audit](../../experiments/python-gamebub-v111/audit/header-focused.json)
binds the candidate, reversible source recipe and actual test artifacts.

Complete decoder qualification runs the unchanged frozen reference workloads:
two seeds, 44 case profiles and 42 directed checks in total, including exact
public events/cycles/counters and canonical pixels. Its terminal result is
recorded separately from focused PASS and native implementation.

The complete header composition now passed both seeds with exact old stdout,
events, cycles and canonical pixels. The
[canonical summary](../../experiments/python-gamebub-v111/canonical/combined/results.json)
has SHA `0fc4dacef1af96b1b339bf3927b2deeee94dd0f07e115675a625d604212ccb80`.
The [measured simulation-cost analysis](simulation-cost.md) records the actual
instrumented host runtime and conditional long-campaign projections.

The [executed harness baseline](harness.md) passed one actual emulated ESP32-S3
receiver → experimental QSPI/CDC/JPEG/memory/LCD frame. Fresh RTL and the
published corrected related C oracle were compiled; guest ELF/flash reuse is
explicit. The run accepted 26 datagrams carrying 26,159 JPEG bytes, checked 28
acknowledged events and compared all 345,600 RGB565 pixels exactly. Its legacy
43 compile warnings remain distinct from the strict custom-decoder flow.

Actual UDP trace capture and five negative controls also passed. The capture
contains 27,199 **application datagram bytes**: 26,159 compressed bytes plus
1,040 MSV1-header bytes. UDP/IP/link/RF overhead is excluded; the separate
728-byte IPv4/UDP estimate is explicitly assumption-based, not measured wire
traffic. See the [accounting receipt](../../experiments/python-gamebub-v111/harness/trace-accounting.json).

## Source and capability inventory

The [inventory](inventory.md) distinguishes implemented paths from proposals.
Sunshine's current custom Python sender is separate from the native server;
ordinary NVENC H.264/HEVC output is not a CS88 stream. No Sunshine server was
executed or interrupted by this baseline.

The emulated guest runs the receiver core, not the full production application.
Guest GP-SPI/DMA and common simulator time remain absent. The bridge freezes
FPGA time on socket waits. Embedded guest oracles and the reused Rust-1.93
binary cannot establish production SRAM use or a rebuild with today's
Rust-1.97 compiler. These are explicit gaps, not passed performance gates.

The current parent still uses JPEG and a shared 100-MHz decoder/memory domain.
It does not yet generate the proposed 125-MHz production decoder domain.
Code-derived panel timing is about 65.08 Hz rather than an assumed 60 Hz; that
nominal value is not a measured panel refresh result. Freeze the actual clocks,
scanout layout and time model before synchronized system-FPS qualification.

The [PCTL1 specification and whole-parent inventory](control-contract.md)
defines the next latency-changing ownership contract, separates operational
signals from diagnostic snapshots, and inventories the remaining actual
control/visibility paths. It is a source-pinned specification, not implemented
RTL or a new clock result. JPEG and custom OOC resource counts are non-additive.

## Bounded physical study

The new [policy](../../experiments/python-gamebub-v111/study-policy.json) allows:

| Trial | Source | Clock | Purpose |
| --- | --- | --- | --- |
| `count-125` | Frozen V110 Count closure | 8 ns / 125 MHz | Actual stricter-clock baseline, not extrapolated old slack |
| `header-100` | Qualified header composition | 10 ns / 100 MHz | Compare against the actual V110 Count −1.022-ns control |
| `header-125` | Same qualified header composition | 8 ns / 125 MHz | Measure the header cut at the roadmap target |

One positive result may receive one fresh-RTL repeat with identical sources,
clock, method and tool image. A negative result does not authorize a repeat or
silent strategy retry. Every initial source/clock/method run consumes a trial.
The first two prepared-only Count cards were superseded before dispatch while
strengthening repeat validation and retaining V110's legitimate host-network
license view; their drivers/cards are preserved as preparation history.

All actual trials read their exact XDC before synthesis and use Default
synthesis by omission, Default optimization/routing and ExtraNetDelay_high
placement. There is no retiming option, source checkpoint load, invented I/O
delay or timing exception. Native reports retain clock, setup/hold/pulse,
methodology/DRC/CDC, control-set/fanout and mapped-memory/DSP evidence. OOC
boundary I/O and full-parent timing remain separate requirements.

Root serializes dispatch decisions and owns global heavy-job grants, including
non-container emulator processes. The Docker active-name check is supplemental;
independent simultaneous native launchers are not supported. At most two heavy
jobs run, each with two CPUs and at most 8 GiB memory=swap, with available-RAM
and pressure gates and bounded watchdogs. No swap was added or cleared.

## Results and reproduction

| Source / role | Target | WNS ns | TNS ns | Setup-failing endpoints | Hold / pulse ns |
| --- | ---: | ---: | ---: | ---: | --- |
| Frozen V110 Count control, reused | 100 MHz | −1.022 | −1,125.069 | 4,620 | +0.085 / +3.750 |
| Fresh Count baseline | 125 MHz | −3.264 | −40,607.203 | 34,864 | +0.080 / +2.750 |
| Header candidate | 100 MHz | −1.526 | −3,066.815 | 8,110 | +0.101 / +3.750 |
| Header candidate | 125 MHz | −3.525 | −47,241.035 | 39,342 | +0.096 / +2.750 |

All three new measurements have zero routing errors, matching target clock
reports and no unconstrained internal endpoints. None passes setup; positive
hold/pulse does not compensate. At the same clock, the header source worsens
WNS by 0.504 ns at 100 MHz and 0.261 ns at 125 MHz. It also increases failing
endpoint counts by 3,490 and 4,478, respectively. The old 100-MHz result is
reused, not remeasured. No positive candidate exists for the one fresh-repeat
slot, so no repeat or extra strategy trial was launched.

The 100-MHz header route is limited by admission `tile[1]` → `group_visible[3]`
(15 logic levels, 11.474-ns data delay). The fresh 125-MHz Count route is limited
by scratch `read_segment[1]` → `busy_owned` (15 levels, 11.211 ns). The 125-MHz
header route ends at scratch `state[0]_rep` from the same `read_segment[1]`
(12 levels, 11.401 ns). Final native audits retain the full hierarchies and
raw reports. Correct arithmetic/local staging alone did not establish better
whole-component placement and timing.

The independent terminal audits are
[Count-125](count-125-audit.md), [Header-100](header-100-audit.md) and
[Header-125](header-125-audit.md). They compare target clocks separately and
retain the authoritative native summary precision.

The next measured targets are local admission/flush ownership and the fixed
geometry visibility computation in [PCTL1](control-contract.md), with an
explicit new event/latency contract. The conditional visibility ROM/pipeline
must prove its actual consuming domain before replacing generic behavior.
The [SRAM anchor capacity study](sram-anchor-study.md) also documents a future
data-reuse option: one 518,400-byte YUV420 reference fits nominal 512-KiB SRAM
with 5,888 bytes spare. Current SRAM integration, fitted-device I/O/access
timing, copy/drain/ACK behavior and performance remain open; it is not a new
RTL or 125-MHz claim.

[The receipt summary](../../experiments/python-gamebub-v111/results.json) and
[native comparison](../../experiments/python-gamebub-v111/native-comparison.csv)
separate running jobs, completed measurements and repeated qualified clocks.
The comparison profile stays 720×480 CS88 q16/all-BR88 with a 49,152-byte cap.
See [reproduce.md](reproduce.md) for exact commands and scope.

[Source-only replay exports](exports.md) preserve each actual source/clock
selection and passed plain-Tcl real/relocated path checks. They do not run
Vivado again or require the original checkpoint/build directory.

The current V111 work does not establish a shared-time Sunshine system,
full-parent timing, a board bitstream, sustained hardware 30 fps, or complete
validated decoding under 10 ms. A requested clock is not an achieved clock;
the target-specific final routed receipts and fresh repeat decide qualification.

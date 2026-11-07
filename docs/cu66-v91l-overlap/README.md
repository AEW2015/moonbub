# V91l native decode/display overlap

This experiment overlaps the accepted key frame's actual RGB reader with the
next native delta decode. Candidate writes, accepted-reference reads, scratch
and display still use one unchanged SDRAM controller and timed pin model.
The [scratch-inclusive serial control](../cu66-v91l-scratch-service/README.md)
is retained unchanged. Coding syntax, source resolution (720×480), quality and
HEVC/AV1 rate/quality comparisons are unchanged.

The four natural runs reduce the measured two-source interval from
121.852–121.867 ms to 98.832–98.837 ms (18.89%). Contended delta decoding
increases to 40.118–40.127 ms. In the matched seed 912901/tAC 2 trace,
ACTIVATE commands rise 66.11% while READ/WRITE counts remain identical.
This supports a bounded row-locality scheduling experiment; it does not
attribute all latency to row changes or establish 30-fps cadence.

A display lease snapshots bank, source fid, epoch and full generation at a
qualified RGB start. The existing converter's 32-bit generation limit is
checked explicitly; unsupported high generations are rejected, rather than
silently truncated. Fid zero is legal. Changing the accepted-reference pointer
while decoding the delta cannot redirect the old key's RGB reads.

Candidate valid and ready are both gated against the active display bank.
The guard blocks new handshakes; it does not evict an already accepted writer
or provide autonomous fault recovery. RGB starts in this native campaign only
after its source's candidate writes and validation have drained. The key must
already be the front frame, with its pending slot empty, before starting key
RGB and the delta. The existing allocator then protects reference/front/pending
banks normally.

The core's presentation-drain input is computed from the external downstream
hint **and** the actual display lease, RGB engine, canonical reader and
physical reader/mux state. Reset/cancel/error marks a terminal consumer but
preserves its bank until two consecutive physical-drain observations. A cold
reset that discards an active lease is an invalid integration action.
The new guard adds metadata/control, not a frame buffer.

Four natural runs use two seeds and tAC 2/7 ns, retaining the control's seeded
80% RGB output readiness. A fifth, separately labeled guard run holds the
key's final RGB pixel until delta commit plus 17 clocks, with external vblank
and drain hints asserted. It checks that actual consumer ownership blocks
publication after the accepted-reference bank advances. That directed hold
is excluded from performance comparisons. The hold tests a live pixel/consumer
lease; it does not imply a pending SDRAM burst exists at that exact moment.
Pending-read cancellation/drain is covered separately by the directed tests
and retained physical-memory controls.

## Evidence

The standalone guard tests have 147 check entries, including seven invalid
starts, six complete leases and 17 observed candidate alias blocks. Independent
replay checks descriptor capture, terminal/error history and two-sample drain;
14 deliberate receipt corruptions must be rejected causally. Unit pending
signals are abstract stimuli. Native runs connect the actual consumer and
physical controller, checking all memory traffic, source-backed pixels,
canonical/reference history, SHA/C2/HUD/seal validation and publication.

The [measured results](results.md),
[independent audit](../../experiments/python-gamebub-v91l-overlap/audit.json)
and [summary](../../experiments/python-gamebub-v91l-overlap/summary.json)
identify the selected snapshot and distinguish natural and directed workloads.
The [Python contract model](../../experiments/python-gamebub-v91l-overlap/model-contract.md)
provides bank-ownership checks and a zero-contention lower bound; that bound
is not an RTL timing prediction. Actual contention and completion times are
measured in the native campaign. Captured output counters retain immutable
source identity while decoder context advances to the next frame.

```sh
python3 scripts/cu66-v91l-overlap-lease/run.py
python3 fpga/experiments/cu66-v91l-overlap-live/make_wrapper.py
python3 fpga/experiments/cu66-v91l-overlap-live/make_bench.py
python3 scripts/cu66-v91l-overlap-live/run_test.py
python3 experiments/python-gamebub-v91l-overlap/overlap_model.py --check
python3 experiments/python-gamebub-v91l-overlap/verify_generation.py
python3 experiments/python-gamebub-v91l-overlap/verify_results.py
python3 experiments/python-gamebub-v91l-overlap/verify_streams.py
python3 experiments/python-gamebub-v91l-overlap/pin_traffic.py
python3 scripts/cu66-v91l-overlap-summary/summarize.py
```

Use Verilator 5.020/GCC 13.3.0 in `gamebub-cu66-v69-build`. Tests retain strict
warnings, assertions, finite watchdogs, exact source/input snapshots and failed
attempts. Pin logs are losslessly compressed in newline-aligned chunks with
per-chunk and complete raw hashes. Clock phases and functional memory delays
are inherited; no SDF/PVT, routing, CDC, hardware clock or board validation is
claimed. The timed simulation wrapper includes a pin model and delayed clock;
it is not a board-ready top. Integrating the guard/arbiters into the real top
requires device memory/I/O/clock constraints and physical qualification.

## Next work

Use the measured contention to select a bounded arbitration, reference reuse
or prefetch change, one at a time. Preserve exact pixels, source leases and
publication fences, with these natural overlap and serial controls retained.
A lower pair completion time does not establish fixed-source 30 fps; competing
RGB reads can increase delta decode latency. Complete all-RTL HUD interpretation
and composition, mixed entropy or tested fallback, real ESP32/transport costs
and V91m's distinct-source fixed-cadence workload before product promotion.
V100–V110 retain the planned 7-series mapping, placement/routing and hardware
gates. V91l remains partial. Sustained hardware 30 fps and complete validated
decoding strictly below 10 ms remain open.

# V91l bounded reference-tile grants

This tests one scheduling change against the
[frozen native-overlap control](../cu66-v91l-overlap/README.md): retain the
reference reader's turn for up to four contiguous 16-byte chunks of one
64-byte tile. Candidate writes, reference assembly, scratch, the physical
controller, RGB converter and display leases remain unchanged. The native C++
workload is byte-identical after replacing only its generated Verilator top
typename. Codec bytes, 720×480 resolution and quality are unchanged.

The [measured results](results.md),
[independent audit](../../experiments/python-gamebub-v91l-tile-grant/audit.json)
and [summary](../../experiments/python-gamebub-v91l-tile-grant/summary.json)
separate four natural seed/tAC comparisons from the existing directed native
publication guard. This is an experimental scheduling option, not a hardware
release or a completed 30-fps decoder.

## Policy and ownership

`REF_LINES=1` preserves the original per-line round-robin behavior; every
ordinary output is compared cycle by cycle with the frozen mux in its directed
control. `REF_LINES=4` permits a group only for a valid nonzero epoch/ticket,
video bank 0–2, a 64-byte-aligned address and a complete tile within the
canonical aperture. The last legal tile starts at 518336; its final 16-byte
line starts at 518384 and the exclusive tile end is 518400.

A continuation requires the same epoch/bank, address exactly +16 inside the
same tile, and the next 32-bit physical ticket, skipping zero on rollover.
Full 64-bit frame/reference identity remains checked by the unchanged outer
tile reader. A legal 16-byte line that does not start a tile is standalone.
Invalid first requests retain the lower bridge's error contract and never
create a reservation. The mux adds no payload storage.

An accepted line owns its response until matching ACK and bridge drain.
Four successful chunks exhaust the grant; a waiting display gets the next
round-robin opportunity. Reset/cancel, error, a changed continuation descriptor
or a missing next offer yields early. Missing offers may reserve at most eight
idle clocks; a matching offer stalled at the lower port and held responses
are governed by their existing handshake/drain contracts. Fairness is bounded
by reference credits under eventual progress, not an unconditional wall-clock
latency guarantee.

The policy changes both row locality and read-credit weighting: continuous
contention may serve four reference lines per display line. Decode gains
must therefore be assessed alongside key RGB latency and display service.
Measured ACT/PRE changes alone do not attribute elapsed time to locality.
No equivalent eligible-offer maximum was logged in the frozen control, so
new request-wait maxima are reported without inventing a baseline comparison.

## Qualification

The directed tests pass **2,056 check entries** across REF_LINES 1/4,
including all four credits, display opportunity, ticket rollover, short and
expired gaps, descriptor changes, held/epoch-wrong responses, cancellation,
reset, errors, standalone reads and aperture boundaries. Unit memory is an
explicit behavioral responder; actual timed SDRAM is checked in the native
campaign. REF_LINES 1 logs both identical legacy/candidate instances: the
checker requires exact pairs before normalizing them. Source-reviewed cold
reset boundaries split the twenty scenarios per parameter.

Independent replay adds credit, contiguous-scope, gap and wait-time checks to
the complete frozen native/pin/scratch/validation/display-lease oracles. It
rejects 18 deliberately corrupted policy receipts for their causal reasons.
Cancel and immediate-mismatch stimulus also relies on source-reviewed directed
bench assertions: a yield record alone does not capture every unaccepted
input. This is directed simulation, not exhaustive formal proof.

The four natural runs use seeds 912901/912902 and memory tAC 2/7 ns. The fifth
run retains the separate final-pixel hold across delta commit; it is excluded
from performance comparisons. All ten full RGB outputs, 10,250 RTL SHA jobs,
canonical/HUD commitments, accepted quantizer history and source-bank contents
must remain exact. Each native delta still uses 7,806 reference tiles and
31,224 physical BL8 reads. No pixel/canonical memory preload is introduced.
The earlier exploratory attempt is retained with its source-freshness failure;
only the selected fresh report qualifies.

```sh
python3 fpga/experiments/cu66-v91l-tile-grant/generate_wrappers.py
python3 scripts/cu66-v91l-tile-grant/run.py
python3 fpga/experiments/cu66-v91l-tile-grant-live/make_wrapper.py
python3 fpga/experiments/cu66-v91l-tile-grant-live/make_bench.py
python3 scripts/cu66-v91l-tile-grant-live/run_test.py
python3 experiments/python-gamebub-v91l-tile-grant/grant_model.py --check
python3 experiments/python-gamebub-v91l-tile-grant/verify_generation.py
python3 experiments/python-gamebub-v91l-tile-grant/verify_results.py
python3 experiments/python-gamebub-v91l-tile-grant/verify_streams.py
python3 scripts/cu66-v91l-tile-grant-summary/summarize.py
```

Use the existing `gamebub-cu66-v69-build` container, Verilator 5.020 and GCC
13.3.0. Strict warnings/assertions, two compile jobs, finite watchdogs, exact
source/input snapshots, compressed raw receipts and failed attempts are
retained. The [packaging check](../../experiments/python-gamebub-v91l-tile-grant/packaging-check.json)
records exact whitespace exceptions for raw compiler-version output and
byte-identical frozen source snapshots; other staged files pass Git checks.
No compiler warning or assertion is waived.
The independent [Python contract model](../../experiments/python-gamebub-v91l-tile-grant/model-contract.md)
checks all 8,100 tile geometries and the policy contract; it makes no timing
prediction. All times assume a 100-MHz source clock. Timed wrappers contain
simulation memory/delayed-clock models; they are not board-ready tops.
No mapping, placement/routing, CDC, SDF/PVT or achieved-clock claim follows.

## Next work

Separate scheduling weight from locality before choosing a product policy.
A bounded equal-byte/quantum comparison, or a deadline-aware choice that caps
reference priority, should retain these exact source bytes, leases and
publication fences. Compare complete intervals, decoder latency, RGB latency
and worst observed service together; keep both per-line and tile-grant
controls. Do not trade unbounded display delay for a decode-only win.

Full RTL HUD interpretation/composition, mixed entropy or tested fallback,
actual ESP32/transport costs, V91m's fixed distinct-source cadence and
V100–V110 7-series mapping/physical/hardware gates remain open. V91l is still
partial. Sustained hardware 30 fps and complete validated decoding strictly
below 10 ms are not proven.

# V80 integrated-prefetch handoff

## What is implemented

The hardware candidate adds `cu80_reference_path`, which holds and authenticates
candidate write completions before retiring a reference-cache slot. It captures
generation, immutable reference bank/ID and candidate bank, and uses the frozen
V79 two-slot reference walker. Keyframes bypass reference prefetch.

`cu80_memory_system` connects the walker to the actual frozen V74 word bridge
and V72 SDRAM controller. It arbitrates candidate writes and prefetch reads at
P0 while retaining existing HUD and dedicated-display service. A 16-byte snapshot
buffer turns the bridge's 128-bit read result into eight owned x16 transfers.

The separate `cu80_overlap_memory_system` exposes a controlled choice: release
the P0 command owner once that snapshot is captured, retain the saved data and
reference lease independently, and permit candidate writes during the stream.
Its final stream beat never releases a newer write owner. A second prefetch
snapshot cannot overwrite an undrained buffer. Both conservative and overlapping
modes pass actual-controller tests at tAC 2 ns and 7 ns with identical traffic/data,
including concurrent final-beat/new-write and final-beat/write-response cases.

The encoded packet format, host encoder fixtures and ESP32 wire protocol are
unchanged by this iteration. The new files are decoder/memory integration and
verification work; no Sunshine or ESP32 firmware build is required merely to
reproduce these simulations. A target implementation still needs its own
integration, resource/timing checks and transport tests.

## Explicit configurations

Set `PREFETCH_ENABLE` on `cu80_system`/`cu80_system_sim`, or select the runner's
matching option. Always select it explicitly; the experimental top/runner
default 1 retains the diagnostic conservative configuration, not a deployment
recommendation.

| Mode | Runner option | Memory path |
|---|---|---|
| 0 | `--variant baseline` | Exact legacy V78/V79 decoder/memory/display path |
| 1 | `--variant prefetch` | Integrated two-slot prefetch, P0 owner held through the snapshot stream |
| 2 | `--variant overlap` | Same prefetch with P0 owner released at snapshot capture |

The mode 0 four-source control matches all original V79 frame/timing/summary
fields, excluding CPU wall time. The default-off overlap module also reproduces
the original conservative mode 1's simulation timing. Its combat command/tile
trace is byte-identical to that original control. Thus mode 1 versus 2 is a
controlled P0-owner change, not a new clock or easier input stream.

## Validity and ownership boundaries

Every frame still uses actual compressed packet parsing, inverse/reconstruction,
hash validation and canonical stores. Reference samples come from prior
RTL-produced SDRAM. Native CPU HUD semantics use actual guarded writes/readback
before their fence. The expected planes and pixels remain an independent oracle;
they never seed canonical memory or supply decoder reference data.

Each delta prefetches all 8,100 tiles, including 294 hidden tiles, in plane/tile
order. It performs 32,400 logical BL8 reads and 259,200 x16 transfers; the tested
positive paths have no P0 read-cache hits. Compared with legacy 31,224 reference
BL8 reads, this is 1,176 additional blocks / 18,816 bytes per delta. No read
elimination or new qmap lookahead is claimed.

The write-completion shim authenticates generation, candidate bank, plane and
tile against the accepted request before translating to the captured reference
bank. Hidden retirement uses the fixed profile shared with `cu66_expand_tiles`.
The two-entry served ledger supports the decoder looking ahead before a prior
write retires. Invalid candidate metadata is rejected before physical forwarding;
invalid terminal completion metadata produces an accepted-identity error and
cannot retire a successful reference slot.

Abort/fault stops new prefetch work but drains accepted physical reads. A held
lookup canceled by the frozen core receives one exact-identity error completion
so both receiver layers can release their pending token. Actual write completion,
held retirement tokens, stream ownership and prefetch leases participate in the
global drain condition. Error cancellation is not a fabricated successful read
or write. Clearing a drained core fault permits key bypass and a fresh delta
epoch; it does not retroactively validate failed data.

The epoch completion signals are one-clock events. The bench records them once
per memory edge, with generation and timestamp. The evidence auditor requires
successful delta completion before validated-ready; the bench also checks it
before the later ACK. They are not expected to remain asserted
through the later processor ACK. The first integrated attempt's incorrect
pulse-level assertion and its exact source/trace are retained.

## Bounded measured comparison

All validated times here are packet-complete to validated-ready, including any
admission queue. They are distinct from post-admission decoder execution and
from the separate packet-complete to CPU-ACK 33.333-ms gate.

The first conservative predicted source takes 31.18542 ms to validate, compared
with legacy 28.76078 ms. Integration correctness alone is not a speedup. The
controlled overlap then validates that same source in 28.64745 ms. Three regular
and three combat predicted sources compare as follows; original immutable
release times, clocks, reset schedule and encoded packets are retained.

| History/source | Legacy validated | Conservative prefetch | Snapshot overlap |
|---|---:|---:|---:|
| regular 1 | 28.76078 ms | 31.18542 ms | 28.64745 ms |
| regular 2 | 26.41404 ms | 29.74557 ms | 26.41133 ms |
| regular 3 | 25.87469 ms | 29.83092 ms | 25.71498 ms |
| combat 1 | 35.63473 ms | 37.66016 ms | 35.47300 ms |
| combat 2 | 38.02204 ms | 40.56410 ms | 37.71609 ms |
| combat 3 | 39.03891 ms | 44.03127 ms | 38.82782 ms |

The overlap recovers conservative integration's penalty, but these gains over
legacy are small. It does not establish a strict 10 ms or sustained 30-fps result.
Keyframes have a small completion-shim overhead; include their regressions in
whole-history measurements rather than reporting only improved delta samples.

Three per-frame counters report snapshot-stream candidate-valid cycles,
candidate-valid cycles with the modeled bridge/controller idle, and candidate
write accepts while the stream is held. The predicates include an accept cycle
and do not establish that a request was unserved. These are overlapping activity
observations, not a critical-path decomposition.
Differences in them must not be subtracted from latency as predicted savings.
The actual native pipeline and memory arbitration can change phases and traffic
windows when service changes; those effects remain in the measured result.

## Complete-history results

The selected snapshot-overlap configuration completed all **457 sources** in
four separate continuous histories (119/119/119/100), with one reset per history
and no reset per source. The model uses 100 MHz and `tAC=2 ns`. All canonical
planes, semantic HUD transfers/readbacks and full native raster obligations
passed, with zero detected memory/display errors, underruns or black lines.
A separate two-source combat run passed at `tAC=7 ns`; the complete corpus was
not run at both corners.

| History | Sources | Validated min / median / max (ms) | ACK within 33.333 ms | Under 10 ms | Faster / slower than V79 |
|---|---:|---:|---:|---:|---:|
| mass-effect-10000 | 119 | 14.13410 / 28.50846 / 30.71957 | 119 | 0 | 76 / 43 |
| mass-effect-4500 | 119 | 19.57636 / 30.44997 / 49.56608 | 82 | 0 | 89 / 30 |
| mass-effect-1600 | 119 | 12.45290 / 25.24239 / 29.15479 | 119 | 0 | 9 / 110 |
| mass-effect-combat | 100 | 21.65702 / 49.32132 / 71.49397 | 6 | 0 | 99 / 1 |

Across these reset-separated samples, validated min/median/max is
**12.45290 / 28.52827 / 71.49397 ms**, compared with V79's
12.41175 / 28.70237 / 78.72296 ms. There are **273 improvements and 184
regressions**, with no equal cases. The worst observed regression is 0.37339 ms;
the largest improvement is 16.45171 ms, including changes in queueing.
The lower-work cohort mostly regresses, so mode 2 is an experimental candidate
rather than a universal replacement recommendation.

The serial ACK budget passes **326/457** sources, compared with V79's 321/457;
131 still miss it and **0/457** meet the strict validated-under-10-ms threshold.
Combat's median per-source improvement is 5.672875 ms, but its admission queue
still reaches 38.16069 ms. This is not a pure decoder execution measurement.

The finite first-to-last full-raster-start cadence is 29.87903 fps for each
119-source history and 29.82627 fps for combat. It excludes startup and tail,
allows queueing, and covers only approximately four seconds per history. It
neither proves sustained 30 fps nor meets the 60/600-second acceptance gates.
These four histories are variations of one walkthrough family, not four games.

The full campaign checks **381,599,180 physical LCD pixels** including borders,
repeated rasters, partial rasters and tail. This is distinct from the 457 required
source presentations: one 480×800 raster each would be 175,488,000 pixels.
Bounded replay pixels are not added to the full-campaign total.

Machine-readable comparisons and exact selected attempt paths are in
[`comparison.json`](../../fpga/experiments/cu66-v80/comparison.json); the campaign
terminal record is
[`campaign results`](../../fpga/experiments/cu66-v80/campaigns/prefetch2-562386e779a7/results.json).
The initial main-system pulse-check failure and three fault-bench failures are
retained with their exact snapshots, alongside the later corrected PASS results.

## Fault and trace evidence

See [faults.md](faults.md) for actual-controller CRC rejection, partial canonical
write abort coincident with a client 3 read acceptance, old reference/HUD/raster
retention and same-delta retry with lost COMMIT ACK. A pending-lookup coincidence
was not observed in that bounded system test and is not claimed; the component
tests separately exercise lookup cancellation. No per-source reset, DUT force,
golden-reference injection or fake successful completion is used.

Traces record actual controller accepts by client and physical address, receiver
tile request/response/write handshakes and postedge cache-fill events. Raw command
owner generation is deliberately unknown 0; trace-window context is not asserted
to be the owning source. A reference-request handshake is not the first cycle
of offered valid, so fill-to-lookup intervals alone do not prove hidden latency.
Deterministic compressed traces retain raw and compressed hashes and event counts.

## Reproduction and next gates

Use the recorded `gamebub-cu66-v69-build` container and mounted repository path.
Each build uses one compiler job. Each variant/TAC has a separately hashed
immutable binary. Each attempt retains exact mutable V80 source bytes plus hashes
of the frozen input/source pool, commands, log digests and explicit status.
Historical failed attempts remain preserved and classified. Running checkpoints
fail closed until terminal verification; they are not qualified result records.

```sh
python3 scripts/cu66-v80/verify_baseline.py
python3 scripts/cu66-v80/run_system.py --variant baseline --cohort 0 --frames 4 --mode fixed30 --skip-build
python3 scripts/cu66-v80/run_system.py --variant prefetch --cohort 0 --frames 4 --mode fixed30 --trace --skip-build
python3 scripts/cu66-v80/run_system.py --variant overlap --cohort 0 --frames 4 --mode fixed30 --trace --skip-build
python3 scripts/cu66-v80/run_history_campaign.py --prefetch 2 --workers 4
python3 scripts/cu66-v80/analyze_results.py
python3 scripts/cu66-v80/verify_evidence.py
python3 scripts/cu66-v80/bundle_manifest.py --write
python3 scripts/cu66-v80/bundle_manifest.py
```

These commands replay the matching binaries on this build host. On a fresh
machine, use a separate checkout and preserve the published package. Before
building each variant/TAC, move its inherited `system/build-prefetchN-tacT.json`
record and any existing `/build/v80-system-prefetchN-tacT` object directory
into uniquely named local archives (or use an empty `/build`), then omit
`--skip-build` for that variant's first run. This records the new compiler/binary identity rather than
pretending the original executable exists locally. Do not archive or rebuild a
variant while another process is using it. Later replay and the four-history
campaign require `--skip-build` and matching source/binary hashes.

Results always go to a new immutable attempt directory. Audit new attempt
identities separately; adding local results changes the published bundle manifest.

The integrated replay still assumes 100 MHz, instantaneous native CPU HUD/control
and complete immutable fixture packets. It is not live ESP32 Wi-Fi/QSPI, target
CPU cost, actual board timing, fit/route/CDC or physical display qualification.
The goal remains 1,800 distinct sources/60 modeled seconds, then 18,000/600 physical
seconds, retaining all failures and original ingress timestamps. Fatal display
recovery remains a separate open gate. No new bitstream or hardware 30-fps claim
is established by this simulator package.

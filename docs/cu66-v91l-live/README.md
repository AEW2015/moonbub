# V91l live canonical and candidate-write integration

This follow-up connects the frozen BR88 admission, entropy, inverse-transform
and reconstruction RTL to the frozen C2/HUD/seal validator and bank-publication
gate. The bounded connection must retain each accepted candidate-memory write
until its matching acknowledgment, including cancellation and warm reset.

The qualification target is the causal c0/f0 key → c0/f1 delta chain under
FAST and SLOW finite service. Delta prediction must read the actual prior
accepted candidate bank. Original packet commitments and independent canonical
pixel goldens provide the oracle. No frame-sized canonical replay input is
permitted to stand in for the live reconstruction producer in this path.

HUD semantic decoding remains the unchanged native C++ implementation before
RTL start. Its actual output is transferred, written and hashed by RTL; CPU
execution time and target memory use remain outside the measured RTL fence.
The current all-BR88 profile is a supported subset; mixed AB38 entropy,
RTL HUD decode/overlay, shared physical memory, ESP32 transport and display
scanout remain separate integration gates.

See the [ownership and ordering contract](write-contract.md),
[independent integration audit](../../experiments/python-gamebub-v91l-live/audit.json),
[standalone adapter audit](../../experiments/python-gamebub-v91l-live/write-join-audit.json)
and [machine-readable summary](../../experiments/python-gamebub-v91l-live/summary.json).

## Qualified simulation results

Two current-source seeds each run the actual two-frame key/delta chain under
FAST and SLOW service: **eight validated commits in total**, representing two
source frames, not eight distinct captures. All **8,200 actual RTL SHA jobs**
are independently recomputed. Every accepted bank contains exactly 518,400
canonical bytes plus 42,240 semantic HUD bytes. Across the nominal campaign,
4,485,120 write requests, matching ACKs and hash deliveries reconcile.

| Timed RTL start → validated commit | FAST cycles | SLOW cycles across both seeds |
|---|---:|---:|
| c0/f0 key | 3,101,135 | 5,781,609–5,783,385 |
| c0/f1 delta | 2,795,859 | 5,528,889–5,528,916 |

The delta also pays a separately reported **1,350-cycle quantizer-cache preload**.
Its 7,806 reference requests fetch actual accepted key-bank pixels. All 1,350
quantizer-cache cells are captured from actual registered RTL lookups, compared
with independent goldens, promoted after validated commit and used as the next
delta's actual preload source. Accepted bank bytes and cache exports are
independently compared, not synthesized from oracle values.

Each integration seed completes **37 directed entries** (some repeated across
profiles); each standalone adapter seed completes 16 entries and 2,000 generated
actual output-byte comparisons. These are bounded simulation suites, not a
continuous source-cadence workload or formal proof. The standalone byte suite
and native full-frame suite are distinct evidence.

At the measured cycle counts, the timed start fence alone would require more
than 310.1135 MHz for the FAST key to be strictly below 10 ms; the slower-service
key would require more than 578.3385 MHz. These are necessary clock calculations,
not achieved clocks, targets promised feasible on 7-series, or complete latency
measurements. The summary also records serial-service 30-Hz clock arithmetic,
with preload charged separately. Software HUD/header work, RGB conversion,
overlay, shared memory arbitration, ESP32 transport and display service are
excluded, so **hardware 30 fps and complete validated decoding below 10 ms remain
open**. Per-byte request/ACK overhead is a reason to compare bounded coalescing,
not evidence that its proposed speedup has already been achieved.

Last-write ACK drain is asserted and counted in the commit fence; its separate
timestamp is not exported in this checkpoint.

## Reproduce

Use the existing `gamebub-cu66-v69-build` container, Verilator 5.020 and GCC
13.3.0. The runners retain strict source/input snapshots, commands, logs,
compressed actual bank/cache exports and complete nominal digest traces.

```sh
python3 experiments/python-gamebub-v91l-live/model.py
python3 scripts/cu66-v91l-live/run_write_join.py --seed 912001
python3 scripts/cu66-v91l-live/run_write_join.py --seed 912002
python3 experiments/python-gamebub-v91l-live/verify_write_join.py
python3 scripts/cu66-v91l-live/run_integration.py --seed 911901
python3 scripts/cu66-v91l-live/run_integration.py --seed 911902
python3 experiments/python-gamebub-v91l-live/verify_results.py
python3 scripts/cu66-v91l-live/summarize.py
```

Compile flags retain `--assert -Wall`, C++ `-Wall -Wextra -Werror`, and two
compiler jobs. The auditor reproduces both generators in an isolated dependency
tree and checks their emitted RTL/bench bytes. Frozen prior RTL, native HUD code
and corpus inputs remain unchanged.

## Test boundaries

The write adapter has one owned byte, one accepted memory request and one held
hash delivery. A wrong epoch/token/bank/address acknowledgment poisons the
candidate while retaining the true lease. Only its matching response can drain
that lease. A matching error response retires the memory operation and drops
the hash byte. Internal adapter `start` is legal only while idle; the wrapper
must qualify external starts and block replacement while any owner remains.
Cold power reset requires quiescent external service. Warm reset and abort
preserve accepted metadata and drain pending writes.

The standalone generated-byte campaign is separate from native gameplay frame
coverage. It tests request/input equality and actual output equality, request
and output backpressure, pending input blocking, cancellation/reset of offers,
accepted requests and held deliveries, same-edge matching response/cancel,
four independent wrong acknowledgment fields, matching bus errors and retry.
It does not test token wraparound or a physical memory controller.

The initial integration uses a processor-provided start/header contract for
expected root, seal and frame identity. The frozen RTL parser checks the actual
supported packet and its envelope/inner streams; the wrapper must bind admitted
frame identity to the transaction before publication. This does not add an RTL
parser for the native HUD encoding. Quantizer-cache preload and all software
HUD/header preparation need separate accounting if outside the timed fence.

## Next optimization gates

After the live path qualifies, measure which service dominates before widening
anything. A bounded coalesced-write experiment should retain the byte control,
price each physical x16 payload transfer and command/response cost, preserve
canonical tile order at hashing, and retain every accepted burst lease until
its matching response. This is an experiment to compare, not a promised speedup.
A useful first candidate is **eight-byte tile-row writes**, rather than assuming
16 adjacent tile-order bytes are contiguous in raster memory. Each canonical
8x8 tile has eight contiguous eight-byte rows separated by the plane stride.
That changes 518,400 canonical byte requests into a calculated 64,800 row
requests; the 42,240 HUD bytes add 5,280 eight-byte requests if fully aligned.
Each row still costs four x16 payload transfers, plus controller service. These
are structural request counts, not measured speedups or a physical burst-mode
implementation. Retain bounded row payloads until the burst ACK and then deliver
their bytes to hashing in the original order; abort must drain an accepted burst
without exposing partial hash publication. A real controller must define byte
masks, alignment, transfer count, errors and refresh/scanout arbitration.

Shared reference, candidate, conversion and scanout traffic must ultimately
compete on one finite memory-service model. Neither independent component
fences nor the new adapter tests establish sustained 30-Hz operation.

## Retained debugging evidence

Early attempts retain strict compile failures for an undriven diagnostic alias
and C++ indentation, followed by a real next-frame failure caused by sticky
producer `done` admitting HUD bytes before the next transaction. An explicit
transaction-active gate fixes that behavior. The transaction-start priority also
allows a legal new start during the previous completion pulse. HUD addresses
now come from an internal bounded counter; wrong indices, last markers and
extra bytes reject before an out-of-range candidate request.

The expanded HUD tests initially sampled a combinational mismatch immediately
after a clock edge, before the C++ upstream actor updated its held index. That
transient was not a latched hardware failure. The negative test now waits for
latched transaction failure or validator error before testing drain. Failed and
superseded attempts remain retained, with their original status and source
hashes. Only reports matching the final live source qualify the summary.

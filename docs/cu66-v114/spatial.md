# V114 reserved-control canonical and transport qualification

Status: **PASS_V114_SPATIAL_CANONICAL**, actual fresh Verilator qualification.
The selected [summary](../../experiments/python-gamebub-v114/spatial/results.json)
is the [raw receipt](../../experiments/python-gamebub-v114/spatial/attempts/20261108T225107629909Z/receipt.json)
plus its selected-receipt pointer. Raw receipt SHA-256:
`681c9ea72bb94bb8cb74a033e75896ce55a6138ac639b47777642b12c0aa54ef`;
summary SHA-256:
`8b4c9e881bb093fa2f9374ce79d807ed6596bc87778e3de4e5d020f4b4919a27`.
The controller, harness and runner are frozen after PASS. Controller SHA-256:
`9e6d2b88ad0f06ca0df5a5218be0d78a9fa9d9e8151d3b0b43aebaafc3ba76bd`.
No existing source or proof is rewritten by this harness.

The source parent is the actual V113 native 18-origin composition. Only
`cs88_pipeline_v91k.sv` is replaced by
`fpga/experiments/cu66-v114-control/cs88_pipeline_v91k.sv`; V113 geometry,
scratch and IV113.1 inverse remain frozen. The helper-packaging split of the
unchanged admission source must still reassemble byte-for-byte. This is an
18-body source set, not a replicated decoder or a new arithmetic lane.

The candidate component model is compiled fresh from the new sources. There is
no old-model reuse switch. The frozen V113 canonical pixel artifacts are content
references, not a substitute for running the changed candidate. Both original
seeds must newly execute 22 case/profile rows and 21 directed checks each:
44 and 42 total. Both actual V97-to-CS88 transport seeds must newly execute
12 successful case/profile rows and two abort/reset canonical retries each:
24 and four total. Every accepted canonical pixel byte must match the retained
V113/V112 raw canonical stream.

The first attempt freshly compiled the original independent 496-line bench
byte-for-byte. Its first canonical frame passed; the next command exposed the
old bench's assumption that child diagnostics reset at public admission. Its
`child start conservation` failure is retained in attempt
`20261108T224508191284Z`; it is not relabeled as a PASS.

The passing retry compiled a **new API-adapted bench**, with two mechanical edits
recorded in the reversible [API derivation](../../fpga/experiments/cu66-v114-harness/bench-api-derivation.json).
The original immediate cache-consumption assertion and reference/Qcache/FID/
generation poisoning still occur immediately after public acceptance E. A new
independent assertion requires no new command, cache, input, coefficient,
residual, pixel, memory-request or reference-request eligibility while pending.
One actual E+1 child-delivery tick then precedes new-frame diagnostic monitoring.
All physical reply/drain checks are unchanged; no eligible output is skipped.
Every original `need` and functional oracle statement remains byte-exact, and
reverse application reconstructs the untouched 496-line original. The compiled
bench is explicitly not claimed to be byte-exact original.

The transport executable has a **separate second-stage** reversible five-edit
clock-hook derivation from that API-adapted base, recorded in
[derivation.json](../../fpga/experiments/cu66-v114-harness/derivation.json).
Its full original coefficient, metadata/order, held-offer, DQ, residual, pixel,
error, counter and real memory/reference ledger/drain oracles remain active. The transport source is the actual V97 RTL with finite 2,048-byte
FIFO and two descriptors plus an explicit synchronous parallel DMA adapter.
This supplies no QSPI serialization, ESP32 firmware, Sunshine or board-clock
performance claim.

The original bench pulses public start for one edge, immediately changes the
reference/cache command pins, requires cache eligibility to be consumed, and
may inspect done/error before offering bytes. A registered command must snapshot
all those operands at the public admission edge and mask stale prior-owner
status during pending delivery. Its internal `accepted_start` oracle hook means actual E+1 child command
delivery/reset, so independent staged/inverse counters reset on that edge.
The reviewed adapter changes only this diagnostic activation fence; value,
held, owner, error and physical-drain checks are not dropped or shifted.

The actual transport admission monitor independently queues each accepted
public command at E and compares its complete registered tuple after that
edge. It requires actual child delivery at E+1 with the same owner sequence;
only that delivery or an externally driven reset/abort retires its expectation.
Candidate pending/flush bits cannot erase the ledger. After admission, the
adapter poisons live packet size, epoch, reference/cache metadata and all four
scheduling controls in its E post-edge hook, **before** the delivery-wait tick. All 16 commands per seed (normal, canceled-prefix and
retry starts) must be counted once and delivered once; complete canonical/
physical-drain oracles remain active. Both seeds passed these monitor checks. The separately pinned focused controller
proof additionally covers:

- Command tuple mutation immediately after admission: packet size, epoch,
  reference/cache flags and identities, and all scheduling/mode controls.
- Credit grant/consumption/rearm, start versus complete/partial cache preload,
  simultaneous start/cache offer, and denied start without another owner's
  cache mutation. An idle child resource remains reserved while credit is held.
- Start/abort/reset coincidence at capture and delivery, held first input,
  final coefficient/residual/EOF ordering, and held output during revocation.
- Current/old faults and ACKs around registered command delivery; bounded local
  kill/flush and immediate public valid/ready masking at the required edge.
- Accepted scratch/reference requests with completion withheld, wrong response
  followed by the real response, retry blocked through physical drain, and
  cache/session/token wrap assumptions made explicit.

The selected fresh attempt `20261108T225107629909Z` passed both seeds 107601
and 107602: **44 canonical case/profile rows and 42 original directed checks**,
plus **24 actual V97 transport profiles and four abort/reset retries**. Each
transport seed counted 16 public accepts, 16 registered E+1 deliveries and 16
poisoned command tuples. Each reached 2,048 FIFO bytes, 2,048 reserved bytes and
two descriptors; each rejected 16 wrong DMA tokens and 16 wrong completion
tokens and held real ACKs for 17,246 cycles. Every accepted canonical raw pixel
stream matched the retained V113/V112 content reference. No candidate model was
reused; the old content artifacts remain references only.

The independent [source and receipt review](../../experiments/python-gamebub-v114/spatial/source-review.json)
verified all 42 source/proof pins, all 58 retained artifact pins, parsed stdout
verdict equality, compressed and expanded artifact hashes, all eight successful
bounded commands and both reversible derivations. The unchanged directed suite
covers partial-cache abort/reload, queued refill cancellation, accepted-write and
reference physical drains, mismatched and bus-error replies, held residual and
pixel revocation, owned IDCT cancellation, metadata snapshots, coefficient/mapped
tuples and clean retry without reset. The public command E to child delivery
E+1 edge is an explicit API change; no cycle-equivalence claim is made.

A local flush does not retire a physical service transaction. No plan, counter,
status or diagnostic bit may replace the external handshake ledger. New clock
stages must preserve immediate public revocation; registering only abort or
sampling readiness without holding a reservation is insufficient. Internal
owner tags do not distinguish external replies with identical epoch-only tags.
Complete production PCTL1/session, memory, CDC, C2/HUD sealing and publication
qualification remain separate gates.

The runner uses pinned Verilator with assertions and fatal SV `-Wall` plus owned
C++ `-Wall -Wextra -Werror`, one compiler worker, two CPUs and 8 GiB RAM with an
equal memory-plus-swap limit. Finite compile/simulation watchdogs and host
available-memory/PSI stop gates apply. Root must grant a heavy slot before any
compile. Each attempt snapshots all sources, selected focused proofs, commands
and artifacts; failed prefixes are retained. After the final PASS, selected
sources and proof inputs are frozen. No native route, bitstream, hardware FPS
or complete-under-10-ms result is implied by this behavioral qualification.

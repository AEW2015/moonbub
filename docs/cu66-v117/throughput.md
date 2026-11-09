# V117 coupled inverse and reconstruction throughput

This work changes scheduling while retaining the codec packet, arithmetic and
canonical byte definition. It is separate from the V117 AC read-validation
setup-timing cut. The V116 row-fast measurement was 1,416,449 post-final-input
cycles; a strict 125 MHz under-10-ms budget needs at least 166,450 fewer cycles.
No savings or achieved clock are inferred from source structure.

## Inverse acceptance: registered validation at II=1

The candidate is
[`cu66_inverse_stream_v91j.sv`](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv),
SHA `67ec3d9d87678a141286dae8815f83380bea133754062179c3cc5793b42f87f4`.
It preserves the two coefficient banks, two arithmetic-result slots and frozen
V115 dequant/IDCT helpers. It replaces the single mutually exclusive
A_VALIDATE/A_COMMIT tuple with two complete capture and validated-commit tuples.
A separate registered reservation frontier advances at capture, while the
original fill frontier advances only on a real coefficient payload write.

Every tuple carries its epoch, child epoch, internally allocated tile token,
plane, scale, block, tile, quantization cell, index and value, together with the
expected owner and static error flags. Validation remains registered and checks
index, metadata, domain and token-exhaustion priority. A bank becomes READY only
when its validated word 63 commits. Readiness uses registered reservation
capacity and bank ownership; it does not look through downstream readiness or
flatten current input validation into all coefficient payload enables.

A captured coefficient still commits at E+2. Capture, registered validation and
an older commit can overlap, yielding true II=1 rather than a renamed II=2
state machine. An older validated private word may commit on the edge that a
younger captured tuple faults. The failure revokes both bank owners, drops all
younger stages and prevents publication; the commit counter records that actual
private write. This is not permission for an invalid/younger tuple to commit.

All original V113 inverse assertion blocks remain byte-identical. New checks
cover complete validated metadata, token-frontier agreement, bank reservation
and accepted-minus-committed occupancy equal to the two stage-valid bits.
The reversible [source recipe](../../fpga/experiments/cu66-v117-throughput/inverse-edit-recipe.json)
and [additive bench recipe](../../fpga/experiments/cu66-v117-throughput/inverse-bench-recipe.json)
retain the original independent E+2 commit ledger, boundary arithmetic goldens,
held outputs, finite owner slots, faults, cancellation and clean retries.

The focused inverse selector is
[`throughput/inverse/results.json`](../../experiments/python-gamebub-v117/throughput/inverse/results.json).
Both actual RTL seeds passed: each executes 48 boundary cases and 27 directed
checks, verifies 4,032 residual samples, accepts the first 64 coefficients in
64 consecutive edges, reaches a measured maximum consecutive acceptance run
of 140, and retains the exact E+2 commit ledger. These are component simulation
results, not a complete decoder latency, routed-clock or hardware-FPS result.

## Reconstruction: exactly two logical tile owners

The refined candidate reconstruction is SHA
`5b12193073a8410ad0d05d251c061f7379cd9dba5a9677e5f8f20da4c581be06`.
It keeps the existing public ports and the physical
reference-response owner. A gather frontier prepares the next tile while an
independent ordered head emits the previous tile. Two bounded owner slots have
FREE, FILL, MATH and READY states. A MODE_REQ handshake reserves a free slot;
a full pair cannot grant a third tile. A head held by output backpressure is
never reused or overwritten.

The existing single `cu66_reconstruct_tile` engine is retained. Its result is
validated in MATH_WAIT, then a separate registered COPY state performs a real
512-bit parallel copy into the reserved owner. This costs an edge and physical
registers. There are two 512-bit completed-owner payload stores in addition to
the existing residual, reference and engine storage. The engine and temporary
residual/reference payloads belong to the active tail owner; they are not
uncounted extra independently queued tiles. The physical `storage_copy` enable is only registered COPY state and the
registered tail-bank selection. The logical `owner_copy` still includes running
and immediate kill masks, and controls engine consumption, READY publication
and frontier advancement. A private inactive-bank write may occur on a
cancel/reset COPY edge; it grants no logical owner. Assertions check complete
engine ownership, no READY-head overwrite even on kill, equivalence on normal
edges, immediate logical masking and no owner surviving a revoked copy.
Only a successful logical COPY advances
the gather frontier. Ordered last-byte acceptance frees the head owner.

The public debug `state` describes gathering, not output occupancy. RESIDUAL=4,
REF_WAIT=6 and MATH_WAIT=8 retain their meanings; COPY=11 is new. The old EMIT=9
state is no longer entered because emission is independent. Assignable
`running`, `done`, `state` and `discard_ref` remain for the existing prepared
fault tests. Setting running false immediately masks public canonical output.

Actual current-engine wires are `engine_out_valid`, `engine_out_id`,
`engine_out_pixels` and `engine_out_error`. The historical `math_out_*` names
now describe the completed head record, captured from that actual response.
The old output-ID assertion compares this captured engine ID against the
independent coordinates stored when the mode request was answered. It is not
an alias of both sides to the same request ID. An additional one-edge checker
compares the complete 512-bit engine response, ID, error and request coordinate
record against the owner storage after COPY. A separate held-head checker
covers the full payload and output tuple; owner checks prohibit overwrite.

Original reconstruction assertion blocks remain byte-identical. Physical
reference epoch/fid/generation/plane/tile debt survives cancellation and warm
reset until its exact response retires. New admission waits for old physical
reference debt to drain before gathering a new frame. This is an explicit
scheduling strengthening; an old response cannot initialize a new frame's
reference pixels. Reference-error and case-error priority remains the original
ordering, and logical owners are revoked on a response failure.

## Reconstruction proof and current qualification

The verification probe is a lossless adapter: only module name and three
function-observation ports are added. Reversing the recorded adapter reconstructs
the complete production bytes exactly. The quantization helper's unchanged
body is checked with the original V103 independent row/column oracle over all
4×8192 input combinations. No sequential dual-DUT cycle-equivalence claim is
made for this deliberately changed schedule.

The new sequential bench independently derives mode, residual, leased-reference
pixels and clipping results over the full 8,100-tile/518,400-byte frame. Each
seed requires three complete key/inter/reference-retry frames, two-owner
backpressure, simultaneous real residual/canonical handshakes, full held-tuple
stability, every reference-owner field mismatch, matching response errors,
residual owner corruption, invalid modes, missing reference, partial EOF,
reset/cancel through gather/reference/math/COPY phases and clean retries.

The first strict reconstruction build passed compilation, but its first actual
seed failed a 3,000-edge wait for state 6. A diagnostic-only retry retained RTL,
stimulus, RNG draws, limits, assertions and oracles and added phase/state/owner
traces. It identified `wrong_ref_2`: the preceding prefix had legitimately
gathered tile 4's reference while tile 3 was still emitting. Cancellation
correctly preserved that accepted physical lease. The next independent fixture
withheld responses before retiring the old lease, so WAIT_ADMISSION correctly
stayed at state 1 with matching model and DUT physical ownership.

Both failed attempts and snapshots are retained under
`experiments/python-gamebub-v117/throughput/reconstruct/attempts/`.
The bench-only repair performs the actual prior-response handshake before an
independent fixture begins withholding a new response. Explicit warm-start-with-
debt cases opt out and still check that new gathering blocks until that old
response drains. No model/DUT owner is cleared by a backdoor, and the watchdog
and all old checks remain unchanged. A new deterministic fixture-drain case
covers the repaired setup.

The initial `4dbd…` reconstruction then passed both focused seeds: each checks
32,768 geometry cases, three full frames, 44 directed cases and 1,564,991
canonical bytes. It observes 1,125,671 / 1,125,955 simultaneous accepted residual
and canonical edges and 262,916 / 263,167 held-tuple checks, with at most two
owners. Standalone key-frame time is 557,496 controller clocks; inter-frame
times are 685,259 / 685,493 under the defined input/reference/output models.
These component timings are not whole-decoder post-final-input intervals or
achieved hardware latency.

That qualified initial source, probe, bench, recipes and runner are preserved
under [initial/](../../fpga/experiments/cu66-v117-throughput/initial/), and its
immutable raw receipt is
[20261109T110312411774Z](../../experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T110312411774Z/receipt.json).
The physical COPY refinement removes the known global-kill term from the RTL
expressions driving 1,024 bulk payload enables, while retaining all original
and initial assertions. The actual mapped control sets still require native
inspection; source structure alone does not prove the hardware CE mapping.
Its [source recipe](../../fpga/experiments/cu66-v117-throughput/reconstruct-storage-copy-recipe.json)
and [additive bench recipe](../../fpga/experiments/cu66-v117-throughput/reconstruct-storage-bench-recipe.json)
reverse exactly to that qualified initial source and bench. Two additional
cases cancel/reset at the second COPY while a different older head is stalled:
they verify the complete head storage stays unchanged, the inactive payload
and actual engine ID really capture, logical ownership revokes, and a fresh
prefix retry is clean. The refined source passed its own fresh two-seed focused run in
[20261109T111821839417Z](../../experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T111821839417Z/receipt.json)
(receipt SHA `ab82508fed471cec452db2edf7308933f01921d8dcf7d8f3fe01315d37c3d906`).
No initial-source PASS was transferred to the refined source.

| Final refined-source observation | Seed 117311 | Seed 117312 |
| --- | ---: | ---: |
| Geometry cases | 32,768 | 32,768 |
| Complete controller frames | 3 | 3 |
| Directed checks | 46 | 46 |
| Independently checked canonical bytes | 1,565,503 | 1,565,503 |
| Simultaneous accepted fill/emission edges | 1,126,574 | 1,125,986 |
| Held tuple checks | 262,678 | 263,775 |
| Maximum logical tile owners | 2 | 2 |
| Physical kill-COPY cases with older stalled head | 2 | 2 |
| No-stall key controller frame, cycles | 557,496 | 557,496 |
| Inter controller frame with modeled stalls, cycles | 685,259 | 685,493 |

The current [reconstruction selector](../../experiments/python-gamebub-v117/throughput/reconstruct/results.json)
binds this refined source. The [retained failure history](../../experiments/python-gamebub-v117/throughput/failure-history.json)
keeps both actual failures, their trace-based diagnosis and the historical
initial-source proof separate. Every selected production source, verification
adapter, recipe, bench and runner is frozen after these focused results.
Fresh combined body/peer/LIVE and native evidence remains necessary.

## Reproduction and boundaries

Root alone grants the global heavy slots. Each runner uses the pinned
Verilator 5.020 image, two CPUs, one compiler job, an 8 GiB memory limit with no
extra swap, strict `--assert -Wall`, and C++ `-Wall -Wextra -Werror`. Memory
availability and pressure gate dispatch, with combined RAM/swap use secondary.
`actual_RTL_run` is persisted before invoking a simulator, including failures.
Every attempt retains source snapshots, commands, image/binary hashes, terminal
logs and artifact hashes. No source changes are allowed during an active run.

```sh
python3 scripts/cu66-v117/throughput/qualify_inverse.py --run --root-grant ROOT_GRANTED_V117_INVERSE
python3 scripts/cu66-v117/throughput/qualify_reconstruct.py --run --root-grant ROOT_GRANTED_V117_RECON
```

The first command already has passing focused evidence and must not be rerun
without a changed source or unresolved concern. Fresh combined body, transport,
peer and LIVE executions are required after both components qualify. A source
combination's own native 125 MHz route is required; no timing result from an AC-
only composition is transferred to the throughput composition. Physical SDRAM,
ESP32 execution, display scanout, sustained distinct-frame hardware 30 fps and
validated hardware decoding below 10 ms remain separate open gates.

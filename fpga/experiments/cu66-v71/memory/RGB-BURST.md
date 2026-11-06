# Explicit RGB BL8 variant and cross-bank map experiment

`cu71_memory_system_burst` and `cu71_word_bridge_burst` preserve the qualified
scalar/LCD baseline in separate modules. PHY/controller bytes, wait4,
274.5-degree read clock and100MHz assumptions remain unchanged.

The new port is an explicit producer transaction:

| Signal | Direction at memory | Meaning |
|---|---|---|
| `rgb_req_valid`, `rgb_req_ready` | in/out | Accept one immutable request |
| `rgb_req_addr[23:0]` | in | x16 word address, aligned8 |
| `rgb_req_data[127:0]` | in | Word`i` at bits`16*i+:16` |
| `rgb_req_mask[15:0]` | in | Bit`2*i` disables low byte, bit`2*i+1` disables high byte; zero writes |
| `rgb_rsp_valid`, `rgb_rsp_ready`, `rgb_rsp_error` | out/in/out | Held actual-recovery completion or rejected-request error |
| `rgb_abort_i`, `rgb_busy`, `rgb_aborted` | in/out/out | Cancel new issue, drain an accepted operation, suppress success, acknowledge drain |
| `rgb_completed_writes`, `rgb_max_wait` | out | Actual controller operations and largest bridge-admitted operation wait |

Only whole aligned8-word blocks within RGB0/RGB1 are allowed. Misaligned,
cross-allocation and non-RGB requests produce an error without controller work.
Partial byte masks and all-masked operations are supported. An accepted BL8
always finishes all8physical beats even when the client aborts; candidates
must remain private and leased until drain. No scalar acknowledgment was
reinterpreted as queue acceptance.

Canonical, auxiliary, LCD and RGB clients have independent request/response
slots. Three-way canonical/aux/RGB round robin operates under the existing
two-LCD-to-one-background quota and four-cycle bounded LCD lookahead.
Stalled RGB responses do not hold the controller. Aliasing writes invalidate
both scalar caches before issue and after recovery.

Either let a canceling painter drain its normal accepted response, or implement
the explicit `rgb_aborted` acknowledgment. Asserting memory abort while waiting
only for a now-suppressed normal response would deadlock. Root ownership must
include RGB busy/drain before freeing memory or committing.

## Functional evidence

`rgb-reference-{fast,slow}01` and
`rgb-reference-crossbank-{fast,slow}01` each pass5,168 checks and42 abort/drain
probes. They retain the earlier component suite and add52 actual RGB operations,
masked-byte/readback/cache checks, RGB allocation guards and last block,
all8accepted RGB abort positions, held-response isolation and four-client
concurrency. Concurrent RGB and HUD results are physically read back afterward;
LCD payloads and the canonical tile are independently checked too.

The isolated RGB transaction checks exactly8physical beats. During concurrent
writers, the global physical-write counter includes other clients, so RGB's
actual-recovery counter and independent readback identify its work. The first
attempt with an invalid global-counter exclusivity assumption is preserved.

The contended reference campaign reads four actual previously stored canonical
tiles with32controller BL8 reads and96private-cache hits. Worst tile service
was1,979modeled clocks with the original map and2,362 with the cross-bank map
under the declared simultaneous workload. Cache hits currently wait for the
bridge's global controller scheduling boundary; a future independent-hit
response path requires its own alias/order tests.

Run `python scripts/cu66-v71/memory/verify_burst.py` to bind these results to
current modules. The tests use exact-controller non-`SIMULATION` logic with
the strict datasheet-correct Icarus model. They do not qualify physical timing,
target fit, clean LCD deadlines or whole-frame30fps.

## Map A/B

`maps/crossbank-v001` is generated from the frozen v70 generator into separate
RTL, C++ and JSON artifacts. RGB1 moves from word`0xc80000` to`0x980000`;
RGB0 stays`0xc00000`. Alignment,32byte guards, allocation collisions and the
single32MiB capacity pass explicit checks. Place this candidate include directory
before the old memory directory; the compatible header filename remains
`cu70_memory_map.svh`, and C++ namespace remains`cu70_map`.

The candidate puts RGB1 in physical SDRAM bank2 instead of bank3. It may reduce
old/new RGB row conflicts, but now shares bank2 with canonical2/HUD2. This is
not a universal bandwidth improvement: matched full-raster tests must exercise
both front slots and active canonical/HUD bank combinations. Legacy LCD slot
address bit19 is a selector, not an additive offset under the new map; use the
new bank-aware scanout translation. No board deployment has occurred.

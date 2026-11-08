# PCTL1: pipeline ownership contract and whole-parent inventory

Status: **V111 specification and read-only inventory, unimplemented**. This contract is for the V112 spatial/control pipeline. It does not alter the frozen V111 header candidate, its exact-cycle checker or its focused PASS, and supplies no new RTL, full-parent fit, 100/125MHz or hardware result.

The machine-readable [inventory](../../experiments/python-gamebub-v111/control-contract/inventory.json) pins actual sources/reports; its [analyzer](../../experiments/python-gamebub-v111/control-contract/analyze.py) only reads and hashes them. All 18 V110 Count source origins match their actual routed snapshot identities. All 43 retained JPEG source bindings match current files. The [V110 control proposal](../cu66-v110/control-contract.md) remains the source for the earlier exact pending-fault algebra; the following contract makes the future stage ownership and resource limits explicit.

## Owner identity and lifetime

Use rising-edge valid/ready transfers. A transfer exists only if both sides are true immediately before that edge. An admitted frame carries a private owner `(reset_generation:u32, admission_sequence:u32)` in addition to the existing supplied frame epoch/FID, reference FID/generation and child epoch. A tile/residual also carries its original inverse token, plane, qscale, block, tile, qcell and sample index. Do not substitute frame-ID equality for ownership.

Warm reset increments reset-generation through a supervisor that preserves outstanding physical transaction records; it invalidates logical owners rather than deleting accepted requests. Admission-sequence increments on every accepted command, including one that subsequently fails. Wrap blocks new admission until a drained, explicitly re-established generation/session boundary. A cold reconfiguration needs an external-channel quiescence/session-reset handshake before admitting work whose identity could alias an old response. Caller-supplied epochs may be repeated or malformed without authorizing old tokens.

A frame moves through `reserved → command/start acknowledgments → active → final outputs/EOF → physical drain → validated provisional result → publication`. Failure or abort moves it to `revoked → local flush plus physical drain → retired`. No failed frame is published as display/reference state. A provisional framebuffer remains owned until every accepted write retires, even if logical decode has stopped. New owners cannot reuse its storage early.

## Reserved admission and local credits

A registered admission credit is a reservation, not a delayed copy of current `start_ready`. Issue one only after matching empty/flush/drain acknowledgments from producer/admission and refill owner, ingress/context/Rice, scratch physical/write/prefetch/tile banks, coefficient handoff/final offer, inverse banks/math, residual handoff/results, and reconstruction/reference owner. Resource acknowledgments stay stable until consumed or invalidated; children cannot independently allocate reserved resources.

`accepted_start = start && admission_credit && !reset && !abort_packet`. It consumes the credit and latches the complete command: packet size, supplied epoch, accepted reference validity/FID/generation, quant-cache validity/identity and mode/profile controls. Later changes on input pins are irrelevant to that command. The registered command reaches children at the next edge. Data readiness requires all matching start acknowledgments.

Cache preload is a separate reservation. Suppress `cache_ready` whenever `start` is asserted; accepted start wins over a coincident offered cache beat. A partial cache preload without accepted start revokes unused frame-admission credit and must complete or be explicitly canceled before a new credit is issued. Never advertise a frame credit while a child can consume its reserved bank for unrelated work.

## Public revocation and registered local flush

Retain an immediate mask at operational boundaries from external reset/abort and qualified current-owner stage/physical errors. Stage-local CEs use local owner/active/error/kill state rather than broad parent readiness and remote sticky-error expressions. A tagged registered kill request invalidates local speculative data later, while the boundary already prevents public transfer and ownership publication.

A sequential fault detected at edge E appears immediately after E and suppresses public transfers at E+1. A transfer accepted just before E is counted and cannot be canceled retroactively; its frame is nevertheless ineligible for validated publication. An external abort/reset asserted before E suppresses the transfer at E itself. Faults of retired owners do not cancel a new owner. The parent retains the first current-owner terminal cause; simultaneous visible causes use reconstruction, inverse, coefficient priority, preserving each stage's reason encoding.

Mask both public `*_valid` and the corresponding ready returned internally for revoked memory/reference requests and public pixels. Otherwise a child could falsely count a request hidden by the wrapper. Keep response matching/drain acceptance operational during logical cancellation. A response with the wrong owner/tag cannot retire the genuine pending request. A matching response with an error retires that physical obligation and rejects the logical frame. Duplicate/stale replies are recorded/discarded according to the channel contract, never used to create new-owner credit.

| Event | Proposed bound in decoder-domain edges |
| --- | --- |
| Accept frame command at E | Consume credit and snapshot at E; children consume registered start at E+1. No input acceptance before matching start acknowledgments. |
| Current-owner sequential fault visible after E | Boundary mask applies in that interval; local kill captures at E+1; private invalidation/flush ACK by E+2. |
| External abort/reset present before E | Mask transfers at E; local kill captures at E; private invalidation/flush ACK by E+1. Physical ledgers survive warm reset. |
| Local flush ACK | Certifies no further private tuple can emerge for that owner. It says nothing about physical request completion. |
| Matching physical drain ACK | Retires a real accepted request exactly once. No finite deadline is claimed without a bounded external service contract. |
| New admission credit | Within one edge after all matching flush/drain/EOF/empty/preload conditions join. With no outstanding service, a new fault after E permits guaranteed credit after E+3 at earliest. |
| Successful `done` | Within two edges after final accepted public pixel, coefficient/residual EOF completion, all physical drains and all required validation results join; fault/abort wins. |

These are future protocol requirements, not measured current RTL timing. Added command/flush/handoff edges are intentional public latency changes and require the new event oracle. Immediate masks and owner comparators themselves must be timed; registering local state does not guarantee 125MHz.

## Coefficient, result and EOF ownership

The coefficient handoff owns exactly one full tuple: parent owner, frame/child epochs, plane, qscale, block, tile, qcell, index, signed value and metadata/domain error bits. Preserve a separate pending-EOF and final-offer owner. If producer completion accompanies an offered but unaccepted final coefficient, that offer must be accepted or explicitly revoked before EOF can advance. Full-slot simultaneous pop/push retains the replacement tuple and all tags; no overwrite or duplication is allowed.

For inverse arithmetic, reserve a finite free result slot before launch. Retain two complete result slots when evaluating math/emission overlap, with actual 64-sample storage, tags, copy/read latency and ports modeled. Arithmetic releases its owner only after transferring the whole result into its reserved slot. Emission owns that slot until the sixty-fourth residual handshake. A full queue backpressures new arithmetic. Coefficient-bank fill, arithmetic and output-result ownership are distinct resources.

A one-entry residual handoff carries the same frame/child/token/plane/block/tile/qcell/scale/sample identity. Inverse completion can arrive while the last residual is held; residual EOF cannot advance until reconstruction accepts that residual. Success joins both EOFs, empty final-offer/result slots, final reconstructed pixel acceptance, reference/scratch writes and validation. `inverse_done` or private math-done alone cannot authorize parent success or retry.

Canceling a frame clears logical data/EOF eligibility through the tagged flush protocol but retains all accepted physical requests and provisional framebuffer ownership until actual drain. Any delayed arithmetic result for an old owner is discarded/quarantined rather than marking a new slot ready. Warm reset with a computing tile, one held result and a stalled final pixel is a required test.

## Operational interface versus diagnostic snapshots

| Family | Required meaning in the new wrapper |
| --- | --- |
| `in/cache/out` handshakes; scratch/reference requests and responses | Operational accepted events with stable held data and explicit current owner. Boundary revocation/drain semantics are mandatory. |
| Frame admission, done/error, reference/display publication | Operational ownership transitions. Source-versioned latency and error lifetime are documented and independently checked. |
| Internal coefficient/residual/lookup/launch/commit observations | Keep actual local wires separate from diagnostic copies. A `trace_live` tag plus complete owner identifies diagnostic events; masking a trace cannot change an internal transfer or hide an operational failure. |
| Raw states, wide coefficient/dequant vectors, cache/bank cursors, inactive payload | Diagnostic values may differ on unowned cycles in the new version. Preserve V110's original exact checker unchanged rather than pretending these are still cycle-equivalent. |
| Handshake/physical ACK/discard counters | Count events at the named boundary, including accepted pre-fault transfers and matching post-cancel drains. Preserve original width/wrap rules unless explicitly versioned. |
| Stall histograms, overlap counts, queue maxima and timestamps | New scheduling changes values. Define each against independent events and service conditions; do not compare shifted traces until they happen to agree. |

Implement coherent diagnostic snapshots: a request token captures selected owner-tagged counters/status into a held shadow bank; multiple CSR words read the same snapshot generation. Across clock domains use request/ack handshakes and per-domain timestamps, without claiming one atomic global edge. A busy diagnostic readout must not stall video; a bounded second bank or explicit dropped-snapshot counter handles overlap. Immediate operational faults remain separately latched. Do not export every vector on every cycle or remove required operational ports merely to improve OOC timing.

## Current physical inventory

Both reports target `xc7a100tcsg324-1`. Counts are observed resources, not a forecast for the future integrated parent.

| Scope | LUTs | FFs | RAMB36 + RAMB18 | Equivalent 36Kb tiles | DSP48E1 |
| --- | ---: | ---: | --- | ---: | ---: |
| Device reference capacity | 63,400 | 126,800 | — | 135 | 240 |
| Retained routed JPEG `moonshine_top`, Vivado2025.2 Windows | 7,362 | 5,994 | 113 + 15 | 120.5 | 32 |
| Actual V110 Count routed OOC `cs88_pipeline_v91k`, Vivado2026.1 | 36,193 | 35,357 | 32 + 12 | 38 | 42 |

The historical JPEG report's 43 source bindings all still match. It is not a newly reproduced implementation. The Count result is an actual fresh route but not a complete board parent. Its timing checks report 1,101 inputs without input delay and 12,885 outputs without output delay, with zero unconstrained internal endpoints. A lean production wrapper still needs real interface clocks, CDC, I/O delays, memory service and operational/diagnostic port classification.

Count hierarchy observations: producer/coefficient admission has19,490LUT/21,279FF and all38BRAM tiles; admission alone has8,824LUT/6,561FF with16RAMB36+2RAMB18; ingress/context has4,025LUT/2,891FF with16RAMB36+10RAMB18 and17DSP. Transform has11,167LUT/10,174FF/25DSP (8 dequant,17 IDCT); reconstruction has5,509LUT/3,763FF and no BRAM/DSP in this component. Cross-hierarchy LUT combining means child totals need not add exactly to parent totals.

Do not add the JPEG and Count rows or subtract one from device totals and call the result an allocation. The production JPEG parent includes a256KiB compressed store, JPEG memories, transport/overlay/line storage and shared service. Count has its own ingress/admission memories. Replacing, sharing or concurrently retaining those resources requires a new complete-top source and port/banking/scheduling design. JPEG fallback may need a separate qualified bitstream instead of simultaneous instantiation. Extra DSP lanes do not create memory ports or solve placement locality.

Current production source uses a50MHz input; PLL outputs200MHz SPI/overlay and100MHz core/memory with279° read capture. Panel MMCM settings imply29.361979MHz nominal pixel clock, agreeing with the retained report's34.058ns rounded period. LCD source totals541×834 imply **65.076Hz nominal**, not an assumed60Hz; active mapping is portrait480×800 with the720-row coded canvas offset40. These are code/report-derived nominal values, not measured panel behavior. Freeze them in the simulation timebase or deliberately qualify a changed panel mode.

The parent exposes only one16-bit SDRAM bus and enables chip0 (`CKE=01`, `CS_n=10`). The memory wrapper prioritizes scanout at burst boundaries and currently accepts decoder pixel writes individually. It has no external SRAM ports. Neither two advertised SDRAM chips nor an external-memory capacity total proves independent bandwidth or integrated full-capacity coverage. A125MHz decoder must cross into the qualified100MHz memory/pixel-control domains through modeled owned FIFOs/handshakes, or the whole system clock design must be explicitly rebuilt and verified. Do not raise memory/panel clocks as an incidental decoder optimization.

## Remaining routed cones and next candidates

The following are **final Count route** paths, not placement estimates or new V111 results:

| Full hierarchy | Final slack / delay | Causal classification and bounded next work |
| --- | --- | --- |
| `coefficients/child/packet_decoder/synchronous.ingress/context_blocks_reg[9]/C` → `coefficients/child/scratch/prepare_block_reg[{1,4,6,8}]/R` | Four paths: −0.895/−0.891ns;10.382/10.378ns;10 logic levels;about78.6% routing | Source metadata admission and error/control fanin reaches a functional zeroing assignment on successful scratch begin. `prepare_block<=0` is inside validated begin, while the scratch reset/cancel branch does not clear it. This is not proof of a global reset-net problem. |
| `coefficients/admission/tile_reg[5]/C` → `coefficients/admission/group_visible_reg[3]/D` | Rank8,−0.940ns;10.933ns;15 levels;70.759% routing | `visible_group` evaluates sixteen tile-offset range/hidden predicates and accumulates their population. It is in admission, not scratch. |
| `coefficients/admission/tile_reg[5]/C` → `coefficients/admission/group_visible_reg[4]/D` | Rank44,−0.891ns;10.925ns;15 levels;70.810% routing | Same spatial-geometry/population family, with another output bit. |

Scratch begin checks block range, three count thresholds, raw count restrictions and capacity before latching metadata and clearing `prepare_block`. A source-preserving candidate could prepare the complete coherent predicate on earlier owned metadata edges, but must prove every threshold/capacity/owner field is final before consumption. PCTL1's latency-changing alternative sends a locally validated reserved command and applies the functional clear under local admission. Keep genuine physical drain ownership and malformed-packet/error priority; do not remove a clear just because the endpoint pin is named R. Optimized net names in the path are not a one-to-one proof of the original source expression.

For visibility, compare a balanced registered mask/popcount pipeline against a small fixed-geometry ROM. Valid non-key GROUP_BEGIN starts appear on16-tile boundaries:338 luma groups and85 groups per chroma plane,508 five-bit counts, or a512×5 logical table. This is an **unimplemented owned-domain hypothesis**, not an all-input replacement. Current HEADER_CHECK rejects dimensions other than720×480 before initializing plane0/tile0; normal group transitions advance to group_end or reset tile on plane change. Nonetheless the consuming precondition—accepted fixed720×4804:2:0 profile, current owner, plane0..2, tile below that plane's count and tile multiple16—must be discharged from actual caller/state transitions before enabling a specialized ROM.

The current `visible_group(p,t)` still defines behavior for a full unsigned32 tile argument and even p3 (via its nonzero-plane path), including wrap in `t+k`; direct/malformed/corrupt-state fixtures may exercise values outside the proposed table. Retain the generic function as default. A separately enabled fixed-profile specialization needs consuming-domain assertions and a whole-packet proof that malformed/unsupported headers are rejected before use; excluded internal domains must remain explicit and tested against the unchanged generic path. Do not silently replace out-of-domain outputs with zero or alias p3 to a valid plane. Preserve same-edge successor plane/tile ownership at a plane boundary rather than sampling the previous group's key. ROM read latency, ports, inference, placement and timing remain to be measured.

## Independent verification and implementation exit

Retain the old exact-cycle V110/header miters and immutable packet/transform/canonical goldens. Build the future event scoreboard from external accepted commands, data, physical requests/responses and publication events, not candidate busy/state bits. It owns expected ordered coefficient/residual/pixel queues and physical response records; stage acknowledgments cannot delete its obligations. Assert no missing/duplicate/cross-owner tuple, no held-data mutation, no masked internal transfer, no EOF before final offered acceptance, no retry before real drain, and no done/publication before final validated output.

Required directed cases include simultaneous slot pop/push, producer done with held final coefficient, inverse done with held final residual, abort plus offered start/cache preload, late/sequential/simultaneous faults, last pixel plus failure, warm reset with scratch write/reference read pending, wrong response followed by the real response, duplicate ACK, all flush/drain ACK orders, token/epoch wrap and replay with otherwise matching public FID fields. Compare event counters and complete identities. Deadlines depend on explicitly bounded external service; wall-clock simulator speed is not silicon timing.

Only new source-bound RTL and tests can implement this contract. Then run the full canonical content/ownership suite, finite memory/display/transport integration, fresh8ns synthesis/place/route and the prescribed independent repeat. Resource fit, clock closure, simulated rate, calibrated device service and hardware30fps/<10ms are separate gates and all remain open for PCTL1.

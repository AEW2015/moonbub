# V116 implementation brief

V116 should run two independently gated workstreams: shorten the remaining routed control/read-word cones, and replace the single-byte write/ACK/hash serialization with a bounded overlapping eight-byte row join. Neither workstream establishes sustained hardware 30 fps or validated under-10-ms decoding by itself. The present study's six source/clock measurements remain its physical budget; this brief does not authorize another native timing campaign.

Inputs remain frozen: [next timing architecture](next-timing-architecture.md), [validated budget](validated-budget-next.md), and their selected-source/receipt pins. The owner certificate and final ingress are separately qualified V115 candidates. First use their final reports to determine which earlier cones survived; do not assume the refined report predicts the final placement.

## 1. Establish one baseline and explicit fences

Before changing RTL, select the final V115 component and live-parent receipts by path and SHA. Pin the exact source composition, clocks, fixtures, memory-service profile and all oracle versions. Keep original single-byte mode and its assertions/checkers unchanged. Add these event records to each comparison:

| Fence | Definition |
| --- | --- |
| Frame command accepted | Owner/credit reservation, before any packet input |
| First packet byte | First accepted outer-stream byte, not the decoder's first internal byte |
| Last packet byte | Last accepted outer-stream byte; capture host/transport pacing separately |
| Last canonical input | Final accepted canonical pixel byte offered to the candidate-memory/hash path |
| Last canonical physical ACK | Final matching successful write retirement for that frame's canonical bytes |
| Last canonical hash delivery | Final canonical byte accepted by the validator after its successful physical ACK |
| Producer done | Existing decoder completion; it cannot substitute for any ACK/hash fence |
| Root / HUD / seal complete | Separate completion events for the original C2 jobs |
| Validated commit | Successful complete validator/publication decision; no pending required write/hash owner |
| Presentation | Distinct frame actually becomes scanout-visible; absent from current abstract publication proof |

Report command→commit, first packet→commit, last packet→commit and last canonical input→commit separately. A short last-input tail is not low end-to-end latency. A single-frame completion is not sustained 30 fps; sustained acceptance/publication requires distinct increasing frame identities, queue depths, deadline misses and physical presentation observations across frames.

## 2. Timing workstream: fix the cone that actually remains

The frozen refined 125 MHz report showed `owner_open`→publish/release counter CE at −3.067 ns, and `read_address[3]`→scratch `heads` RAM write enable at −3.013 ns. Both were routing dominated. These are source-specific starting hypotheses, not final-candidate results.

Implement one reversible local candidate at a time, with this order after inspecting final paths:

1. **Instrumented-event boundary, if its counter endpoint remains critical.** Capture the exact simultaneous publish/release event locally, then retire it into the wide counter. Specify a one-edge counter-read contract or prove a forwarding view; retain reset/owner attribution and drain the event before final metric snapshots. Do not remove the counter or alter its event definition. This removes a counter-enable endpoint, not necessarily the underlying functional ready path.
2. **Two-entry coefficient boundary, if downstream ready remains in the cone.** Store two complete 130-bit tuples and their static validation flags. Drive producer capacity from local occupancy without full-plus-pop combinational look-through; declare the possible one-edge full-queue recovery bubble. Preserve the final-offer/done fence. This cuts downstream ready but does **not** eliminate `owner_open` through immediate fault/cancel masks. If that path remains, prepare a separate private capacity-grant/cancel contract instead of silently removing masks. Public revocation stays on the original edge, and already accepted physical debt must drain.
3. **Prepared AC read tuple, if read-word validation still drives scratch RAM WE.** Capture word, decoded position and complete owner/offset facts on the existing AC_FETCH hit edge; forward from `mem_rsp_data` on the existing matching READ_WAIT edge for misses. Reuse the existing AC_EXTRACT edge. Compare consumed tuple and every validation predicate against the original exact signed/cast algebra. Preserve outer error priority and old late-error write visibility. If the cache-hit capture merely moves address/select delay to AC_FETCH, prepare offset facts on the existing AC_CHECK edge with explicit warmup/hold checks.

Acceptance gates for each candidate:

- Strict actual RTL simulation; all original control, physical drain, scratch corrupt/read-owner/boundary and canonical value/owner oracles remain enabled. New FIFO/preparation cases cover all occupied stages, stalls, simultaneous edges, stale tags, reset/abort and no-reset clean retry.
- Full tuple conservation and stable stalled outputs. FIFO occupancy stays 0..2; prepared read tuples belong to the exact segment/line/offset/epoch. No second owner can consume spare capacity before old physical debt drains.
- Original exact-cycle checkers remain frozen. Any intentional latency or counter-read change gets a separate declared contract and independent ordered value/owner model; do not broadly waive old differences.
- Compare decoded bytes, errors, owner order and counters at the declared fences, then rerun the exact complete composition. Count new bubbles and critical-path families, not just a single WNS figure.
- A later separately authorized native gate must show routed setup slack ≥0 at 8 ns, with hold/pulse/routing checks passing on the exact candidate. Resource use and fanout changes must be reported. A positive component result cannot certify the larger SHA/memory/publication parent.

## 3. Parent-budget workstream: overlapping eight-byte join

The selected live-parent evidence is receipt SHA `0a4b07a9509a89100764f8d9c791a63bac8b53a2b5a9b38cc1646060e69e8663`: fast first outer byte→validated commit 3,092,122 cycles; bounded stalled service 5,772,781. These are actual simulation counts under abstract memory/publication, not achieved physical-clock latency. The unchanged single-byte join's four-edge minimum service consumes at least 2,242,560 cycles for 560,640 canonical/HUD bytes. Its 17.94048-ms conversion assumes 125 MHz; it is a source-derived serialization floor, not a measured physical duration.

Build an optional eight-byte mode beside the unchanged byte mode:

1. Allocate exactly **three eight-byte payload slots**, each with bounded epoch/token/bank/base/length/mask/ordinal descriptors. Split row capture, physical offer/ACK ownership and ACK-retired hash delivery so they overlap. A wrapper that serially fills eight bytes, waits for ACK and then emits eight hash bytes is not the proposed optimization.
2. Initially permit at most one accepted physical row write outstanding. Keep the slot until its matching ACK, while another slot hashes and a third fills. This simplifies response ownership while still removing byte-level phase serialization. Record occupancy and each phase's stalls. If more outstanding rows later become necessary, add that as a separate bounded contract with an explicit retirement queue.
3. Feed the existing validator one byte per edge in exactly the original logical order, only after a matching successful physical ACK. Expand every transaction into its original bytes in the scoreboard; do not replace the required 560,640-byte correctness check with a 70,080-request count alone. Canonical and semantic HUD ordering and C2 domain inputs remain unchanged.
4. Retain a slot on wrong/stale/duplicate ACKs. Matching late/error responses drain accepted ownership after abort but cannot feed hashes or publish a bank. Reset revokes public work while preserving accepted physical debt. No slot/bank/epoch is reusable until its required drain and hash disposition complete.

Start with a directed row-join RTL model and the existing byte-mode oracle, then integrate the real validator/SHA and memory-owner model. Use both deterministic fast responses and bounded stalled/refresh-contention profiles. Cover every slot occupancy, output hash backpressure, row/plane boundaries, partial masks if supported, repeated payloads with distinct tags, all ACK fault classes, every abort/reset edge and same-object clean retries. Keep source snapshots, raw failures and exact full-frame roots/HUD digest/seal.

### Physical-memory contract must follow the abstraction

Eight-byte logical rows map to four x16 writes in the existing `row_to_sdram` path. The current controller uses single-word writes and burst8 reads; an eight-byte logical request is **not** an SDRAM BL8 write. Do not assume a one-edge row ACK. Retain the controller's `ctrl_idle`/recovery/refresh drain fence before acknowledging the row. Explicitly model any write acceptance gaps, open-row behavior and read contention.

The tile-major physical mapping makes adjacent tile rows contiguous; raster logical addresses are separated by 720/360 bytes. Verify alignment after mapping. A future 16-byte logical row pair needs eight accepted x16 writes and still needs the drain fence unless the physical controller itself changes. A new BL8-write controller would require a separate real bus protocol/timing/mask test; it is not part of this first eight-byte experiment.

The existing memory controller's 100 MHz domain and proposed 125 MHz codec domain are distinct. A CDC request/response bridge must carry the full owner tuple, provide finite backpressure, retain reset/drain semantics and be verified under independent clocks/phases. Reference reads and scanout compete for service; include their owners, returned data and arbitration bounds rather than giving candidate writes unlimited memory bandwidth. No accepted reference response may be mistaken for a candidate-write ACK.

### SHA and tail limits remain

The actual SHA byte core already has two buffer banks and overlaps absorption with compression. It uses 64 round edges plus launch/add, at least 66 edges per block. The selected frame has 628,815 message bytes, 10,298 compression blocks and 1,025 serialized jobs. Its source-derived compressor/initial-fill budget is at least 745,268 edges before exposed boundaries; widening the write join does not remove this work or prove that SHA meets 125 MHz.

The current scheduling also retains empty leaves/internal nodes, HUD and seal after canonical work. The source budget is roughly 145.7k ideal post-canonical edges, before remaining boundary effects. Therefore use **about 1.10M cycles to final canonical ACK/hash delivery** as a design budget and require full validated commit strictly below 1,250,000 cycles for an eventual under-10-ms claim at a genuinely achieved 125 MHz. These are acceptance targets, not promised results. Do not add decoder, memory and SHA totals as though they were fully serial; instrument their overlap and attribute exposed stalls.

The first row-join gate is exact full-parent functional equivalence plus demonstrated reduction of phase-induced stalls against byte mode on the same frame/service trace. Record whether the final commit target was met or missed. A missed target should identify join, memory, SHA or tail work from event counters before considering more SHA engines or incremental Merkle/HUD scheduling.

## 4. Make sustained simulation feasible before promising long campaigns

The selected refined main receipt SHA `5dfad8ef50f71ed3605712ef84a91eadb57892e6ffb4ee6b2e7186c88bb37ea5` records 1,731.78 seconds total wall time. Its approximately 28.28M-cycle component seeds took about 418/420 seconds; transport seeds took about 372/374 seconds. Roughly 67k complete-model cycles per wall second is an observed simulation profile, not FPGA throughput.

At that illustrative rate, simulating every 125 MHz clock edge for 60 seconds would require 7.5 billion cycles, about 31 wall hours. A 600-second run would require 75 billion cycles, about 13 wall days. These extrapolations are not executed campaigns and do not establish sustained-frame behavior. Gate the workload in stages: first one frame with all fences, then a short multi-frame ownership/reuse sequence, then **300 distinct scored frames** with bounded memory/transport service and exact publication accounting. Record actual simulated cycles and wall time at each stage; 300 decoded copies of one independent reset test are not a sustained ownership test.

Before a long duration campaign, either optimize the actual simulator or prove an event/idle-skip method against unskipped cycle simulation. Skipping is permissible only over intervals proven to have no state, timer, request/ACK, refresh, hash, CDC, watchdog or presentation consequence; conservation, timestamps and deadline accounting must agree on the same bounded comparison trace. Specify the skipped-state equivalence and test interruption at every pending event boundary. Statistical trace replay can explore service distributions, but must remain labeled a model and cannot replace actual RTL ownership/value proof. Physical long-running 30 fps remains a later hardware gate.

## 5. Integration and handoff sequence

1. Freeze the final V115 evidence and instrumentation/fence vocabulary. Prepare independent fixtures and fault schedules before implementing either candidate.
2. Run local timing-boundary simulation and local eight-byte-join simulation independently. Reject semantic failures locally; keep all original checks and failed attempts.
3. Integrate the passing row join with real validator/SHA and actual tagged memory/reference ownership; compare byte mode on identical inputs and response schedules. Keep the timing candidate separable so a parent-budget change cannot obscure its cause.
4. After both functional gates, simulate the exact combined full parent, including finite clock-domain/memory contention models. Publish a table of each fence, decoded bytes, transaction and expanded-byte totals, all ownership drains, hashes/seal, occupancy maxima and deadline misses.
5. Handoff source/recipes/tests and remaining physical dependencies. Request a distinct native budget only after measured simulation and source review justify it; do not extend V115's current six-measurement budget. Later route that exact larger parent and test sustained frame publication on hardware before claiming real 30 fps or validated decode latency.

Neither faster component logic nor a burst request counter proves network/capture/ESP32 throughput, SDRAM service, display refresh or game input latency. Those remain separately measured end-to-end constraints.

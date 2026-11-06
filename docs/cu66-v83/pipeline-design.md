# Application-specific causal execution: implementation plan

V83 develops a Python scheduling model for the application-specific operations
proposed in V82: COPY_REF, profile-defined CONST128, and the existing quantized
residual path. It changes neither decoded pixels nor residual entropy coding.
It does not implement a new encoder, transport serializer, ESP32 firmware, or
RTL decoder. The opt-in V82 content-tree profile remains an internal prototype;
old CU66/GU66 flat-SHA tags cannot silently acquire its new meaning.

The useful specialization is to avoid work that can be proven unnecessary, then
schedule the remaining reconstruction, storage and content validation causally.
The workload is an executable architecture experiment, rather than a physical
memory-controller or FPGA timing simulation.

## Buffer ownership and execution

Use groups of up to 16 consecutive tiles within a single canonical plane. The
last group in a plane may be shorter. Compare one group buffer with four group
buffers. Each slot holds at most 16 tiles of 64 bytes: 1,024 bytes per slot or
4,096 bytes for four slots. A fixed ring admits group `i` only after group
`i - N` releases its slot. It never reuses a group buffer merely because inverse
arithmetic has finished.

The 4 KiB figure is **group output payload capacity**, not total decoder storage.
Reference reads, inverse results, entropy coefficients, hash state, command
queues, response snapshots, maps and tree metadata require additional state.
The present DAG bounds admitted groups but does not model a byte-limited FIFO
for every intermediate edge. Hardware must bound those edges and propagate
backpressure; a dependency-correct list schedule does not prove their storage
requirements or maximum occupancy.

The existing [inverse RTL](../../fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv)
returns 64 signed 24-bit samples in its 1,536-bit `out_tile`, requiring 192 bytes
per retained inverse result. A conservative static workspace allocation for all
64 tiles admitted by four groups is therefore 64 bytes of reference plus 192
bytes of inverse result plus 64 bytes of output per tile: **20 KiB**, including
the 4 KiB output groups. This is a logical storage bound for those three edge
payloads, not a fitted memory estimate or a total-decoder bound. Coefficient and
dequant input retention, response/command FIFOs, SHA state and control still
need explicit admission/port contracts and accounting. Narrowing or saturating
the 24-bit residual earlier would require separate bit-exact range proof.

A practical first RTL experiment can use separate banks for the group slots.
Specify the port contract before selecting a memory primitive: reconstruction
writes group bytes, physical stores read those bytes, and leaf hashing also
reads them. Concurrent store and hash consumption needs arbitration, separate
read ports, or an explicit captured transfer buffer. Four hash lanes do not
create four free reads from a single memory. The Python model prices separate
resource lanes but does not establish payload RAM port bandwidth, physical
banking, BRAM rounding, timing closure, or fit.

For each tile:

1. Read its accepted residency certificate and determine its operation. Derive
   COPY_REF from decoded all-zero quantized coefficients under the zero-motion
   profile. Do not replace that derivation with an unverified host skip flag.
   CONST128 applies only to the profile-defined hidden tiles. Preserve native
   packet, canonical, HUD and display oracles during development.
2. Start residual inverse arithmetic independently of its reference fetch.
   Reconstruction waits for both, including actual returned reference bytes.
   V83 supplies a hypothetical inverse cost and a separate reconstruction cost;
   the latter defaults to 64 clocks per visible residual tile on one shared
   reconstruction resource. These parameters are sensitivity inputs, not
   measured hardware latency. COPY and CONST avoid that residual arithmetic.
3. Read a reference tile for a visible residual, a COPY that must be
   materialized into a nonresident candidate, or a resident COPY whose bytes
   are needed by a mixed dirty hash leaf. A resident COPY in an entirely reused
   leaf does not require its pixels solely for hashing.
4. If a physical store is required, clear the old candidate-bank certificate
   before the first store. The store waits for reconstructed or copied payload
   and for this invalidation. An abort must not restore a certificate naming
   bytes already overwritten. A certified resident-store elision must prove
   the candidate's existing bytes rather than synthesize a false write ACK.
5. Complete the tile's shadow-map entry only after its payload/store dependency
   finishes. A group releases only after its physical stores, shadow-map
   updates and recomputed leaf digest write finish. Reused leaves still wait
   for their required tile operations and stores.

The modeled inverse and reconstruction each have one shared lane. Hash lane
count, group count and memory-service assumptions are separate controls. This
permits controlled comparisons without interpreting more concurrency as a
measured speedup.

## Content-tree and candidate fences

Retain the V82 domain-separated compact SHA-256 messages and independently
rebuilt expected roots and seals. Leaf hashes depend on group payload readiness.
Internal-node jobs wait for required child digest production and metadata
reads. Dependencies of recomputed-but-equal subtrees remain live; digest equality
must not discard an unfinished content check.

The model keeps accepted and shadow digest trees. Every delta prices a complete
shadow-tree clone. Its selected implementation serially reads then writes each
32-byte digest using one 32-byte temporary buffer. It uses independent
32-bit tree-read and tree-write resources, but does not overlap consecutive
clone copies. Leaf/internal metadata reads and digest writes are additional
priced work. Residency maps have separate read and write resources; the map
write work includes both candidate invalidations and shadow entries. These are
explicit architectural port assumptions, rather than an inference that existing
on-chip memories provide them for free.

HUD writes are split into bounded eight-BL8 chunks. Each corresponding readback
waits for its write. The seal waits for all required HUD readback and content-root
dependencies. The native semantic HUD digest supplies the expected content;
V83 does not model the cost of computing that HUD digest on hardware. Candidate
completion also waits for every physical canonical store, group release and
shadow-map update. It is not the same event as leaf completion or root hashing.

An RTL implementation must then wait for real command and response drain,
validate the expected seal and HUD, and publish reference identity, root,
residency map and candidate bank together. Keep the displayed front bank and any
still-draining bank leased. Do not admit stores into a leased bank. Generation,
frame, reference, plane, tile and block identity must survive queues and delayed
responses. A late or stale response cannot complete a new generation.

A content SHA commitment is unkeyed; it does not authenticate the sender. New
profile negotiation and any transport authentication remain separate concerns.

## Interpreting the service sensitivities

The 18-clock read and 16-clock write inputs originate in the previous bridge's
successor-command interval accounting. V83 conservatively charges the complete
interval to every modeled BL8, including the final command. Consequently its
completion value is not the earlier metric that subtracts the last successor
interval, nor a measurement of the bridge's physical completion latency.

A proposed 12-clock read / 8-clock write configuration is an unqualified
architecture sensitivity. It requires a changed controller/bridge and renewed
verification of command, data, turnaround, row and refresh timing. An eight-clock
payload service is an idealized bus payload bound, not evidence that every
read/write sequence can legally achieve it. Do not program hardware timing
registers from either sensitivity.

An optional periodic memory exclusion reserves clocks `[0, 2000)` in each
10,000-clock period. This is an illustrative 20% reservation with a fixed phase.
Memory tasks are nonpreemptive and must fit a contiguous free interval. It is
not a raster model, a display deadline guarantee, a refresh schedule, an SDRAM
bank/row model, or a worst-phase contention proof. Real LCD service and refresh
must be modeled and verified separately.

Other missing costs include real ingress and entropy timing, wire framing,
ESP32 receive/forward limits, payload RAM ports, intermediate FIFO backpressure,
physical timing/CDC and real error recovery. A modeled source finishing below a
budget does not close the sustained distinct-frame 30 fps or validated
under-10-ms FPGA decoding milestones.

## Staged RTL experiments before hardware handoff

1. **Operation and ownership interface.** Implement native-derived COPY/CONST
   classification, generation-tagged reference requests, group-slot ownership
   and candidate-store invalidation. Compare all canonical bytes and residency
   certificates with the independent native oracle. Test keys, cold deltas,
   mixed dirty leaves, clean reused leaves and short plane tails.
2. **Bound every streaming edge.** Select explicit reference, inverse and store
   FIFO capacities and payload-memory port arbitration. Instrument occupancy,
   backpressure and group-slot lifetime. Test one and four group slots with
   delayed reads/writes and independent hash stalls. Check that no buffer is
   overwritten or released before its last consumer completes.
3. **Commitment engine.** Validate compact leaf/node/seal vectors bit for bit,
   including recomputed-equal dependencies and HUD binding. Retain the full
   shadow clone as the initial control. Implement tree/map ports and measure
   actual metadata contention before optimizing clone representation.
4. **Controlled memory variants.** Keep the existing conservative service as a
   control. Add a bounded next-command queue or bridge/controller overlap as a
   separate variant. Compare all actual SDRAM commands and data at both tested
   SDRAM timing corners, with row changes, read/write turnarounds, refresh and
   continuous display traffic. Do not infer legality from the Python intervals.
5. **Transactional fault campaign.** Abort before/after certificate invalidation,
   during reads and stores, during hashing and before publication. Drain issued
   commands, retain the accepted root/reference/front image, and retry safely.
   Exercise reset, stale generations, changed-reference replay, lost ACK,
   duplicate commit and forged COPY. Rollback must never resurrect an invalid
   candidate certificate or publish partially written content.
6. **Whole-path qualification and integration.** Re-run native packet/canonical/
   HUD/raster scoreboards and actual controller tests. Define an explicit new
   wire-profile version, capability rejection/fallback and recovery handshake
   before Sunshine or ESP32 adoption. Account for actual packet bytes and
   receiver limits. Qualify sustained distinct sources and full validated
   latency with real display contention before claiming either milestone.

This advances an application-specific execution profile. It does not yet improve
wire bitrate or establish compression/quality superiority over HEVC or AV1.

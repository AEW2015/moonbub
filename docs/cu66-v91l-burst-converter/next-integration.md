# Next V91l work: one live physical-memory service

The direct-line consumer addresses local byte-handshake overhead. It does not
complete the native codec. Keep its static scalar/direct comparison as a frozen
component control while joining the existing live producer and validation path.
Do not infer full throughput by adding or subtracting isolated component times:
overlap, arbitration and changed refresh timing determine the real result.

## Starting source boundaries

| Existing qualified component | Starting source | Integration obligation |
|---|---|---|
| Live supported BR88 producer / row writer | [cs88_rows_v91l.sv](../../fpga/experiments/cu66-v91l-rows/cs88_rows_v91l.sv), [row-write/hash join](../../fpga/experiments/cu66-v91l-rows/cu66_row_write_hash_join_v91l.sv) | Connect actual eight-byte candidate requests and matching ACKs; only ACK-backed bytes continue to hashing. |
| Tiled physical row bridge | [tiled row_to_sdram.sv](../../fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv) | Preserve canonical-to-8×8-tile address mapping and linear HUD region, while using the qualified controller's real command service. |
| Burst read and retention | [bl8_read_bridge.sv](../../fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv), [tile_rowpair_reader.sv](../../fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv) | Preserve logical line tickets/epochs/generations, retained-byte validity, physical eight-word capture and drain. |
| Direct-line base RGB | [canonical_rgb565_tiled.sv](../../fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_tiled.sv) | Retain native arithmetic and tagged descriptor lifetime through final consumer closure. |
| Controller / functional pin control | [controller](../../fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv), [pin model](../../fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv) | One command/response ownership boundary for all clients, with actual timing rather than separate logical actors. |

The linear writepipe bridge and tiled writer have the same module name but
different address semantics. Select exactly one intended source explicitly in
the build manifest; a linear producer wired directly to the tiled reader is
incorrect. First check each physical write/read address against the same
independent canonical layout oracle. The existing partial integrations are
controls for this work, not an already connected complete top.

## Freeze the service boundary before connecting clients

Use the unchanged physical controller and qualified read/write bridges. Define
one arbiter-facing descriptor with operation, bank, epoch, generation, ticket,
address, payload and byte-mask intent. Define each bridge's command acceptance,
physical ownership, completion and error events. There must be one owner for
each accepted controller command and one place to correlate its response.
An arbiter grant is not a physical ACK. Drain accepted BL8 words, writes and idle
fences before changing owner, retrying, publishing or reusing a bank.

Start conservatively with one active bridge transaction at a time: a BL8 read
or one logical eight-byte row write. Preserve the qualified writer's bounded
group of up to four accepted x16 writes and drain the entire group before
switching bridge owners. Count individual physical command acceptances
separately from logical rows. Retain
candidate row writes, accepted-reference reads, scratch reads, validation/hash
reads and RGB/display reads as distinct observable clients. Charge actual
read/write turnarounds, refresh, row misses and finite response backpressure.
Preserve logical tags through every physical translation. Do not replace a
remaining client with free, zero-time software memory to report a full join.

The current controller has single-word writes and lacks byte enables at its
request interface. Use the qualified aligned full-word path where possible.
For a partial word, implement and qualify a real mask/RMW contract before using
it: preserve the untouched byte, serialize competing access, charge its reads
and writes and retain ownership until ACK. Unsupported writes must be rejected,
not silently widened to an all-byte write.

## Integration order and acceptance evidence

1. Connect the live supported BR88 key/delta producer to physical candidate
   writes. Compare every ACK-backed byte against the qualified live control.
   Verify that the delta reads the actual accepted key bank and the captured
   registered quantizer snapshot, with no canonical preload substitution.
2. Move reference/scratch and C2/HUD/seal hashing reads to the same arbiter.
   Check actual native content hashes and atomic publication. Reject malformed
   ownership without issuing physical work; test reset/cancel before command
   acceptance, during transfers, during refresh and while responses are held.
3. Add the qualified direct-line RGB consumer and continuous display service.
   Define deadlines, bank roles and leases for accepted reference, unpublished
   candidate and still-presented frame. A bank cannot be overwritten while
   either validation/reference or scanout still owns it. A late candidate must
   retain/repeat the previous valid presentation under a documented policy.
4. Replace the native C++ semantic HUD endpoint with exact bounded RTL decode
   and overlay before claiming a complete RTL path. Resolve mixed entropy with
   an implemented decoder or a negotiated, tested sender fallback.
5. Run V91m with fixed 30-Hz releases, distinct frame IDs, real finite ingress,
   all clients active and queue high-water/latency distributions. Report
   packet-complete → validated publication separately from RGB conversion,
   display refresh and end-to-end capture/network latency.

Begin with the two native key/delta sources for causal debugging, then extend
to the fixed gameplay corpus, cold starts, motion/hard frames, failures and
long runs. An unchanged frame repeated in a fast loop is not distinct-frame
throughput. ESP32 Wi-Fi/QSPI, firmware copies/DMA, audio/UI/input and retries
must eventually be measured or explicitly bounded. A Python transport budget
does not establish actual ESP32 timing.

## Keep physical and product milestones explicit

The current read probe adds a combinational 128-bit byte-select path. During
V100–V110, inspect its real 7-series netlist, placement and worst paths along
with the whole design's BRAM ports, fanout and control sets. Compare a registered
variant only if path evidence justifies it, and rerun the same byte/RGB/abort
tests with its real extra latency. Zero additional RTL payload bytes is not
proof of unchanged routed area or frequency. Do not increase all domain clocks
to convert simulation counts into an achieved frequency.

After routed fit/timing and proper I/O/CDC constraints, hardware qualification
still requires 60 seconds then 600 seconds of 30 distinct frames/s. The following
goal is every complete validated-decode sample strictly below 10 ms, including
entropy, transform/reconstruction, all memory waits, integrity/HUD checks and
safe publication. An isolated reader below 10 ms, or base RGB below 33.33 ms at
an assumed clock, passes neither product gate.

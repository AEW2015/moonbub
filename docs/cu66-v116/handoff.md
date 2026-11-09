# V116 integration boundaries

The study branch keeps the packet format and ESP32-to-FPGA transport unchanged.
Composition A's two decoder-body source replacements are the Rice parser under
`fpga/experiments/cu66-v116-rice` and admission under
`fpga/experiments/cu66-v116-admission`. Use the complete selected 18-source map
in the spatial receipt; do not combine files by version-number guesswork.
Rice and admission add no public cycles and preserve the frozen malformed,
cancel, stalled-output and invalid-output behavior in paired simulation.

Composition B additionally selects the scratch/caller pair under
`fpga/experiments/cu66-v116b-control` and the coefficient boundary under
`fpga/experiments/cu66-v116b-domain`. The pair factors the exact owned abort
target; the coefficient boundary derives the domain flag from its already-held
payload. Composition C replaces only B's scratch with
`fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv`. Two private
speculative payload banks isolate bulk data capture from the cancellation cone,
while publishing the single logical pending tuple on its original edge.
Its focused generic and actual-caller tests compare every old pending-field
view, including reset/error/stall edges. These are separate source compositions;
use their own source-bound receipts and timing outcomes. No packet revision,
additional logical queue capacity, or ESP32 firmware change is required.
The final C source is a development handoff: its decoder-body route still
fails 125 MHz setup at −1.847 ns. A's measured 100 MHz control also fails.
Neither source is presented as a clock-qualified production parent. Use the
remaining routed source cause and the full memory/CDC/display integration
gates before making a board timing or sustained-frame-rate claim.

The optional memory/hash change is internal to the FPGA. The three-slot join
under `fpga/experiments/cu66-v116-rowjoin` keeps the existing eight-byte row
interface: 64-bit little-endian payload, `req_bytes=8`, and complete
`epoch/token/bank/address` response ownership. It has three eight-byte slots,
one accepted physical request at a time, and ordered one-byte hash output.
A successful matching ACK is mandatory before any byte of that row is hashed.
Wrong ACKs retain physical debt; cancellation revokes public work and retains
accepted debt until its matching response. Keep cold power-reset quiescence
separate from warm cancellation. Partial rows are not supported.

The V116 LIVE wrapper supports `ROW_WRITES=0` for the frozen byte join and
`ROW_WRITES=1` for the three-slot row join. It normalizes the candidate request
bus to 64 bits plus byte count, retains registered local producer-fault
cancellation, and exposes observation-only slot states for the test bench.
C2, SHA, semantic HUD commitments, and publication RTL are unchanged; the
semantic HUD decoder remains software in this partition.

An eight-byte request needs four x16 data transfers in the current memory
architecture. The existing row-to-SDRAM adapter is a useful interface starting
point, but the integrated physical controller, tile-major address mapping,
refresh/recovery drain, arbitration and clock-domain crossing still need their
own tests. The current LIVE test charges data transfers plus explicit overhead;
it does not simulate SDRAM pins or prove a burst-write controller.

Read `README.md`, the selected receipts, and the independent audits together.
Decoder-body OOC timing covers neither the new join nor SHA, physical memory,
transport/CDC, scanout or board I/O. A positive decoder-body clock result must
not be copied into a full-parent latency claim. The new test records actual
accepted-byte, successful ACK, hash, root/HUD/seal, commit and abstract
presentation fences. Its single keyframe and no-reset retries do not establish
continuous distinct-frame presentation at 30 fps.

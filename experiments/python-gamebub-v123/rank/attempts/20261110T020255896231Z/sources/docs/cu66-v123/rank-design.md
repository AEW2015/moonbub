# V123 APPEND rank threshold mask

This experiment changes only the scratch selected by frozen V122,
`fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv`, SHA-256
`49a1731b2259dc089ca8d5e24b17e162b8c7bbd94c983cea938a793d3fdbda72`.
All other V122 origins, including V122 admission and the V121 refill queue,
remain frozen. The source derivation is reversible; the original interface,
state transitions, error ordering and every original assertion block remain.

The V122 125 MHz routed setup report at
`/home/lori/gamebub-build/cu66-v69/v122-bounds-125-20261110T011151964670Z-88dca6/results/route-setup-paths.rpt`
reports ingress `raw_mode_reg` to scratch `state_reg[0]/D` as its global worst
path: WNS -1.949 ns, data delay 9.896 ns, logic 3.361 ns, route 6.535 ns,
18 levels with three CARRY4 and twelve LUT6 cells. The reported cone passes
through producer geometry selection, sparse input ordering and scratch state
control. Scratch ready itself remains the simple INGEST/cancel predicate.
This experiment targets only the sparse rank/order portion; a fresh route is
required to establish its physical effect.

The old sparse order is the full32 comparison
`{10'd0,coef_block,zigzag(coef_index)} <= previous_position`.
The exact decomposition is:

```text
previous_position[31:22] != 0
OR coef_block < previous_position[21:6]
OR (coef_block == previous_position[21:6]
    AND zigzag(coef_index) <= previous_position[5:0])
```

The live high-ten and block-sixteen fields preserve all generic uint32 previous
positions, including values outside naturally produced 22-bit positions.
The last rank relation is prepared as `rank_threshold_mask[63:0]`: bit k is
`zigzag(k) <= pending_position[5:0]`. The mask is captured inside the original
APPEND case on precisely the same edge and under the same outer response/cancel
priority as `previous_position <= pending_position`. No new phase, owner slot,
acceptance edge, tuple latency or payload reset is introduced. The declared
natural public cycle delta is zero.

Only the existing sparse order subpredicate changes. Coefficient epoch, band,
block bound, signed16 range, zero, count, raster/DC validity, and all eight
phase encodings retain their literal old expressions. Error 2 versus 3,
physical response error/debt/drain priority, speculative record-bank writes and
view selection, packed bytes and memory handshakes remain unchanged.

The 64 new payload bits have no reset. `previous_valid` owns their use.
Verification-only valid/epoch/phase/threshold certificates bind each actual
sparse consume to an APPEND capture. The certificate caches only the low6 rank
threshold, because all other full32 order fields are still live. Literal full32
ordering and all64 mask bits are independently asserted at each owned consume.
Reset/matching abort and phase/begin retirement clear certificate validity;
foreign abort preserves the original normal behavior. Every pre-existing
assertion block remains byte-exact, including the original scalar phase and
input_bad references and exact speculative-bank shadow checks.

Focused verification derives reversibly from every V119 scratch generic and
actual-caller test. The reference is the selected V122 scratch, with all other
caller sources bound to the frozen V122 composition. Strict Verilator warnings,
assertions and C++ `-Wall -Wextra -Werror` remain enabled. All inherited generic
abort/debt, corrupt response, tile, write slot, full16 coefficient, selected AC,
full32 format and natural caller checks remain mandatory.

The inherited arbitrary previous32 fixtures receive a declared prepared-domain
adapter. A real accepted RAW-format coefficient first creates the desired low6
threshold, and a real APPEND clocks the mask. The inherited fixture then binds
its full32 previous_position while preserving those low6 bits. This does not
claim that injected high bits are naturally emitted by 16-bit block inputs.
No new mask or owner bit is forced, no pair comparison is skipped, and added
fixture clocks are counted separately from natural packet latency.

Each of two generic seeds adds 106,496 full32 cases: every raster index, every
rank threshold, all eight phases, below/equal/above block relationships, high32
previous-position aliases, and 8,192 independent full32 random cases. Another
7,680 prepared APPEND contexts cross all phases/thresholds with reset, matching
and foreign abort, response/debt/owner/error overlap and clean retry. Matching
response errors without a prefetch/write owner deliberately retain the old
case-write behavior; the test never replaces that priority with a blanket
`!response_failure` gate. The unchanged inherited natural transactions retain
their complete physical request/response debt checks and packed-byte oracles.

The source is a single module; `packaging.json` records one lossless whole-file
fragment with no split. `edit-recipes.json` records production, module-name
adapters, unchanged fixtures and the additive prepared-domain adapter.
All focused inputs and this document are frozen before each execution attempt.
Finite focused simulation does not establish full-parent qualification or
routed timing closure; those remain separate parent-owned gates.

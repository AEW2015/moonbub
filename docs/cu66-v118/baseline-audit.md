# V118 baseline audit

This is an inventory of the frozen V117 reference and the evidence required to
evaluate the bounded V118 timing hypotheses. It does not authorize source
changes, builds, or native runs. V117 source remains the independent baseline.

## Source-bound reference

The source18alias contract is derived by `scripts/cu66-v117/spatial_c.py`
`prepare()`, not by directory enumeration. It starts with
`control['source_order']['rtl_read_order_aliases']` followed by the `.svh`
entries in `control['source_origins']`; the runner asserts 18 distinct aliases,
checks each origin path and SHA256, and applies exactly eight named overrides.
The candidate is V117 C (`experiments/python-gamebub-v117/repair-study/spatial`),
with V117 B's complete canonical simulation records/events/canonical bytes and
focused A/C module receipts serving as independent references. The generated
source contract and a future audit should preserve alias, source path, and
digest together; filenames alone are not identity.

The direct source recipe and exact hashes are in the V117 C terminal receipt
and its `source_sha256` map. `experiments/python-gamebub-v117/results.json`
contains the five native result records and the V117 open-milestone flags.
V117's native runs are all failures: A125 WNS −1.925 ns, B125 −2.202 ns,
C125 −1.679 ns, B100 −0.100 ns, C100 −0.317 ns. C125 has 17,428 setup
failures and C100 has 324; all five have zero hold/pulse failures and zero
routing errors. No clock is qualified. See [native results](../cu66-v117/native-results.md)
and [C mapping review](../cu66-v117/final-c-mapping.md) for complete metrics.

## Measured parent baseline and open milestones

The source-bound guarded B parent run measures the same `actual_001` recovery
fixture as the V116C/A control. Fast row completes in 1,126,533 cycles
(9.012264 ms if 125 MHz were achieved); stalled row is 1,553,878 cycles.
Fast/stalled byte profiles are 3,704,690 / 9,484,122 cycles. The interval is
final accepted outer byte through validated commit; presentation is a separate
fence. These are finite-model counts and conditional time conversions, not a
qualified clock or a general latency bound. V117 C's required parent proof is
an exact B schedule/event comparison; do not infer it from B or a component
simulation.

Still open: full-parent routed clock qualification, board-validated decode
under 10 ms, sustained distinct-frame hardware 30 fps, and production Sunshine /
ESP32 endpoint integration. Memory, CDC, display, board I/O, hardware ACK/debt,
and measured end-to-end behavior need their own evidence; OOC component timing
does not close them.

## Required evidence for proposed V118 residual pipeline and copy

For the residual acceptance/validation/commit pipeline, preserve the unchanged
arithmetic, accepted-event/commit ledger, II=1 when capacity permits, and
separate accepted and committed frontiers. Test complete tuple ownership and
expected-owner snapshot, malformed owner/token/plane/block/tile/qcell/scale/
index, validation and first-fault precedence, cancellation/reset, older fault
cancelling every younger acceptance, word63 readiness only after commit,
canonical publication fences, final drain, and exact physical response lease
ACK/debt behavior. Include independent schedule assertions and record actual
added startup/drain clocks and sustained throughput. Old-cycle equality must
not be asserted by suppressing clocks or weakening assertions.

For the proposed 16-byte ×4-edge copy, first retain all old atomic-copy
baseline cases. Add an independent whole-512-bit four-beat ledger proving each
lane's payload and owner metadata, engine-result/ID stability through beat 4,
READY only after all beats, ordered old-head emission while the inactive owner
fills, held-head stability, and final drain. Inject cancel/reset/error at
every beat boundary, including a physically sampled cancel-edge beat; prove
partial inactive data cannot become valid in a later token/frame or overwrite
an older READY head. Exercise fault priority and any physical kill-COPY
semantics. Use existing engine result/destination storage and report the actual
new beat/index/owner state and storage cost. No replicated FF/KEEP claim stands
in for ownership or routed evidence.

Keep these as separately attributable changes first. Source-bound focused and
whole-component/LIVE comparisons, exact bytes/hash/ACK/root/HUD/seal fences,
and fresh native positive repeats are gates. The V117 scheduling arithmetic
(39,912 raw projected edges combined; 83,555 after projection under an assumed
125 MHz 10 ms budget) is an estimate only, excludes stalls/fill/drain coupling,
and uses a clock that has not passed timing.

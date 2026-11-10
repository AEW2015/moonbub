# V123 focused rank-mask results

The selected focused qualification is **PASS**, with actual RTL execution.
The [selector](../../experiments/python-gamebub-v123/rank/results.json) names
[attempt 20261110T020438206695Z](../../experiments/python-gamebub-v123/rank/attempts/20261110T020438206695Z/receipt.json),
schema `v123-rank-owned-selected-record-exact-pair-v1`. It completed in
576.786 seconds. This note was written after that attempt; it is additional
reporting and changes no frozen focused input.

| Pinned artifact | SHA-256 |
| --- | --- |
| Selected V122 reference scratch, `fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv` | `49a1731b2259dc089ca8d5e24b17e162b8c7bbd94c983cea938a793d3fdbda72` |
| V123 production, `fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv` | `12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7` |
| Lossless whole-module `fpga/experiments/cu66-v123-rank/packaging.json` | `ef149a1613306fba510b6739ddd41a356ee3030d2dee35a7ae77e402609c713c` |
| Reversible production/fixture `fpga/experiments/cu66-v123-rank/edit-recipes.json` | `9063f2b9c915d430b5f8fcfa4887a49da84de7d937b68993890b25b31ae539e6` |
| Selected focused attempt `receipt.json` | `4753315a9dd045c77a348dfdc134404e6b7de1fa70f092385287d8833de886f4` |

Both generic seeds, **123301 and 123302**, and both actual-caller seeds,
**123401 and 123402**, passed. Generic and caller models were freshly compiled
with Verilator 5.020, `--assert -Wall --public-flat-rw` and C++
`-std=c++17 -O2 -Wall -Wextra -Werror`. Both compile logs had no Verilator
warnings. No warning severity or assertion was disabled or downgraded.
Containers were bounded to two CPUs and 8 GiB memory-plus-swap, with the frozen
host memory/pressure gates, per-command timeout and resource-stop watchdog.
The receipt retains commands, resource samples, source snapshots, compiled
source hashes, binary hashes, raw logs and compressed traces.

The reference is the frozen V122-selected scratch. The only production change
is the logical 64-bit `rank_threshold_mask`, captured on the original APPEND
edge from `pending_position[5:0]`, plus the equivalent sparse-order
decomposition. Live full32 high/block comparisons remain. Other V122 source
origins, including V122 admission and the V121 request queue, are recorded and
pinned. The focused caller elaborates the actual coefficient child pipeline;
this is separate from full-parent functional qualification.

The following retained generic results passed **per seed**. Counts describe
the individual suites and can overlap; they are not a sum of distinct packets.

| Retained oracle | Selected actual coverage per generic seed |
| --- | --- |
| Original prepare/corruption/owner tests | 72 full transactions; 128 corrupt responses; 4 read-owner cases; 12 pending cancellations; 12 stale pending-abort checks; 24 complete retries; 48 DC-line boundary transactions |
| Tile/slot raw-view and cancellation tests | 8 natural pending kills and 8 same-object full retries; 9 prepared storage-event and 5 outer-priority fixtures; 128 visible raw words compared per checked edge |
| Generic abort and physical debt | 90 prepared abort cases: 36 foreign and 54 current/reset; 24 unsolicited-response errors; 4 physical pending-abort cases |
| Coefficient/record shadow | 1,048,576 full16 coefficient-domain cases across all eight phases/raw formats; 983,031 invalid coefficient cases; 15 outer-priority contexts; one logical pending tuple and two physical speculative banks |
| Selected AC/cache/response tests | 10,496 cases, including all 8,192 signed13 values; 8,960 hits; 192 misses; 192 same-edge forwards; 768 kills; 192 each response errors, wrong owners and physical drains; all 16 offsets, three AC bands and four segments |
| Full32 format and output-plan tests | 489,216 full32 input cases with phase mask 255; 360 output-plan cases; 36 wrapped-next cases; 86 actual prefetch requests and 86 matching responses |

The additive `v123_rank_verdict` passed these checks **per generic seed**:

| New rank check | Actual coverage |
| --- | --- |
| Full32 order/input checks | 106,496 cases, including 8,192 deterministic random full32 cases; 4,109 good and 102,387 bad outcomes |
| Rank/index/phase domain | Every one of 64 raster indices, every one of 64 threshold ranks and all eight phase encodings; index and threshold masks both `0xffffffffffffffff`, phase mask 255 |
| Previous-position high bits | 57,348 cases for seed 123301; 57,349 for seed 123302 |
| APPEND response/cancel overlaps | 7,680 contexts: 2,560 captures and 5,120 killed/overridden captures; matching and foreign abort, reset, unsolicited/mismatched/matching responses, error/owner combinations and clean retries |
| Explicit fixture priming | 740,608 separately counted priming edges |
| Added public/error cycles and skipped pair edges | 0 / 0 / 0 |

The high-bit cases are **prepared-domain fixtures**, not naturally received
packets. A real accepted RAW-format coefficient and real APPEND first establish
the required low6 mask threshold. The inherited original full32 previous-position
fixture then supplies its high bits while retaining those low6 bits. No new
mask or verification-owner field is forced. Independent C++ scalar ordering
checks still compare the complete unsigned32 relation, and the original full32
phase/input references remain active. This separation permits generic high-bit
coverage without claiming those high bits are naturally produced by the
16-bit-block coefficient interface. The prepared APPEND response contexts also
remain distinct from natural physical request/debt transactions.

The actual caller uses naturally fed retained packet vectors, with the original
producer handshakes, memory service, packed-byte and dense-value oracles. **Each
caller seed** passed 20 packets under two configurations, producing 40 case
rows and 4,501,888 dense comparisons. It passed 56 directed checks, nine
synchronous-staging checks and 18 caller-prepare checks, with observed modeled
memory response delays from 1 to 501 cycles. The staging checks include
unaligned header/descriptor access, padding rejection before metadata, queued
and registered-read cancellation, restart, context failure, held sparse output
and RAW-pair hold until acceptance.

The V123 contract is **zero additional natural public cycles relative to
selected V122**. Ready/valid, state/error, memory events, tuples, packed bytes,
raw views and counters remain compared on every applicable pair edge. All
original assertion blocks and C++ `need`/`require` checks are retained through
reversible derivations. The historical V115 verdict deliberately still reports
`old_public_cycle_equivalence: false` and 807 private preparation edges for 269
descriptors. Those retained three-edges-per-descriptor fixture counters describe
an earlier architecture contract; they are not new V123 mask latency and are
not reclassified as V123 natural packet cycles.

The [first attempt](../../experiments/python-gamebub-v123/rank/attempts/20261110T020255896231Z/receipt.json)
is retained as **FAIL**, SHA-256
`0c7e577e6b17580160e03b053f0d092ea337e76f8b5eaa290d4a027633252a72`.
Its generic simulation stopped at the original reference assertion
`V118 prepared apply decision differs from current whole owner` in
`observed_original.sv:548`. The old deposited fixture initialized only the
candidate's AC lane caches because its historical reference predated those
caches. The selected V122 reference also owns them. The fix adds reversible
reference-side mirrors of that same already prepared AC-lane poststate in
`tb_slot.cpp` and `tb_ac_base.cpp`. It removes no checks, changes no production
RTL and forces no new rank predicate. Production, packaging and the frozen
rank design document are identical across the failed and selected attempts.

The separate [Python algebra result](../../experiments/python-gamebub-v123/python-model/rank-model.json)
is additional evidence, **not RTL proof**. Its source is
[`scripts/cu66-v123/rank_model.py`](../../scripts/cu66-v123/rank_model.py),
SHA-256 `733deef00828eb247bda2d252c4c112b59c659cdb94de50c35ad8d8eae68c256`;
the result hash is
`0eaea0aa8d0cc182cec3930233ba7fb9f89ac8331a9f9b606aaa7edcc0231cf2`.
It checks the raster/rank table against an independent V91c ordering formula,
1,536 block-boundary comparisons, 33,024 high-bit/equality comparisons and
100,000 deterministic random full32 comparisons, plus illustrative gating and
error examples. It does not compile or execute RTL, establish capture timing
or ownership, or replace the actual RTL response-priority checks. In
particular, its simplified response-failure gating is not evidence for the
RTL's matching-error/no-prefetch/no-write-owner fallthrough behavior; that
behavior remains covered by the retained and additive RTL tests.

The evidence establishes finite **two-state** generic-width and transaction
behavior for the enumerated cases. It does not exhaust the Cartesian domain
of all 2^32 previous positions, 2^16 blocks, ranks and control histories, and
does not claim four-state X/Z equivalence or formal proof. No focused result
establishes routed timing closure, CDC correctness, system throughput, frame
rate, physical memory performance or hardware qualification. Those require
their separate parent-owned implementation and system evidence.

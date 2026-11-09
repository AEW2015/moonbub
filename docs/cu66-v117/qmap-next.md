# Next qmap timing cut: stable header facts before Q_CHECK

This is a **read-only source study**, not implemented RTL, a new source candidate, a test result or timing credit. No tool instance, heavy job or simulation was launched for it. V117's frozen AC source, runner, proof inputs and admission baseline remain unchanged. An optional admission candidate needs an actual new A/B routed cause and a source experiment allowed by the V117 master policy before implementation.

## Evidence and exact source boundary

The frozen admission source is [V116 admission](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv), SHA256 `584491cbcd6168cb87ea1c0dafb59ae6c7fdaec2bcd22cf0210ad82085844ac7`.
V116 C's actual [routed report](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-setup-paths.rpt) contains 32 admission q-index reset paths among its capped 50-path report. That is a reported path family, not a count of all failing endpoints. Its worst q-index-family slack is −1.555 ns; the overall V116 C worst is the separate selected-AC path. The earlier synthesis qbuffer→q-index estimate must not be substituted for either routed result.

The relevant unchanged source edges are:

| Source state/edge | Actual behavior |
| --- | --- |
| [ACTIVE_SCAN terminal](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv#L539) | Completes `required_cells`; initializes q-index/CRC/trailer; enters Q_LOAD. |
| [Q_LOAD](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv#L546) | Requests packet byte `q_start+q_index`, returning through FETCH_REQ→FETCH_WAIT→Q_BYTE. |
| [Q_BYTE](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv#L547) | Writes `qbuffer[q_index[8:0]]`; updates CRC or trailer; final byte enters Q_CHECK. |
| [Q_CHECK](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv#L554) | Checks inner CRC first, then static header/length, method, required-cell count, and reuse restrictions. Only success initializes q-index=12/Q_RUN or enters PLANE_BEGIN. |

There is **no Q_CRC state** in this parser. `CRC_CHECK` is the earlier outer-packet CRC state. Inner qmap CRC is accumulated in Q_BYTE and compared in Q_CHECK.

The actual q-index reset-enable family includes the Q_CHECK chain:
`32'({qbuffer[8],qbuffer[9]})+16!=qmap_bytes`, along with preceding CRC and following header/method/required-cell conditions, before the constant q-index initialization. Delaying q-index, changing its width or bypassing validation changes the parser; it is not this proposed cut.

## Existing-edge opportunities

**Preferred starting point: Q_LOAD with q_index=12.** By this edge, Q_BYTE 11 has committed all qmap header bytes 0–11. None of those header bytes is written again during this qmap's remaining load/check/run interval. `qmap_bytes` was retained at HEADER_CHECK and `required_cells` finished at ACTIVE_SCAN; both are stable while the current packet is being parsed. On naturally reached parses the outer header already enforces `16<=qmap_bytes<=354`, so byte 12 is requested before the terminal Q_CHECK for both full-map method 2 and bodyless reuse method 6.

At that existing Q_LOAD edge, a small owned preparation tuple can capture the exact header predicates relevant to the newly measured path: magic/version/cell-count/length bad, method bad, required-count bad, and method-is-reuse. Reuse reference/length facts may be kept as separate held owner facts if needed. Q_CHECK would consume the tuple **on its original edge**, still evaluating CRC first and retaining the original ordered branches. A candidate should limit the tuple to the measured cause; the study does not authorize implementing all possible facts speculatively.

This edge needs no same-edge header-byte bypass. It must not capture `q_run_byte` from qbuffer[12]: byte 12 has **not** been fetched yet at Q_LOAD 12. The existing Q_CHECK assignment to q_run_byte and Q_FILL's next-run preparation remain unchanged. For method 6/16-byte qmaps, byte 12 is the first CRC trailer byte, not a run byte.

Other coherent opportunities, with different tradeoffs:

- **Q_BYTE 9:** the length pair becomes complete here, but qbuffer[9] still holds the previous value before the edge. A length predicate must use `{qbuffer[8],byte_value}`, explicitly zero-extended to 32 bits before adding 16. This can isolate the specific length cone, but cannot prepare required-cell bytes 10/11 yet.
- **Q_BYTE 11:** all header facts can be prepared with `{qbuffer[10],byte_value}` for required count; earlier bytes are already stable. This requires an explicit last-byte bypass and a proof for each captured fact.
- **Final Q_BYTE:** all header bytes are already stable in a naturally reached qmap, so header predicates can be captured without bypassing header RAM. However its enable `q_index==qmap_bytes-1` contains a full-width comparison; this may move a long path into the new payload CE. Fixed index 12 is the cleaner first acquisition boundary.
- **The FETCH_WAIT preceding the final Q_BYTE:** header predicates are also stable here. The final trailer byte is only being loaded into byte_value, so a precomputed CRC result would need the appropriate ram_data forwarding rather than stale byte_value. This extra coupling is unnecessary for the header-only hypothesis.

No new Q_CRC or validation state is necessary for these same-schedule options. If a coherent existing edge cannot support a proposed cut, adding a state must be declared and checked as a changed schedule; it cannot be hidden behind a delayed status flag.

## CRC-first and full-width arithmetic contract

Keep the original priority exactly:

1. `(~q_crc)!=q_trailer` → error 9.
2. Magic/version/cell-count/length mismatch → error 10.
3. Method not 2 or 6 → error 4.
4. Required-cell mismatch → error 11.
5. For method 6, key/missing reference/missing accepted qcache → error 7, then `qmap_bytes!=16` → error 10.
6. Otherwise retain the original plane/cursor/state or q-index/q-runs/q-run-byte writes on the same edge.

A prepared header error is data, not permission to reject before CRC completes. Leave the CRC comparison in Q_CHECK for a first header-only candidate. If a later actual route justifies moving it, the final Q_BYTE uses `~q_crc` versus `{q_trailer[23:0],byte_value}`: the final trailer byte is not in q_trailer until that edge. Comparing against the stale trailer would be wrong. Both CRC and error-priority equivalence then require new proofs.

`32'({qbuffer[8],qbuffer[9]})+16` is a 32-bit expression. Its 16-bit field can produce sums up to 65,551; narrowing the addition to 16 bits silently wraps near 65,535. Keep comparison against **all 32 qmap_bytes bits**, including synthetic high-bit/boundary fixtures. That particular zero-extended-field sum cannot overflow 32 bits. Other existing parser expressions do retain modulo-2^32 behavior: `q_start+q_index`, `qmap_bytes-1`, `qmap_bytes-4`, q-index increment, and Q_RUN run-count addition. Do not silently widen, narrow or rewrite their boundary semantics as part of this cut.

## Owner, cancellation and stability proof

The preparation belongs to retained `receipt_epoch`, not the changing external epoch input. It must name exactly the current qmap length/header fields and required-cell count. Keep all dependent flags in one coherent tuple or independently prove that they were captured for the same owner. The backing qbuffer is intentionally unreset and contains prior-packet data outside the bytes written by this owner.

Clear only the small preparation-valid control on reset/start/abort, and invalidate at the start of a new qmap acquisition. Existing payload storage need not acquire a global reset. Preserve the original reset/start/abort priority and same-edge public masks; a canceled synchronous packet-RAM request must not certify preparation for a replacement owner. Incoming cache writes and lookup/replay traffic must retain their original RAM-port priority and scale/mode-store behavior.

Assertions should compare prepared facts with literal old expressions **at every actual Q_CHECK consumption**, check epoch/length/required-count stability through acquisition and consumption, and prove acquisition was reached before consumption. No assumptions may force old backing bytes or accepted cache values into the new predicate. Arbitrary direct Q_CHECK backdoor fixtures must be replaced by declared coherent predecessor acquisition fixtures or explicitly scoped as unrelated; disabling the old pair checker is not acceptable.

## Reuse the strict admission proof; add focused boundaries

The existing [V116 admission runner](../../scripts/cu66-v116/admission/qualify.py) and immutable all-output probe provide the starting point. Preserve its 86 case profiles, 44 directed legacy checks, exact cycle/debug/counter/invalid-data comparisons, independent coordinate/quant/mode/scale replay, exhaustive prepared header/quant/cache-port suites, and the 25,344 full-width chunk boundaries plus 294 cancellation cases per seed. Keep all original assertions and strict compile flags; no skipped edges or warning downgrade.

Add independent bytewise/header math fixtures through actual Q_LOAD/Q_BYTE predecessor edges, including:

- Both valid methods, all header fields, every length-field byte boundary, `0xffef`, `0xfff0`, `0xffff`, sums 65,535–65,551, and qmap_bytes upper-bit values such as `0x00010000`, `0x80000010` and `0xffffffff`. Keep out-of-range synthetic predicate fixtures separate from naturally admitted packet claims, without clocking invalid RAM addresses.
- CRC-invalid plus every header/method/required/reuse fault combination; CRC-valid with overlapping faults to verify ordered errors. For real packet mutations, repair the outer CRC when intending to reach inner qmap rejection; otherwise error 3 must still win before this parser phase.
- All nonzero reset/start/abort combinations at header bytes 8–12, the chosen capture edge and its fetch phases, the last trailer byte and Q_CHECK; clean retry with a different header, qmap size, method and owner. Poison unaccepted epoch/header-side inputs while busy to prove retained ownership.
- Method 6 key/reference/cache/16-byte combinations; method 2's exact q-index=12 and first run-byte binding; malformed runs and terminal run count retain old behavior. Preserve accepted qcache/scale lookup and RAM replay checks around cancellation and FINISHED.
- Full-width counter wrap and q-index arithmetic in separate coherent prepared states, while original receipt timing and every public output remain exact.

## Lossless packaging and promotion gate

The frozen [packaging manifest](../../fpga/experiments/cu66-v116-admission/packaging.json) splits the complete production file at byte offsets 32,939 and 33,630 into the admission module and unchanged scale/mode helper modules. A new source cannot reuse those byte offsets or production/fragment hashes. Generate a **new** reversible source recipe and packaging manifest, prove concatenating fragments exactly reconstructs the complete new production bytes, and retain the unchanged helper module bytes. Do not edit the V116 manifest or any old archived snapshot.

Focused paired adapters must retain byte-exact old oracles; shared helper definitions may be removed from compile units only through the same lossless split proof. Full/peer/LIVE Verilator runners need the new candidate-specific packaging path and exact source order; silently leaving V116 fragment pins while selecting a new whole admission source is invalid. Fresh native runs still read the new complete selected source map, with the same clock/XDC and implementation method.

Promotion would require focused pairs and independent replay, fresh actual full decoder/transport/peer/LIVE qualification for the exact combined source map, then an eligible source-bound native trial and independent audits. This study alone supplies neither timing closure nor savings against the separate inverse/reconstruction cycle budget.

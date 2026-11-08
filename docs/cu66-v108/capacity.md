# V108 isolated capacity-control fallback

This candidate caches packet-only capacity bounds during existing header fetch clocks and compares them with the live full-width block count at the original scratch admission edge. It does not add a public cycle. It is a separate RTL fallback to the frozen-source placement/routing matrix. The focused actual RTL proof now passes; full-pixel integration and physical timing qualification remain open. Nothing here establishes 100 MHz, sustained hardware 30 fps, or under-10-ms board decoding.

## Source closure and scope

The four V107 bodies at commit `5187b56e9431f7a9e2874c10879e148ee5262d70` remain untouched. [prepare.py](../../scripts/cu66-v108/capacity/prepare.py) checks their exact hashes, applies an explicit reversible edit recipe, and writes only `fpga/experiments/cu66-v108-capacity/`.

| Body | V107 SHA-256 | V108 preparation SHA-256 |
| --- | --- | --- |
| synchronous ingress | `079381563a110d26886829c9ebb7b4655c232af6886a86d3f42b7cf4e94b2063` | `6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6` |
| ingress wrapper | `2c4a0ab1ba74b8ede056c6ce9958e6401f35beabcaaeeb681a90abe8947db5e4` | `9529b8a76b531d22f7d0a4498295153f8a397c004725787c34af9824ee84cfb1` |
| child pipeline | `a5d8a86d4bccca42377423abf8a318fc3acb8bfe9de38fcda9e5dd8eb46a5cc4` | `cb440ed9c12c6fa3eac579aea99f2c03716e33b97ce50822ab00b93de08a4360` |
| scratch | `f0bab2ba60d290405b9726f69fab3e6c2aabb7a474ef1255d3857293b977097f` | `5c4e6fc665c81920a2f907bb87d34e78f0eac22a114f75633a1f1dc2ddd33676` |

The wrapper and child forward three new internal sidebands: upper bound, lower bound and wrap flag. The child external interface is unchanged. Scratch replaces only the `plan_used>262144` capacity rejection predicate. Actual `plan_used`, start addresses and `used_bytes` capture/debug arithmetic remain original. Earlier stale-epoch, invalid-block, count-threshold and RAW-count checks retain their original order and values. The eight-edge V107 count-threshold DSP pipeline remains unchanged.

Reset clears valid and owner-live state. The private capacity payload and arithmetic stages have no reset. A simultaneous valid commit and flush can write an unowned payload, while validity clears immediately. Assertions require a complete matching owned tuple at metadata publication and stability while metadata is held. The legacy `SYNC_STAGING=0` branch computes the same bounds combinationally from its existing prefix; no legacy timing improvement is claimed.

## Exact finite-width predicate

For aligned unsigned 32-bit packet prefix `P` and full unsigned 17-bit live block count `b`, let `M=2^28`, `C=16384`, `a=(2+(P>>4)) mod M`, and `r=ceil(b/8)`. The unchanged original sparse capacity expression divided by sixteen is `(a+r) mod M`, with `0<=r<=C`.

```text
upper_b = ((C-a) mod 2^28) << 3
lower_b = ((~a) & (2^28-1)) << 3
wrap = a>C
sparse_capacity_bad = b>upper_b || (wrap && b<=lower_b)
raw_capacity_bad = b>2047
```

The lower comparison is intentionally inclusive in the rejection predicate. At `a=M-1`, zero blocks fail this particular capacity check and positive blocks pass it; other unchanged checks may reject the packet. At `P=0xffffffe0`, `a=0` and every unsigned 17-bit block value passes this particular capacity check. Such malformed-wrap behavior is retained rather than assuming valid packet sizes. Both cached bounds fit unsigned 32-bit: maximum `2^31-8`. Full unsigned 17-bit RAW arithmetic cannot overflow unsigned 32-bit, so its threshold is exact.

All prefix and aligned-count low nibbles are zero. The new arithmetic stages therefore operate directly on exact unsigned 28-bit units of sixteen; modulo 28-bit addition matches the old modulo 32-bit sum followed by a right shift. No padding bits, truncation assumptions or warning suppression stand in for this alignment proof.

## Existing-edge schedule

Count1 and count2 are already captured at header WAIT33 and WAIT37. Their aligned prefix sum is settled before WAIT41. At WAIT41 the current high byte of count3 must be forwarded: reading the old fetch-array high byte on that edge would use stale data.

| Relative edge | Exact new action | Earliest actual RAW fetch edge |
| --- | --- | --- |
| E0 / WAIT41 | Separately capture settled `P12>>4` and aligned count3 units, using the current response high byte | 83 |
| E1 | Add the captured operands modulo 28-bit | 84 |
| E2 | Add two header units modulo 28-bit | 85 |
| E3 | Compute upper/lower units and wrap flag | 86 |
| E4 / WAIT43 | Commit the complete tuple when its four-edge valid token arrives | 87 |
| E9 / HEADER | Existing metadata becomes visible with an owned tuple already settled | 92 |

This gives four complete clocks between the cache commit and earliest HEADER. It does not depend on future free-running prefix values after E0. Start, reset, abort, context failure and terminal context completion invalidate pending ownership; the old response-owner assertion and cancellation priority remain intact. The actual received RAW fixture must still take exactly 93 fetch clocks to first metadata.

## Preparation results and proof recipe

[preparation.json](../../experiments/python-gamebub-v108/capacity/preparation.json) records `PASS_PREPARATION_MODEL_NOT_RTL`:

- 2,097,152 full-unsigned 17-bit grid checks across normal and wrapped prefixes, 300,000 arbitrary full-unsigned 32-bit count triples, and all 131,072 RAW block values.
- Four seeds totaling 120,020 register-pipeline clocks, including flush/commit collisions and arbitrary initial private stage payload.
- 2,560 complete prepared headers, 2,048 interrupted headers/retries, 43,520 held-metadata edges and 512 flush/commit collisions. Last-word capture 83, bound commit 87 and earliest HEADER 92 remain exact.

These counts describe Python arithmetic/register/schedule models. They do not describe simulator cycles or formal-tool proof. The initial wider preparation and its report are retained under `capacity/preparation/001/`; the exact 28-bit preparation supersedes it before any RTL run.

[verification.py](../../scripts/cu66-v108/capacity/verification.py) prepares eight lossless whole-body control/candidate adapters. Every old public port, invalid/debug value, counter and original assertion remains in the comparison. A separate exact-production block extraction verifies the new arithmetic with an independent literal original-plan predicate. The full ingress fixture retains original context-owner and threshold checks; its manually injected high-count fixture has two quiet edges between count words so `P12` is coherent at E0, matching real fetched-header spacing. Real received RAW tests retain their exact schedule. Foreign valid-response cases run as six separate expected-original-assertion subprocesses; they are not treated as successful recovery tests.

[qualify.py](../../scripts/cu66-v108/capacity/qualify.py) defaults to source/recipe verification only. Its explicitly launched `--run` sequence is:

1. Strict Verilator production-block arithmetic, two seeds: complete unsigned 17-bit grids/RAW domain, 300,000 arbitrary tuples per seed, live blocks and flush collisions.
2. Strict complete synchronous ingress, two seeds: original 1,728 prepared cases, 128 high32 owners, original abort/retry/hold assertions, added E4 flush/retry case, and six separate expected owner-assertion rejections.
3. Strict complete four-body old/new pairing in `SYNC_STAGING=1` and 0, two seeds each, preserving original vectors, cycle checks, golden outputs and malformed/error contracts.

Uniform simulator C++ `-O1` changes compile cost only; it is used for control, candidate and independent oracle. Assertions, `-Wall`, C++ `-Wextra -Werror`, single-job compilation, output splitting, source snapshots and before/after hashes remain enabled. Each run is bounded inside a network-disabled, read-only-source tools container, 8 GiB RAM with no extra swap, 2 CPUs. Parent allocation permits at most two heavy jobs globally. No compile or simulation starts during source-only preparation.

After focused RTL PASS, the candidate must pass the parent canonical full-pixel regression and a new native implementation at unchanged 10-ns constraints, with complete setup/hold/pulse-width/DRC/route evidence. Actual plan data arithmetic can remain critical after this control cut. The RuntimeOptimized baseline's primary routed read-segment/cache mux is a separate cone and is deliberately not combined into this candidate, preserving causal measurement.

## Focused actual RTL result

[The source-pinned receipt](../../experiments/python-gamebub-v108/capacity/attempts/20261108T092432378016Z/results.json), SHA-256 `38426794992493fff85e5d0d91471584f16f277ea451fadbd9a46abdac28eebe`, records terminal `PASS` and `actual_RTL_run=true`. Verilator 5.020 ran every stage with strict assertions/warnings and the uniform compile flags above. All four production hashes in the source table remained unchanged before and after execution. No failed attempt or warning waiver was needed.

| Actual focused test | Seed 108201 | Seed 108202 |
| --- | ---: | ---: |
| exact extracted arithmetic clock edges | 2,558,339 | 2,558,339 |
| literal original-plan predicate checks | 5,116,667 | 5,116,667 |
| arithmetic flush/commit collisions | 234 | 210 |
| complete ingress clock edges | 24,849 | 24,849 |
| complete four-body SYNC1 public-cycle comparisons | 7,982,501 | 7,982,857 |
| complete four-body SYNC0 public-cycle comparisons | 7,945,620 | 7,945,533 |

Each arithmetic seed includes 2,097,152 unsigned 17-bit grid cases, all 131,072 RAW block values and 300,000 arbitrary prefix/count cases. Each ingress seed includes the original 1,728 prepared cases, 128 high32 metadata owners, eight received RAW packets, 2,312 held-metadata edges, three old threshold flush/retries and one capacity E4 flush/retry. The RAW first-metadata schedule remained exactly 93 clocks. Six foreign-owner negative cases separately exited 134 at the original stale-response assertion, with capture disabled before rejection; no post-rejection recovery is claimed for those subprocesses.

The four complete paired runs total 31,856,511 comparisons of every original public/invalid/debug/counter output, 9,326 metadata edges and 8,840 held-metadata edges. Each also retains 20 original vector packets across two configurations, 4,501,888 dense golden comparisons and the original malformed/error tests. SYNC1 retains 56 directed checks including nine synchronous staging checks; SYNC0 retains 47 directed checks. These are behavioral RTL results. Full custom top, native timing, board I/O and hardware performance remain separate gates.

The suite's container commands totaled 969.28 seconds. Minimum sampled host available RAM was 21,126,971,392 bytes and maximum full memory PSI avg10 was 0.0. The completed heavy lane was released to the parent full-pixel integration run; this agent starts no further heavy job.

## Read-only follow-up: m2 transform abort to output enable

This section maps the completed frozen-source `m2` result; it is not a capacity-candidate timing result. [m2's routed report](../../experiments/python-gamebub-v108/native/20261108T092652611829Z/reports/route-setup-paths.rpt) has WNS −2.038 ns from `transform/error_reg[0]` to `transform/inverse/out_tile_reg[1506]/CE`. Data delay is 11.749 ns: 2.006 ns logic and 9.743 ns route (82.926%), with twelve LUT levels. The final shared output enable has fanout 384. Setup remains open despite legal routing and clean hold/pulse width.

The report's netlist names cross hierarchy and can represent merged expressions; they do not prove one unique source expression. The following source connections explain the observed control dependency without guessing from names alone:

| Observed cone | Selected source behavior |
| --- | --- |
| transform error → base abort | [top control](../../fpga/experiments/cu66-v107-meta-flags/cs88_pipeline_v91k.sv:200) pulses `base_abort` for an unacknowledged inverse error and routes it to the coefficient producer |
| base abort → child scratch readiness → accepted start | [producer readiness](../../fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv:1046) includes child busy/drain and abort; [top accepted start](../../fpga/experiments/cu66-v107-meta-flags/cs88_pipeline_v91k.sv:195) combines base readiness, arithmetic busy and coefficient-token ownership |
| accepted start → inverse cancellation | [inverse_cancel](../../fpga/experiments/cu66-v107-meta-flags/cs88_pipeline_v91k.sv:201) suppresses stale coefficient/reconstruction cancellation on an accepted retry |
| inverse cancellation → IDCT abort | [inverse arithmetic ports](../../fpga/experiments/cu66-v107-meta-flags/cu66_inverse_stream_v91j.sv:982) pass `start||cancel||error!=0` to the IDCT |
| IDCT abort/state → output reset/write enable | [selected IDCT](../../fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv:147) clears the public 1536-bit output on reset/abort, clears it on an accepted invalid/zero tile, broadcasts DC results, and writes 384-bit column-pair groups during the final pass |

Each final-pass group covers sixteen 24-bit samples: all eight rows of column pair `2*group_index`/`2*group_index+1`. This matches the observed 384-endpoint shared enable. The public `out_tile` remains observable when invalid and during partial group updates. Removing its reset or allowing arbitrary private writes while leaving the existing unmasked output would violate the current contract.

Suggested narrow experiments, each isolated and requalified before physical comparison:

1. **Constant-index output words and local final-pass decode.** Express 64 fixed 24-bit output words with explicit reset/zero/DC/final-pass priority. Predecode the four column-pair groups at the preceding existing `SECOND_MUL` edge, with current `k/group_index` ownership checked before the consuming `SECOND_ACC` edge. Keep global abort immediate. This targets variable packed writes and the shared 384-endpoint enable without adding a public cycle. Synthesis may merge identical enables again, so only a new report establishes benefit.
2. **Separate arithmetic-abort factoring.** In the selected parent wiring, let `S=accepted_start`, `A=abort_packet`, `C=coefficient_error!=0`, `R=reconstruct_error!=0`, `E=inverse_error!=0`. The current arithmetic abort is `S || A || (!S && (C || R)) || E`, exactly equivalent to `S || A || C || R || E`. A dedicated arithmetic-only sideband could express that factor directly while keeping outer inverse cancellation/retry semantics unchanged. Replacing outer `inverse_cancel` with the broader expression would be wrong on a retry with a stale error. This algebra removes a redundant gate; it does not establish that the whole readiness detour disappears after mapping.
3. **Explicit zero visibility for private output payload, if the previous cuts are insufficient.** Keep public zeroing exact using owned zero/visibility flags, while physically storing output words without a global payload reset. A flag may expose a word only on the same edge that its complete replacement is written. Flags must also model accepted zero/bad tiles, DC broadcasts, all four partial groups, held output, reset/abort and retained previous-tile values before the first new group. Existing all-cycle `out_tile` comparisons must remain. Local flag replicas could reduce payload reset fanout, but output masking adds area and a data mux; this needs an independent invariant and new timing measurement, not an assumption that invalid output is ignored.

No error, cancellation or readiness path should receive a false-path/multicycle exception merely because it is control. Registering the cross-module abort by one cycle would change immediate suppression and can permit a stale publication unless the interface and owner protocol are explicitly redesigned and proved. The capacity candidate stays isolated from all three proposals.

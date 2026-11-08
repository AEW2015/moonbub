# V107 count-prefix unit qualification

This isolated candidate has passed actual unit qualification: complete four-body controller pairs, full-production ingress ownership probes, and extracted cache/math tests. [`results.json`](../../experiments/python-gamebub-v107/plan-prefix/results.json) is `PASS`, `actual_RTL_run: true`, selecting `attempts/20261108T064412631092Z/results.json`. A vendor trial remains conditional on recorded remaining routed failure and complete pixel-pipeline canonical qualification. Existing selected sources and historical receipts remain unchanged.

The [preparation model](../../experiments/python-gamebub-v107/plan-prefix/preparation.json) passes source-recipe reconstruction, 108,000 full-32-bit count triples, and a finite header/prefix schedule model. It is `actual_RTL_run: false`. These results establish a plausible implementation and mathematical invariant, not production timing, complete behavioral equivalence, or roadmap completion.

## Source closure and unchanged behavior

Four RTL files are required. The existing packet wrapper separates synchronous ingress from the child pipeline; adding only three files would leave a missing connection or require a synthesis hierarchy reference. The [four-file recipe](../../fpga/experiments/cu66-v107-plan-prefix/edit-recipe.json) reconstructs and reverses every complete body:

| Candidate file | Baseline SHA prefix | Candidate SHA prefix |
|---|---|---|
| `br88_packet_ingress_sync_v91h.sv` | guard `feeae3ffff6a` | `f7e05105dc7b` |
| `br88_packet_ingress_v91h.sv` | wrapper `1dece92fc047` | `83577ff72781` |
| `br88_pipeline_v91h.sv` | telemetry `c6f839570988` | `d00f774fd8c4` |
| `packed_scratch_v91g2.sv` | guard `2a468e5566d7` | `4d06f2c15b85` |

The files live under [`cu66-v107-plan-prefix/`](../../fpga/experiments/cu66-v107-plan-prefix/). Only three new internal 32-bit metadata fields are carried: aligned count1, the aligned count1+count2 prefix, and the aligned count1+count2+count3 prefix. External top/child pipeline ports, old public ingress metadata values, their update edge, debug values, error guards/priority, epoch checks, raw layout, and public cycle schedule remain in the recipe's original body. No production hierarchy reference is introduced.

Scratch retains live `plan_start1 = 32 + aligned(32'(begin_blocks)*2)`. It replaces exactly:

- start2's count-derived terms with `plan_start1 + begin_prefix1`;
- start3's count-derived terms with `plan_start1 + begin_prefix12`;
- only sparse used-size terms with `plan_start1 + begin_prefix123`.

The original raw `32 + 32'(begin_blocks)*128` branch and every full-width count/blocks/epoch/capacity check remain unchanged. Prefixes exclude block count and all context/epoch/error predicates. Changes in the current scratch block input therefore still affect the plan immediately; no early context-stability assumption is needed.

The wrapper forwards prefix ports in `SYNC_STAGING=1`. In `SYNC_STAGING=0`, it computes identical modulo-32 prefixes combinationally from the actual legacy `meta_count1..3` outputs. This preserves the legacy functional path while offering no legacy timing optimization.

## Exact count reads and ownership

Synchronous ingress originally reads little-endian header counts at `cached32(30)`, `cached32(34)`, `cached32(38)`, and commits `counts[1..3]` only on the existing HEADER edge. Reset/abort clear those public count registers; replacement start retains them until the next HEADER update. The candidate preserves these assignments. Later descriptor validation and metadata output read these same count registers, and scratch stores their unchanged full 32-bit values. No count register has a new write site.

A private aligned-count register captures at the validated **F_HEADER FETCH_WAIT** completion of byte 33, 37, or 41. It combines the current `ram_data` as the high byte with the three previously fetched lower bytes. Reading the old high byte from `fetch_bytes` would be wrong on that edge. Captures require the original effective cache-store eligibility: no reset/start/abort, no active context failure or done diversion, matching RAM epoch/address, and the actual response valid. Wrong-owner responses and context priority cannot populate the private cache as successful reads.

The private cache comprises five unreset 32-bit registers: three aligned counts, `prefix12`, and `prefix123`, **160 bits** total. Every clock updates the latter two from the previous registers. During cancellation or unowned stages they may process stale values; they have no public meaning until the same packet reaches METADATA.

After byte 41, existing F_HEADER byte reads 42–45 each require the REQ/WAIT progression before HEADER. Thus the newly captured final aligned count has at least the next fetch edge for the prefix sum to settle; the first two aligned counts/prefix12 were ready earlier. Even the shortest raw path reaches METADATA only after those four reads and HEADER. Sparse input also traverses four descriptor fetch/validation phases. Descriptor reads may overwrite `fetch_bytes`, but cannot change the count cache because the capture requires `fetch_kind==F_HEADER`.

In stalled METADATA, no new F_HEADER capture occurs; all prefix pipeline stages have already converged and remain stable. A failed, cancelled, or abandoned partial header owns no metadata. A successful retry must fetch its complete 46-byte header and replace all three aligned counts before it can expose METADATA. No epoch tag/reset is added to the private payload; existing ingress state and metadata validity own it. New prefix fields outside owned metadata are unspecified, while every existing public value remains subject to exact equality.

Simulation assertions are prepared for `meta_valid` count-prefix identity and held metadata stability. Scratch also asserts all three incoming prefix identities on a begin handshake. Prepared internal-state tests must initialize a consistent prefix owner; arbitrary stale sideband injection does not represent valid metadata.

## Mathematical and finite evidence

Define, in the ring of integers modulo 2^32,

`A(c) = ((4*c + 15) mod 2^32) & 0xfffffff0`.

This is the exact original `aligned(begin_count*4)`, including multiplication and rounding overflow. Prefixes are `A1`, `(A1+A2) mod 2^32`, and `(A1+A2+A3) mod 2^32`. Carry-save `sum3/4/5` and ordinary addition have identical modulo-32 results; associativity therefore permits the cached count terms with a live base. No width is reduced and no malformed high bits are declared irrelevant.

The independent Python model checks 8,000 Cartesian boundary triples and 100,000 seeded full-32-bit triples. It includes values near 2^30 multiplication wrap, signed boundaries, and top-of-range rounding wrap. The schedule model executes 328,360 edges, with 2,048 abandoned-header retries, rejected capture events, poisoned/stale prior header bytes, random full-32-bit replacement counts, and 34,816 held metadata edges. It confirms the modeled cache is correct before HEADER and stable through ownership. This is finite supplemental evidence; it is not exhaustive over all 2^96 count triples or actual RTL behavior.

## Actual ownership and paired qualification

The actual full-production synchronous ingress pair has passed seeds 108041 and 108042. Each checks all existing public ports, invalid data/debug/counters, and the actual private capture/prefix registers before and after every edge. The complete source bodies differ only by module renames in the verification adapters.

Per seed the actual probe passes 8,305 edges, 1,728 positive prepared capture/priority cases (192 each for matching response, valid-low foreign epoch noise, reset, replacement start, abort, reset+start+abort, context done, context error, and non-header response), 128 full-32-bit prepared metadata owners, four real interface-driven RAW packets, three abort/restart cases at actual header response bytes 33/37/41, and 2,244 held metadata edges. Every capture index sees independent poisoned-old-high-byte/current-byte forwarding tests and full-width boundary/random counts. Independent Python replay checks all 16,610 retained edge records and all three captured words plus the exact nonblocking prefix sums. Prepared states establish cache owners explicitly; high counts are not claimed reachable through valid encoded packets.

Six additional **expected negative** subprocesses inject a valid foreign epoch or address at each capture index. Their pre-edge log records capture disabled. The unchanged original `stale staging response` assertion rejects each with exit 134. These are preserved contract rejection results, not normal positive runs or evidence of post-rejection recovery. Matching and valid-low foreign-noise cases supply normal post-edge behavior checks. No assertion is disabled or waived.

Real RAW packets exercise the earliest metadata path: exactly 93 existing header-fetch/HEADER edges after packet reception. Metadata remains held for 17 edges while live external blocks/epoch/packet size change; the accepted packet owner and prefixes remain stable. Real aborts before captures 33, 37 and 41 suppress metadata, then a full real retry replaces the private cache before the next metadata offer.

The extracted actual SV cache/math probe also passes 108,000 full-width count triples. It copies the production forwarding/prefix block and original carry-save helpers, poisons old high bytes, checks all three current-byte forwards, varies live blocks, and checks held cache and exact plan results. Its role is distinct from the complete-controller probes.

Complete original/candidate **four-body** child pipelines pass both seeds in both configurations. Adapters change module/type names only. All 167 original top ports are wired explicitly; the comparison covers every existing public output, invalid payload, debug value, unpacked telemetry array, counter, and state output without validity masking. The original real-interface/golden memory bench retains all checks, with only pre/post comparison hooks and an extra verdict. The independent portable audit removes those exact hooks and recovers the original bench byte-for-byte.

| SYNC_STAGING | Seed | Public-cycle edges | Held metadata edges | Directed checks | Synchronous staging checks included |
|---|---:|---:|---:|---:|---:|
| 1 | 108041 | 7,983,723 | 1,678 | 56 | 9 |
| 1 | 108042 | 7,981,610 | 1,678 | 56 | 9 |
| 0 | 108041 | 7,946,405 | 2,742 | 47 | 0 |
| 0 | 108042 | 7,944,672 | 2,742 | 47 | 0 |

Each run checks all 20 inherited packet vectors under two memory profiles and 4,501,888 golden dense values. Memory response delays span 1–501 clocks. The four runs total **31,856,410** public controller cycles and **8,840** actual held-metadata edges. The synchronous staging obligations include queued/read-response aborts, reset and restart with a pending response, context-failure cancellation, partial descriptors, malformed padding, held sparse values, and held raw pairs. No historical obligation was removed for the new cache.

The [portable audit](../../experiments/python-gamebub-v107/plan-prefix/audit.json) passes `PASS_ACTUAL_CAPTURE_OWNERSHIP_AND_ALL_FOUR_BODY_PUBLIC_PAIRS`. It verifies frozen source and artifact hashes, reverses every production edit and all eight module/type adapters, reconstructs the exact original historical bench, independently replays both full-production capture traces, checks each priority mode's actual post-edge state/error and count, and binds all six expected assertion rejections. Actual math and controller proof scopes remain distinct.

The first compile attempt `20261108T063833408908Z` is retained as timeout exit 124 at 300 seconds while compiling the unchanged context's large generated geometry tables. No source warning or functional failure occurred. A separate bounded continuation validates the previous frozen sources, fixtures, generated C++/headers/Makefile/objects and completes the same generated build with one compiler. Subsequent complete-controller builds have a 600-second cap. Runs use an isolated existing Verilator tools image, 8 GiB/two CPU limits, and available-memory/PSI launch/live-stop gates; heavy steps run sequentially.

Complete pixel-pipeline canonical equality and new native mapping/place/route remain unperformed for this candidate. No timing gain, full parent 100 MHz closure, hardware frequency, or roadmap completion is claimed.

Lightweight preparation/audit commands:

```sh
python3 scripts/cu66-v107/plan_prefix.py
python3 scripts/cu66-v107/plan_prefix/qualify.py
```

The first audits prepared source and models. The second validates adapters and exits without launching tools. `qualify.py --run` requires a scheduled heavy-job slot. `python3 scripts/cu66-v107/plan_prefix/audit.py` checks retained evidence without compiling or launching FPGA tools.

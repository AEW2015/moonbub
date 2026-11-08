# V107 header sums captured during existing byte loads

The candidate targets the actual quant-aligned synthesized path from admission `header_reg[47][3]/C` to `bit_cache_reg[1]/R`: WNS−3.131 ns, data12.490 ns (4.555 logic /7.935 estimated routing),22 logic levels including8 CARRY4s, at unchanged10 ns. The actual report is `/home/lori/gamebub-build/cu66-v69/v107-quant-aligned-20261108T041620091920Z-79440d/results/synth-setup-paths.rpt`. Root reports the elastic control has the same synthesized endpoint. These are synthesis estimates, not routed qualification. The path passes the HEADER_CHECK error/acceptance chain into successful-header initialization of bit_cache.

Starting source is frozen V107 quant `58d0fcb876692c2ad38fa0585a5d2e13cd83079f64a84538f8de5a5c4d139d61`. Five private35-bit caches capture exact sums on already existing HEADER_BYTE edges:

| Header index consumed | Captured value |
| --- | --- |
|39 |128 + MODE32, forwarding current byte39 |
|43 | cached mode start + QMAP32, forwarding byte43 |
|47 |4 + HUD32, forwarding byte47 |
|51 | cached residual start + DATA32, forwarding byte51 |
|55 | cached residual end + cached HUD tail |

For each32-bit field's final byte, preceding bytes are already stored while the current byte_value has not yet reached header[] through its nonblocking write. The new expression forwards exactly that final byte. Index55 does not depend on the unrelated current byte; DATA was captured at51 and HUD at47. Fields36..51 are stable through the rest of header loading56..127.

HEADER_CHECK uses only cached35-bit packet-total equality against zero-extended size_bytes, and low32 cache projections for q_start/residual_start/residual_end. Every original full32 range guard, padding/header/identity/reference/key priority, output field, state transition, request/response schedule, counter, scale/cache collision rule and error value is retained. No public cycle or port is added. This is a register cut of the measured arithmetic chain, not a claim that merely narrowing a sum proves timing closure.

The sum is exact over the entire32-bit input domain: maximum `132 +4*(2^32−1) =2^34+128 <2^35`. Thus no intermediate or total wraps at35 bits. Original64-bit total comparison and cached35-bit comparison are equal for every size_bytes32. Low32 projections equal the original modular32-bit address expressions. Valid-length guards are not assumed for this identity; malformed and overflow inputs remain rejected with original priority.

Caches are intentionally unreset. They are consumed only at HEADER_CHECK after the complete sequential0..127 load; reset/start/abort bypasses the state case, and a subsequent complete load recaptures all fields. Non-synthesis assertions check all five full-width original identities whenever HEADER_CHECK is live and no reset/start/abort is asserted. No hardware validity flag, new error or prepared cache can affect public rejection priority. Prepared HEADER_CHECK tests explicitly initialize all cache invariants; they are separate semantic stress, not arbitrary-state reachability proof.

Candidate SHA-256 is `7a417f9a647e77571e6d31d6780412bc62dda4bdc1ef879017266694df9763a9`. The [exact recipe](../../fpga/experiments/cu66-v107-header/edit-recipe.json) reconstructs it against the frozen quant source. Both verification adapters strip exactly back to their entire production bodies; only observation ports and selected public-access comments are added. The probe compares all64 production ports'42 public outputs/counters every edge, common quant controller state and live header cache identities, with no cycle tolerance.

Independent [model evidence](../../experiments/python-gamebub-v107/header/model-results.json) passes299,792 full32 tuples (22 boundary values^4 plus65,536 seeded tuples),1,199,168 total-equality checks and5,995,840 byte-capture steps over random stale backing bytes. The full-domain width/modular argument is recorded separately from this sampled/boundary arithmetic campaign.

The prepared actual-RTL plan covers738,933 header edges per seed: every22^4 full32 boundary tuple,2,048 error-priority/snapshot combinations,2,048 actual128-byte capture sequences over stale header storage, all cancellation/start masks at HEADER_CHECK and all five capture edges. The inherited quant prepared suite adds348,673 edges per seed, with its now-quant baseline's real run-byte cache explicitly initialized when preparing Q_RUN. These prepared streams are not claimed as legal packet reachability. The independent public-interface packet suite retains its original corpus, coordinate/packet/scale/collision oracles and adds reset/abort/replacement recovery in HEADER_LOAD, HEADER_BYTE and HEADER_CHECK.

The explicit backend is historical Verilator, strict `-Wall --assert` and C++ `-Wall -Wextra -Werror`, finite compile/runtime/edge watchdogs, no warning suppression or assertion downgrade. ## Actual focused RTL result

**PASS**, seeds107701 and107702, first strict compile and both bounded runs. No source, checker, coverage-floor or warning-policy adjustment was needed. All64 ports/42 public outputs and counters compare exactly on every pre/post edge against the complete frozen quant production module. All five live cache assertions, the original quant/coordinate assertions and independent header-priority/address, packet, coordinate and scale oracles remain enabled.

| Campaign | Seed107701 | Seed107702 |
| --- | ---: | ---: |
| Public-interface packet edges |10,228,414 |10,228,230 |
| Independent header prepared edges |738,933 |738,933 |
| Retained quant prepared edges |348,673 |348,673 |
| Base packets (positive /negative) |86 (52 /34) |86 (52 /34) |
| Directed checks |44 |44 |
| Independent scale lookup checks |980,118 |980,122 |
| Independently replayed run /fill edges |3,100 /116,100 |3,100 /116,100 |

Total actual focused edges: **22,631,856**. Prepared tests explicitly initialize cache invariants when entering HEADER_CHECK; actual HEADER_BYTE capture streams and complete public-interface packet cases supply separate transition/reachability evidence. Reset/start/abort captures remain suppressed at all five update edges; complete positive packets recover after real HEADER_LOAD/BYTE/CHECK cancellation. There are no rejected or overwritten focused attempts.

The [selection](../../experiments/python-gamebub-v107/header/results.json) points to immutable [results](../../experiments/python-gamebub-v107/header/attempts/20261108T044158674756Z/results.json), SHA-256 `085fc5a2dde1890f8a22e093b424dd872aab39a4f76d2eced5cc01f5bc2cca28`. Adjacent snapshots retain both full production adapters, probe, bench, model, exact recipe, original corpus, compiler/tool/binary logs, full case verdicts and compressed traces. The [artifact audit](../../experiments/python-gamebub-v107/header/audit.json) verifies retained hashes, unchanged source inputs, all verdict/coverage counts and the full-width model result. Reproduce with `python3 scripts/cu66-v107/header/model.py`, `python3 scripts/cu66-v107/header/recipe.py`, serialized `python3 scripts/cu66-v107/header.py`, then `python3 scripts/cu66-v107/header/audit.py`.

Parent exact-cycle complete canonical comparison and matched fixed10 ns implementation remain separate required gates. Frozen Rice/quant/elastic/profiling evidence is unchanged.

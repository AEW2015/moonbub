# V108 IDCT output visibility and payload reset cut

This isolated candidate replaces resettable 1536-bit IDCT output storage with 64 private 24-bit payload words and 64 resettable written bits. The public 1536-bit `out_tile` still compares on every clock, including invalid output, partially updated tiles, reset/abort and output holds. The preparation model and focused complete-module RTL proof pass. Full-pipeline integration and native timing remain separate gates. Source and focused proof artifacts are frozen at PASS.

The measured motivation is frozen-source [m2](../../experiments/python-gamebub-v108/native/20261108T092652611829Z/reports/route-setup-paths.rpt): transform error to IDCT output CE, WNS −2.038 ns, 11.749-ns data path, 12 LUT levels and 82.926% routing delay. Its final enable drives 384 output bits. This source change targets that enable/reset distribution; it does not establish a timing gain.

## Exact source recipe

[prepare.py](../../scripts/cu66-v108/outtile/prepare.py) reads the actual selected V107 source [cu66_idct8x8.sv](../../fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv), SHA-256 `2495e1d5461771cd2d09ce8770ea7818f4f38703bf035bbed4049cdd4226d44f`. The new [candidate](../../fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv) is SHA-256 `3a30e2c527755ee5e34480274a7998795a773e23fef6cec8471fdd89c31a7808`. The checked [reversible edit recipe](../../fpga/experiments/cu66-v108-outtile/edit-recipe.json) leaves all original math, state, counters, readiness, error, token and input-source ownership behavior intact.

For each word `w`, the public result is `written[w] ? payload[w] : 0`. The 64 written bits follow exactly the original output storage operations:

| Original operation and priority | New visible-storage action |
| --- | --- |
| reset or abort, highest priority | clear every written bit |
| IDLE accepts a bad-domain or all-zero input tile | clear every written bit |
| DC_SECOND_ACC | set every written bit and replace every payload word with the DC result |
| SECOND_ACC with k=7 | set only the current sixteen-word column pair; replace every payload word in that pair |
| every other edge | retain written bits and visible previous words |

An accepted nonzero tile intentionally does **not** clear visibility. The old output retains the previous tile during the next tile's first pass and changes only as the next final-pass groups are written. The new mask retains that exact invalid/partial behavior.

Each payload register's enable uses local math state, `k` and its fixed column pair. It has no reset or abort input. Its fixed result lane is `(row<4 ? row : 7-row)+4*(col%2)`, and its group is `col/2`. A local write can occur on an abort/reset edge; the higher-priority written-bit clear hides it. No previously hidden word becomes visible without a same-edge complete payload replacement. A production assertion checks that every rising written bit has the matching preceding write event. All old operand ownership assertions remain.

## Visibility invariant and preparation evidence

The invariant relates the old public register to the new representation word by word:

```text
old_out[w] = written[w] ? private_payload[w] : 0
```

Assume the invariant before an edge. Reset/abort or accepted zero/bad input makes both visible representations zero, regardless of private writes. A DC edge writes all words identically and marks them written. A normal final-pass edge replaces the exact same sixteen words and marks precisely those words written. Other edges preserve visible state. A reset establishes the invariant with arbitrary private payload. Arbitrary changes to a hidden word preserve it. This is a source-level induction argument, not a formal-tool result.

[model.py](../../scripts/cu66-v108/outtile/model.py) uses a literal original lane-index update model and an independent fixed-row/column candidate model, with arbitrary residual symbols. [preparation.json](../../experiments/python-gamebub-v108/outtile/preparation.json) reports `PASS_PREPARATION_MODEL_NOT_RTL` across 105,536 control edges:

- Four full 16,384-case grids cover all sixteen state encodings, every 3-bit k and 2-bit group value, reset/abort and every input/zero/bad combination.
- Four 10,000-edge arbitrary sequences repeatedly poison hidden private words.
- 3,643 reset/abort edges coincide with a local private payload write. All public words remain zero after the higher-priority clear.
- 1,486,496 arbitrary hidden-word replacements remain invisible.

An initial source-preparation reverse-recipe assertion failed because a declaration-removal edit used an empty replacement string. Its source/script/error record is retained under [preparation/001](../../experiments/python-gamebub-v108/outtile/preparation/001/preparation-error.json). The recipe now includes nonempty surrounding context and reverses exactly. This was a source-generation error; no simulator ran.

## Prepared strict actual RTL proof

[verification.py](../../scripts/cu66-v108/outtile/verification.py) preserves complete original and candidate bodies, using module renames and observation-only ports. It retains the exact old probe comparison expression. Every original public IDCT port compares at pre-edge, post-edge and falling evaluation; the entire output tile is compared even when invalid. Existing math products, samples, basis, state/k/group and accepted source ownership checks remain unchanged.

The old 4,303-tile independent two-pass Q14 fixture remains unchanged, including its arbitrary AC, DC and malformed-domain tiles. The old 30 directed reset/abort cases cover all ten FSM states, output stalls, retry and 1,024 idle-noise clocks. New checks independently model all 64 written bits and inspect every public word each edge. Before clocking, the test poisons only private words whose written bit is zero; it never changes an exposed payload word. This forces stale private data to be arbitrary and catches an incorrect visibility rise or missing same-edge replacement through the unchanged old/new output comparison. Independent poison randomness does not consume the old stimulus RNG or change its seed sequence.

[qualify.py](../../scripts/cu66-v108/outtile/qualify.py) defaults to recipe/fixture verification only. An explicitly allocated `--run` will compile strict Verilator 5.020 with assertions, `-Wall`, public private-register access, output splitting, single-job compilation and uniform C++17 `-O1 -Wall -Wextra -Werror`. It will run seeds 108301/108302, retain complete command/source hashes and compressed raw traces, and independently replay all signed multiply products. Containers are capped at 8 GiB RAM with no additional swap, 2 CPUs and no network; source mounts are read-only. The parent must grant one of the globally limited heavy lanes before execution.

After focused PASS, the parent will test the exact capacity+outtile composite in the full canonical pixel pipeline before any new native implementation. Native timing must retain the unchanged 10-ns clock and complete setup/hold/pulse-width/DRC/route checks. Sixty-four mask registers and output masking add area and another data selection; a new physical report must determine whether the trade improves the actual limiting path. No hardware 30-fps or under-10-ms decoding claim follows from these preparation results.

## Actual complete-module RTL result

[The terminal focused receipt](../../experiments/python-gamebub-v108/outtile/attempts/20261108T095511806742Z/results.json), SHA-256 `f31dfef5f525fd750d593a85fd8644ff0bcbe82338a69c32d5f94ea3674c2af5`, records `PASS` and `actual_RTL_run=true`. The candidate remains exact SHA-256 `3a30e2c527755ee5e34480274a7998795a773e23fef6cec8471fdd89c31a7808`; every recorded source hash matches after execution. Strict assertions and warning checks passed without waivers or a failed simulator attempt.

| Actual test counter | Seed 108301 | Seed 108302 |
| --- | ---: | ---: |
| complete-module clock edges | 271,037 | 271,180 |
| original independent golden fixture tiles | 4,303 | 4,303 |
| original directed reset/abort cases | 30 | 30 |
| completed tiles including reset/retry cases | 4,333 | 4,333 |
| arbitrary hidden private-word poisons | 2,884,800 | 2,885,888 |
| all-cycle public-word visibility checks | 69,385,472 | 69,422,080 |
| newly visible words with complete replacement | 33,152 | 33,152 |
| kill/private-payload-write collisions | 3 | 3 |
| accepted input-source owner checks | 522,537 | 522,871 |
| independently replayed signed multiply edges | 122,024 | 122,024 |

Each seed visited every FSM state and every original reset/abort state target (`states=abort_state_mask=1023`), retained 1,024 idle-noise clocks and the original held-output/golden/domain-error checks. The complete output tile compares before and after every clock and at falling evaluation, including invalid and partially updated values. The new word visibility checker makes 138,807,552 total word comparisons; actual simulation injects 5,770,688 hidden-word poisons. Its poison RNG is separate from the old test RNG. Both raw signed-product traces replay independently and are retained as compressed artifacts.

The three actual kill/write collisions in each seed are the original DC_SECOND_ACC reset/abort tests. The all-state fixture reaches SECOND_ACC before its first k=7 write, so it does not separately target every final-pass write-boundary cancellation. The finite preparation grid independently covers all four k=7 groups and every kill combination, and ordinary RTL playback compares every partial group update. A future unchanged-source regression can strengthen the actual boundary coverage with twelve group-by-reset/abort cases; no such extra execution is claimed here.

Container command wall times totaled 18.01 seconds; minimum sampled available host RAM was 23,558,115,328 bytes and maximum full memory PSI avg10 was 0.0. The heavy lane was released to the parent exact composite canonical proof. This agent starts no further heavy job or source edit.

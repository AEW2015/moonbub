# V110 parallel PREFIX cut

The exact existing-edge candidate removes a redundant clamp from the Rice parser's parallel PREFIX take and quotient/suffix load expressions. It starts from the actual qualified V110 unmasked Rice body, SHA-256 `dfa58d806ce93ab273f0eb4a2d45b391198ab4bee9ce33aea324d5285d1cc5df`. Its candidate [body](../../fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv) is SHA-256 `c07d936e807a09ee332b5df4c3f743f88f284784fbcf1e704d1a8db770c33eac`; its [recipe](../../fpga/experiments/cu66-v110-prefix/edit-recipe.json) is exactly reversible. No old source or proof changes.

## Actual final-path motivation

READY+RICE final native receipt `experiments/python-gamebub-v110/native/20261108T141714174050Z/receipt.json` is negative: WNS −2.871 ns, TNS −10,185.816 ns, 16,322 setup-failing endpoints. The actual worst source is **cached_remaining[5]**, not a reservoir register. It ends at Rice quotient[3] CE with seventeen levels including three CARRY4s, 12.618 ns data delay: 3.186 ns logic and 9.432 ns routing (74.751%). The path report SHA-256 is `c4cbdb808d3d190df6a2a47fdcbe877658dbfc73a6f3e5673e6e794cd24ff65a`.

Fifteen of the reported fifty paths launch at cached remaining and reach quotient CE/D, suffix-left CE and state D. Other top-fifty families are reconstruction pending-fault to scratch state (nine), scratch read-segment to state (two), math-bank to dequant output CE (twenty-three) and ingress position to context block D (one). Fixing the Rice path alone does not establish whole-component closure.

The source dependency is `cached_remaining → window=min(remaining,15) → zeros=min(window,prefix_rank) → take/quotient/suffix decisions`. The routed optimized names traverse quotient/available aliases and three carries before the endpoint; their names do not uniquely identify each source expression. This candidate removes the window-to-zeros-clamp dependency from take and selected quotient/suffix payloads. Current can-step, tail/truncation and ownership guards still depend on window. CE delay improvement and the fate of the mapped carry chain require new measurement.

A serial-only direct-bit rewrite was rejected as a physical first choice: the actual child pipeline drives serial mode zero, which propagates through ingress/context to Rice. Such a generic rewrite is exact but may be dead in this native closure. The mapped name `serial_reg_2` is a LUT alias, not proof that a serial branch survives. A window register would put subtraction/take feedback into its own D path; no latency or feedback benefit is established here. AggressiveFanoutOpt is also not the strongest causal hypothesis for the worst Rice cone: most of its early nets have fanout one to four, with intermediate 76/50-load nets. The largest reset/cancellation nets appear in other timing families; cloning them does not remove the seventeen-level Rice logic dependency.

## Exact identities and original priority

Let R be prefix rank 0..15, W be window 0..15, Z=min(W,R) and F=(R<W). The original parallel take is:

```
Z==15 ? 15 : (F ? Z+1 : W)
```

The replacement is `F ? R+1 : W`. If F is true, Z=R<15. If Z=15, R=W=15, F is false and W=15. Otherwise both choose W when F is false. This identity holds for every combinational rank/window pair, including stalled/inactive cycles and arbitrary unowned prefix bits. Serial take remains one.

The original parallel quotient/suffix write is reached only after the prior truncation branch has not won: `found_one || window==15`. If found, Z=R; if W=15, rank cannot exceed W, so Z=R again. Consequently `quotient<=zeros` becomes `quotient<=5'(prefix_rank)` and its suffix escape choice tests `prefix_rank==15` instead of `zeros==15`. Those two RHS changes stay inside the **same original parallel, nontruncated write branch**. They are not used earlier during a partial/truncated prefix.

All reset/start, active, request acceptance, input-word acceptance, failure, empty-prefix, availability, truncation, output hold and response priorities remain unchanged. The original zeros, first-one, extracted/suffix expressions and all prior assertions remain present. New assertions check the take identity on every PREFIX edge and the rank/escape identity on every selected parallel write. No register, counter, invalid public value or public cycle is intentionally changed.

## Actual proof and limits

The [model](../../experiments/python-gamebub-v110/prefix/model.json) exhausts 33,280 rank/window/availability/serial rows and 6,610 selected parallel loads, with source hash/reverse-edit checks. This algebra is separate from RTL execution.

The complete old/new parser miter compares every public output, including invalid values and counters, and every stored register including the full raw reservoir. All inherited independent low-queue/parameter/malformed-word/reset/start/historical goldens remain intact. The additive inactive fixture now compares two unmasked bodies, so it additionally asserts their raw ranks equal; its unowned-bit coverage metric is bound to an independently calculated masked linear reference rather than expecting the original parser to be masked. All 8,320 inactive raw-bit cases and their existing public/raw-state comparisons remain active. This checker rebinding is explicitly recorded in `verification/fixture-adapter.json`.

Focused **actual RTL PASS**, first attempt `20261108T143620604828Z`, is selected in [results.json](../../experiments/python-gamebub-v110/prefix/results.json), SHA-256 `8db0ad05912a69dd5c97eb61f70f00b03659ac04963e5631b1bc52b27184e1e4`. The immutable attempt receipt SHA-256 is `0bcb63b471fe00594b696a526d71472b7cbee7db09ecd438db2b1c66979ec3ea`.

Seeds 111101/111102 each pass 6,096 parameter cases, 189,105 prepared clocks, 1,520 historical cases across eight configurations, 173,061 requests per configuration, 104 directed checks and 8,320 inactive cases. Historical execution covers 8,649,211/8,648,960 clocks. All four commands exited zero with strict Verilator 5.020 `--assert -Wall`, C++ warnings as errors, one compile job, two CPUs and 4 GiB memory/memory+swap; no resource or timeout stop occurred. Total wall time was 25.76 seconds, with no failed attempt in this namespace.

Source/proofs are frozen after PASS and current hashes match the passing receipt. Full canonical qualification of the complete composition, followed by a separately audited final adaptive native trial, remains required. The source cut and passing arithmetic/protocol tests do not predict a timing PASS or qualify parent/hardware throughput.

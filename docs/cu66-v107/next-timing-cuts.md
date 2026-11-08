# Read-only candidates after runtime route

This file records source reasoning and counterexamples only. No candidate RTL was edited, no new simulator/formal job ran, and no area or timing gain is established by these proposals. The completed runtime route determines priority; earlier synthesis and placement paths remain stage-specific evidence.

## Priority: actual routed scratch read-segment cone

The [runtime route](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/reports/route-setup-paths.rpt:15), SHA-256 `57f2154b9f65f8efd3066e42fe0354a8b533d40d3c5ba58f697967af8bc30689`, has WNS −2.333 ns. Its worst path is scratch `read_segment_reg[1]` → `state_reg[3]_rep/D`: 12.281 ns data, comprising 2.956 ns logic and 9.325 ns route; thirteen levels, including two CARRY4s. The path traverses a cache-select decode with fanout 165, selected head/word logic, cursor/order checks and state control. Nearby failing paths reach cursor reset/control and error registers. These are measured native netlist names; they are not proof of one unique RTL expression after optimization.

The frozen [scratch source](../../fpga/experiments/cu66-v107-count-threshold/packed_scratch_v91g2.sv:220), SHA `f0bab2ba60d290405b9726f69fab3e6c2aabb7a474ef1255d3857293b977097f`, selects `read_word` and predecoded `read_position` with `read_segment` and `read_address[3:0]`. In [AC_FETCH/AC_EXTRACT](../../fpga/experiments/cu66-v107-count-threshold/packed_scratch_v91g2.sv:679), it then checks live cache validity/tag, block range, band/rank, signed nonzero value bounds and order against the previous accepted head position before updating heads/cursors/state. Removing guards would change malformed-memory behavior.

A small zero-added-cycle proposal is to register a one-hot bank decode at the existing DC_FETCH/RAW_FETCH and AC_FETCH edges, alongside the unchanged binary selector. Per-bank word/position/tag selection could then use local decode bits instead of a binary decode shared across wide muxes. Every selector write site must update the redundant decode; only owned extraction states may rely on its initialization. Foreground/prefetch cache writes and all old public/debug/counter outputs must remain exact. A source rewrite alone may be optimized back into the same mux, or merely move fanout; physical benefit is unknown.

A stronger architectural cut would register an owned extracted word/position/check tuple before the live state decision. An existing-edge version needs explicit current-byte/line forwarding on memory responses and correct handling of **every** cache writer, including simultaneous background prefetch. Capturing old cache data while a same-edge writer updates the selected line would be wrong. A separate validation stage is easier to state but adds latency and requires a declared schedule plus an independent latency-aware model. It must not be hidden by weakening existing timing/counter checks.

Pure per-record value/rank checks can potentially be cached with a line, but the prior-head ordering comparison is live. Comparing against an adjacent word from the current line is not automatically equivalent to comparing the actual previously accepted head if line generations or memory contents differ. Cache/band/epoch ownership, malformed responses, hits/misses, refill forwarding, reset/cancel/retry, all sixteen byte offsets and full-width cursor/count domains need explicit proof. The current source's predecoded `cache_positions` already performs part of this work; the remaining measured mux/comparison/control chain must be remeasured rather than presumed fixed.

A bounded post-route physical optimization probe is a separate parent-authorized experiment. Its outcome must not be represented as an RTL implementation of these proposals.

## Rice availability mask: guarded-use proof

The earlier runtime **synthesis estimate** had `parser/available_reg[1]` → `parser/state_reg[0]/D`, −4.877 ns, nineteen levels. That is not the final route's worst path. The current [Rice body](../../fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv:54), SHA `f39c3f90d0242097ea3cd2693e6f4d99e58e33a0b49c644c720497f50e6777dc`, masks candidate bit `i` with `available>i` for i=0…14 before a balanced first-one tree. Bit 15 remains the zero sentinel.

Consider the proposed future change that removes only those availability masks. Let `a=available`, `w=window`, and let `r` be the first-one rank, or 15 if absent. Here `w` is always 0…15. This reasoning does **not** assume that unowned reservoir bits are zero:

- Nonserial PREFIX uses `needed=w`. A consuming step requires `can_step`, hence `a>=w`. Every bit with index less than `w` is valid in both versions. If a one exists in that window, the first rank is identical. If none exists, either tree may find a later one, but both produce `zeros=min(w,r)=w` and `found_one=false`. Therefore the consumed `take_bits`, quotient, suffix width, truncation decision and all corresponding register updates match.
- PREFIX with no consuming step may have different private rank/zeros/take/extraction values, but `needed` and `can_step` are unchanged. No parser consumption uses them. Word acceptance has higher priority and its readiness/bad-word checks do not depend on rank. Input-wait accounting also uses `needed/can_step`, not rank.
- Serial PREFIX always uses one-bit `take_bits`/extraction. Its updates use that extracted bit and quotient, not `zeros/found_one`; the nonserial truncation branch is explicitly gated off. Empty-prefix error priority remains unchanged.
- SUFFIX derives needed/take/extraction from suffix state alone. IDLE/RESPONSE have no rank-dependent updates. Existing suffix extraction assertions therefore remain applicable.

The only public combinational outputs are `in_ready`, `req_ready` and `reservoir_bits`; they do not use rank. Other public outputs, including invalid `out_value/out_consumed/out_error`, are registered. Reset/start, request and bad-word/sticky-failure priorities, output holds, symbol/bit/input/wait/stall counters and the reservoir's updates all remain subject to exact equality. This supplies a binary guarded-use induction argument from equal registered states; it is source reasoning, not a formal-tool or simulation result.

Two private counterexamples prevent an overbroad equivalence claim:

| Situation | Private old/new difference | Why public behavior can still match |
| --- | --- | --- |
| nonserial PREFIX, a=0,w=15, unowned MSB=1 | masked rank/zeros/take =15/15/15; unmasked =0/0/1 | can_step is false; no consumption |
| nonserial PREFIX, a=w=3, first three bits zero, unowned index5=1 | masked raw rank15; unmasked rank5 | both zeros3/found=false/take3; same truncation/consume result |

Even raw rank equality **on can_step** is too strong. A future checker may distinguish these private combinational observations, but must preserve every public/invalid output, counter, stored-state and normalized reservoir check. Used nonserial `zeros/found_one/take_bits` must match. It must retain original assertions, cover arbitrary unowned-bit patterns in an independently scoped combinational proof, and keep real complete-production restart, malformed-size/word, serial/nonserial, parameter, suffix and backpressure tests. No source or checker changed for this analysis.

## Coefficient CE prewrites: current debug-contract counterexample

The earlier **placement estimate** had scratch state → inverse coefficient-word CE, −1.954 ns, ten levels, with 9.969 ns estimated route delay. It is not the current route's primary cone.

The [inverse](../../fpga/experiments/cu66-v107-meta-flags/cu66_inverse_stream_v91j.sv:953), SHA `afc0ebb4f8ea72e5a07b4606f0d2f5fa4f6ab8ec858e4a35203a625f34541738`, exposes `dbg_coefficients=coefficients[math_bank]` without a validity mask. [Word writes](../../fpga/experiments/cu66-v107-meta-flags/cu66_inverse_stream_v91j.sv:966) require the original reset/start/cancel/error/running/input-fault/handshake and target-word guards. The storage has no reset, but that does not make arbitrary writes unobservable.

Counterexample to ignoring global kill for a locally matching prewrite:

1. Bank zero is FILL and is also `math_bank`; fill index is 17. The entire 108-bit owner tuple matches the staged token, whose index is 17 and value is 123. Stored word 17 currently contains 456.
2. Cancel is asserted on this edge. The original payload CE holds 456; the main FSM immediately frees owners and resets `math_bank` to zero.
3. A kill-ignoring prewrite stores 123. The unmasked public debug coefficient vector differs immediately, although no valid tile is published.

FREE-bank writes have a similar problem when reset/start selects that bank for the debug mux. Writing the currently unselected bank can become visible when `math_bank` later flips before that bank has been fully rewritten. Thus “all 64 words overwritten before publication” protects eventual arithmetic ownership, but is insufficient for the existing public-cycle contract. Local writable-bank/epoch/tile/expected-index matching alone does not prove idempotence. Static-domain errors, partial-done and token-exhaustion priorities also remain obligations.

A redundant global guard already implied by `in_ready` can be removed by exact Boolean equivalence, but synthesis may already perform that simplification. It supplies no measured timing gain. A truly idempotent write is safe only with a proved unchanged value/observation argument, not an assumption that the next word was previously written.

The user's delayed-status goal permits considering a **new versioned debug snapshot/valid API**: telemetry could have explicit ownership, epoch and delayed-snapshot semantics while operational kill/ready/error behavior remains immediate. A future production wrapper might leave unused legacy debug outputs unconnected with the core unchanged. That would require separate top/interface qualification. Neither changing observability nor disconnecting debug ports automatically removes functional payload CE dependencies; a complete owned-read, fault/cancel, held-token and frame-publication proof is still required. No present debug check is waived, and no such API or wrapper is implemented here.

## Secondary capacity-control model: packet bounds with live blocks

This additional result is **MODEL ONLY**, not RTL simulation, formal-tool proof, area/timing evidence or an achieved clock. It is relevant to Default8’s completed route: context_blocks[4] → scratch assembler reset/control, −3.137 ns slack, eighteen levels and 12.624 ns data (5.216 logic / 7.408 route). Its setup-report SHA is `c24795c4c3a3bdaf5d7bda5edfe179aab8ea364e3f6615eee3364b48441c03a2`. The runtime route’s measured read-segment cone remains the current primary priority for that flow.

For arbitrary aligned unsigned 32-bit packet prefix `P`, let `M=2^28`, `C=16384`, `a=(2+(P>>4)) mod M` and `r=ceil(b/8)`. Full unsigned 17-bit blocks give `0<=b<=131071` and `0<=r<=C`. The original sparse plan is `(32+align16(2*b)+P) mod 2^32`; dividing its multiple-of-sixteen result gives exactly `(a+r) mod M`. Capacity is therefore `(a+r) mod M <= C`.

If `a<=C`, no wrap can occur because `a+r<=2C<M`. Capacity requires `r<=C-a`, equivalent to `b<=8*(C-a)`. If `a>C`, only the wrapped window can pass: `M-a<=r<=M-a+C`, equivalent to the strict lower bound `b>8*(M-a-1)` and inclusive upper bound `b<=8*(M-a+C)`.

The literal finite-width simplification is:

```text
upper_b = ((C - a) mod 2^28) << 3
lower_b = ((~a) & (2^28 - 1)) << 3
wrap    = a > C
capacity_ok = (b <= upper_b) && (!wrap || (b > lower_b))
```

Both cached bounds fit unsigned 32 bits: their maximum is `2^31-8`. In the normal case the upper bound is at most 131072, which intentionally exceeds maximum b at a=0. For example `P=0xffffffe0` produces a=0 and all full-u17 block values satisfy this capacity predicate. At a=M−1, b=0 fails while every positive b passes the wrapped window; changing the strict lower comparison would be wrong. The raw expression `32+128*b` cannot overflow32 for full-u17 b, and its capacity predicate is exactly `b<=2047`.

The independent [model script](../../scripts/cu66-v107/capacity_model.py) compares the original modulo-32 plan, two-window derivation and simplified masked-bound form. [results.json](../../experiments/python-gamebub-v107/capacity-model/results.json) records 33,554,432 full-u17 edge-grid cases across 256 a values; 1,966,080 boundaries tied to each b's ceil(b/8); all 131,072 raw block values; 1,048,576 random arbitrary aligned prefixes; 1,048,576 random full-u32 count triples including their alignment/sum wrap; and 1,048,576 modeled existing error-priority combinations. It passed in 0.403 seconds with existing NumPy2.5.4. Initial diagnostic syntax and default-Python missing-NumPy failures are retained; neither ran a numeric model or RTL. Reproduce with `/home/lori/gamebub-streaming-prototype/.venv/bin/python scripts/cu66-v107/capacity_model.py`.

The proposed future change is only to precompute packet-owned control bounds during existing header cycles and compare them with **live** b at the original capacity-guard edge. It must leave actual `plan_used`, start addresses, used_bytes capture/debug, stale-epoch priority, block/count/raw checks and all later owner/error behavior unchanged. The arithmetic feeding a data capture can remain critical even if a control predicate is cheaper. A future implementation still needs real stage/owner/deadline assertions, all malformed-wrap and live-context domains, complete old/new public/debug/counter checks, canonical qualification and actual native reports. No production source was changed by this model.

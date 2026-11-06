# Packet prefix timing option, pending routed-path review

Read-only design proposal. No parser RTL, selected source, constraints, build or hardware change has been made. The immutable parser is `fpga/experiments/cu66-v69/packet/cu66_packet_control.sv`, SHA-256 `20d761a514073e8e5212eb70861f843441bc8d8f32b81bf7f02925cd202ae5a2`.

## Evidence boundary

DY01's intermediate post-route phys-opt messages mentioning `vector_end`/`plane_start` identify optimizer activity, not a final setup violation or a complete path. The older CU71 implementation06 has separately measured metadata/event-control cones; those belong to its frozen source selection and are not final DY71 v005 timing. Select this experiment only if the actual completed DY71 setup report identifies this parser prefix cone. Record its start/end pins, path delay, logic levels, fanout and source manifest first. This proposal does not predict a slack improvement.

## Actual parser arithmetic and priority

The controller finishes byte135 and pauses byte requests in CHECK_INNER. Its first predicate rejects header/profile/identity/geometry/reference errors with code6. Only if that predicate passes, its second predicate rejects qmap/vector grammar, plane length bounds or the complete inner-length equation with code7. On success, the same edge builds prefixes and payload addresses, marks `inner_validated`, and resumes READ_REQUEST. No byte response is outstanding in CHECK_INNER.

Let `M=inner32(44)`, `Y=inner32(48)`, `U=inner32(52)` and `V=inner32(56)`. Keep these original domains:

- Each header field is unsigned32. The inner validation expression is **32-bit modular** `inner32(40)+M+Y+U+V+32'd64`, compared with zero-extended `inner_bytes`. Keep the explicit individual bounds and key-dependent M==0/P-dependent M==3 checks. Do not silently replace this with a narrowed or widened sum.
- The outer size equation is explicitly **33-bit** and belongs to earlier code4 validation. It must remain separate and unchanged.
- Vector end and three dispatch starts are **16-bit modular** `474+M`, `474+M+Y`, `474+M+Y+U` after the original16-bit casts.
- Three payload addresses are corresponding starts plus16'd1; plane byte counts are `16'(length)-16'd1`. The original addr2 expression, `475+M+Y+U`, has three serial additions if mapped literally. Valid packets are bounded, but retaining the original cast/wrap semantics avoids changing malformed behavior while staging.
- `byte_bad` keeps its existing later-byte priority: qmap8, overwritten by nonzero-vector9, then by bad plane-dispatch10 in loop order. CRC error priority remains outer13, inner14, HUD15. Code6 must remain ahead of7 even if multiple predicates fail.

There is no source-level combinational `vector_end` register output feeding the `plane_start` register input: both are assigned from header expressions on the same edge. A phys-opt message mentioning both can refer to common logic/fanout; only an actual timing path establishes register-to-register connectivity after synthesis.

## Smallest staged-prefix candidate

Leave CHECK_OUTER, both CHECK_INNER validation predicates and their priority untouched. On CHECK_INNER success, instead of immediately resuming reads:

1. Capture16-bit `prefix0 = 16'd474 + 16'(M)` and `sum_YU = 16'(Y) + 16'(U)` in parallel. Capture `Y16` if needed to avoid the next stage reading the header array. Preserve the original successful block-size and plane-byte metadata assignments. Enter a new PREFIX_STARTS state.
2. PREFIX_STARTS captures `vector_start=474`, `vector_end=prefix0`, `plane_start[0]=prefix0`, `plane_start[1]=prefix0+Y16`, and `plane_start[2]=prefix0+sum_YU`. Each registered prefix path contains at most one16-bit addition in that stage. Enter PREFIX_ADDRESSES.
3. PREFIX_ADDRESSES captures each `metadata_plane_addr[i]=plane_start[i]+16'd1`, sets `inner_validated`, then resumes READ_REQUEST.

This adds exactly two successful inner-header parsing clocks. Addition is associative modulo2^16, so the resulting starts/addresses equal the original expressions, including wrapped intermediate values. There is no prefix reuse before its state-valid fence. Keep all original debug-state numeric codes by appending new enum entries after DRAIN rather than inserting them. New-state debug values are explicitly new, not hidden as an old state.

Retain ordinary global reset priority and abort priority. New states have no outstanding byte request, so abort returns directly to IDLE with the existing aborted/done behavior; no stale metadata may become valid. Keep state/control/payload reset behavior unchanged in this first candidate to avoid mixing reset relief into prefix staging. Header and packet snapshots remain immutable throughout the extra states. Keep `metadata_valid`, commit acceptance and qmap readiness exactly state-qualified as before; no provisional prefix or metadata is a frame commit.

This deliberately leaves the32-bit validation-sum cone and the later scan/CRC/control fanout unchanged. If final timing instead ends at validation/control or a high-fanout comparator, this candidate may not address it. A later split validation sum would require its own original-width partial-sum staging and code6-before7 proof; do not bundle it automatically. Precomputing during byte ingestion is also a separate, more complex validity/last-byte-dependency experiment.

## Existing tests and required extensions

The archived packet results cover two seeded runs6910/6911, each with457 valid packet metadata records, **23 structural rejections plus five downstream-semantic-deferred cases**. The commonly cited28 negatives are not28 parser rejects. Each run checks625,050 qmap responses, request stalls, delayed byte responses, held metadata/commit and three abort/retry scenarios. Results SHA-256 is `f9d0f40f58dd86c511f477b98035206e238689169a70655e3a318515d0223218`; test source SHA-256 is `104c67880c5a586b717ca782af2bc7eb79c54ced59a8dea591d96742eedaf6f1`.

The existing `await_parse` checks whether a structural error occurred, but does **not** assert the exact expected error code per negative case. It therefore cannot alone prove priority preservation. Preserve those archived results, and extend an isolated successor harness with:

1. All457 packets and28 negatives, exact metadata/qmap/byte-read-address sequence, same caller-owned reference snapshots, stable held metadata and commit fences. Valid packet read count remains exactly one per packet byte; compare logical output traces with declared extra parse latency rather than requiring identical total cycles.
2. Directed code6-only, code7-only and simultaneous6+7 headers; malformed lengths with high bits, 0/46/47/49152/49153/0xffff/0x10000/0xffffffff; total-sum wrap attempts; key/P M boundaries; prefix/address truncation boundaries. Recompute envelope CRCs where needed so the intended header predicate is reached. Distinguish earlier code4 failures from inner-code targets.
3. Standalone arithmetic equivalence of the old16-bit prefix/address expressions and staged equations over boundary vectors plus seeded full-width operands. Malformed operands rejected before prefix calculation still need exact acceptance/error equivalence, not an assertion that every malformed equation reaches the new states.
4. Abort and shared reset/flush on each new state and each adjacent edge, held abort, retry with the same snapshot, and old delayed-response drain tests. Assert no request/metadata/commit/qmap acceptance in new states, no memory read outstanding there, no reused stale prefix after abort/reset, and no publication before CRC/downstream owner checks.
5. Exact error-code/priority comparisons for all original and directed negatives, original CRC priority and plane-dispatch/qmap/vector cases. Assert successful payload addresses point one byte after the matching dispatch and retain all plane block-count/width behavior.

Only after root selects an isolated successor: source-bound component proof, matched exact-part OOC timing/resource comparison, full native KEY/P/P and then real full-board final setup/hold/pulse/route/DRC/CDC. Added private metadata latency is not a throughput improvement and positive OOC timing is not hardware readiness. Do not use timing exceptions, narrower unchecked fields, relaxed IO/clocks or altered rejection priority to obtain a pass.

# Final routed evidence and next local cuts

Both final component targets failed routed setup: **−2.974 ns at 125 MHz** and **−0.263 ns at 100 MHz**. These actual routed results supersede earlier synthesis/placement hypotheses for choosing the next work. Historical [synthesis queued-epoch](queued-epoch-next.md) and [placement admission-read](admission-read-next.md) notes remain unchanged. No source replacement, repeat native run or budget extension is proposed as part of this diagnosis.

| Final routed report | SHA256 | Worst actual path |
| --- | --- | --- |
| `/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T035613295775Z-79cccd/results/route-setup-paths.rpt` | `cc8bdcd81ceebb7691f2b3d41cc31df835d23686fd6a6eab6ff55f2b310290d9` | `base_kill_authorized_reg` → Rice `out_value_reg[12]/R`; 10.366 ns data, 11 LUT levels, 81.84% wire |
| `/home/lori/gamebub-build/cu66-v69/v115-integrated-100-20261109T035613740494Z-60d7e2/results/route-setup-paths.rpt` | `64d645ec57c691e58828a94995b9d11141046587428d3bcd20fdfae0dc2a70a1` | admission `plane_reg[0]` → `state_reg[1]_rep__0/D`; 10.098 ns data, 14 levels including three CARRY4, 71.45% wire |

Clock/hold/pulse/routing residue qualification is separate. Negative setup alone is sufficient to reject a claim of either requested achieved clock for this composition; the following are future source hypotheses, not measured fixes.

## 125 MHz: distinguish Rice request arbitration from the refill queue

The actual path crosses the registered owner certificate, producer abort logic, `packet_abort`, a fanout-1,033 `p_37_in` net, a fanout-230 `E[0]` net, **Rice-local** `req_valid` and `parser_in_ready`, then available/suffix controls into the synchronous reset pin of 24-bit output data. It does not pass through the admission BRAM read-enable endpoint that was worst at placement.

Actual source dependencies:

- `br88_context.sv:4080` forms a symbol request from context REQ_DC/REQ_RUN/REQ_LEVEL state, with reset/start/abort guards. It feeds `.req_valid(req_valid)` on the Rice parser at line 4098.
- The same context connects `.reset(reset||abort_context)` to Rice and uses a guarded input valid (lines 4094–4096). It masks external input-ready separately at line 4091.
- `br88_rice_elastic.sv:104–106` makes word-input readiness depend on `!(state==IDLE && req_valid)`. This is symbol-request versus word-load arbitration, not the replay-byte FIFO's capacity expression.
- Rice sequential priority is request acceptance, else accepted word load, else prefix consume, else suffix consume. Error/truncation and reset branches zero `out_value`; successful suffix completion writes decoded payload. Thus synthesized reset/enable logic for the output data can include the request/load readiness chain.

The path's `req_valid` alias is under `context_decoder/parser`; the source symbol request and the separately named `byte_refill_queue_v91i2b.req_valid` are distinct protocols. Removing the refill queue's same-edge-pop capacity look-through does **not** sever this actual worst chain. It remains a potentially useful independent cut for an admission replay-enable path, but must not be sold as this routed Rice fix. Synthesis aliases `E[0]`/`p_37_in` are not a source register declaration; exact mapped fan-in should be retained when implementing.

### First local candidate: remove late zeroing from the output payload bank

Keep the existing response/control protocol and all original cycle checks. Separate the successful 24-bit decoded payload into a private unreset register whose only write is the original successful suffix completion. Replace reset/error data clearing with a small logical zero/view flag. Set that flag on the **same original reset, stream_start, respond_error and prefix-truncation edges**, clear it on the original successful suffix completion, and hold it otherwise. Public `out_value` is zero when the flag is set, otherwise the retained payload. A successful decoded zero remains ordinary successful data.

The required equivalence is exact public `out_value`, including outside valid, on every edge after the original initialized view. Do not merely assert that consumers ignore the output on reset/errors. Original output_valid/error/consumed/state/timestamps and all branch priorities remain unchanged. This is analogous to separating logical validity from private payload, but does not authorize changing reservoir initialization, suffix arithmetic, request priority or raw public values.

This removes the 24 physical payload reset endpoints from that late chain; the view flag still has the real control dependency, and its output mux adds combinational logic. Other payload/counter/state endpoints may remain critical. There is no claim that this alone achieves 125 MHz or lowers total area. Do not duplicate/remove owner certificates or delay public abort to repair this path.

Required focused tests before adoption:

- Retain the original exact-cycle Rice paired checker, original prefix/rank and remaining/load assertions, all bit-domain/rounding behavior and finite watchdogs. Compare every public output every edge, not only decoded values when valid.
- Exercise reset/start/abort in IDLE/PREFIX/SUFFIX/RESPONSE and stalled output, request and word offers; all serial/parallel and 16/32-bit modes; k/escape zero and limits; failed request parameters, malformed/padded words, zero-length/truncated prefix and suffix, serial escape and every successful zero/nonzero payload.
- Verify old output data holds after response consumption, on a new request without response, under backpressure and through consecutive errors. A new owner must not expose an old successful payload while the zero-view flag is set.
- Retain whole ingress/context/scratch/control/peer and canonical retries. No exact-cycle checker is weakened because this first candidate intends no public latency change.

### Later candidate only if the actual readiness cone survives

A bounded registered word-input slot or local symbol-request-intent register could decouple request arbitration from upstream ready. This is a distinct schedule change: current simultaneous symbol request wins and prevents word acceptance. Capturing a word on that edge would change acceptance, reservoir timing and perhaps request error ordering. Specify a finite one-/two-word capacity, complete bits/last/owner tuple, exact priority and final-input fence; preserve immediate public masks and compare ordered symbol/error behavior with an independent model while retaining old exact-cycle checks unchanged. A register called “ready” is not sufficient if it still depends combinationally on the same high-fanout abort/request signal. No such design is selected here.

## 100 MHz: admission plane selection and chunk-validation preparation

The actual path starts at admission `plane[0]`, crosses high-fanout plane/plane-block aliases (121/119 loads), error-selection logic, three CARRY4, word-accumulator/fetch-address aliases and the parser FSM D input. This is in the structural admission parser, not the inverse DSP datapath. The bit names alone do not identify a single case branch, but the source has concrete plane-selected full-width chunk predicates:

- CHUNK_NUMBER compares `word_value` to `(plane_blocks[plane]==0 ? 0 : 1)` and decides whether another chunk header can fit.
- CHUNK_BLOCKS compares the parsed word to `plane_blocks[plane]` and rejects zero.
- CHUNK_LENGTH checks `word_value<46`, `word_value>46+128*plane_blocks[plane]`, and the separate full-width residual-end sum/bound before requesting magic.

The dynamic plane selection feeding the length limit is a strong source hypothesis for the error/carry family; mapped combinational input tracing is needed to distinguish it from neighboring cursor/header bounds. Do not declare a carry to be a multiplier from its name.

### Existing-edge preparation candidate

At the existing PLANE_BEGIN edge, capture the selected plane's block count and plane identity into an owned tuple before requesting CHUNK_NUMBER. Following existing FETCH_REQ/FETCH_WAIT/WORD_BYTE edges provide ample actual preparation edges before CHUNK_NUMBER/BLOCKS/LENGTH consume the count. On a subsequent existing edge, form the exact original 32-bit wrapped `46+128*selected_blocks` limit. Keeping selection and dependent arithmetic on separate existing edges avoids simply moving the whole cone to a new register input. It adds no public read or parser state if the original request sequence is untouched.

Use the prepared selected count/zero flag for CHUNK_NUMBER/BLOCKS and the prepared limit for CHUNK_LENGTH, while leaving the residual-end 64-bit bound independent. If mapped fan-in instead identifies that bound, prepare its stable cursor/residual terms on their own existing predecessor edge and preserve exact width/carry behavior. Do not narrow block counts or arithmetic because ordinary 720×480 frames use small values; preserve the original comparison's explicit/full expression width and wrap domain. Capture after any plane transition, not before the old plane increments.

Proof obligations:

- Assert at each real CHUNK consume that the tuple's plane equals current plane, selected count equals the original `plane_blocks[plane]`, and prepared limit equals the exact original expression. The count is constructed during the completed mode pass, but prove it remains stable from capture through all chunk words rather than assuming it.
- Cover all legal planes, empty/nonempty planes, PLANE_NEXT transition, abort/reset on every preparation/fetch/word edge and clean retry. Invalid length zero/minimum/maximum/one-over, truncated chunk, residual sum boundary, frame-size wrap and foreign/stale owner failures retain their original error code and edge.
- Preserve the original request_word/address/byte-order/read-response behavior, raw data holds, RAM collision guards and reference/drain ownership. Private preparation must not issue an early read or consume a malformed next-plane descriptor.
- Retain original full-width corruption tests and exact admission outputs. Add arithmetic boundary models with the original unsigned/signed casts; if a private state-injection fixture is used, construct every legal dependent poststate and keep all old SVAs.

## Next sequence and limits

The next development iteration should first implement and simulate the isolated Rice output-view candidate and admission selected-plane preparation under separate reversible recipes. Qualify their unchanged public-cycle contracts before combining them. Preserve the final negative routed reports as evidence, and use the full production-interface/parent plan to avoid timing a debug-only or SHA-free proxy as the final system. Any later native qualification requires a new explicit budget decision; V115's six source/clock measurements are complete, both final setup targets failed, and no repeat was launched here.

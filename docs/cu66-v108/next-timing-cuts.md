# V108 final routed limits and the next narrow cuts

The five-body capacity+output-mask composite improves the clean paired route, but **does not meet 100 MHz**. This document diagnoses actual final routed reports only. It introduces no RTL/XDC edit, new tool run, timing exception or claimed hardware throughput.

## Exact final comparison

Both fresh runs use `xc7a100tcsg324-1`, the unchanged 10-ns clock, RuntimeOptimized synthesis and the same ExtraNetDelay_high placement/Default routing recipe. The clean control re-synthesizes V107; the new run changes exactly four capacity bodies and the IDCT output-storage body. The result is a paired composite comparison; it does not identify separate physical gains from each change.

| Final routed result | Fresh V107 control | V108 capacity+outtile |
| --- | ---: | ---: |
| WNS | −2.342 ns | −2.020 ns |
| TNS | −17,923.600 ns | −11,717.641 ns |
| setup-failing endpoints | 23,783 | 16,953 |
| worst hold slack | +0.096 ns | +0.098 ns |
| worst pulse-width slack | +3.750 ns | +3.750 ns |
| routing errors | 0 | 0 |
| worst source → endpoint | scratch read_segment → scratch state/D | transform error → Rice reservoir/CE |

WNS improves 0.322 ns, TNS magnitude 34.62% and setup-failing endpoints 28.72% in this pair. Setup closure remains open. Board I/O and complete hardware performance are separate unqualified scopes.

Evidence:

- [Fresh control receipt](../../experiments/python-gamebub-v108/native/20261108T101654614323Z/receipt.json), SHA-256 `bcb7ff683a584b1026ee9bd26170b29cee7a7fe9d40b2bc883b640eb702efe1c`; [final setup report](../../experiments/python-gamebub-v108/native/20261108T101654614323Z/reports/route-setup-paths.rpt), SHA `8062e6e8da24e3cfb4767eb9bf1c8b499d7a4f8e4661bc701605b0ecd826931a`.
- [Composite receipt](../../experiments/python-gamebub-v108/outtile-native/20261108T101802940240Z/receipt.json), SHA-256 `e6f76901d9817dbeabedbf916370985cf5e99fc83f8243f20d82e88fb9241cfb`; [final setup report](../../experiments/python-gamebub-v108/outtile-native/20261108T101802940240Z/reports/route-setup-paths.rpt), SHA `953730106d6c2396a90020a5b15762dfd212139d857d323f7e4c67c239811b1b`.

These fresh final runs must not be conflated with the earlier checkpoint-start m2 path or synthesis/placement estimates. Fresh control's worst path is 12.290 ns, comprising 3.028 ns logic and 9.262 ns routing across thirteen levels; its second-worst capacity/assembler reset path is −2.324 ns. The earlier checkpoint m2's transform-error→IDCT-output path was a different final implementation, useful for motivating the storage experiment but not a substitute for the fresh control.

## Current primary: global fault to entropy storage enable

The composite's actual worst path is `transform/error_reg[1]/Q` → `coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/reservoir_reg[45]/CE`, with −2.020-ns slack. Data delay 11.731 ns comprises 2.192 ns logic and 9.539 ns routing (81.315%); there are fourteen LUT levels. The report includes cancellation/start-related decoded nets with fanouts 1035, 247 and 143, and a 2.269-ns routed segment between parser-control regions. The final reservoir enable drives 71 loads on that path. This is predominantly a distributed control-routing problem, with meaningful logic depth remaining.

Among the reported fifty worst setup paths:

| Endpoint family | Paths | Worst slack | Actual source |
| --- | ---: | ---: | --- |
| Rice reservoir CE | 23 | −2.020 ns | transform error[1] |
| scratch state D | 5 | −2.008 ns | output_block[2] |
| scratch cursor CE | 9 | −1.957 ns | read_segment[1] |
| dequantized output D | 4 | −1.933 ns | dequant group_index[1] |
| ingress word_valid D | 1 | −1.919 ns | fetch_return[2] |
| Rice cached_remaining CE | 8 | −1.856 ns | transform error[1] |

This is a top-fifty distribution, not a census of every failing endpoint. No IDCT output payload or written-mask endpoint appears in these fifty paths. The new word storage removes direct reset/abort dependence from its 1,536 payload bits by construction; 64 visibility bits retain exact public zeroing. It has not removed the global fault network or all of its other storage loads. The same network now limits a different consumer.

## Source-bound control chain

The receipt's `source_origins` and read-only snapshots establish these actual bodies, despite historical v69/v91 alias filenames in the native source list:

| Selected origin and source location | Exact SHA-256 | Relevant behavior |
| --- | --- | --- |
| [full top](../../fpga/experiments/cu66-v107-meta-flags/cs88_pipeline_v91k.sv#L195) | `582e6cf1f56d678c0356822b6e2b4e8371bd43827870b7a8fb947b1fb4e61e86` | accepted_start depends on base readiness, arithmetic busy and token ownership; line 200 creates one-shot base_abort from sticky inverse/reconstruction errors and acknowledgement flags; cancellation branches preserve a replacement start |
| [coefficient producer](../../fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv#L1045) | `396b0d9ac27a6bea6f1694252b18078ed5ac42351201b6c7e201c2091736061d` | start readiness includes child busy/drain; local_abort adds FAILED state; child_abort forwards the fault |
| [child pipeline](../../fpga/experiments/cu66-v108-capacity/br88_pipeline_v91h.sv#L121) | `cb440ed9c12c6fa3eac579aea99f2c03716e33b97ce50822ab00b93de08a4360` | packet_abort combines parent abort with owned scratch error and explicitly lets a replacement start win |
| [ingress wrapper](../../fpga/experiments/cu66-v108-capacity/br88_packet_ingress_v91h.sv#L137) | `9529b8a76b531d22f7d0a4498295153f8a397c004725787c34af9824ee84cfb1` | synchronous branch forwards the same start/abort interface |
| [synchronous ingress](../../fpga/experiments/cu66-v108-capacity/br88_packet_ingress_sync_v91h.sv#L326) | `6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6` | context abort is packet abort OR start; context start and input offers are also gated by cancellation/failure |
| [context wrapper](../../fpga/experiments/cu66-v106-context/br88_context.sv#L4020) | `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277` | request/input/response readiness is gated by start/reset/abort; line 4,034 maps reset OR abort to parser reset and start-without-abort to stream_start |
| [Rice parser](../../fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv#L97) | `f39c3f90d0242097ea3cd2693e6f4d99e58e33a0b49c644c720497f50e6777dc` | request/input ready suppress reset/start immediately; line 112 resets storage/control; input append and PREFIX/SUFFIX consumption write the reservoir at lines 145/154/177 |
| [IDCT output storage](../../fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv#L145) | `3a30e2c527755ee5e34480274a7998795a773e23fef6cec8471fdd89c31a7808` | local-state-only private payload enables; public mask clears immediately on reset/abort |

The actual timing path passes through top base_abort, coefficient/child abort logic, parser reset/start/state decode, input readiness and consume/availability decisions. Netlist names are shared aliases and optimized expressions; the source connections explain the dependency but do not establish a unique one-LUT-to-one-expression map. Accepted-start suppression and fault acknowledgements elsewhere in this network preserve retry priority. They must not be removed merely because the nominal failing route starts at a sticky error register.

## Narrow zero-added-cycle follow-ups

1. **Co-register the operational fault cause with the existing error next state.** Derive a one-bit owned fault/flush cause on the same edge that the current error register changes, rather than registering the already registered error one edge later. Check its complete truth table against the existing error/acknowledgement expression at every cycle, including sticky error, accepted retry, external abort and simultaneous failures. Use small local fault predicates for downstream control instead of repeatedly decoding wide status and readiness through several wrappers. Keep reported error values, acknowledgement timing and every immediate public fence exact. This may reduce wide decoding and distributed cancellation depth; synthesis can still merge predicates, so native measurement is mandatory.
2. **Isolate Rice reservoir payload from reset control, using a canonical zero view.** Every reservoir data write replaces all 64 bits. A resettable one-bit zero/visibility flag could hide an unreset private reservoir after reset/start, with first append/consume writing the complete canonical next word before exposure. The canonical old-visible reservoir, not arbitrary hidden bits, must feed append/shift. Dropping reset alone is wrong: input append ORs into the old reservoir, so stale bits would leak and violate zero-padding assertions. Preserve all original assertions and normalized private-reservoir checks. Private operation qualifiers must be proved equivalent whenever owned; simply reusing in_ready/req_valid may retain the same global kill path. If a kill-independent private offer is needed from the parent, introduce and prove that sideband explicitly while keeping public handshakes unchanged. Do not call this a proven timing fix yet.
3. **Separate scratch prefetch arithmetic from the same-edge state decision.** The next-worst path is output_block[2]→scratch state, 11.953 ns (4.668 logic/7.285 route), fourteen levels including five CARRY4s. It traverses next-block/line candidate arithmetic and prefetch launch before EMIT/RAW_EXTRACT decides whether to enter PREFETCH_DRAIN. Cache only owned address/range terms on existing earlier fetch/prepare edges; compare live cache tags/validity and response state at the original decision edge. Preserve first-DC-then-band priority, same-edge dense acceptance, exact request order, counter timing and malformed full-width arithmetic. RAW and sparse paths need different deadline/forwarding proofs. A stale cached hit/miss or one-cycle-late launch changes the current contract.

The four-bank read_segment decode/cache mux remains a secondary measured problem (−1.957-ns cursor path). A one-hot bank decode captured alongside read_segment at existing fetch edges is still a useful isolated candidate, with all bank 0–3 writes, refill forwarding, rank/value/order checks and malformed-memory behavior preserved. It is **not** a fix for the current primary error→Rice path. Similarly, availability-mask removal from the Rice first-one tree targets a separate data cone, not the measured operational-fault enable chain.

## If an explicit control pipeline is needed

Keep immediate externally visible fences local: no accepted input, published output, new memory request or stale owner token may escape on a current-cycle cancellation. A registered local flush can follow only if all intervening private work is provably unowned and cannot become visible. Current public/debug counters and reservoir_bits also have exact reset/start timing; delaying their reset without a matching canonical public view breaks the existing proof.

A deliberately staged ownership/flush protocol is therefore a separately versioned alternative, with an explicit start/abort latency table, epoch-tagged in-flight tokens, drain acknowledgement and a latency-aware independent model. Preserve immediate output/acceptance fencing, declare any changed start_ready or telemetry timing, and remeasure complete-frame latency/FPS. Do not silently insert a register into the present abort path, loosen cycle checks, or mark it multicycle/false-path because it carries control.

Before V109 full integration, choose one narrow cut, prove complete original/public behavior and cancellation/retry first, then qualify the exact composite and run a clean matched native comparison at 10 ns. Retain final setup/hold/pulse-width, routing, methodology and source provenance reports. A different placement estimate or fewer resettable bits alone does not close the remaining 2.020-ns setup deficit.

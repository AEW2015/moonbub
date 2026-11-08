The final P9 route supersedes the mapper placement hypothesis. P9 finishes with WNS −1.022 ns, TNS −1125.069 ns and 4620 setup failures; all 50 reported setup paths launch from header fetch byte[23] (44), context blocks[9] (4) or admission tile[5] (2). There are **zero context-position mapper launches** in that top 50. The measured next target is header length-sum validation. This mapper proposal is conditional, unimplemented, and should be reconsidered only if a later final routed path exposes it.

The [source-pin analysis](../../experiments/python-gamebub-v110/mapper-analysis.json), SHA256 `531e6798f3f2aa4b6dbdf3f97c8fb66bf62ff909cde640c2239c2d5878c76c67`, retains the final receipt/report and the superseded placement report. Placement's RAMB18E1→out_block path was 10.558 ns/14 levels/six CARRY4; placement estimates do not establish the final bottleneck. Actual context source is `cu66-v110-count-domain/br88_context.sv` SHA `029e1ed9b7fd9d3cd8bdf46d0d8e87d773062e1e238001c4b8e672553bb7ab64`; parser is actual `cu66-v110-prefix/br88_rice_elastic.sv`.

The source has `byte_qr`, `remainder_sum4`, `correction_index`, `quotient_sum5`, `position_geometry` and `sparse_geometry`; it has no `divmod` or `pack_sparse` symbol. Each byte lookup supplies a weighted 16-bit quotient modulo 65536 and 6-bit remainder. The four remainders sum to at most 168. Correction supplies quotient increment 0–3 and the six-bit zigzag index. Preserve all original widths/operators/helpers.

The shortest successful AC run-to-output path has **four edges**, not three. Let E0 accept a successful WAIT_RUN response and register the new position:

| Edge | Earliest event / available preparation |
| --- | --- |
| E0 | Run accepted; context enters REQ_LEVEL. Its old WAIT_RUN state has no request. |
| E1 | Level request accepted; Rice enters PREFIX, context enters WAIT_LEVEL. Capture four byte contributions from the now-registered position. |
| E2 | PREFIX consumes. It always enters SUFFIX, even when k=0; it does not emit a successful response. Register corrected index and four quotient candidates. |
| E3 | SUFFIX emits registered out_valid/value, even for a zero-width suffix. Context sees previous out_valid=0. Privately select/pack geometry. |
| E4 | Earliest context successful WAIT_LEVEL capture. Use the prepared geometry on the original public output-write edge. |

This minimum is attainable with blocks1/band1/events1/k0=k1=0 and buffered bits `11`: run0 followed by level0 (coefficient −1). It applies to serial/parallel and 16/32-bit input modes. Rice request acceptance is an earlier if/else branch than PREFIX; PREFIX always transitions through SUFFIX; context reads the previous registered parser out_valid. No combinational response bypass exists.

A held previous parser output blocks req_ready. Input acceptance, insufficient bits and stalls only lengthen the sequence. Error responses can be earlier, but the context's first parser_error branch fails before any geometry write. Invalid start parameters fail before the run/level sequence. Output backpressure holds the published slot after capture; it cannot shorten preparation time. Thus E1/E2/E3 are three guaranteed intermediate edges for a successful AC geometry consumer.

The conditional pipeline can retain the old lookup/arithmetic exactly: E1 registers four 22-bit contributions; E2 registers corrected eight bits and four 16-bit quotient candidates; E3 registers the selected 22-bit geometry. That is 182 private payload bits. Free-running reset-free payload is possible because only the owned consuming branch uses it, but an ownership/use assertion must prove equality to the untouched original `sparse_geometry` on every successful AC capture. Keep the original full-32 helper/probe/oracle and generic count validation defaultFalse. Stage/owner validity must not assert readiness or alter any public handshake.

Do not publish block/index early when private preparation completes: public invalid output values retain their old payload until the original successful capture. DC/default mapping stays directly `{emitted[15:0],0}` because it has no WAIT_RUN preparation chain. Empty AC produces no geometry. Parser errors, malformed runs, coefficient range/zero errors and final consumed-bit-count errors retain their original priority and old invalid payload. Reset/abort/start keep the original output clearing/IDs/counters; every replacement AC output requires a new run chain before consuming any prepared data.

This is source edge analysis, not a new simulation or implementation. Any later experiment would retain full generic/specialized context, all goldens/geometry/invalid/counter checks, earliest buffered zero-width-suffix cases, modes, stalls, cancellation and whole-ingress/full-canonical tests. Physical BRAM register packing and timing benefit require measurement. No RTL variant, test, native run or hardware action was performed here.

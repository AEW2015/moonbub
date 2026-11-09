# Conditional next cut: accepted coefficient validation

This is a future V119+ proposal grounded in the completed A100 and A125 routes. A125 confirms the same raw-mode input-validation family as its worst path. No source B, new RTL or additional native launch was selected in V118; the coordinated changes need the chronology and physical-debt proofs below.

A100 meets its internal10ns target with WNS+0.061ns, but its worst path is ingress `raw_mode_reg_rep` through the selected raw/context coefficient position and scratch input validation to `busy_owned`. The15-level path includes3 CARRY4 primitives and9.886ns data delay:3.069ns logic and6.817ns routing. The source register has172 loads. All six new scratch head predicates survive as FDREs; none appears in the bounded50 worst paths. Those paths also include20 `emit_bank` to `count_publish_release_same_edge` counter-enable paths. These observations do not establish the next125MHz cause.

## Existing edges that can own the work

Scratch already accepts one coefficient in INGEST and consumes its pending record in APPEND. It cannot accept another coefficient while in APPEND. Current INGEST validates the incoming unregistered tuple, flips the private record bank only if good, and enters APPEND; APPEND writes the assembler and advances `written` and `previous_position`.

An owned pipeline can capture a complete accepted coefficient tuple and immutable expected context on INGEST, then validate that captured tuple and gate assembler commit on the existing APPEND edge. Good coefficients need no additional data edge if the new captured-path timing closes. This cuts the ingress raw/context selection from the later position comparison and broad status/state consumers. It is a real accepted owner, with one logical pending slot, rather than an unqualified sample of changing live input.

Capture full untruncated input epoch, band,16-bit block,6-bit index and signed16-bit value. Capture or explicitly bind the expected epoch, full phase encoding, raw mode, block limit, full32-bit count/written frontier and previous-position/valid frontier. The old packed sparse record truncates block/value bits and cannot independently validate illegal range inputs. Preserve full modulo32 arithmetic, exact signed limits, ordering and the original phase/range casts; do not narrow a predicate because current natural fixtures use smaller values. Register the selected full position before the comparison, and certify it against the original complete expression at acceptance.

## Error chronology requires an explicit contract

An invalid coefficient now reports its error one edge later. Its private pending view can change. This is not old-cycle equivalence. The original checker remains frozen; a new checker must prove the declared accepted/validated/committed schedule and every value/owner/error/debt obligation.

Moving the `input_bad` branch mechanically is unsafe. Original invalid INGEST clears the write slot and assembler immediately. With delayed validation, an older held write might otherwise accept on APPEND, or a matching write-error response arriving there could replace the older coefficient reason3 with reason5. Prevent that with an explicit chronology rule and tests:

1. Capture only a logically eligible INGEST transaction under the original outer response/cancel priority. A handshake observation alone is not proof that the original case branch owned it.
2. On APPEND bad, suppress assembler commit and any newly offered physical write that original invalid INGEST would already have revoked. Good tuple request timing may remain unchanged only if proved with the complete memory-service comparator.
3. Preserve the older coefficient reason against later matching write errors. Retain the original higher-priority external reset/cancel and unsolicited/wrong-epoch response behavior; do not globally reorder response faults to make one test pass.
4. Drain each actually accepted physical request exactly once, including a request accepted on the original INGEST edge. No canceled tuple may publish a packed byte or permit a younger coefficient to commit.

The relevant matrix includes invalid epoch versus geometry, bad first/last/domain values, simultaneous coefficient/band-end, held old write, request acceptance on the bad edge, matching success/error reply on the validation edge, wrong-epoch/unsolicited reply, reset, matching/foreign abort and full retry. Check all8 original phase encodings and full-width endpoint/wrap cases. Track accepted, committed, discarded and physically outstanding owners independently. Payload need not be reset; logical ownership must be revoked immediately.

## Other candidates remain conditional

Registering a whole selected output record in ingress can also cut its late raw/context mux, but the context completion edge lives inside `br88_context`. A zero-edge solution would require exposing or owning the complete next tuple at that actual parser-response edge. Adding a new parent register after `ctx_out_valid` would add a real presentation edge and must be measured. Retaining the old invalid-data view through a late mux can preserve the original unwanted cone, so source syntax alone is insufficient.

If final A125 timing instead identifies status-counter enables as dominant, a separately owned one-edge delayed statistics event is another candidate. It must not feed back into stream control. Define its complete event tuple, reset/cancel/epoch behavior and terminal flush; compare exact event counts and declared one-edge lag without dropping original clocks or weakening functional data/owner oracles. The existence of competitive A100 paths alone is insufficient justification to include this in source B.

The dormant replay lease addresses the older V117 selected-offset response cone. It remains dormant unless current final A125 evidence shows that cause is still material. No timing exceptions, fanout directives or unchanged-source reroute replace a measured architecture cut.

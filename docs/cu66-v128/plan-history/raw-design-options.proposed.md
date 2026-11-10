# V128 sparse-ingress validation design options

This proposal is not applied or qualified. Root is collecting scoped mapped fan-in before selecting production edits. The measured V127 global path is ingress `raw_mode_reg/C` through selected metadata/validation to scratch state, −1.193 ns, 9.140 ns data with 72.331% routing. Mapped carry-cell names do not alone identify their arithmetic.

The first bounded option factors the **complete** scratch coefficient validation before the ingress RAW/context tuple selection. It is cycle-preserving Boolean distribution: `f(select ? raw : context) == select ? f(raw) : f(context)`, for the entire full-width tuple. Epoch-only factoring could leave mode selection ahead of block/range/value/position checks. This does not assume that mode, valid or ready certifies ownership.

## Exact four-origin scope

| Selected origin | Proposed edit |
| --- | --- |
| [Sync ingress](../../fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv) | Expose selector and direct RAW/context tuple views alongside unchanged original selected outputs. RAW block is exactly16'(raw_position>>6), index raw_position[5:0], value raw_coefficient, epoch context_epoch, band0. Context views are ctx_block, ctx_index, signed ctx_coefficient, ctx_epoch and band. |
| [Capacity wrapper](../../fpga/experiments/cu66-v108-capacity/br88_packet_ingress_v91h.sv) | Forward direct views for SYNC_STAGING1. For legacy SYNC_STAGING0, duplicate the existing selected tuple to both new views and select context lane. The legacy implementation source stays unchanged. |
| [Child pipeline](../../fpga/experiments/cu66-v127-owner/br88_pipeline_v91h.sv) | Forward new private wires from packet decoder to scratch. Original selected coefficient outputs and all public debug/payload wiring remain unchanged. |
| [Scratch](../../fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv) | Evaluate two independent complete eight-phase bad-decision lanes using the direct tuples; select one Boolean per phase. Factor the selected epoch-bad Boolean similarly for the original error2/error3 assignment. |

The remaining14 of18 origins, including producer, context parser, inverse and admission, stay byte-identical. No register, payload state, reset, synthesis attribute, public top port, public clock or wire-format change is proposed. Every actual parent uses the retained24-entry order. The machine-readable [proposal](../../scripts/cu66-v128/raw/proposal.json) pins the four input sources.

## Tuple and mode contract

Each direct tuple is72 bits: epoch32, block16, index6, signed coefficient16 and band2. Proposed scratch names are `coef_select_raw`, `coef_raw_*` and `coef_context_*`; the wrapper's outputs use corresponding `view_select_raw` / `view_raw_*` / `view_context_*` names. No narrower epoch or block key is permitted. RAW block truncation and shift exactly match the current selected output, including out-of-domain raw_position values; the proposal does not silently replace it with a different full-position expression.

**Ingress selector and scratch format mode are distinct.** The ingress's raw_mode selects which tuple is offered. Scratch's independently stored raw_mode selects raster versus DC/AC format validation. Every new lane uses scratch format mode unchanged. Tests must cross both selector values with both scratch format modes and all8 phase encodings, including invalid, unready, reset, abort and foreign-owner views.

Each phase lane retains the full epoch mismatch, low2 band comparison, original16'(blocks) cast, signed −2048/+2048 bounds, full32 written/count test and original raster/DC/AC ordering expression. Phases4–7 retain their existing low2 count/band lookup and full phase==0 distinction. Sparse ordering retains full previous_position high/block terms and existing64-bit rank_threshold_mask relation; no new position shortcut or assumed canonical tuple is introduced.

Only `phase_input_bad` production expressions and the INGEST epoch error-class expression change. Existing selected payload, prospective record, input_position, bank state, physical outstanding request, DRAIN choice and cancel/response/first-error edge priorities remain unchanged. The original selected helpers can remain as verification references, consumed through real selected-lane equality assertions so strict lint does not require suppressing unused signals. All original guarded assertions must be recovered verbatim after removing only exact new additive assertion text.

## Verification before native release

The authored source-extracted probe should instantiate original V127 and candidate scratch validation logic, drive two independent full tuples, and derive the baseline selected tuple from the actual selector. Require exact selected-view identity on every evaluation, all8 bad-decision lanes, epoch error class and full original expression equality. Exercise upper epoch/block bits, boundaries/overflow casts, signed value edges, index/band/DC/AC distinctions, previous-position high bits and rank thresholds, all format/selector/phase crossings and held/cancel/error contexts. Do not force a new bad decision or certificate into the DUT.

Existing standalone scratch fixtures must connect the two new views to their old selected inputs and select context lane, preserving their original contract. Whole-parent focused tests need namespaced baseline/candidate copies of all four changed modules so the baseline does not accidentally instantiate new ingress or scratch logic. Retain every old public/canonical/event/debt oracle and the existing strict compiler flags. Follow focused PASS with the complete decoder, actual V97 transport, peer and byte/row ordinary/stalled parent regressions and exact4/2/4 raw comparisons.

A fresh8ns native route decides physical benefit. Synthesis may refactor the distributed expressions. Matched RAW-mode, selected epoch/block/value, scratch control and every existing mode/producer/admission/hidden/coordinate family must remain in the comparison. A positive local result is not global closure; a positive global route requires a separate identical-source/tool/recipe fresh repeat.

## Separate near-critical admission path

The admission header→tile synchronous R-pin path is −1.165 ns, within0.028 ns of the global worst. It remains a different concern. Precomputed owned header rejection classes on existing byte-loading edges may help, but require full header ownership, ordered error selection, last-padding-byte forwarding and exact reset/abort/retry logical views. Do not combine that larger change with this first RAW trial without its own independent proof and source map. Removing tile reset or assuming invalid-header payloads are unobservable would weaken the current contract.

If the distributed full-tuple expression merely moves reconvergent logic, a future latency-changing sparse-ingress validation buffer is the fallback. It needs captured full tuples, tag-bound certificates, offered-malformed versus accepted behavior, accepted-memory debt and seal/cancel fences, bounded fault latency and demonstrated II=1. That is not this cycle-preserving proposal, nor is it the separate dense-output queue.

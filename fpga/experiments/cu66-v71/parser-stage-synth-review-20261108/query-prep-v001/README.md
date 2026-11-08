# Prepared parser synthesized-cone query — HOLD

No Vivado query has run. Root owns the active synthesis; this runner requires completed synthesis, an explicit root receipt with the exact constrained-checkpoint SHA, a matching prepared-manifest SHA, unchanged79-source bindings and no other Vivado process. No source, checkpoint, property, constraint, reset, clock, route or hardware mutation is requested.

After root review, the concrete command is:

`python run.py --checkpoint C:/moon/builds/parser-stage-v001/constrained.dcp --out C:/moon/dev/evidence/parser-stage-synth-cone-v001 --review-receipt ROOT_RECEIPT.json`

The output path must be unique. The default receipt denies execution; the saved negative HOLD test did not launch Vivado. `syntax-check.json` establishes Tcl lexical completeness and Python syntax only, not installed native query success.

The read-only Tcl verifies exact parser hierarchy/module, part and raw100 period. It requires real reference-tag registers/Q pins, inner-header registers, parser state FFs/D-or-CE inputs and all three plane-byte register/CE collections. Empty/missing queries are errors, not evidence of removed paths. It uses explicit supported state-name patterns (`state_reg[*]` or `FSM_sequential_state_reg[*]`), with inventories, rather than silently broadening a failed query.

Per plane it records reference-tag-Q→plane-byte-CE timing-path presence, every CE startpoint and reference-tag startpoint count, and worst CE setup. It separately requires header validation and reference tag timing paths into state FF inputs, preserving evidence that validation still affects state. The header launch selection includes inner bytes0–39 plus metadata key/frame/reference/tag comparison operands; it is a structural selection, not a claim that one named net is the complete code6 predicate. Parser sequential/state inventories and global worst50setup complete the synthesized inspection.

The exact control-plane hud_ticket_reg[4]/CE cone, setup/hold, driver/load count and HUD-metadata startpoint count provide a local comparison to the prior CE experiment. Clock/exception reports are preserved. Every timing result is from the constrained synthesized checkpoint; it is not placed/routed timing or a margin/physical-pass claim.

`publication-integrity-review.json` independently rechecks all199 preserved files,44original frozen entries, all57actual packet hex cases and their payload hashes, the exact control/candidate executed compile paths, successful direct-oracle runs and all79restored production input hashes. The two replacements versus V028 remain the earlier CE receiver factor plus the new staged parser; no publication or baseline file was edited by that review.

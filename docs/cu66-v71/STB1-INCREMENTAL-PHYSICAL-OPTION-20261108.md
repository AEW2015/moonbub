# Conditional physical-reuse experiment

Keep the passing V028 BIT and routed checkpoint fixed. The CE-factoring source is functionally checked, but its fresh implementation currently has negative intermediate slack. Its final flow and exact-cone query must finish first. Nothing in this note asserts a new timing pass or authorizes a concurrent Vivado job.

A useful next experiment is to implement the **same** CE-factored synthesized design using the passing V001 routed checkpoint as an incremental reference. This tests whether preserving unaffected physical placement/routes avoids the whole-chip regression seen with fresh placement. It is an inference to test, not a guaranteed improvement or a source fix.

AMD documents reference-checkpoint placement/routing reuse, including partial reuse and the possibility that the tool discards reused objects during optimization. A one-line RTL change does not establish the actual cell/net matching rate. [AMD UG904 2025.2, Running Incremental Place and Route](https://docs.amd.com/r/2025.2-English/ug904-vivado-implementation/Running-Incremental-Place-and-Route?contentId=HIWFUevlf56NDq5MF3e_Kg).

The tool can choose an incremental flow or fall back to a full flow after matching; its documentation describes typical incremental eligibility above80% cell reuse. Record actual mode, matching and reuse reports, rather than assuming eligibility or that the original place/route directives still control every incremental algorithm. [AMD UG904 2025.2, Incremental Mode](https://docs.amd.com/r/2025.2-English/ug904-vivado-implementation/Incremental-Mode).

Before launch, verify installed2025.2 command help and review a new source-bound Tcl script. Use a NEW C:/moon build directory, the exact already-qualified CE constrained checkpoint, unchanged opt_design/source/clock/pin/exception settings, then the explicit passing reference checkpoint. Bind both checkpoints and scripts. Do not force incremental eligibility, fix arbitrary routing, introduce Pblocks, relax budgets, reuse a failed V003 checkpoint or overwrite the reference. This is a separately named physical-flow experiment.

Promotion still needs final positive setup/hold/pulse, complete routing, zero unwaived DRC errors, clock/CDC/coverage and actual CE-cone review, unchanged source bindings, and a unique generated BIT identity. Existing exact-source CE model results qualify that source only; they do not certify an unexamined netlist or physical result. Hardware and30unique displayed frames/s remain separate gates.

If insufficient window remains, preserve this as the next controlled experiment and use V028 for the initial hardware tests. Do not substitute an unfinished or failing cleanup image merely to deliver a newer version number.

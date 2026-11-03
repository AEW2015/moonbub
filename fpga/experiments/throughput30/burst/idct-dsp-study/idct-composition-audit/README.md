# IDCT stage-composition audit

The proven X and Y substitutions support a **conditional, two-state, cycle-by-cycle IDCT-level equivalence inference**. It is not unconditional equivalence from unrelated arbitrary power-on states and is not a monolithic full-IDCT formal proof. The argument uses the manually composed stage proofs in `../narrow-x-proof/` and `../narrow-y-coeff/`, with their default parameters and a synchronous reset edge. It does not establish four-state behavior, other parameterizations, full JPEG decoder equivalence, physical timing or device fit.

## Actual hierarchy and wiring

The pinned vendor `jpeg_core.v` instantiates one `jpeg_idct` without parameter overrides. In that IDCT, Yosys 0.52 elaboration finds exactly one X (`INPUT_WIDTH=16`, `OUT_SHIFT=11`) and one Y (`INPUT_WIDTH=32`, `OUT_SHIFT=15`), both without overrides. They and the input buffer and transpose receive the same top-level clock, reset, image-start and image-end signals. Input RAM drives X's four 16-bit inputs, valid and index; all three X outputs (data, valid, index) drive the transpose; its four 32-bit outputs, valid and index drive Y; all three Y outputs drive the parent outputs. Transpose ready is tied high. The parent ID FIFO is WIDTH 32, DEPTH 8, ADDR_W 3; it pushes external EOB/ID, flushes on image start, and pops on Y valid and index 63. `inport_accept_o` and input-buffer ready connect directly to the parent. Neither candidate alters this surrounding wiring or state.

`audit.py` checks these elaborated nets, stage instance counts/parameters, FIFO wiring, vendor instance inventory, source and candidate hashes, and the retained stage-proof and negative-control markers. It also checks that the transpose RAM reset ports are not connected internally. It does **not** rerun the stage proofs or prove top-level equivalence itself; use each proof study's wrapper for that.

## Conditions needed for substitution

Compare two instances supplied the same top-level inputs and clock. At the comparison start, couple the initial values of all unchanged surrounding state between them, including the input RAM, transpose RAM/read registers and ID FIFO memory; reset alone does not initialize all of those storage elements. At the **first** synchronous reset edge, also require that the pre-edge X outputs do not cause differing transpose RAM writes. A simple sufficient condition is `outport_valid_o=0` for both X instances at that edge. Alternatively, the full X state relation may already hold before that edge. No assumption about the numerical range of X outputs or Y inputs is required.

The first-edge condition matters because X reset is synchronous, while `jpeg_idct_transpose_ram` ignores both reset inputs and writes whenever its write enable is high, including a reset edge. If the independently unconstrained pre-reset X data/valid/index differ, they can drive different writes at the first reset edge even when the two transpose memories were initially identical. Holding reset for additional edges does not retroactively clear those RAM words. The ID FIFO similarly resets pointers/count but does not clear its data memory; its `outport_id_o` is an unconditional RAM read. Image-start flush is not a substitute for the stage proofs' synchronous reset.

With the stated coupling and first-edge write condition, both X stage instances satisfy their proved relation after reset and produce identical data, valid and index on **every** subsequent cycle, even when invalid. Equal X signals drive equal writes and controls into the identical, initially coupled transpose; its state and Y inputs therefore remain equal. The Y proof accepts arbitrary 32-bit inputs and gives equal Y outputs, which also makes the ID FIFO pop decisions identical. With common FIFO and input-buffer state and common external inputs, their outputs remain equal. This is a standard substitutivity/induction argument over the unchanged surrounding state; the conclusion is a manual inference from the machine-checked stage obligations and the audited wiring, not a standalone full-IDCT certificate. The assumptions do not prove that a particular board's power-up or reset sequence meets them.

## Reset-memory negative control

`reset-ram-control.v` instantiates two actual `jpeg_idct_transpose_ram` modules. It starts their state at zero, drives reset high, writes different data to the same address and checks whether the outputs can differ. Yosys finds a counterexample: mismatch is 0 initially and 1 at step 3, due to the real synchronous read/write behavior. This demonstrates that the RAM's reset ports do not suppress writes or establish equivalence. It is a **small RAM-level witness**, not a full-IDCT counterexample or proof that an actual board reaches these unconstrained pre-reset X states. The separately audited X valid/data wiring explains why the first-edge condition is needed.

## Reproduce

From this directory, set `BUILD_DIR` to a nonexistent path and `YOSYS` to Yosys 0.52 (paths without spaces):

```sh
BUILD_DIR=/new/idct-audit YOSYS=/path/to/yosys ./run.sh
```

The wrapper elaborates the pinned vendor hierarchy, checks source/proof markers and connections, then runs the bounded reset-RAM negative control. It requires `STRUCTURAL_AUDIT_PASS` and a real SAT counterexample with mismatch 0 at step 1 and 1 at step 3. It does not modify RTL. `results/` holds the clean run's Yosys log, audit output, counterexample log and tool version. The separate stage formal wrappers contain the reset-base, induction and multiplier obligations.

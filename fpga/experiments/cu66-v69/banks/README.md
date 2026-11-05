# CU66 frame-bank controller reference and simulation

`reference.py` is the independent sequential ownership model. `export_vectors.py` applies directed ownership cases and 400 deterministic seeded cycles (`69004601`), then writes cycle-by-cycle input, pre-edge ready, and post-edge state/event expectations to `vectors.txt`. `tb_bank_control.sv` checks every exposed DUT signal against those rows.

From the repository root, regenerate vectors with:

```sh
python3 fpga/experiments/cu66-v69/banks/export_vectors.py
```

The captured Icarus and Verilator builds/runs use the `gamebub-cu66-v69-build` container and are recorded in this directory's `*-compile.log`, `*-run.log`, `vectors.json`, and `results.json`. Verilator was built with `--Wall`; the testbench accepts both simulators' EOF return conventions while rejecting partial rows.

Coverage includes invalid IDs/key references and missing/mismatched P references; retained accepted-reference, front, and pending leases; pending-slot commit backpressure; undrained vblank; atomic safe-swap plus commit; failed-commit abort with a full pending slot; abort priority over a valid commit; safe presentation during abort; drain-delayed candidate release; held-abort begin gating; and reset flush. The bank signals are a single-clock control contract. This simulation does not include memory writes/reads, DMA reset isolation, CDC, a physical panel, or recovery on the board.

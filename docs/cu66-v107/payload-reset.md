# V107 private dequant payload reset experiment

The isolated candidate removes reset and input-acceptance control from 1,027 private payload bits in `cu66_dequant`. It preserves the complete public interface on the measured cycle traces, including invalid-cycle data, partial multiplication results, reset, abort, and output stalls. State, ownership, group count, output ID/error, and all 1,280 public output bits still reset. Existing production and qualified experimental files are unchanged.

Selected source: [`cu66_dequant.sv`](../../fpga/experiments/cu66-v107-payload-reset/cu66_dequant.sv), SHA-256 `579cb5d397e6638c0533fd54250e161612bdaed74117a29475afbab648aec7fb`. Baseline: `fpga/experiments/cu66-v69/inverse/cu66_dequant.sv`, SHA-256 `1ce06c26460a63b69ca9d742edb04ee9654827f883212c4bfe71293e0ed71084`. The edit recipe reproduces the complete candidate, and strict compiler adapters differ only in module name.

## Ownership argument

The private 1,024-bit coefficient vector, one chroma bit, and two scale bits load on every edge whose **old state is IDLE**, independently of `rst`, `abort_i`, and `in_valid`. They hold throughout MULTIPLY and HOLD_TILE. Captures without a transaction, including captures during reset/abort, have no owner.

Every legal entry to MULTIPLY follows an accepted IDLE edge that overwrites all 1,027 bits. The group counter starts at zero. Bad-input and all-zero shortcuts compute their decision directly from the external input, clear the public output, and enter HOLD_TILE without consuming private products. Reset/abort dominates the public machine, clears the public fields, and returns IDLE. A subsequent legal multiply must again overwrite the complete payload first. Private contents can differ while unowned; no private field is exposed as a public debug signal. This is an overwrite-before-use argument, not a claim that unreset storage begins at a defined value.

Unconditional IDLE capture intentionally permits extra idle switching. This experiment targets control/reset load and does not claim lower power. The qualified elastic tuple already had reset-free private storage; this experiment does not take credit for changing it.

## Actual behavioral proof

[`results.json`](../../experiments/python-gamebub-v107/payload-reset/results.json) selects `attempts/20261108T053336577698Z/results.json`, status `PASS`, `actual_RTL_run: true`. Verilator 5.020 compiled the original and candidate together with `--assert -Wall`, and C++ with `-Wall -Wextra -Werror`. The test compares all **1,315 public bits**, without masking invalid outputs, before and after every edge. A separate C++ integer/state model checks packed signed coefficients, quantization constants, partial groups, held outputs, shortcut results, public reset values, and exact readiness/validity.

| Seed | Edges | Accepted | Retired | Reset/abort discarded | Multiply edges | Held-output edges |
|---|---:|---:|---:|---:|---:|---:|
| 107901 | 40,322 | 6,716 | 6,686 | 30 | 23,004 | 3,282 |
| 107902 | 40,632 | 6,716 | 6,686 | 30 | 23,244 | 3,352 |
| 107903 | 40,774 | 6,716 | 6,686 | 30 | 23,236 | 3,502 |

Directed cases cover both chroma choices, all four scale codes, each of 64 coefficient positions, and values `-32768,-2049,-2048,-1,0,1,2048,2049,32767`; each seed also has 2,048 dense randomized blocks. Reset alone, abort alone, and both are held for three edges at every multiply group and held-output phase, followed by restart. Raw input fields change throughout owned work and stalls. Every seed also exercises 512 invalid-IDLE/reset/abort cycles. Acceptance equals retirement plus deliberate discard.

[`audit.json`](../../experiments/python-gamebub-v107/payload-reset/audit.json) independently replays all **121,728** trace edges in Python from immutable compressed CSVs and the frozen CPU quantization constants. It checks the full public data on every edge, all eight multiply groups, kill in IDLE/MULTIPLY/HOLD_TILE, source hashes, snapshot hashes, and the exact source edit recipe. The trace records handshake decisions; the active C++ bench separately checks the raw input protocol and paired ready/valid signals.

The first attempt `20261108T053128323569Z` is retained as `FAIL`: C++ range iteration is unsupported for this Verilator version's wide input port. The fixture was changed to index its 32 words explicitly. No DUT bytes or checks were changed.

## Actual component inference

The source-bound native experiment uses Vivado 2026.1, `xc7a100tcsg324-1`, OOC synthesis, rebuilt hierarchy, Default directive, two threads, readonly existing tools/license, bounded runtime and host-memory checks. Each original/candidate build runs sequentially. A synthetic 10 ns unit clock is for inspecting this component; no board clock relationship or `HD.CLK_SRC` value is invented.

The [selected component receipt](../../experiments/python-gamebub-v107/payload-reset/native/20261108T053458446649Z/receipt.json) and [corrective read-only fanin query](../../experiments/python-gamebub-v107/payload-reset/native/query/20261108T053716594951Z/receipt.json) bind the actual source and retained reports. The actual mapped reset connection is examined for **every** one of the 1,027 named payload FDREs, rather than inferred from source text.

| Synthesized component | Original | Candidate |
|---|---:|---:|
| Private payload FDREs | 1,027 | 1,027 |
| Private payload R pins tied to GND | 0 | 1,027 |
| Total FFs | 2,352 | 2,351 |
| LUTs | 1,580 | 1,578 |
| DSPs | 8 | 8 |
| Flat reset-register endpoints reached from `rst` | 2,352 | 1,324 |
| Flat reset-register endpoints reached from `abort_i` | 2,352 | 1,324 |

The endpoint reduction is 1,028 because synthesis also changes the FSM implementation by one register; the directly bound payload change is exactly 1,027 bits. This is a synthesis connectivity/resource result, not a placed/routed timing or reset-tree result.

The initial native receipt's `ce_port_fanin` / `reset_port_fanin` columns used `get_ports -of_objects` on startpoints and were empty for **both** designs. Those columns are uninformative, and its broad status label alone must not be used as CE evidence. A separately retained read-only DCP query classifies each actual `all_fanin -startpoints_only` object by `CLASS == port`, verifies nonempty baseline port sets and the candidate register-only CE fanin (`FSM_onehot_state_reg[0]/C` as the timing startpoint, directly driving CE from its `/Q` pin), and hashes checkpoints before and after. Its receipt is authoritative for input-control removal. No RTL or DCP was altered to repair the reporting query.

Native synthesis reports zero synthesis warnings/critical warnings. Later reporting retains flat-netlist floorplanning advisory `Netlist 29-101`, OOC missing `HD.CLK_SRC` warning `Timing 38-242`, and empty-fanin notices when querying grounded reset pins. These are disclosed rather than waived. No route, hardware run, four-state startup proof, formal equivalence, full decoder canonical proof, or full parent 100 MHz closure is claimed by this unit experiment. Parent integration requires its own frozen-source canonical run and native timing qualification.

## Reproduce and audit

From the repository root, with the documented existing containers/tools:

```sh
python3 scripts/cu66-v107/payload_reset.py
python3 scripts/cu66-v107/payload_reset/native.py
python3 scripts/cu66-v107/payload_reset/native_query.py
python3 scripts/cu66-v107/payload_reset/audit.py
```

The first three commands create fresh, bounded receipts and require a scheduled heavy-job slot. The last is a lightweight portable audit of retained snapshots/traces/reports; it needs no FPGA tools. Failed runs and their source snapshots are kept.

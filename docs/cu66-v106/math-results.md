# V106 exact coordinate evaluator candidates

Both candidate evaluators pass exhaustive binary-input equivalence against the original helper and an independent Cartesian geometry oracle. Six complete production-source candidates are frozen: NARROW and LUT versions of the inverse adapter, canonical coefficient producer, and fresh-path coefficient producer. Native timing results remain a separate gate: this focused result does not yet demonstrate that the 100 MHz timing requirement is met.

Baseline revision: `eececf35da97c9b14230d464ecde7576cb7840db`.
Selected focused receipt: `experiments/python-gamebub-v106/math/attempts/20261108T004859781567Z/results.json`.
Reproduce: `python3 scripts/cu66-v106/math.py`.
Offline audit: `python3 fpga/experiments/cu66-v106-math/audit_trace.py`.

## Exact changes

NARROW replaces only the `quant_cell` helper's explicitly 32-bit arithmetic with explicitly 13-bit arithmetic. Inputs retain their existing 2-bit plane and 13-bit tile widths; return width remains 11 bits. For all tile inputs 0…8191, division by 90 gives row ≤91 and column ≤89, and the largest pre-return Y result is 2069. The existing 11-bit return wrap is preserved, including all 44 Y inputs whose untruncated result exceeds 2047. Plane 1, 2 and invalid plane 3 retain the exact low-11-bit tile return.

LUT replaces the same helper with combinational truth tables. Because row width 90 is even, tile pairs `(2n, 2n+1)` have identical Y cells. The 8192-input Y function therefore needs 4096 table values. The source organizes them into 64 banks of 64 entries, with eleven 64-bit bit tables per bank; `tile[12:7]` selects a bank and `tile[6:1]` selects a bit. There is no clock, register, handshake, memory write, macro, or external include in the helper. The 704 constants describe the construction; they are **not a measured FPGA LUT count**, and synthesis may optimize or decompose them differently.

Each source has one `v106-edit-recipe-v1` JSON recipe. Applying that single unique helper replacement to the original reproduces the candidate exactly; replacing the candidate helper with the original reconstructs the original complete source byte-for-byte. Guards, metadata validation, error ordering, coefficients, owner state, public widths and cycles are untouched. The storage agent's separate coefficient-write-process changes can compose independently with the helper edit.

## Frozen production sources

All paths below are under `fpga/experiments/cu66-v106-math/`; the adjacent `.recipe.json` file binds the original and candidate hashes and literal edit.

| Candidate | Source | SHA-256 |
| --- | --- | --- |
| NARROW | `narrow/cu66_inverse_stream_v91j.sv` | `4d765060d2764d7e230974ee0d57f34116514fd72ec853f3eb9e9a5ad175dcd8` |
| NARROW | `narrow/cs88_coefficients_v91k.sv` | `41c44eda4021abbaf817d164fd5eb993607616ec177ef4bfeaccd2cb189d2029` |
| NARROW | `narrow/cs88_pipeline_v91i2b.sv` | `e1b364f4296cb697b08384846860a00cb1778103f145aa080a32087db66c6b32` |
| LUT | `lut/cu66_inverse_stream_v91j.sv` | `d8a3fc8b11cbbb61df864fc55ba44242c11094d50f27d33346cbb467bec2ffe2` |
| LUT | `lut/cs88_coefficients_v91k.sv` | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| LUT | `lut/cs88_pipeline_v91i2b.sv` | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |

The selected receipt's `production` list additionally freezes all six recipe hashes.

## Focused evidence

| Check | PASS result |
| --- | ---: |
| Independent Python plane/tile cases | 32,768: 4 × 8192 |
| Actual Verilator input/output rows | 32,768 |
| LUT constants decoded and independently checked | 704 |
| Adjacent Y tile pairs checked | 4096 |
| Preserved Y return-wrap inputs | 44 |
| Largest untruncated Y result | 2069 |
| Complete source bodies verified outside helper | 6 |

The Verilator proof top uses the exact original, NARROW and LUT helper text bound to the complete production candidates. Every output is checked by both SystemVerilog assertions and the C++ testbench. Python independently derives Cartesian row/column cell indices, reconstructs the LUT constants from the actual helper, models the bounded arithmetic, and checks every retained RTL row. This covers invalid plane/tile values and truncation, not just the nominal 5400/1350 active positions.

The existing Verilator 5.020 backend runs with `--assert -Wall`; C++ uses `-Wall -Wextra -Werror`. Compilation uses two jobs and an in-container 300-second watchdog with a five-second kill grace; runtime has its own finite in-container watchdog. The inherited available-RAM/PSI launch gate remains in force. All source snapshots, command lines, compiler output, binary hash and compressed trace are retained. `attempt-ledger.json` records an initial strict unused-upper-bits diagnostic in a named narrow intermediate; the final direct expression preserves truncation without dummy reads or warning suppression.

`trace-audit.json` comes from a separate offline auditor which rechecks source and artifact hashes, literal recipe reconstruction, all LUT constants, all 32,768 retained input/output rows, wrap behavior, and strict tool settings. It binds its own source hash and the selected receipt/summary/trace hashes; it does not import the simulation runner or rerun RTL.

## Next timing gate

The root workflow must measure inverse-only, producer-only and combined substitutions against the frozen V105 GEOMETRY source map, with original dequantization. NARROW and LUT are alternatives; do not combine their helper edits. Preserve the 10 ns constraint and all validation guards. Compare actual synthesis/route area and the measured `mapped_tile → metadata_bad → coefficient RAM WE` cone, then rerun fresh/canonical full-pipeline lanes and the independently composed storage variants. A cheaper arithmetic expression or a truth-table construction is insufficient evidence of timing closure. Full routed setup, hold, pulse and routing checks—and the final worst-path identity—decide the next selection.

This result proves exhaustive two-state combinational helper equivalence. Full-module owner/cancellation/cycle regression, routed timing, board I/O qualification, sustained hardware 30 fps and complete validated decode below 10 ms retain their separate gates.

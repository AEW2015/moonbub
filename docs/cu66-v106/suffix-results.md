# V106 selected-SUFFIX extraction

The suffix-specialization candidate passes **18,522,021 clocked whole-module comparison edges** across two seeds. It removes the PREFIX/state-dependent extraction-amount mux from the selected SUFFIX value while preserving every public output and original clocked update. Native timing improvement remains separately measured.

## Actual measured motivation

The previous combined PREFIX/telemetry synthesis report identifies parser `reservoir_reg[22]` → `out_value_reg[22]`, WNS **−3.897 ns**, 13.857 ns data delay (3.983 ns logic and 9.874 ns estimated routing), 20 logic levels. In the RTL, common `extracted` uses `take_bits`, whose combinational selection includes PREFIX rank/window and state logic; SUFFIX output requires only suffix length/serial controls. The retained report supports studying this dependency; optimized signal names do not prove an isolated source-level delay attribution.

This is a synthesis-stage observation, not this candidate's routed timing. The independent model and equivalence tests establish the substitution's behavior; actual combined routing must establish any fixed-100-MHz improvement.

## Three exact edits over frozen PREFIX

Original: `fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv`, SHA-256 `745a322dad262cbad732aea9af5d57ebfb940a961adc724b7d644b90baf25dbb`.

Candidate: `fpga/experiments/cu66-v106-suffix/br88_rice_elastic.sv`, SHA-256 `8940a4313a1efc88bdc7b55e885ae58d55e0e1f88208659010c5e5eb4e409ef7`.

The candidate adds a six-bit `suffix_take_bits` and 64-bit `suffix_extracted`:

```text
suffix_take_bits = (serial && suffix_left != 0) ? 1 : suffix_left
suffix_extracted = suffix_take_bits == 0 ? 0
                   : reservoir >> (available - seven_bit(suffix_take_bits))
```

Only `suffix_value` uses this independent extraction. The original common `extracted`, `take_bits`, reservoir masking, loaded/consumed counts, cache updates, guards, error priorities, latency and all sequential parser behavior stay unchanged. The original zero-take rule, seven-bit subtraction, logical-shift width and 24-bit suffix accumulation are retained exactly. In particular, serial zero-take still shifts the existing accumulator as before; it does not force the entire suffix value to zero.

A private clocked assertion compares the selected suffix value with the original common-extraction expression whenever state is SUFFIX. **Unconsumed `suffix_value` and `decoded_value` may differ in other states**. Private old/new comparisons for those two values are therefore scoped to SUFFIX; all public outputs and unchanged private controls remain compared on every tested edge.

The three-edit `v106-edit-recipe-v1` recipe is `edit-proof.json`, SHA-256 `7962fdf91885521ead324cd0a361b1c0b49d0f90ae77190ccb27c3a7756e7662`: declarations, selected suffix-value substitution and private selected-state assertion. The complete module interface and all original sequential statements remain byte-identical.

## Clocked actual-module results

Selected receipt: `experiments/python-gamebub-v106/suffix/attempts/20261108T021331840332Z/receipt.json`, SHA-256 `c7d60c6ce67a0b2e137d3f2c964b0f2e83c02fe943fe1fee0287ea488998da43`.

| Seed | Prepared edges | Historical edges | New suffix-domain cases |
| --- | ---: | ---: | ---: |
| 106401 | 611,057 | 8,649,476 | 12,480 |
| 106402 | 611,057 | 8,650,431 | 12,480 |

Each seed retains the complete **1,520-vector corpus × eight serial/fast, 16/32-bit and stalled/unstalled configurations**, **173,061 golden requests/configuration** and **104 directed checks**, plus all earlier full32 cache, rank/window and availability prepared cases. New clocked cases cross every availability value 0–64, suffix-left value 0–31 and serial flag, with zero/all-one/random reservoir and accumulator patterns.

The wrapper instantiates complete production modules with only module names changed. All 13 output names across 27 public port names, all public counters, original parser state and unchanged combinational controls remain compared. The independent C++ oracle checks size/loaded/consumed, both full32 caches, word validation, reservoir/occupancy, original prefix scanning and all six counters every clock. Complete-body reversal and the exact three-edit recipe are independently verified.

The first strict actual compile and both runs passed without failed attempts. Verilator 5.020 uses assertions, `-Wall` and the established module-renaming `DECLFILENAME` exception; GCC uses `-Wall -Wextra -Werror`. Compilation uses two jobs and a 300-second watchdog, taking 3.62 seconds; runs take about 8.38 seconds each under 120-second timeouts and the inherited 100-million-clock watchdog. The existing available-RAM/PSI gate is unchanged.

## Python identity and audit scope

`experiments/python-gamebub-v106/suffix/model.json` records an independent selected-SUFFIX model. It checks **24,960 legal availability 0–64 cases**, **49,152 cases covering all binary seven-bit availability values**, **1,536 zero-take cases**, and **100,000 random full64 reservoir/24-bit accumulator cases**. The universal argument is direct: in SUFFIX, original `take_bits` equals the independent suffix expression, so substitution into the unchanged width/shift/zero/accumulation operations is identical for every binary operand. This does not require a nominal stream size or newly assumed range.

The final `suffix/trace-audit.json` binds its auditor, source/recipe/receipt hashes, model, inherited cache/rank proofs and all recorded checkpoints. Prepared traces log every edge; historical traces remain sampled every 256 edges plus reset/start. The offline checker verifies recorded cache/reservoir checkpoints rather than replaying omitted historical transitions. The actual C++ oracle and old/new comparison check every edge.

Reproduce:

```sh
python3 scripts/cu66-v106/suffix.py
python3 fpga/experiments/cu66-v106-suffix/audit_trace.py
```

Source, recipe, bench, runner and auditor are frozen. Prepared internal states are not full-packet reachability proof; private unconsumed-value differences outside SUFFIX are deliberate and scoped. No four-state, mapped-netlist, achieved-Fmax, hardware 30-fps or complete under-10-ms decode claim follows from these tests. Root integration owns combined regression and native timing qualification at the unchanged 100-MHz target.

# Isolated Y-stage coefficient narrowing

This candidate changes only the five Y-stage coefficient registers from signed 32 to signed 13 bits, retaining all five signed 32-bit data registers and every other line of logic. The seven possible coefficients are nonnegative and at most 4017, so fit in signed 13 bits; reset selects zero. This is an experimental copy, not a production RTL edit. `generate.py` verifies the exact original and candidate hashes and checks that only the module name and five coefficient-width declarations differ after line-ending normalization.

Yosys 0.52 `synth_xilinx -family xc7 -run begin:coarse` for this standalone stage reported 22 DSP48E1 cells for the original and 14 for the candidate. These are generic **intermediate mappings**, not actual target-device resources, final synthesis, a fit, a timing, power or speedup result. The tool logs and warning context are retained in `results/`.

## Formal scope

The Y candidate has an **unbounded, two-state compositional sequential equivalence argument after a synchronous reset edge**, with the default parameters `OUT_SHIFT=15` and `INPUT_WIDTH=32`. All four Y data inputs remain arbitrary 32-bit bit vectors; no X-to-Y range, legal JPEG or image-data assumption is used. All index, valid and frame-control inputs are arbitrary after reset, and data/valid/index outputs are compared every cycle, including invalid cycles. The proof is manually composed from machine-checked obligations, not a single end-to-end proof certificate:

1. The operand miter checks exact equality of `i0`, all five unchanged 32-bit data registers and all five original coefficient registers against sign-extended candidate registers. One-step temporal induction proves the relation from zero state. A separate two-step SAT base case starts from arbitrary initial state, asserts reset on the first step and proves the relation afterward.
2. `product.v` proves for **every** signed 32-bit multiplicand and signed 13-bit coefficient that the 32-bit product equals multiplication by its 32-bit sign extension. Thus no assumption is needed about the magnitude or sign of any data value, even when `i0` wraps in 32-bit arithmetic.
3. A proof-only abstraction replaces the five actual multiplication RHSs on both modules with the same arbitrary 32-bit values. One-step induction proves equality of all 1,054 downstream register bits and all outputs; another SAT check proves the reset base from arbitrary pre-reset state. Equal operands and the multiplication identity establish that real products meet the shared-cutpoint abstraction.

The source generator also creates two isolated mutants: one changes a coefficient assignment, the other inverts a downstream product-register transfer. Both yielded actual SAT counterexamples. Yosys's initial SAT attempt could not import a Y-specific inferred ROM; the reproducible proof script explicitly maps proof-only memories before SAT. See the neighboring `../narrow-x-proof/` for the same methodology. Four-state X/Z semantics, non-default parameters, the combined X+Y design and full decoder equivalence are outside this proof.

## Simulation

A side-by-side stage test exercised 100,000 deterministic pseudorandom cycles of arbitrary 32-bit values, index/control/reset changes and injected signed extremes. Both Verilator 5.020 and Vivado 2025.2 XSim reported `NARROW_Y_COEFF_EQ_PASS`; XSim used the Vivado MCP project flow. These are the same testbench and seed, not two independent stimulus sets.

A separate one-frame behavioral pipeline run used **original X and candidate Y** with the experimental JPEG marker guard, QSPI path, burst memory, functional SDRAM and modeled LCD. The single synthetic 720×480 JPEG produced 345,600 decoded pixels exactly matching the related fixed-color C model and 345,600 ordered modeled scanout pixels, with no modeled LCD underruns. The C model shares algorithms with RTL. One fixture does not establish sustained 30 fps, exhaustive image coverage, real ESP32/Wi-Fi behavior, physical memory timing, implementation or board performance.

## Reproduction

Use absolute paths without spaces, a new output directory per invocation, Yosys 0.52, Verilator 5.x, Python 3 and GNU timeout:

```sh
ORIGINAL=/absolute/path/to/jpeg_idct_y.v CANDIDATE=$PWD/jpeg_idct_y_coeff.v \\
  BUILD_DIR=/new/formal-run YOSYS=/path/to/yosys ./run-formal.sh
ORIGINAL=/absolute/path/to/jpeg_idct_y.v BUILD_DIR=/new/mapping-run \\
  YOSYS=/path/to/yosys VERILATOR=/path/to/verilator ./run-mapping-sim.sh
FPGA_DIR=/absolute/path/to/fpga BUILD_DIR=/new/pipeline-run ./run-pipeline.sh
```

Set `VERILATOR_ROOT`, `PATH` and `PYTHONPATH` as required for the installed Verilator and Pillow. The pipeline builds a fresh candidate copy with the expected module name and excludes only the original Y source, retaining the original X source. The associated FPGA tree and host C-model driver must be present. XSim was run through a bounded Vivado MCP project with the three sources in `/ross-work/idct-y-equivalence/src`; the retained `results/xsim-mcp.py` and `xsim-mcp.log` show the exact MCP flow and PASS check. `results/` also holds the clean proof, mutation, mapping, Verilator and pipeline logs and one verified frame record.

# X-stage sequential equivalence: compositional proof

This isolated study proves unbounded two-state, cycle-by-cycle equivalence of the narrowed X-stage candidate and the original **after a synchronous reset edge**, under the default parameters `OUT_SHIFT=11` and `INPUT_WIDTH=16`. All inputs, indexes and control signals are unconstrained thereafter, including resets. The output data, valid and index are compared every cycle, including invalid cycles. The result is a **manually composed proof from independently machine-checked obligations**, not a single end-to-end miter proof. It does not cover four-state X/Z behavior, other parameterizations, the Y stage, the complete decoder, timing or hardware.

`generate.py` checks exact SHA-256 of both actual DUT sources and checks that, after line-ending normalization, the candidate differs only in module name and the ten operand-width declarations. The generated copies add observation ports or replace multiplier RHSs for proof only; production files are not changed. Exact input hashes:

- Original `fpga/vendor/core_jpeg/src_v/jpeg_idct_x.v`: `99b8681e002d948fa4ed5fbd3a29704634400c31c376b5e120c07d1392ef62c0`.
- Candidate `../narrow-x/jpeg_idct_x_narrow.v`: `d3cefd3651622c793ec92cff696a971a7e22bcdc694541960292d2b499880cde`.

The proof is composed as follows:

1. **Operand state:** `operand-miter.v` compares the actual original 32-bit `i0` and five operand-register pairs with sign-extended candidate values. It also asserts `i0[31:17] == {15{i0[16]}}`, the necessary signed-17 invariant when `i0` is assigned into `mul4_a`. One-step temporal induction proves the relation and invariant from zero state for arbitrary subsequent inputs. Separately, `operand-reset-miter.v` starts with arbitrary pre-reset state, asserts synchronous reset at step 1, and proves the relation at step 2. This explicitly establishes the base case rather than assuming the DUT powers up at zero.
2. **Product cutpoints:** `product.v` proves for every signed 16-bit or signed 17-bit multiplicand and every signed 13-bit coefficient that the 32-bit narrow expression equals the expression using their 32-bit sign extensions. The 32-bit result is the actual registered `mul*_q` width, including any modulo truncation. Because operand equality above is bit-for-bit after sign extension, the five corresponding products are equal at every cycle; no coefficient-range or JPEG-input assumption is needed.
3. **Downstream state:** both actual module copies have only the five product RHS expressions replaced by the same five arbitrary 32-bit symbolic inputs, leaving registers, reset and all other logic unchanged. `state-miter.v` asserts equality of all **1,054 downstream register bits** (five product registers, five delayed products, four valid/index pipeline stages, thirteen arithmetic registers, eight output words, output temporary, valid shift register and pointer), and the three outputs. One-step temporal induction proves equality from zero state for arbitrary shared product values and inputs. `state-reset-miter.v` independently proves the same state/output equality after one reset edge starting from arbitrary pre-reset states. Equal actual products from steps 1–2 satisfy this more general shared-product abstraction, so the two state machines remain equivalent for all later cycles. The composition of these obligations is a mathematical inference; the tool did not build a single transitive proof certificate across cutpoints.

To test that the checks are sensitive, the wrapper creates separate mutants: invert one operand assignment and invert one downstream register assignment. Both produced actual SAT counterexamples (`model found: FAIL`), rather than timing out or merely failing to parse. The original monolithic `equiv_induct` and earlier ten-step full miter timed out; neither is used to establish this result. The proof does not rely on the random simulation results in the neighboring study.

## Reproduce

Requires Python 3, GNU `timeout` and Yosys 0.52 with `sat` and `chformal`; `results/version.txt` records the tested version. Use a **new** work directory and absolute paths without spaces (the Yosys command parser receives these paths):

```sh
ORIGINAL=/absolute/path/to/fpga/vendor/core_jpeg/src_v/jpeg_idct_x.v \\
CANDIDATE=/absolute/path/to/narrow-x/jpeg_idct_x_narrow.v \\
BUILD_DIR=/new/empty-proof-directory YOSYS=/path/to/yosys ./run.sh
```

The script creates the directory itself, verifies source hashes and exact delta, bounds each positive obligation to 120 seconds and each mutation check to 90 seconds, requires exact success/counterexample markers, and prints `COMPOSITIONAL_EQUIVALENCE_OBLIGATIONS_PASS` only when all checks succeed. `results/` contains the complete clean-wrapper logs, including the arbitrary-initial-state reset base cases and mutation controls. The tool version was `Yosys 0.52 (git sha1 fee39a328, ccache clang 18.1.3 -O3 -flto -flto)` via YoWASP in the isolated build container.

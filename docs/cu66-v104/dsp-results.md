# V104 registered dequantizer multiply experiment

The [candidate](../../fpga/experiments/cu66-v104-dsp/cu66_dequant.sv) derives
from the unchanged [original dequantizer](../../fpga/experiments/cu66-v69/inverse/cu66_dequant.sv)
at provenance baseline `1d0a702a758787522723ac52ff44a1bf220c39d1`.
Candidate SHA-256 is
`75ee246145b8374a6954e663f2a418183cbf72774476047d7089eaeb371bae3f`.
All fourteen production port names, the fixed quantizer ROM, sixteen-bit
coefficient operands, twenty-five-bit products, twenty-bit packed output
values, enum states and public edge schedule are preserved. There is no
`USE_DSP`, `KEEP`, retiming attribute or operand-width narrowing.

## One existing microcycle of prefetch

The original computes eight combinational products from its saved input tile
and current group, then writes those products into the public packed result
on each `MULTIPLY` clock. The candidate stores group-zero products on the
accepted, valid, nonzero `IDLE` input edge. Each `MULTIPLY` edge writes the
previously registered products into exactly the original eight output slots;
except at the final group, the same edge registers the next group's products.
The eight original multiply/write clocks and the final held-output protocol
are unchanged.

Input selection is explicit: group zero uses the incoming coefficient/chroma/
scale inputs at accepted input, while later prefetches use the saved tile and
metadata. Inputs presented during `MULTIPLY` or held output remain ignored.
A valid nonzero input acceptance retains the prior public packed output until
the first original `MULTIPLY` edge; unwritten output groups retain their old
values exactly. Invalid coefficients or scale code 3 and all-zero inputs use
the original immediate hold path with zero packed output. Reset or abort
clears the public state and product registers on the same original edge,
including simultaneous valid/ready events. A held valid result retains all
public values until the original output-accept edge.

This exposes a product-register inference opportunity. Whether Vivado maps
that register into DSP48E1 `MREG`/`PREG`, changes DSP count, or improves any
component timing path must be read from the parent's native primitive and
routed reports. Source structure and the passing test are not such proof.

## Actual clocked RTL checks

The [selected receipt](../../experiments/python-gamebub-v104/dsp/results.json)
uses strict Verilator 5.020 behavioral simulation and GCC 13.3 with
`--assert -Wall` and C++ `-Wall -Wextra -Werror`. Both whole production module
bodies are instantiated through adapters that change only the module name;
removing that rename recovers the original and candidate byte-for-byte.
The checker compares all five public outputs, including all sixty-four
packed values even when `out_valid` is low. It checks before the rising edge,
after it, and after the falling edge (the first uninitialized pre-edge sample
is omitted). No internal state is forced.

| Seed | Clock edges | Public samples | Packed-element comparisons | Accepted input transactions |
| --- | ---: | ---: | ---: | ---: |
| 104401 | 289,872 | 869,615 | 55,655,360 | 25,426 |
| 104402 | 289,922 | 869,765 | 55,664,960 | 25,426 |
| Total | 579,794 | 1,739,380 | 111,320,320 | 50,852 |

Each seed includes all **4,097 legal signed coefficient values** from −2048
through +2048 at all sixty-four raster positions, across both chroma choices
and all three valid scales: 24,582 exhaustive-value transactions. It also
checks every coefficient position with −32768, −2049, +2049 and +32767;
invalid scale with zero and nonzero tiles; 512 dense random tiles; input
changes while busy; randomized held-output intervals; all eight multiply
groups interrupted by reset, abort or both; held-output interruptions;
valid/ready/reset collisions; and good retries. There are 36 directed
interruption cases per seed, 75,804 held-output edges total, 130 reset edges
and 54 abort edges. These are component-test counts, not displayed frames or
hardware frame rate.

The C++ oracle is independent of the prefetch mechanism. It derives outputs
from the frozen host `QY`/`QC` tables, scale rounding/clamping, saved accepted
coefficients and the original eight-edge public write schedule. The tables
are parsed from the host codec, not the RTL ROM. Every candidate and original
public result must match that oracle.

The independent Python state/math replay streams **all 579,794 actual rising-
edge trace rows**, checks full packed partial outputs and metadata, validates
input/hold/reset/abort/interrupt totals, and confirms the C++ sample-count
relations. The separate [trace audit](../../experiments/python-gamebub-v104/dsp/trace-audit.json)
reruns that Python oracle and verifies every declared source/artifact hash
and complete-body adapter. The Python oracle is independent of RTL and C++;
the separate audit intentionally reuses the same Python replay function.
The compressed input/output traces retain all actual input noise and have
raw and gzip SHA-256 pins.

## Retained non-RTL failures

The [failed-attempt ledger](../../experiments/python-gamebub-v104/dsp/failed-attempts.json)
records two earlier attempts. A host PSI launch gate denied the first before
any compiler or simulator command. The next compile stopped on a GCC
misleading-indentation warning in the C++ harness. Only testbench statement
formatting was corrected; no design RTL or warning policy was changed.
Both failed receipts and available artifacts remain retained separately from
the selected passing attempt. The selected run required no warning downgrade.

## Reproduce and limits

```sh
python3 scripts/cu66-v104/dsp.py
python3 fpga/experiments/cu66-v104-dsp/audit_trace.py
```

Each run creates a fresh attempt, snapshots inputs, records bounded commands,
retains traces, compiler/simulator logs and executable checksums, and uses
at most two compiler jobs. Executables remain in the external build directory.
The state/math model and simulator are two-state. This is not formal,
four-state, mapped-netlist or whole-decoder proof. It does not measure native
DSP register absorption, achieved clock, complete decoder latency, 30-fps
hardware streaming, or under-10-ms hardware decoding. Parent-owned integrated
and native comparisons qualify those separate claims.

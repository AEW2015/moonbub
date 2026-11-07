# V100 fresh CS88 RTL results

**PASS:** the previously unexecuted V99 new-user q16 key frame 0, P frame 1,
and late inner-CRC fixtures now pass the unchanged V91j RTL pipeline and
unchanged `tb_pipeline.cpp` under both configured memory profiles and two seeds.
This establishes component coefficient, signed20 dequantization and signed24
IDCT residual parity for this fresh source. It does not establish complete
pixel/HUD/C2 publication or hardware frame rate.

## Execution and retained evidence

- Baseline: `f403a5f5149de60ebc128ac57911c4912bec0ddf`.
- Backend: explicitly selected historical Verilator 5.020, with GCC 13.3.0 in
  `gamebub-cu66-v69-build`; behavioral compiled RTL, `--assert -Wall`,
  `-std=c++17 -O2 -Wall -Wextra -Werror`. Build parallelism was limited to two.
- Top: `cs88_pipeline_v91j`; explicit non-project source list. No RTL or C++
  testbench edits. No XSim/Vivado simulation claim.
- Input: three cases and 17,887 transform tile rows from
  [`20261107T1909-new-user-q16`](../../experiments/python-gamebub-v99/cs88/rtl-facing-attempts/20261107T1909-new-user-q16/results.json).
  The key and P contain 7,806 and 3,606 active tiles; the late-CRC fixture
  provides the completed 6,475-tile Y/U prefix of key frame 0.
- Seeds: `100401`, `100402`. Each run completed six case/profile checks,
  thirteen directed checks, and an explicit terminal `TEST_PASS`.
- Bounds: 300-second compile timeout, 900-second simulator timeout per seed,
  plus unchanged testbench frame and ownership-drain watchdogs. Compile took
  8.08 seconds; simulations took 15.39 and 15.44 seconds; retained attempt
  completed in 41.20 seconds including validation/compression.
- Resource gates passed: at least 8 GiB host available RAM and memory PSI
  `full avg10 < 1`; swap occupancy alone was not a failure condition.
- Vivado MCP and exact-part availability were checked separately in the
  [V100 preflight artifacts](../../experiments/python-gamebub-v100/preflight/).
  MCP transport was unavailable; the configured container's batch Vivado
  2025.2 reported no installed `xc7a100tcsg324-1` part. These are exclusions
  from Vivado execution, not a simulator substitution made during this test.

The [selected report](../../experiments/python-gamebub-v100/rtl/results.json)
points to the immutable
[attempt report](../../experiments/python-gamebub-v100/rtl/attempts/20261107T193326863575Z-775b4e04/results.json).
That attempt retains the exact runner/source snapshots, canonical gzip input,
full compile and simulation transcripts, tool executable hashes, binary hash,
and two compressed per-tile transform traces. Every trace record was parsed;
each trace has 107,322 complete 64-sample events covering assembly,
dequantization and residual stages. Plain TSV expansions were removed after
their hashes were pinned. The executable remains outside Git under
`/build/v100-20261107T193326863575Z-775b4e04/` in the configured container;
its SHA-256 is
`12b0f58a8d2bf29f68778ae2f4e5fff0da193d2690fea9f96d90103aa67416b2`.

The independent retained-artifact
[audit](../../experiments/python-gamebub-v100/rtl/artifact-audit.json) verified
all 36 recorded artifact hashes and all 16 FPGA source/testbench snapshots
against the Git baseline. It also matched all 107,322 semantic event keys,
mapping fields and value hashes across the two seeds, ignoring timing and
epoch/token differences.

Reproduce into a new immutable attempt:

```sh
python3 scripts/cu66-v100/run_rtl.py --seeds 100401 100402
```

`--vectors` accepts another directory with the same manifest and fixture
contract. The V100 runner intentionally requires three fixtures, 17,887
transform rows, and at least two distinct seeds; the old V91j runner and its
fixed corpus remain unchanged.

## Workload in cycles

Cycles run from frame start through the final ownership drain. P-frame qcache
preload costs a further 1,350 cycles before frame start; key and late-CRC
fixtures require no preload. These are simulated cycle workloads, with no
conversion to milliseconds or FPS and no newly assigned clock frequency.

| Fresh fixture | FAST, both seeds | SLOW, seed 100401 | SLOW, seed 100402 | Preload cycles | Residual samples per profile |
| --- | ---: | ---: | ---: | ---: | ---: |
| q16 key, frame 0 | 1,386,271 | 1,565,551 | 1,564,284 | 0 | 499,584 |
| q16 P, frame 1 | 850,193 | 935,023 | 935,038 | 1,350 | 230,784 |
| q16 late inner CRC | 1,221,370 | 1,371,568 | 1,371,822 | 0 | 414,400 provisional prefix |

FAST accepts requests and output without random stalls and returns external
memory acknowledgments after one modeled cycle. SLOW randomly stalls input,
output and requests; external writes wait 16–19 modeled cycles and reads wait
18–21. The seeds fix both random streams and address-dependent delay jitter.
Both profiles preserve the original held-offer, tuple stability, epoch binding,
two-bank ownership, refill conservation and request/acknowledgment checks.

## Functional coverage and limits

Each seed made 2,289,536 exact comparisons at **each** of four interfaces:
decoded coefficient tuples, assembled coefficient tiles, signed20 dequantized
tiles, and signed24 residual samples. Across both seeds this is 4,579,072
comparisons per interface. All planes, tiles, qcells, scales, frame/child epochs
and inverse ownership tokens were checked by the existing bench. Each seed
visited 35,774 tiles across its two profiles; completed cases drained all
request and inverse ownership.

The late inner-CRC case reported expected error `147`, preserved the exact
completed Y/U prefix, produced no successful frame completion, and recovered
to a clean key frame without reset. The unchanged directed checks also passed:

- Abort and warm reset with both queued and pending refill ownership.
- Abort and warm reset with an accepted external write; replacement starts
  remain blocked until acknowledgment drain.
- Abort of a held residual tuple and of an owned nonzero-AC IDCT job.
- Partial qcache-load abort, consumed qcache rejection (error `7`), and zero
  frame-epoch rejection (error `65`) before decoder starts.
- Per-case snapshot latching, first-byte cache-tag latching, and exact
  coefficient/mapping tuple values.

No assertion was disabled or severity downgraded. Both runs returned normally
with all required rows and terminal markers; no causal failure, timeout or
tool defect occurred. No UVM environment, SDF timing simulation, VCD/SAIF,
statement/branch/toggle coverage database, standalone inverse boundary corpus,
or wider malformed-packet corpus was run here. The retained focused JSONL
traces are per-tile checked evidence, not a full waveform dump. Prediction,
normalized pixels, RGB565, HUD, reference publication and C2/shared service
remain outside this component. No synthesis, routing, new frequency, CDC,
formal equivalence, hardware validation or full-FPS claim follows from this
simulation result.

## Full V91k standard-conversion qualification

A separate paired regression now qualifies the complete frozen
`cs88_pipeline_v91k` component converted by official sv2v 0.0.13, using the
historical V91k corpus. The conversion SHA-256 is
`f2d9fc81b19d3f8f268a28c2dcfca5bbc1fc3f706e5dce4100887b1be31ad98d`.
The [final qualification receipt](../../experiments/python-gamebub-v100/converted-rtl/verification.json)
is `PAIRED_RTL_PASS`; its pinned
[attempt report](../../experiments/python-gamebub-v100/converted-rtl/attempts/20261107T194621466713Z-cb41164d/results.json)
retains the exact inputs, converted source, original sources, executable
hashes, compile logs, full transcripts and compressed event/canonical traces.

For each seed `911501` and `911502`, original and converted components passed
22 case/profile runs and 21 directed checks. The same-seed full transcripts
(including cycle counters), 378,996 stage-event rows, and actual canonical
SRAM bytes matched exactly. Across both variants/seeds this is 88 pipeline
case/profile runs and 84 directed passes. Each seed's identical actual memory
was replayed through the unchanged separate RGB565 component: 12 additional
case/profile runs, 4,147,200 exact output pixels and eight directed checks per
seed. This paired run completed in 265.69 seconds.

The [verification adapter](../../fpga/experiments/cu66-v100-sim/README.md)
restores nine public unpacked output arrays with wires and slices only; an
independent [port audit](../../experiments/python-gamebub-v100/converted-rtl/port-audit.json)
checked all 308 ordered names, directions and total widths. The final receipt
independently verifies 53 artifact hashes and parses every record in all four
retained event traces. This is full-component source-conversion behavioral
qualification, not formal equivalence or mapped-netlist simulation. It does
not imply that Yosys successfully mapped the full component.

The physical conversion uses `-D SYNTHESIS --exclude=Always`. Original
`always_comb`/`always_ff` constructs remain; synthesis-guarded RTL assertions
are omitted from the converted branch. Original-side RTL assertions and every
unchanged C++ checker remain active. The first strict converted compile stopped
on 245 generated-code warnings; the retained retry uses the documented
[Verilator `-Wno-fatal` policy](https://verilator.org/guide/latest/exe_verilator.html#cmdoption-Wno-fatal)
and rejects warning classes outside the seven observed categories. Every
warning is preserved, original compilation stays strict, and no functional
assertion/checker was edited or severity downgraded. The fresh V99 q16 result
above remains a separate unchanged-V91j proof; these historical V91k inputs
extend qualification to the full converted component and its controls.

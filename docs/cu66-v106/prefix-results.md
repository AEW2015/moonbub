# V106 balanced Rice prefix rank

The balanced-rank candidate passes **18,497,061 clocked whole-module comparison edges**, including the complete generic Rice corpus, an exhaustive 15-bit prefix/window domain and an independent original serial-scan oracle. It moves the late remaining-bit window dependency after the priority search without adding a cycle. Physical timing improvement remains a separate native measurement.

## Actual remaining cone

The earlier closure synthesis report identifies `cached_remaining[25]` → `out_value[0]`, WNS **−3.461 ns**, 13.421 ns data delay (3.632 ns logic, 9.789 ns routing), 19 logic levels with two CARRY4 and 11 LUT6 cells. In the source, `window=min(remaining,15)` gates each iteration of the old successive `found_one`/zero-count scan. The cached remaining value therefore still feeds the priority search and output control in one cycle. The report concerns the earlier closure, not this candidate.

The historical V103 [prefix model](../../scripts/cu66-v103/prefix_model.py) already compared original scanning with an aligned-window formulation in Python. V106 uses its original-scan reference but keeps the existing guarded reservoir-index expressions rather than introducing an alignment or range assumption.

## Two exact source edits

Baseline: frozen Rice-cache source `fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv`, SHA-256 `5ad9997d61a74bd650999c96508c17fc03d17323ab5b1f3689ad991126b3fe5e`.

Candidate: `fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv`, SHA-256 `745a322dad262cbad732aea9af5d57ebfb940a961adc724b7d644b90baf25dbb`.

The candidate evaluates the same 15 `available>i && reservoir[available-1-i]` predicates independently of `window`. A balanced 8→4→2→1 priority tree finds their first true position, or rank 15 when none is true. The old scan's result then follows exactly:

```text
zeros     = min(first_one_rank, window)
found_one = first_one_rank < window
```

For any defined binary 15-bit predicate vector and any window 0–15, the original loop counts precisely that many zeros and reports that same first-one presence. Missing available bits still contribute false predicates through the original guards. There is no new reservoir alignment, payload-size cap, availability-range assumption, narrowed parser counter, modified state/guard/error priority, or extra cycle. The module header, all sequential logic and both full32 cache updates/assertions are unchanged from the Rice-cache baseline.

`edit-proof.json` contains the two uniquely anchored replacements, schema `v106-edit-recipe-v1`, SHA-256 `2eb2d9c06869ffa2d9c313f26406afb9a4874c428b4c4ff06e282eb2959abc51`: new combinational temporary declarations and replacement of the old scan block. Complete-body adapter reversal and exact recipe reconstruction are independently checked.

## Actual clocked comparison

Selected receipt: `experiments/python-gamebub-v106/prefix/attempts/20261108T014422333376Z/receipt.json`, SHA-256 `187b3a3ac812a113c92369c57b0a95043550195d56423e444709eddd2dd61777`.

| Seed | Prepared edges | Historical edges | Pattern × window cases | Availability corners |
| --- | ---: | ---: | ---: | ---: |
| 106401 | 598,577 | 8,649,476 | 524,288 | 8,320 |
| 106402 | 598,577 | 8,650,431 | 524,288 | 8,320 |

Every edge compares complete original and candidate production modules: all 13 output names across 27 public port names, private parser state, reservoir and original combinational controls. The independent C++ oracle retains the original serial prefix scan and additionally checks `zeros` and `found_one`, alongside size/loaded/consumed, the full32 caches, reservoir/occupancy, word validation and all six public counters.

Both seeds retain all **1,520 generic vectors × eight serial/fast, 16/32-bit, stalled/unstalled configurations**, **173,061 golden requests/configuration** and **104 directed checks**. These cover truncation/zero streams, escapes/parameters, malformed source words, failed re-requests, request/input priority, refill, held results, reset and stream replacement. The inherited full32 boundary/cache-consistent inactive probes remain. New prepared cases exhaust all **32,768 patterns × 16 windows**, plus all 65 availability values 0–64 crossed with 16 windows and eight representative patterns. Prepared cases are explicitly not valid-stream reachability proof.

The first attempt `20261108T014325466870Z` stopped at the unchanged resource gate before any tool command: full memory PSI avg10 was observed at 1.57, while available RAM was ample. Its generic FAIL receipt and `failure-note.json` remain retained. After stable PSI below 1, the unchanged retry passed its first actual compile and both seeded runs. Verilator 5.020 uses assertions, `-Wall` and the existing module-renaming `DECLFILENAME` exception; GCC uses `-Wall -Wextra -Werror`. Compilation used two jobs and a 300-second watchdog, taking 3.47 seconds; runs took about 7.4 seconds each under 120-second timeouts and the inherited 100-million-clock watchdog. No warning or gate was relaxed.

## Python proof and artifact scope

`prefix/trace-audit.json` pins its auditor and selected receipt. It independently compares the balanced rank model with the retained V103 original scan over **1,048,576 pattern/window/serial-mode combinations**, **16,640 availability-corner/mode cases** and **100,000 random full64 reservoir cases**. The rank argument covers every defined binary candidate vector; available values 0–64 and arbitrary tail bits test its reservoir construction. This is not a four-state or out-of-range bit-select qualification.

The auditor also retains the exact inherited full32 cache algebra, reverses module renames, reconstructs both source edits and verifies the historical bench's only changes are class/main renames and clock-oracle hooks. Every prepared clock is logged. Historical traces remain sampled every 256 edges and reset/start, as clearly distinguished from the C++ comparator/oracle, which checks every clock. The offline auditor verifies recorded checkpoints, not omitted transitions.

Reproduce:

```sh
python3 scripts/cu66-v106/prefix.py
python3 fpga/experiments/cu66-v106-prefix/audit_trace.py
```

Source, recipe, bench, runner and auditor are frozen. Root integration owns full-packet regressions and the combined native timing flow. No native timing gain, achieved Fmax, board 30 fps, complete under-10-ms decode, or mapped-netlist/four-state equivalence is claimed by these behavioral results.

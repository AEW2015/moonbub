# V106 Rice remaining-bit caches

The full32 cache candidate passes **17,431,845 clocked whole-module comparison edges across two seeds**, including the complete retained generic Rice corpus. Both caches retain exact modular identities with the original size/loaded/consumed registers. This result removes specified source arithmetic from the current cycle without changing parser latency or validation; timing improvement still requires the root-owned native flow.

## Measured critical-cone motivation

The retained first-LUT route report `experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-setup-paths.rpt` contains **12** `parser/size_bits_reg` → `parser/out_value_reg` paths among its top 50. The first runs from `size_bits_reg[1]/C` to `out_value_reg[1]/D`, WNS **−6.531 ns**, 16.479 ns data delay (5.458 ns logic, 11.021 ns route), 27 levels including 10 CARRY4 cells. Names along it include suffix/quotient control, available-bit control and output selection. Source inspection identifies the full32 `size_bits-consumed` subtraction feeding the bounded prefix window/leading-zero controls; `size_bits-loaded` also feeds input sizing, and the old loaded-plus-input equality adds another full32 carry dependency. Optimized net names do not uniquely attribute every physical cell to one source expression. No leading-zero or validation rewrite is included here.

`experiments/python-gamebub-v106/rice/motivation.json` pins that report and extracts the 12 matching path headers. These are actual routed measurements of the previous candidate, not measurements of this new source.

## Exact source changes

Original: `fpga/experiments/cu66-v91/br88_rice_elastic.sv`, SHA-256 `f10846002fc007d4e5c25133fa425aa34ea492ff2738aeedd6aa5de7252acd47`.

Candidate: `fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv`, SHA-256 `5ad9997d61a74bd650999c96508c17fc03d17323ab5b1f3689ad991126b3fe5e`.

The candidate adds full32 `cached_remaining` and `cached_load_remaining`. **Every reset or stream-start edge initializes both to `stream_bits`**, including reset with a nonzero stream size. One existing successful input-load update decrements the load cache by the same zero-extended input-bit count. The two existing successful PREFIX/SUFFIX consumption updates decrement the remaining cache by exactly the same zero-extended take count. Their enclosing guards and original counters remain unchanged. Idle, failed, held, rejected-word and non-update cycles retain the caches.

The combinational remainders select these registers. Last-word validation changes only the exact ring identity:

```text
(loaded + input_bits) mod 2^32 == size_bits
        iff
(size_bits - loaded) mod 2^32 == input_bits
```

No width narrowing, packet-profile assumption, extra cycle, error-priority change, state/port/counter deletion, false path or clock change is introduced. Private non-synthesis assertions check `cached_remaining == size_bits-consumed` and `cached_load_remaining == size_bits-loaded` on **every non-reset/non-start clock**, including inactive cycles.

The eight uniquely anchored replacements are in `edit-proof.json`, schema `v106-edit-recipe-v1`, SHA-256 `92238d4c6053dacb40ce3c02b358b9f144f6375112f2920547f5aa270a2e23ab`. The original module header and every parser statement outside those replacements remain byte-identical.

## Per-clock verification

Selected receipt: `experiments/python-gamebub-v106/rice/attempts/20261108T012856162019Z/receipt.json`, SHA-256 `ad3c76b40eabbe5397c27acdfa734c8ff1d1533832bb15aac0bb63ad448a7f66`. Pointer: `rice/probe-results.json`. Offline evidence audit: `rice/trace-audit.json` under the same experiment area.

| Seed | Prepared edges | Historical interface edges | Historical accepted good words | Historical PREFIX steps | Historical SUFFIX steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| 106401 | 65,969 | 8,649,476 | 359,754 | 2,664,636 | 2,609,222 |
| 106402 | 65,969 | 8,650,431 | 359,754 | 2,664,636 | 2,609,222 |

Every edge compares the complete original and candidate production modules: all **13 output names across 27 public port names**, all public counters, original private parser state and the entire 64-bit reservoir. An independent C++ oracle tracks original size/loaded/consumed values, mode and active flags, reservoir data and occupancy, both modular cache identities, input-word validity and all six public counters. It derives prefix take sizes from its own reservoir/window search and suffix take sizes from observed parser control. This is an independent arithmetic/retention oracle and complete old/new comparison, not a second independently implemented full parser state machine.

Both seeds run all **1,520 retained generic vectors × eight serial/fast, 16/32-bit and stalled/unstalled configurations**. There are **173,061 golden requests per configuration** and **104 retained directed checks** per seed, covering zero/truncated streams, maximum escape, all supported parameter boundaries, invalid `k`/escape, malformed source words, poisoned-stream re-requests, extra input rejection, input/request priority, refill, held responses, reset/start cancellation and all mode combinations. The historical bench changes only its model class/main names and pre/post oracle hooks; its golden checks and schedules remain intact.

Prepared cases exercise 0/1/15/16/17/31/32/33-bit sizes and full32 boundary sizes up to `0xffffffff`, successful load and PREFIX/SUFFIX updates near those boundaries, all reset/start combinations with independently varying input `stream_bits`, and **65,536 arbitrary cache-consistent inactive size/loaded/consumed triples per seed**. The latter verify modular relationships and combinational word-validation identity without claiming valid active-stream bounds or packet reachability.

The explicit backend is Verilator 5.020 with `--assert -Wall` and the established `DECLFILENAME` exception for module-renamed adapters; GCC uses `-Wall -Wextra -Werror`. One two-job compile passed on the first attempt in 3.8 seconds; seeded simulations passed in about 5.9 seconds each. Compilation has a 300-second timeout, each simulation a 120-second timeout, and the C++ harness a 100-million-clock watchdog. The existing available-RAM/PSI gate remains unchanged.

## Python algebra and artifact audit

`audit_trace.py` normalizes affine coefficients modulo 2^32. It proves the update identity `(size-count)-delta == size-(count+delta)`, the reset identity `stream_bits == stream_bits-0`, and that old/new last-word zero tests are additive inverses. These identities hold over the **entire full32 ring**, independently of active-stream bounds or nominal payload sizes. Another **102,197** boundary/random numeric cases include **50,810** wraps as supplementary checks. This is exact algebra for the stated identities, not a formal proof of the whole parser.

The auditor reverses module renames to recover complete production bodies, replays all eight exact edits, verifies original update multiplicities and cache initialization/assertion locations, and proves the retained historical bench adaptation is limited to hooks/renames. It verifies every recorded cache/reservoir checkpoint and all historical verdicts/hashes. Prepared traces log every edge. To keep artifacts bounded, historical traces log every 256th edge and every reset/start; their **45,999 / 46,004 checkpoints** are sampled evidence. The C++ oracle and old/new comparison still run on **every edge**. The offline trace checker does not claim to replay omitted historical transitions.

Reproduce:

```sh
python3 scripts/cu66-v106/rice.py
python3 fpga/experiments/cu66-v106-rice/audit_trace.py
```

The first offline audit counted `consumed<=` inside `out_consumed<=` as well; `audit-failures.json` retains this checker-pattern error. Exact stripped-line matching corrected it. There were no RTL compile or functional failures, warning relaxations, historical-source edits or native jobs in this lane.

Production source, recipe, bench, runner and auditor are frozen. Root integration owns the combined LUT/storage/PLAN/context/Rice full-packet regressions and native measurement. Four-state behavior, mapped-netlist timing, complete-parser formal reachability, board timing/I/O, sustained hardware 30 fps and complete under-10-ms decoding remain separately qualified work.

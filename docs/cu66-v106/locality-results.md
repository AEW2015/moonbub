# V106 coefficient storage locality experiment

The static bank/word candidate passes **41,431 clocked whole-module comparison edges across two seeds**, including the retained inverse boundary suite and an independent 2,048-bit coefficient-store oracle. This establishes bounded behavioral equivalence; primitive mapping, placement/routing and timing improvement are measured separately by the root-owned native matrix.

## Actual V105 timing motivation

The V105 geometry routed report `experiments/python-gamebub-v105/native/20261107T235546839098Z/reports/route-setup-paths.rpt` identifies the worst path from `coefficients/mapped_tile_reg[2]/C` to `transform/coefficients_reg_0_1_124_124/DP/WE`, a **RAMD32 write-enable endpoint**, with WNS −13.124 ns at 10 ns. The 22.507 ns data path has 30 logic levels: 8.977 ns logic and 13.530 ns routing. It passes through the quant-cell/metadata/error network, then a fanout-74 fill-bank control net and fanout-32 coefficient WE net near the endpoint. Their recorded net delays are 1.187 ns and 1.392 ns. This motivates both the separately owned math-helper work and this coefficient-store locality experiment.

The retained Vivado preliminary inference table names `coefficients_reg`, depth 2 × width 1,024, implemented as `RAM16X1D x 1024` for inverse module specializations. This table is a preliminary inference observation, not an independently counted final routed primitive inventory. The routed RAMD32 coefficient WE endpoint confirms that distributed-memory coefficient storage survives in the measured failing cone.

## Isolated source change

Baseline commit: `eececf35da97c9b14230d464ecde7576cb7840db`.

Original source: `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv`, SHA-256 `277e4ea7018a9463c505be09112309de936e8b28b9aada7908994c087595dd08`.

Candidate: `fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv`, SHA-256 `683e4fda539cd0149c6a88dbb2f33e941dde1269be1483cc2333e1ed9ef2f599`.

Two banks × 64 generated 16-bit scalar words replace the single dynamic bank/variable-part-select write. Each scalar word has a fixed bank/word connection and a local bank/index-qualified write condition. Continuous packing preserves the existing `coefficients[0:1]` views used by both `dbg_coefficients` and the dequantizer. Payload contents remain unreset. The candidate adds no latency, synthesis attributes, primitives, validity shortcuts or clock changes.

The new write condition retains the original reset/start/cancel, running, existing-error, input-fault and valid/ready guards. A **later arithmetic failure on the same edge still allows a valid coefficient write**, matching original nonblocking/source ordering. All metadata checks, error priorities, owner transitions, counters, tokens, handshakes and arithmetic producers remain unchanged. The module header and entire original `quant_cell` helper remain byte-identical, allowing composition with either helper-only math recipe.

`edit-proof.json` uses schema `v106-edit-recipe-v1` and exactly two uniquely anchored replacements. Its SHA-256 is `62b7a8adddd02ef5d27d838fe2dd138c9867082ca8354e467d04121d5a62c0bd`. The edits insert before the dequantizer instance and remove only the old coefficient-write statement; the math helper is outside both edits. Parent integration verifies both-order composition.

The intended trade is explicit register-word storage instead of tiny shallow distributed memories, with more local write selection. The source expresses 2,048 payload register bits; actual FF/LUT/CE optimization and timing effects require synthesis/route reports. No mapping or timing gain is inferred from source shape or Verilator runtime.

## Clocked evidence

Selected receipt: `experiments/python-gamebub-v106/locality/attempts/20261108T005122434234Z/receipt.json`, SHA-256 `4ee6012d52fb6b048952b3db04279f352b71bfc42ce824d3ee74db45453c057e`. Pointer: `locality/probe-results.json`. Independent replay/body proof: `locality/trace-audit.json` under the same experiment area.

| Seed | Prepared edges | Historical real-interface edges | Prepared writes | Historical writes | Prepared guarded edges |
| --- | ---: | ---: | ---: | ---: | ---: |
| 106401 | 9,365 | 11,375 | 8,378 | 3,423 | 897 |
| 106402 | 9,365 | 11,326 | 8,378 | 3,423 | 897 |
| Total | **18,730** | **22,701** | **16,756** | **6,846** | **1,794** |

Each edge compares all **42 output names across 58 public port names**, including packed debug coefficients and bank-state arrays, before and after the clock. The wrapper also compares both complete coefficient banks directly, including inactive/stale words. The C++ oracle checks all 128 words after every edge, independently updates coefficient data, expected fill position, token and metadata, and independently computes malformed-input fault priority. Thus the check covers complete retained storage, not merely output samples or the last written location.

Prepared cases cover both banks/all 64 coefficient positions, all 8,100 legal full-grid tile coordinates across the three planes, all eight reset/start/cancel combinations at every bank/word, valid/invalid index and metadata mutations, scales, coefficient bounds, partial completion, token exhaustion and combined-error priorities. Two additional cases per seed specifically exercise valid first/last coefficient writes while the other bank owns a mismatched dequant response; error 5 occurs after the write, and the stored value must survive.

The **retained historical inverse suite** runs through real public interfaces in the same dual-instance wrapper, with only model-class/main renaming and pre/post clock-oracle hooks added. Both seeds pass **48 boundary cases**, 2,688 golden residual samples per seed and **15 directed checks**: coefficient ordering, metadata immutability, partial completion, cancel/reset during partial fill, cancel/reset in math states 1–4, held output, two-bank backpressure and clean retry/drain. Arithmetic source and golden boundary vectors are pinned in the receipt.

The offline Python auditor verifies all compressed traces and their hashes, independently replays the store updates/retention and digest on every clock, checks 128 unique written words, confirms the retained historical verdicts, reverses module-only renames to recover exact production bodies, verifies the two-edit recipe and byte-identical header/helper, and verifies that historical bench adaptation added only the stated hooks/renames. Its replay uses the fault field computed independently by the clocked C++ oracle; the offline replay is not a second full metadata/error-state model.

Reproduce:

```sh
python3 scripts/cu66-v106/locality.py
python3 fpga/experiments/cu66-v106-locality/audit_trace.py
```

The explicit backend remains Verilator 5.020, `--assert -Wall`, with only the established module-renaming `DECLFILENAME` exception. GCC uses `-Wall -Wextra -Werror`. One two-job compile passed on the first attempt, with a 300-second timeout; each seeded simulation has a 120-second timeout and a one-million-clock internal watchdog. The existing available-RAM/PSI gate was retained. There were no failed attempts, warnings downgraded, historical-source edits or extra native jobs in this lane.

## Scope and next measurement

Prepared cases directly set verification-only internal states, metadata and arithmetic-response state; they do not prove full packet reachability. The historical tests supply genuine inverse public-interface transactions, but full CS88 packet integration and six-variant fresh/canonical regressions belong to the root lane. Two-state power-on zeros initialize the test model; FPGA power-on memory contents are not qualified. Warm reset/cancel/start retention after writes is explicitly checked, and the candidate never resets payload storage.

The next native measurement must confirm whether static words eliminate coefficient distributed-memory primitives, quantify FF/LUT/fanout tradeoffs and inspect the new critical endpoint. Timing may remain limited by metadata validation or move elsewhere. Board clocks/I/O, sustained hardware 30 fps and complete under-10-ms decoding remain open until separately qualified. No placement/routing result or bitstream is produced by this focused experiment.

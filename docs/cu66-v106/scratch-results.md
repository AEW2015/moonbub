# V106 sparse scratch position predecode

This isolated candidate targets the measured closure-route `read_segment` → scratch `state` cone (WNS −3.831 ns), which selected a cache word, shifted its bytes, calculated a zigzag rank and compared it with the previous sparse record. The baseline is the frozen V106 PLAN scratch implementation; its carry-save plan arithmetic is retained byte for byte.

The candidate mirrors each original cache write with 16 fixed-offset sparse-position predecodes per bank. All four banks participate, including byte offsets 13–15, where the original logical shift zero-fills missing bytes. The new 19-bit position is exactly `{record[31:19], zigzag(record[18:13])}`. This equals the original full 32-bit arithmetic `block*64+rank` for every possible 32-bit record, because the maximum result is 524,287. No public input, record word, cursor or address is narrowed.

Both demand and prefetch response writes retain their exact enclosing guards, owner and statement order. Constant-bank enables select the corresponding added payload. The sole successful head write also mirrors the consumed position under its original validation guard. Cache and head payloads are not reset; the original cache-valid, cursor and owner conditions qualify their use. AC extraction validates the cached rank with an equivalent rank-only band helper; write-side coefficient validation remains unchanged. No state, error ordering, cancel/drain rule or public cycle is added or removed.

Live assertions compare all valid bank/offset positions with the original shift-and-zigzag expression, and compare the selected current and previous-head positions wherever the sparse validation consumes them. Inactive private payloads are outside the equivalence claim.

## Boundary timing qualification

Predecoding on `mem_rsp_data` deliberately moves the rank calculation to the existing memory-response capture edge. For each constant offset, the new data path is bit slicing/zero-extension plus one six-input zigzag truth table and the original owner-qualified register enable. This is a structural description, not a measured parent timing result. The isolated native flow has no real external input delays; parent input arrival, setup/hold and board CDC qualification remain open. An internal 10 ns pass would not by itself qualify this new input-to-register path. No delay values, false paths, multicycle exceptions or clock changes are added.

## Focused evidence

[Focused receipts](../../experiments/python-gamebub-v106/scratch/results.json) select attempt `20261108T023424705362Z`; schema `v106-scratch-clocked-production-comparison-v1`. The strict Verilator 5.020/GCC run used assertions, all warnings as errors, j2, and finite compile/run watchdogs. Complete original/candidate public outputs, original cache words/cursors/heads and valid position mirrors compare at every evaluation. The independent C++ oracle checks all valid bank/offset positions before and after every edge, plus each consumed head/current position and emitted dense coefficient.

| Evidence | Seed 106401 | Seed 106402 |
| --- | ---: | ---: |
| Main clock edges | 111,571 | 111,458 |
| Complete raw/sparse scratch transactions | 72 | 72 |
| Arbitrary response-line capture cases | 128 | 128 |
| Read-owner reset/abort/stale/error cases | 4 | 4 |
| Independent cache-position checks | 7,673,712 | 7,659,168 |
| Response snapshots / consumed sparse records | 1,937 / 3,314 | 1,937 / 3,311 |
| Qualified previous-head comparisons | 2,978 | 2,975 |
| Memory requests / matching ACKs | 6,114 / 6,114 | 6,109 / 6,109 |
| Independent dense coefficients | 18,432 | 18,432 |
| Historical accepted-write hazards / clocks | 9 / 311 | 9 / 311 |

The 72 transactions per seed cover 1/3/8 blocks, sparse/raw modes, serial clear, write overlap, prefetch and tile overlap with request/response and dense-output backpressure. Every bank and all 16 offset entries are checked, including the unaligned/end-of-line observations even though normal sparse reads use aligned record offsets. These are complete scratch transactions rather than a complete encoded-packet decoder test; parent integrated regression supplies that additional scope.

[Independent offline audit](../../experiments/python-gamebub-v106/scratch/trace-audit.json) rechecks the frozen sources/recipe/adapters, all 3,874 retained cache response snapshots, all 6,625 consumed sparse record rows and 5,953 qualified previous-head comparisons. It uses a literal zigzag permutation separate from the production helper, checks all 524,288 upper-record geometries and the 256 band/raster cases. All 223,651 clock edges (including historical cases) passed the actual comparison. Offline replay is over response/read event rows; the frozen clocked C++ bench checks all valid positions on every evaluation.

The independent Python model additionally passes 262,144 fixed-offset line probes and 262,144 full-32-bit record/address random probes. The exact concatenation identity is independent of low 13-bit coefficient payloads, alignment and record validity; neither the random model nor reachable simulation is a formal proof of arbitrary internal states.

[Attempt ledger](../../experiments/python-gamebub-v106/scratch/attempt-ledger.json) retains three failures before the selected pass: Verilator 5.020 unsupported nested procedural NBA array writes (recovered with explicit constant NBAs), a missing C++ QData unpack overload, and a missing bench reevaluation after cancel release. Assertions and strict warnings remained enabled throughout. No production assertion or public-equivalence failure was observed. The documented Verilator limitation is [BLKLOOPINIT](https://verilator.org/guide/latest/warnings.html#cmdoption-arg-BLKLOOPINIT).

## Frozen source

- Baseline PLAN scratch SHA-256: `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48`.
- Candidate `fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv` SHA-256: `0ee1196e2f0cafdf52742656d4c1a53604c79544c339b171989ad2785f051f8c`.
- Exact nine-edit recipe SHA-256: `e63235fca7cb34360c75a8ae5b2532c2d335088df7029618a16ac0fb78cc6796`.

Full pipeline integration, native area/timing and the parent I/O/CDC qualification remain separate gates. There is no hardware FPS or complete validated decoding latency claim.

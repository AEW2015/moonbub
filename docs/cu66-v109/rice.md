# V109 Rice prefix contingency: prepared, not selected

This source-only contingency removes the `available > i` mask from the fifteen fixed prefix taps before the existing balanced first-one tree. It starts from the actual selected V107 parser, SHA-256 `f39c3f90d0242097ea3cd2693e6f4d99e58e33a0b49c644c720497f50e6777dc`. Its candidate SHA-256 is `dfa58d806ce93ab273f0eb4a2d45b391198ab4bee9ce33aea324d5285d1cc5df`. The [recipe](../../fpga/experiments/cu66-v109-rice/edit-recipe.json) is exactly reversible. No existing qualified source, harness, proof or native script is modified.

The source reasoning follows the [V107 guarded-use analysis](../cu66-v107/next-timing-cuts.md). Nonserial PREFIX consumes only when `available >= window`. Every bit within the selected window is then valid in both versions; a later first-one rank clamps to the same window and yields the same zeros/found/take result. Serial PREFIX consumes one fixed bit and does not use rank. SUFFIX extraction is independent. Input acceptance, request handling, empty-prefix and sticky-failure priority, reset/start priority and wait/stall accounting remain unchanged.

The complete original assertion block remains byte-identical. A supplementary assertion compares the selected nonserial PREFIX zeros/found/take result with an independently calculated masked reference. The source adds no public port, stored operational state or public cycle.

Raw, unused combinational ranks can differ when arbitrary unowned bits are nonzero. For example, with no available bits and a high unowned bit, masked rank is 15 and unmasked rank is 0; no consuming edge is permitted. With three available zero bits and an unowned one at index five, raw ranks differ but both selected results consume three bits and report the same truncation. These differences are explicitly private. No public value, invalid output, counter, stored register or normalized reservoir comparison is masked or relaxed.

The independent model exhausts all 32,768 possible fifteen-bit prefix patterns. It checks each word against both an independent linear rank and the balanced tree, then groups exactly equivalent masked/unmasked first-rank/first-bit classes. Across every available count 0–64, window 0–15 and serial mode, the model covers 68,157,440 represented combinations in 33,280 exact guarded classes. It assumes no zero padding in unowned bits. [The result](../../experiments/python-gamebub-v109/rice/model.json) is a source/model result, not an RTL qualification.

Preparation commands are:

```sh
python3 scripts/cu66-v109/rice/prepare.py
python3 scripts/cu66-v109/rice/model.py
python3 scripts/cu66-v109/rice/qualify.py
```

The focused command is prepared for a future explicit heavy-slot grant:

```sh
python3 scripts/cu66-v109/rice/qualify.py --run
```

Its complete old/new parser wrapper compares every public output, including invalid values and all counters, and every stored register including the full raw reservoir. It also checks every guarded PREFIX/SUFFIX semantic. It retains the complete existing V107 independent low-queue oracle, 6,096 request-parameter cases, full-size malformed-word and prepared-state cases, historical V91 corpus, all eight historical serial/word-size/stall configurations, resets, restarts, suffix cases and backpressure checks. The inherited prepared-state assignment is adapted only because the old parser is now actual V107 MSB storage rather than the historical V106 low-aligned store; both complete modules receive the same aligned state, while the independent normalized queue oracle is unchanged. All original historical cases execute against both modules in the miter.

Seeds are 109701 and 109702. Each invocation is bounded to 4 GiB memory with no extra swap, two CPUs, one compile job and finite compile/simulation watchdogs. Source snapshots, original fixtures, vector hash, logs, binary hash, compressed traces and failures are retained when run. Preparation does not decompress/replay the historical corpus.

No focused RTL, canonical pipeline or native trial has been run for this contingency. It remains unselected. The synthesis availability-prefix cone motivates readiness only; final routed measurements must determine whether this cut is relevant, and no clock improvement is claimed.

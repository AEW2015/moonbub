# V109 redundant cache-bank owner

This narrow candidate starts from the frozen V109 prefetch scratch body, SHA-256 `742726be34e0560b72f3cd0026edcd9be44bffbede5200a179edd483c24fca34`. It targets V108's measured secondary `read_segment` to scratch-cursor cone (−1.957 ns), independently of the already qualified prefetch arithmetic cut. No timing improvement is claimed before native measurement.

The [candidate](../../fpga/experiments/cu66-v109-bank/packed_scratch_v91g2.sv), SHA-256 `1ff4901cdaa98ef5267215f7454042a95d2dc001234caf5b4e4d44f0c6283843`, adds four redundant one-hot owner bits alongside both original binary `read_segment` assignments: DC/RAW fetch captures bank 0, and AC fetch captures the current bank 1–3. There is no additional cycle and no public interface change.

Each bank shifts its current cache word and selects its current offset position locally. The captured owner selects those local words/positions and the live cache tag/valid/prefetched hit. The decision is recomputed from the current registers, preserving foreground/background response forwarding. Foreground response writes and prefetched-bit consumption use the redundant owner with fixed bank indices. Background prefetch ownership and updates are unchanged. The original procedural ordering—consume, background fill, foreground fill—is retained when simultaneous writes overlap.

The original binary selector has no reset. Its redundant decode likewise holds through reset and cancellation; both are captured together before the FSM first consumes a cache line. New simulation assertions check the exact binary/one-hot relationship and live word/position/hit selection on every subsequent edge, including warm resets, failure and invalid cycles. A verification-only observation flag marks the first existing owner capture. All original assertions remain byte-identical. This is an owned-state proof and does not claim arbitrary four-state startup equivalence for unowned private registers.

The [reversible recipe](../../fpga/experiments/cu66-v109-bank/edit-recipe.json) records every substitution. Source preparation and model commands are:

```sh
python3 scripts/cu66-v109/bank/prepare.py
python3 scripts/cu66-v109/bank/model.py
python3 scripts/cu66-v109/bank/qualify.py
```

The source-only model checks 262,144 combinations of four banks, sixteen byte offsets, cache-valid masks, prefetched masks and matching-tag masks, plus 512 simultaneous foreground/background/consumption update combinations. It is explicitly not an RTL verdict.

The focused command, after the root grants a heavy slot, is:

```sh
python3 scripts/cu66-v109/bank/qualify.py --run
```

This compiles only the complete frozen prefetch scratch and the complete new bank scratch, with transparent observation adapters. The V106 full scratch bench, independent dense/position/rank goldens and accepted-write hazard oracle are byte-identical; the qualified V108 coherent prefix/threshold/capacity wrapper is unchanged. Every existing public, invalid, debug, counter and memory-request comparison remains active. Seeds 109501 and 109502 must each complete 72 transactions, 128 corrupted response cases, four physical read-owner cases, every bank 0–3 and every offset 0–15, including resets, stale responses, malformed records and foreground/background interactions. No four-body hierarchy is rebuilt for this focused test; the root's full canonical pipeline is a separate composition gate.

Each Docker invocation is bounded to 4 GiB memory with no extra swap, two CPUs, one compile job, no network and a finite watchdog. Receipts retain exact source snapshots, logs, binary hashes, model inputs and compressed traces, including failures. Preparation alone does not qualify the candidate.

An additive `tb_bank.cpp` runs the complete unchanged inherited suite first, then adds 48 transactions using nine and seventeen blocks across all legal sparse/RAW service profiles. The existing independent packet builder includes AC data in sparse transactions. These cases cross DC line boundaries 7→8 and 15→16 while every unowned begin sideband changes each cycle; the same original dense, request, cache-position and rank checks stay active. This supplements the inherited one/three/eight-block cases without modifying or replacing their checks.

Focused result: **PASS**, actual RTL executed. The selected [receipt](../../experiments/python-gamebub-v109/bank/results.json) points to attempt `20261108T111224012564Z`, whose receipt SHA-256 is `df2494f8b7395370f14bccf303737272d6bef45a1f07ee8e72ce0908bbc806c3`. Both seeds completed the unchanged 72-transaction, 128-corruption, four-read-owner and nine-hazard suites, all four banks and sixteen offsets, plus 48 additive line-boundary transactions. Total clock edges were 291,675 and 291,203, with 128,596 and 128,409 live begin-noise edges respectively. There were no focused compile, assertion or RTL failures. Production remains frozen at `1ff4901c…`; full canonical composition and native timing remain separate required gates.

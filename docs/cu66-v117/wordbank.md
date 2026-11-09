# V117 optional reconstruction wordbank and direct bank enables

Composition C candidate: the fresh strict two-seed reconstruction proof passed and matched every B baseline terminal field and cycle. The full decoder, transport, peer and parent regressions also passed with exact B event/cycle agreement. Native timing measurements remain pending; this source does not alter the preserved B reconstruction or its receipts.

## Measured reason for the experiment

Actual B125 routing finished at WNS −2.202 ns, with its fifty worst paths in ingress descriptor arithmetic. Separately, the routed high-fanout report identifies reconstruction's CARRY4-driven `residual1[-1111111107]_1[0]`, fanout2152 entirely on Data/Other loads, with worst slack −1.379 ns. A separate residual/reference reset net has worst slack −0.984 ns. The retained top50 report does not include a complete path through the fanout2152 net, so identifying the exact insertion-index cone remains a hypothesis rather than a proven full-path classification.

The already-qualified B canonical payload banks have CE startpoints limited to registered COPY state and tail owner and a constant-zero reset pin, but their routed fanout512 CE nets still show −0.742/−0.235 ns worst slack. The native reports establish locality, not closure. The candidate tests two bounded RTL structure changes before any composition C native run.

## Exact changes and preserved behavior

The existing dynamic `residual[int'(fill_index)*24+:24] <= in_value` assignment becomes a sixty-four-iteration elaboration-constant loop, selecting one constant24-bit word with `fill_index == 6'(word_index)`. It remains in the same always_ff accepted-tuple branch, on the same edge, behind the same whole-owner validation and error priority. Every reset, MODE_WAIT bulk clear, residual/reference value, mode, state and physical debt transition is retained. In particular, copy mode still receives its required zero residual, avoiding a silent stale-residual corruption.

Two physical bank-enable FFs default0 on every central FSM edge and are armed only on the existing valid MATH_WAIT→COPY transition using the existing owner tail. At the following existing COPY edge, each predicted strobe equals the old state-COPY/tail decode and directly enables that bank's payload/tag copy. No extra state or edge is introduced. A reset/cancel arriving at COPY still permits exactly the same inactive physical bank copy while revoking all logical/public ownership; the old strobe is sampled before its default0 NBA. The original `storage_copy`, `owner_copy`, state/tail observations and all public ports remain unchanged.

Additional assertions check both predicted enables against the original physical predicate at every initialized preedge, including kill-at-COPY, and reject simultaneous grants. All old assertion blocks remain byte-identical. There is no reset removal, latency relaxation, RTL attribute, retiming directive, timing exception or physical-flow change.

## Qualification and independent baseline comparison

The new production/probe bodies have a reversible recipe from qualified R5b. The probe remains a lossless module/geometry-port adapter; its bench is byte-identical to the current qualified reconstruction bench. The new runner first independently checks the full original derivation, selected R5b raw receipt, every baseline source/artifact hash, strict commands and original terminal records.

Root will execute both original seeds117311/117312 using Verilator --assert -Wall, C++ -Werror and compiler -j1, under the same2CPU/8GiB/no-extra-swap limits. Each new run must retain three full frames, 32,768 geometry cases, all46 directed cases, both physical kill-COPY checks, held-head storage/whole-owner checks, reference-tag/debt/reset/fault and retry checks. It must then equal **every** field in its independently retained baseline terminal record, including total cycles, key/inter-frame cycles, overlap, held samples, physical debt and residual counts. This is an actual new RTL run requirement; the old proof is a comparison control, not reused execution credit.

The baseline raw receipt is [20261109T111821839417Z](../../experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T111821839417Z/receipt.json), SHA `ab82508fed471cec452db2edf7308933f01921d8dcf7d8f3fe01315d37c3d906`. Its seed117311/117312 total clocks are1,948,079/1,948,093; key frames557,496 each and inter frames685,259/685,493. The new runner fails honestly on any mismatch and sets actual_RTL_run before invoking the simulator, preserving failure logs and snapshots.

Run only through Root's global heavy-job coordinator:

```bash
python3 scripts/cu66-v117/reconstruct_wordbank/qualify.py --run --root-grant ROOT_GRANTED_V117_RECONSTRUCT_WORDBANK
```

The independent selector is `experiments/python-gamebub-v117/reconstruct-wordbank/results.json`. There is no source selection or timing success until focused qualification and C's full/peer/LIVE/native proofs complete.

## Prepared peer fault-state adapter

The isolated `fpga/experiments/cu66-v117-peer-wordbank` fixture derives reversibly from the same frozen V115 original plus all existing V117 edits. Its header is byte-identical. The existing prepared post-fail injection additionally clears both new bank-enable FFs, reproducing the real central fail-edge defaults without clocking an extra edge. All old need checks remain; an added check verifies these flags are zero. No accepted scratch, reference or candidate physical lease is assigned, cleared or hidden. Original B peer sources and proofs remain frozen.

The new fault contract pins the actual current inverse/reconstruction fail-task bodies, the additional default FF effects and complete injected-body hash. Root must select this isolated fixture for C peer verification before running C.

## Limits

No measured timing gain is claimed. Constant word selection may change LUT/carry mapping, and direct FF enables may improve their source cone, but only actual C synthesis/place/route can establish resource and timing effects. Full-parent routing, physical SDRAM/ESP32 behavior, hardware30fps and validated under-10-ms decoding remain separate open milestones.

## Preserved compile failure

The first focused attempt [20261109T124955603501Z](../../experiments/python-gamebub-v117/reconstruct-wordbank/attempts/20261109T124955603501Z/receipt.json) failed strict compilation with `actual_RTL_run=false`. A missing trailing separator in the generated replacement joined the closing `end` to `count_residuals`. The error and snapshots remain preserved. The recipe now appends the required newline/indentation and regenerates production and probe; no intended logic, bench, assertions, cycles or baseline checks changed. Fresh strict retry [20261109T125304434518Z](../../experiments/python-gamebub-v117/reconstruct-wordbank/attempts/20261109T125304434518Z/receipt.json) passed both seeds, with every terminal field and cycle exactly matching the B baseline. Independent review is in [wordbank-independent-review.md](wordbank-independent-review.md).

## Candidate pins

- `fpga/experiments/cu66-v117-reconstruct-wordbank/cu66_reconstruct_stream_v91k.sv` — `6bef0bea8d721bc9550dd0a3c7af73e8aa6e793b8b44c683bef42897a5e25bc4`
- `fpga/experiments/cu66-v117-reconstruct-wordbank/reconstruct_probe.sv` — `69955421a5fab8ee6de903c7ed6bb6356680e8b8b179a7e6b8a426a2df1c125a`
- `fpga/experiments/cu66-v117-reconstruct-wordbank/tb_reconstruct.cpp` — `f9dec8fc8da71ff00a7a78f247c0ab20bc565e6e6929ee74234f0e23118b7f8e`
- `fpga/experiments/cu66-v117-reconstruct-wordbank/wordbank-edit-recipe.json` — `c1d77624b461a22a346563fb1f55a65b6605dd469048d8b6d2ef1c4e1743420e`
- `fpga/experiments/cu66-v117-reconstruct-wordbank/reconstruct-probe-recipe.json` — `95cbe7b6f112a945c94bb1cb91d31725f77b8aad82af1f1d28a880c6ac7caa58`
- `scripts/cu66-v117/reconstruct_wordbank/qualify.py` — `d4c99a48340a4509a4e7c2ee8c5b1504ed023004946a34b5ef0df31f07ea42e7`
- `fpga/experiments/cu66-v117-peer-wordbank/tb_peer.cpp` — `a3587961a1ca412b08513cf536b637f67d02494e43e1fb01a7811df349ce887e`
- `fpga/experiments/cu66-v117-peer-wordbank/derivation.json` — `a48973a852146e30e3d4a3901c539d5101233a7b4d6fa72b509b4a40774a5547`
- `fpga/experiments/cu66-v117-peer-wordbank/fault-injection-contract.json` — `d426bf1903b71199a1748fe6a07f078524dee2650650e00978c04ec75bf57390`

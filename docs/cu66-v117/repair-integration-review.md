# V117 composition C integration review

Read-only preparation review, 2026-11-09. C is the selected B composition plus the new synchronous-ingress bound preparation. No C simulation, native preparation, synthesis or implementation was executed by this review. Missing unfinished ingress source/proof remains a prerequisite, not an audit failure. Shared A/B tools and RTL were not edited.

## Findings — static integration PASS

The executable composition is consistent: eight replacements in the frozen eighteen-source alias contract, eight focused selectors, and exact agreement between `spatial_c.OVERRIDES`, native policy `candidate_aliases`, and `focus_source_paths`. The ingress alias names the original synchronous ingress slot, not a nineteenth source. Main and peer use eight-replacement checks; LIVE imports C's source preparation and verifies its selected canonical source origins. The corrected two-owner harness hashes match their pinned values.

The causal-provenance gap found in the first review is repaired. The policy now includes both V116C125 and actual A125 in `comparison_controls`. The existing native qualifier independently verifies both receipt SHA/clock/WNS and all five routed report hashes, then reparses timing/routing before preparing C. This review independently rechecked both actual receipt pins and all ten report hashes. A125 remains the actual routed ingress descriptor-bound cause, WNS −1.925 ns, receipt SHA `4cf20bb3d05c8adcbd3d7c9d5c48011a3a9e276e75878e000c3efcff06a31204`. Launch reruns qualification against the frozen source contract.

LIVE C retains stale wording (`both V116 overrides`, B-specific comparison assertion labels). These labels should identify inherited B scheduling and C ingress preparation accurately, but the actual paths, selected source bindings, eight-replacement gate, and semantic comparisons are correct.

## Retained checks

Strict assertions/warnings and source-bound command/artifact receipts are inherited unchanged. C main/transport keep original independent canonical byte/golden, held-transfer, accepted request/ACK, error, reset, drain and finite-watchdog checks. C peer retains the new two-owner post-fault adaptation and original physical-debt accounting. LIVE retains reversible derivation, every original functional need, exact byte/hash/C2/HUD and publication/drain comparisons. Its changed schedule is explicit rather than claiming old-cycle equivalence. Admission's lossless compile packaging remains independently checked; the additional ingress source does not alter that packaging.

Native preparation reconstructs seventeen SV plus one SVH aliases from the frozen V115 contract, binds focused and peer receipts to current source hashes, requires C canonical/transport proofs, snapshots fresh RTL, loads the selected 8 ns/10 ns constraint before synthesis and requires an independently pinned preflight audit. Fixed part, method, timeout, memory/swap and resource-pressure gates remain unchanged. Source identity uses alias-to-content hashes, and dispatch records are counted across V117, preventing path renames from resetting the global budget. The actual frozen master permits three initial 125 MHz and two initial 100 MHz trials (five total), at most three source compositions and two positive fresh repeats, at most one repeat per clock. Its current SHA matches the policy pin.

This source review does not resolve the separate actual B LIVE cancellation failure. That failure is preserved; an isolated diagnostic-only exact replay was prepared to determine the leaking public diagnostic channel before proposing a wrapper fix. No C success or hardware throughput claim is implied.

## Reviewed snapshots

- `scripts/cu66-v117/spatial_c.py` — `30be126d4646a751123fa3f4c6f322c1bf66ab9317f9e3fb5f847bb6105bc795`
- `scripts/cu66-v117/peer_c.py` — `f8a3af3476510fbcd17999eb9213d9fb43776eb548bca3be681801089333ea69`
- `scripts/cu66-v117/live_c/qualify.py` — `07dc32ede622cefdce0a223e5591c0eb6721f207abc0ec6d5067638b18b732bb`
- `scripts/cu66-v117/native_repair.py` — `fb4ff549345f171766d151b043ecf19426971417789e6fcfbf6e55cd1ec05874`
- `experiments/python-gamebub-v117/repair-study/study-policy.json` — `c8e571f28d56cf7beeaa9fceba92bf0b80427ffe2c0248ddf1d035b9dd86532d`

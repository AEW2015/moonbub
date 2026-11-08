# V110 producer readiness predicates

This narrow candidate removes the selected producer's live FSM and eleven-bit cache-zero reductions from operational readiness. It derives from the actual current V109 fault producer, SHA-256 `5f18c913b6f2702e8f1036ba70b3ba7328d7cdbdfbc8810972c577bee167e86b`. It changes only `fpga/experiments/cu66-v110-ready/cs88_coefficients_v91k.sv`; it does not change child modules, top acknowledgement/cancellation, protocol latency, cache contents, public ports, counters, invalid outputs or original assertions.

The actual COMBINED final route `experiments/python-gamebub-v110/native/20261108T132110377648Z/receipt.json` is negative at the fixed clock: WNS −1.700 ns, TNS −6,860.993 ns, 12,612 setup-failing endpoints. Its producer-state-to-ingress-buffer CE family motivates this source cut. The earlier placed cache-count-to-readiness path supplies secondary motivation; it is not substituted for final route evidence. Both old source/proof namespaces remain frozen. This candidate has no native result.

## Exact source construction

The reversible [recipe](../../fpga/experiments/cu66-v110-ready/edit-recipe.json) inventories every original write and line. Each of the **31 actual state assignments** is replaced by a local `begin/end` statement block containing that original assignment followed by `frame_running_owned <= predicate(next_state)`. Nineteen destinations are active; twelve are quiescent (IDLE once, FAILED ten times, FINISHED once). The compile-time REFILL_STREAM/REFILL_REQ choice is active in either branch. Existing single-statement if/else/case arms retain their original scope because the pair is itself one statement. Nested original blocks retain their ordering and implicit holds.

An accepted start first assigns ADMIT/true, then an invalid/nonmonotonic epoch assigns FAILED/false later in that same original block. The later assignments still win together. All queue, child, admission, entropy, nonce, replay, bounds and ownership failures, plus final NEXT_PLANE completion, receive their own exact next-state predicate.

The **three original cache-count assignments** receive `cache_nonzero_owned`: reset/abort zero gives false; accepted terminal cache beat zero gives false; increment gives `(11'(cache_count+11'd1)!=11'd0)`. The explicit width preserves modulo-2048 assignment behavior, including prepared count-2047 wrap, while the original increment assignment remains byte-identical. Legal loads terminate at count 1349 regardless of last/data errors. Accepted start and all other hold branches leave the redundant bit held just as they leave count held. Malformed data, early last, missing last, first-byte tags, cache-error priority and one-shot completion remain unchanged.

`frame_running` becomes an alias of the new running register. `busy` and `start_ready` use the redundant cache predicate in place of the corresponding count reduction. Every other original count use stays unchanged. Live `child_busy`, `child_draining`, reset, abort and accepted-start priority retain their original consuming edges. No cross-process readiness credit or delayed status is introduced.

After the first reset/abort initializes the original and redundant state, two assertions compare both flags against the original state/count expressions on **every** edge, including resets, aborts, accepted starts, failures and sticky holds. Every original assertion remains intact.

## Verification scope and reproducibility

```sh
python3 scripts/cu66-v110/ready/prepare.py
python3 scripts/cu66-v110/ready/model.py
python3 scripts/cu66-v110/ready/qualify.py
python3 scripts/cu66-v110/ready/qualify.py --run
```

The source/model audit reverses every edit, confirms all original state/count/error/fault assignments are unchanged, classifies all 31 state writes and three cache writes, checks accepted-start/FAILED last-write priority, exhausts 65,536 count/control combinations across every eleven-bit count including wrap, and checks 65,536 state-predicate pairs. This is a two-state algebra/source audit, not formal HDL equivalence or actual RTL execution.

The focused miter instantiates the **complete actual original/candidate producer bodies** with the nine actual selected child bodies from the qualified COMBINED+dequant source contract. Unused arithmetic/top bodies are not substituted or stubbed. The existing V107 admission compile packaging is split losslessly into its original three fragments with exact fragment hashes; the production source is unchanged. Every public output is compared, including invalid values, counters and unpacked observation arrays. Additional comparisons cover producer owner/control registers and the entire raw 1,350-word scale RAM.

An independent cache protocol oracle predicts count, first-beat FID/generation tags, completion/error priority, accepted start, actual RAM commit/address/data, and retained known RAM contents. Cases include complete 1,350-beat preloads with random idle gaps; invalid data at first/interior/final positions; early last; missing last at the cap; fresh retry after bad preload; partial preload; warm abort; start plus stalled final beat; start plus first beat; all reset/abort/start conflicts; and invalid epoch ADMIT-to-FAILED priority. Verification-only direct counter preparation covers all 2,048 values with data 3 suppressing any out-of-range RAM write; those states are explicitly not represented as legal stream reachability. Original assertions remain enabled during these tests.

This focused test covers cache/readiness and admitted/failed/abort control behavior, not a complete frame. The existing independent frame/pixel/entropy/reference goldens belong to the full canonical pipeline harness; root must replay them for the exact proposed composition before selection. The unit does not invent a producer pixel golden or claim every state transition was reached by packets. All-source pairing plus the unchanged full canonical checks are separate evidence.

Strict Verilator `--assert -Wall`, C++ `-Wall -Wextra -Werror`, one compile job, two CPUs, 4 GiB memory and memory+swap, network disabled, pressure gates and finite watchdogs are mandatory. Every attempt retains source snapshots/hashes, logs, failures, trace, binary and receipt. Source/proof files freeze only after actual focused PASS.

## Retained attempts

- `20261108T135014778068Z`: compile failure before RTL. The initial generator appended paired statements to original bare if/case arms. It was corrected to wrap each pair in a single begin/end statement, preserving original branch scope.
- `20261108T135053508001Z`: strict Verilator width warning before RTL. The new next-count expression used unsized one; explicit eleven-bit operands corrected the predicate without changing the original count assignment or adding suppression.
- `20261108T135136942588Z`: C++ compilation failure before RTL. The new bench assumed a range interface for Verilator wide input storage and had an unbraced loop warning; indexed initialization and explicit braces corrected the checker.

- `20261108T135230514047Z`: strict compile succeeded; 14,447 actual edges passed all public/state/RAM/oracle comparisons before a new driver assertion sampled stale `start_ready` after deasserting abort without evaluation. The driver now reevaluates controls before that same retained readiness assertion. No production source changed and no equality check was removed.

The selected candidate source after those preparation repairs is SHA-256 `b5f9dce886ce9d6d1460ac6d8579512750bc66504e306ecabf8bdd7f11bb40fd`. Focused **actual RTL PASS** is selected in `experiments/python-gamebub-v110/ready/results.json`, SHA-256 `34453cbde56ea4de13a2c31816e17124ff4d8668b36e0208963b3981d04950a2`. The immutable attempt is `20261108T135647247841Z/results.json`, SHA-256 `4d8c325e714d8d68643ae849802604203de33be2e46bc505a53aeaba82f287c1`. Both seeds 111001/111002 passed: 16,516/16,662 edges, 60,371/60,809 public comparison checks, and each 14,892 accepted cache beats, 12,838 RAM commits, thirteen preload sequences, 2,048 explicitly prepared counter cases and nineteen start attempts. All 193 public outputs and full raw scale RAM comparisons remained active. A separate read-only adapter audit confirmed both complete producer adapters are exact module renames of their pinned bodies.

All four bounded commands exited zero with no resource/timeout stop or strict warning; Verilator reports 5.020 and total wall time was 210.15 seconds. Current source/proof hashes were rechecked against the actual passing receipt. The source and proof namespace is now frozen; four prior failures remain retained. Full canonical qualification, including actual frame goldens, and a separately audited policy-counted native trial are distinct remaining gates. Source-local decode removal alone predicts no timing gain, and synthesis may merge equivalent registers.

# V130 active-scan lookahead independent review

## Scope and pinned evidence

Read-only review of the candidate RTL diff, positive paired-RTL receipt, expected-failure receipt, directed scan injection, and frozen source/artifact hashes. No tests or builds were run for this review.

- Positive selector: `experiments/python-gamebub-v130/active-prefetch/results.json`, status `PASS`, SHA-256 `384a7d1c02fcfdaf29770c279ba3284c4f1b6877dcf7b5a67d41ebc09401b5dd` for the selected receipt.
- Positive receipt: `experiments/python-gamebub-v130/active-prefetch/attempts/20261111T033050818538Z/receipt.json`. Its freeze SHA is `679a80251d4df492e394d84e3ac043c1f7b31bb69d2b0614ad90542ed673641c`.
- Negative selector/receipt: `experiments/python-gamebub-v130/active-prefetch/negative/results.json` selects receipt SHA-256 `16ef4a76af014ae5629871b437d6b0b7a5b8ddc3bdd83fd023653ad3d59a1803`, status `PASS_EXPECTED_FAILURE_DETECTED`.

I recomputed all 16 positive artifact hashes, all 12 source-snapshot hashes against both saved snapshots and current source files, and the freeze hash; all matched. The negative receipt’s log hash, positive receipt hash, binary hash, and fixture hash also matched their referenced files.

## RTL change and paired comparison

The production candidate at `fpga/experiments/cu66-v130-active-prefetch/cs88_admission_v91i2a.sv` is derived from the frozen V130 speculative-read source (SHA-256 `0b7131bbccc7c9cbc794b51a205210a32138f74bc751d5d8679a87745acb7168`). The stated functional edits are limited to a registered `active_scan_value` lookahead read and using that registered bit for `required_cells` counting. It reads cell 0 on the existing `MODE_END` edge and cell `active_index+1` during `ACTIVE_SCAN` while `active_index<1349`; it adds no public state-machine cycle. Simulation-only assertions check the lookahead’s scan index, receipt epoch, and data alignment. The derivation labels this `PREPARED_NOT_QUALIFIED` and explicitly does not claim physical timing.

The verification pair runs original and candidate full admission FSM instances on shared inputs. Its mismatch comparator checks the public/control outputs and cycle counters each evaluation, while qualifying replay data by replay response-valid and stage-read data by stage response-valid. It does not compare the two data outputs during invalid cycles. This is consistent with the inherited exploratory contract, which leaves invalid-cycle data and external debug consumers unverified.

The positive build uses the frozen Verilator image, `--assert -Wall`, top `admission_pair`, and the recorded 2-CPU/8-GiB container bounds. Both seeds (130301, 130302) report PASS. Each run checks six scan maps (all-zero, all-one, and four deterministic sparse/random maps) over 1,350 count cycles per map, then verifies the terminal transition. Each also checks 15 cancel positions/causes, including scan indices 0, 1, 674, 1349, and 1350, followed by a same-epoch retry. The receipt reports 18,222 scan edges and 15 cancellations per seed; the paired comparator reports no public-output mismatch.

The scan maps are deliberately injected through Verilator private-root access into both instances’ `active_cell` arrays, after a real positive key-frame fixture has completed. The test forces both internal FSM states to `MODE_END`; the RTL resets `active_index` to zero on that edge. This gives direct coverage of the scan logic over boundary maps but does not establish that normal packet traffic creates every tested map or that synthesis implements the registered lookup as intended hardware.

## Negative control and limits

The separately pinned negative run reuses the exact positive binary and fixture, injects `active_index=1351` into both instances while scanning, and detects the candidate’s simulation assertion `scan index outside reachable range`. It exits 134 with that exact fatal text; the negative runner rejects timeout/host-stop exits and pins the log, binary, fixture, and positive receipt. This is a useful assertion-path control, not a proof of all possible scan faults.

These receipts establish a bounded paired Verilator experiment on two admission FSM instances. They do not establish full-parent behavior, synthesis or BRAM inference, routed timing, hardware performance, or a public contract for data while response-valid is low. In particular, the `ifndef SYNTHESIS` ownership assertions are simulation checks and do not become production hardware checks.

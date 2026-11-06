# V84 evidence scope

V84 is a Python research prototype for entropy credits and bounded scheduling. Its evidence can support claims about the implemented Python models, documented inputs, and retained checks. Python results do not establish behavior or performance on Game Bub hardware.

The study observes primitive operations with a native C++ decoder and evaluates their conditional cost on Python finite-queue dependency DAGs. The frontend audit sums the retained per-tile counters for each of the 457 input frames and checks the documented raw-bit, header, probability-initialization, and emitted-tile relationships. These are operation and byte counts; they do not themselves establish cycle costs. Any weighted cycle, latency, throughput, or resource figure is a model output under stated assumptions, not a physical measurement or proof of a deployed implementation. Finite corpus results describe only that corpus, and DAG results depend on the supplied dependency edges and queue model.

This evidence does not qualify RTL, FPGA implementation, ESP32 firmware, physical 30-fps operation, hardware timing closure, transport or scanout behavior, or a strict validated completion time. A software integrity pass is not a functional or performance verdict.

The frozen V83 baseline is `ebbc104d2be8bfe1b2a5b0ee1b10e0d524a166b6`. `scripts/cu66-v84/verify_baseline.py` checks that this commit is an ancestor, that paths tracked at V83 retain their bytes, and that the V83 artifact manifest verifies. It performs integrity checks only and does not rerun V83's functional or performance workflows.

The V84 artifact manifest covers files under `docs/cu66-v84`, `scripts/cu66-v84`, and `experiments/python-gamebub-v84`, excluding its own manifest and Python cache files. It records SHA-256 file integrity only. Write the V84 manifest after the retained artifacts are final, then verify it with the corresponding script.

## Retained campaign and checks

All four processes in `campaigns/session-20261106T061822755444Z-55caaa8d/`
completed with observed exit code 0: histories contain 119, 119, 119 and 100
native sources, each in eight configurations. The final evidence verifier
created `summary.json` and verified it again, both with observed exit code 0;
exact commands and output are retained in `evidence-audit.log` under the V84
experiment directory. The earlier `attempt-20261106T061716547539Z-78c51b07/`
is a two-source smoke test, not the complete campaign.

The verifier checks every retained row's identity, counts, native primitive
totals, weighted work and summary statistics. Four full witnesses are
independently reconstructed from frozen workloads and native observations and
then receive fresh dependency, resource and credit-lifetime audits. The other
3,652 schedules retain producer audits and timeline hashes/summaries, rather
than full timelines. This is directed construction/timeline evidence, not a
formal proof that every required hardware edge exists.

The selected V1/V2 metadata reports retain 28 checks each and five/four vectors.
Independent verification recomputes every operation-array digest from native
zero masks and the fixed hidden profile, recomputes size totals, and parses the
vectors with a separate grammar/CRC implementation. The V2 vectors include a
real RLE packet with a 128-position run. Historical body-only-CRC and
three-vector V2 attempts are preserved and explicitly unselected.

The initial native collection compile failed warning-as-error indentation
checks; its source snapshot and logs remain retained. A verifier preflight
also found equivalent millisecond float presentations from multiplication and
division; its source/failure record is preserved. Final integer weighted-work
checks remain exact, while the independent millisecond presentation comparison
uses an absolute 1e-12-ms tolerance. Neither correction changed campaign inputs,
pixel semantics or the selected scheduling model.

Verify the retained evidence without rerunning the full study:

```sh
python3 scripts/cu66-v84/verify_baseline.py
python3 scripts/cu66-v84/verify_evidence.py --session experiments/python-gamebub-v84/campaigns/session-20261106T061822755444Z-55caaa8d --output experiments/python-gamebub-v84/summary.json --verify-summary
python3 scripts/cu66-v84/bundle_manifest.py
```

The 557 credit construction checks and 9 independent audit checks are recorded
in `credits-tests.json` and `audit-tests.json`. Independent native entropy
verification is described in [entropy.md](entropy.md); cost assumptions and
the frontend audit are linked from [cost-assumptions.md](cost-assumptions.md).
The binary metadata experiment is described in [mode-map-v2.md](mode-map-v2.md).

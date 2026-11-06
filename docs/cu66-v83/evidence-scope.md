# V83 evidence scope

V83 is a Python-only research study. Its retained evidence can support claims
about the implemented models, input data, and checks described by the study
artifacts. It does not by itself establish behavior or performance on the
Game Bub hardware.

Any cycle, byte, command, latency, throughput, or resource result produced by
an analytical or software model is a model result under its stated assumptions.
It is not a measured physical result. Results from a finite corpus describe
that corpus and do not guarantee behavior on future content. Synthetic checks
exercise only their documented cases.

V83 adds no RTL or ESP32 firmware qualification. It does not establish physical
30-fps operation, hardware timing closure, transport or scanout behavior, or a
strict validated completion time below 10 ms. Do not interpret a software
integrity pass as a functional or performance verdict.

The frozen V82 baseline is `d65ea56b44db9edfb48a664e57f18fab1122d92d`.
`verify_baseline.py` checks that this commit is an ancestor of the working
revision, that every path tracked at V82 retains its original bytes, and that
the V82 bundle manifest still verifies. It does not rerun the earlier study's
expensive functional or performance workflows.

The V83 bundle covers files under `docs/cu66-v83`, `scripts/cu66-v83`, and
`experiments/python-gamebub-v83`. It excludes its own manifest and Python cache
files. The manifest records SHA-256 file integrity only. Create it with
`python3 scripts/cu66-v83/bundle_manifest.py --write` once the retained V83
artifacts are final, then check it with `python3 scripts/cu66-v83/bundle_manifest.py`.

## Retained checks and reproduction

Run the three independent check suites from the repository root:

```sh
python3 scripts/cu66-v83/test_scheduler.py
python3 scripts/cu66-v83/test_workload.py
python3 scripts/cu66-v83/test_audit.py
```

The retained test records report 37 scheduler checks, including 12 randomized
DAG cases checked against a cycle-by-cycle tick oracle; 206 workload checks
covering six synthetic cases and eight native workload cases; and 10 audit
checks. The test records are `scheduler-tests.json`, `workload-tests.json`,
and `audit-tests.json` under `experiments/python-gamebub-v83/`. These counts
describe the recorded check suites, not hardware qualification.

The independent campaign runner is
`python3 scripts/cu66-v83/run_campaign.py`. Its four-history, eight-configuration
campaign is retained in
`campaigns/session-20261106T055521696101Z-11ab770e/`; all four processes have
now completed with exit code 0 and the session result is PASS. Its 457 sources
produce 3,656 conditional schedules. The aggregate verifier created
`experiments/python-gamebub-v83/summary.json` and repeat verification passed;
`evidence-audit.log` records a successful repeat with observed exit code 0.
The earlier
`campaigns/attempt-20261106T055331938563Z-863bac3f/` attempt covered two frames
and seven configurations. It is a historical smoke run from before the runner
configuration expansion, not the qualified eight-configuration campaign.

The campaign's `audit.py` independently validates timing for the DAG supplied
to it: durations, declared dependency timing, resource capacity, reserved
memory windows, and group-buffer capacity. It does not infer omitted dependency
edges from workload semantics. The structural workload checks exercise
selected expected dependency relationships; they are not a formal proof that
every required edge is present in every generated workload.

Only four full DAG/timeline witnesses are retained and independently reaudited
by the final evidence verifier. The remaining 3,652 schedules retain their
in-process audit results, timeline hashes, identities and priced counters,
rather than full timelines. The verifier recomputes all summary statistics and
compares every retained row against the frozen V82/native sources.

Verify the existing retained evidence without rerunning the campaign:

```sh
python3 scripts/cu66-v83/verify_evidence.py --session experiments/python-gamebub-v83/campaigns/session-20261106T055521696101Z-11ab770e --output experiments/python-gamebub-v83/summary.json --verify-summary
python3 scripts/cu66-v83/analyze_tradeoffs.py --verify
python3 scripts/cu66-v83/workspace_analysis.py --campaign experiments/python-gamebub-v83/campaigns/attempt-20261106T055521729032Z-e28b6c60 --output experiments/python-gamebub-v83/workspace.json --verify
```

The workspace postprocessor's first invocation failed before writing its
report because a relative campaign path was compared with an absolute root.
The original source and observed failure are preserved under
`experiments/python-gamebub-v83/development/workspace-relative-path/`. Resolving
the input path fixed that postprocessing issue; the native data, workload,
scheduler and running campaign did not change. The corrected workspace report
passes independent recomputation by the evidence verifier.

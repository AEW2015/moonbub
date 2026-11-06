# CU66 V75 BRAM painter and guarded HUD burst study

## Scope

V75 implements two bounded display-path targets on the frozen V74 baseline:

1. BRAM-friendly V75 painter input reads.
2. Guarded full-BL8 HUD upload and readback, retaining scalar compatibility.

The controller and system model are held unchanged for the A/B comparison. V75 baseline verification pins the V74 parent and checks the V69–V74 frozen bundle authorities. The verifier establishes ancestry and file integrity only.

## Evidence rules

The V75 evidence audit will verify source and log hashes against the delivered schemas, report finite PASS counts, require all 20 out-of-context source pins to identify the actual unavailable/no-synthesis state, and keep native and converted counters separate. For the system comparison it will require exact scalar and burst output equality and report each comparison from the actual run artifacts. Historical counts are not copied forward as V75 results.

Direct YUV remains a future RTL direction. This iteration makes no 30 fps, sub-10 ms, or target-fit claim. Simulation comparisons do not establish hardware timing or physical memory service.

## Baseline verification

Run `python3 scripts/cu66-v75/verify_baseline.py`. Expected integrity counts are V69 4,879; V70 460; V71 122; V72 131; V73 161; V74 149. These counts are manifest sizes, not test counts or performance results.

## Reproduction

Once the V75 result artifacts are finalized, run the read-only evidence auditor at `scripts/cu66-v75/verify_evidence.py`. Create the V75 bundle manifest only after the artifacts are final, using `python3 scripts/cu66-v75/bundle_manifest.py --write`; check it with the same script without `--write`.

## Completed iteration

The finite native/converted painter campaigns, scalar/burst system ablation,
four-source burst history, guarded control tests and evidence audit passed.
The exact declared device remains unavailable before synthesis. See the
[measured handoff and next milestones](hardware-handoff.md) for performance,
resource tradeoffs and the remaining physical 30-fps/under-10-ms gates.

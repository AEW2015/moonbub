# V108 final-pass output-write cancellation regression

The separate regression closes the actual RTL coverage gap identified after the first [outtile proof](outtile.md). Both seeds pass all twelve final-pass write-boundary cancellations and good retries. The production candidate remains unchanged SHA-256 `3a30e2c527755ee5e34480274a7998795a773e23fef6cec8471fdd89c31a7808`; the earlier source, scripts and proof results were not edited.

[The terminal receipt](../../experiments/python-gamebub-v108/outtile-kill-collisions/attempts/20261108T095951774667Z/results.json), SHA-256 `673d61e7d29da2f571064b08dd07e4c348d8a74d64d0a467db28583559f9bfe1`, records `PASS` and `actual_RTL_run=true`. [prepare.py](../../scripts/cu66-v108/outtile-kill-collisions/prepare.py) copies the exact lossless full-body adapters and appends tests after every original golden fixture and directed case, preserving the original test RNG sequence. [qualify.py](../../scripts/cu66-v108/outtile-kill-collisions/qualify.py) retains strict assertions/warnings, complete old/new public comparisons, masked-payload poisoning and independent product replay.

Each seed reaches `SECOND_ACC`, `k=7`, at each group 0–3, then collides that actual sixteen-word payload write with reset, abort and both. Every case checks the exact selected sixteen-word write mask before clocking, clears all public words and visibility flags on the collision edge, then completes a fresh unchanged golden AC tile. All partial output words continue to compare before/after every clock. Independent raw trace replay confirms each matrix entry exactly once, actual write masks, zero postedge visibility and zero public output.

| Actual counter | Seed 108301 | Seed 108302 |
| --- | ---: | ---: |
| complete-module clock edges | 273,896 | 274,039 |
| original golden fixture tiles | 4,303 | 4,303 |
| original directed reset/abort cases | 30 | 30 |
| additional AC write-boundary collisions | 12 | 12 |
| additional completed golden retries | 12 | 12 |
| total kill/private-write collisions, including three DC cases | 15 | 15 |
| arbitrary hidden private-word poisons | 3,038,464 | 3,039,552 |
| all-cycle public-word checks | 70,117,376 | 70,153,984 |
| independent raw-trace matrix mask | 4095 | 4095 |

The receipt exposes `write_boundary_group_mask=15`, `write_boundary_guard_mask=7`, `write_boundary_matrix_mask=4095`, `write_boundary_collision_cases=12` and `write_boundary_good_retries=12` in each verdict. The matrix bit is `3*group+guards-1`, where guards 1/2/3 mean reset/abort/both. These fields and candidate hash can bind native promotion to the actual tested production body.

No RTL or simulator failure occurred. Source hashes match after execution; compressed traces and complete source/command snapshots are retained. The bounded container commands totaled 17.51 seconds, with 8 GiB RAM/no extra swap, 2 CPUs and single-job compilation. The lane was released to the parent. This regression establishes behavioral coverage, not native timing or hardware throughput; exact composite full-pipeline and implementation gates remain separate.

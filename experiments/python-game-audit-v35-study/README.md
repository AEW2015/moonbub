# V35 audit baseline

`baseline.json` snapshots the actual v34 CP34/HX33 `control` stream and the
lowest-byte sampled HEVC/AV1 points meeting its mean RGB MSE and 49,152-byte
frame cap. The native rates are prospective budgets with the same HX33 sidecar
and 60-byte binding; no native codec was rerun.

The causal controller has four cohorts (two scenes × unmasked control and
guarded core8), 192 accepted frames, 1,128 candidate packets, and 96 exact
CP34/HX33 control parity rows. The source guard selects all 96 masked frames
and saves 19,096 / 33,040 complete bytes. Aggregate MSE rises from 14.386886 to
14.393638 in the primary scene and 26.303889 to 26.349043 in the complex scene.
Each masked frame passes a strict current-frame quality/byte guard against the
original-source control winner computed on that policy's own reference chain.
The guarded cohort then forms a different reference history; its same-history
shadow totals (497,449 / 1,187,655 bytes) are not the standalone control totals
(441,224 / 1,068,678 bytes).

The four fresh HEVC/AV1 cases encode the exact selected core8 source trace, use
the same actual HX33 sidecar and 60-byte binding, and match aligned-v35 masked
native anchors byte-for-byte. All meet guarded custom quality and the frame cap.
The reuse-v35 timing study is a separate component benchmark on v34's already
paid maps; its speedups do not reduce the current v35 controller's reported
policy time.

`audit.py` replays accepted CP34/HX33 cohorts, recomputes each per-background
strict shadow and guarded selection, checks mask/source identity and paid work,
verifies every native AU accounting row, and preserves own-history shadows
separately from the full-control cohort. Its flat `source_sha256` map closes
the study results, dependencies and audit inputs. `--check` requires
byte-identical output without writing. `test_baseline.py` checks exact SSE/MSE,
cap arithmetic, guard boundaries, complete matrices, and the measured
byte/quality tradeoff.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v35-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v35-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v35-study/audit.py --check
```

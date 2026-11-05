# V33 independent audit

`baseline.json` snapshots v32 `band_control` and the lowest-byte sampled
HEVC/AV1 points meeting its mean active RGB MSE and 49,152-byte frame cap. The
v33 audit then checks provenance and accounting for the completed global-motion,
run-HUD, and shared-work studies. It derives prospective custom and native
totals using the exact same per-frame HX33 HUD bytes and 60-byte binding.

The global-motion campaign contains six independent causal cohorts (two reused
48-frame scenes × control/cross/grid), 288 accepted frames, 1,128 actual candidate
attempts, and 96 exact control packet/ACK/pixel parity rows. The global policies
reduce measured SAD work and decoder reference reads, but raise complete bytes
and mean RGB MSE in both scenes. They are not rate/quality improvements.

The shared-work experiment preserves packet, plane, and output parity on 46
paired instances / 92 outputs over 24 retained frames. Its measured pair time
falls from 127.052 ms to 85.170 ms on average (1.492×), with timing limited to
the documented host pair-encoding path.

The HX33 HUD component is exact across all 2,027,520 words and 96 frames. Its
sidecar totals are 199,566 bytes (primary) and 462,520 bytes (complex), compared
with HU25 totals 310,961 and 623,615. Applying HX33 bytes to custom, HEVC, and
AV1 improves each common-sidecar total equally; the sampled HEVC/AV1 points
continue to beat custom in both bytes and mean MSE. These are prospective
accounting figures: there is no integrated HX33 custom receiver or native
standard endpoint. No hardware fit or physical 30 fps claim is made.

The added hierarchical 32→16 fixed-reference probe covers exactly IDs 0–11 in
each retained scene. Against each actual accepted v32 packet it selects five
complex-scene frames, saving 1,811 bytes (0.356%) and 459,744 active RGB SSE
(0.108%) across 24 frames. The unguarded raw strict-band16 set adds 56 bytes to
control and includes per-frame quality regressions; it is not a causal stream.
The small selected saving costs about 205 ms/frame of additional Python work.
This probe is separately scoped and its gain is not added to global-motion or
HUD results.

`audit.py` checks all pinned source inputs, 48 ordered IDs per global cohort,
own-history reference IDs, packet component sums, cap, exact SSE/sample MSE,
paid-work subtotals, shared-work parity flags and common-HUD standard points.
It writes the derived report to `audit.json`; a flat repository-relative
`source_sha256` map closes the study and audit inputs, while source pin-set
digests and result-file hashes remain summarized. `test_baseline.py` checks exact
SSE/sample MSE arithmetic, inclusive cap behavior, and common-HUD quality
treatment. Run with:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v33-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v33-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v33-study/audit.py --check
```

The values were copied from the retained independent v32 audit. Creating this
audit did not rerun native encoders or codecs.

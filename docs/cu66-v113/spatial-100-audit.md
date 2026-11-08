# V113 spatial-100 native preflight audit

Status: `PASS_V113_NATIVE_PREFLIGHT_AUDIT`. This read-only audit checked the prepared 10 ns (`spatial-100`) card against the current frozen native driver and policy.

The preflight digest binds the external `inputs.json` card. The card matches the prepared external input record, current policy and current `native.py` tooling pins. Read-only `native.qualify()` passed the selected full spatial proof, focused proofs, V112 source lineage, all four timing-control receipt/report pins, and candidate/source/artifact bindings. All 18 prepared source snapshots and all five tooling plus four recipe files match their SHA-256 pins. The local Vivado image ID matches the card. The card is fresh RTL, Default synthesis by omission, 10 ns, with a 3600-second bound; it records no repeat, hardware contact or bitstream.

No native launch or tool build was performed. Detailed checks and calculated digests are in `experiments/python-gamebub-v113/audit/spatial-100-preflight.json`.

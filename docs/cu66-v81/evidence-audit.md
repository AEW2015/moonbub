# V81 evidence audit

Run from the repository root:

```sh
python3 scripts/cu66-v81/verify_baseline.py
python3 scripts/cu66-v81/bundle_manifest.py
```

The baseline verifier requires the frozen V80 commit to be an ancestor, then
runs the V80 baseline, bundle, and evidence verifiers. A baseline pass
establishes ancestry and retained V80 integrity only. The V81 bundle manifest
covers files under `docs/cu66-v81`, `scripts/cu66-v81`, and
`fpga/experiments/cu66-v81`; it excludes itself and Python cache files.

V81 evaluates a tagged 128-bit fill experiment. No performance gain is claimed
until its completed evidence and comparisons are audited. Preserve V80 as the
frozen reference. Its mode-2 campaign contains four independent finite
histories with 457 fixture sources: 457 functional PASS results, 326 meeting
the modeled serial 30-fps ACK budget, and 0 meeting strict validated-under-10-ms.
Compared with retained V79 histories, validated time improves for 273 sources
and regresses for 184. These are simulator observations, not proof of physical
frame rate or a hardware speedup.

All simulations use behavioral Verilator models and 100 MHz clock-conversion
assumptions. Functional correctness, modeled 30-fps ACK completion, strict
maximum-packet completion with validated latency below 10 ms, and physical
qualification are separate outcomes. V80 did not achieve the strict
under-10-ms goal. Simulation evidence does not establish physical 30 fps,
fitted clock timing, or continuous stream qualification.

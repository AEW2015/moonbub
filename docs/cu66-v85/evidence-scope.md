# V85 evidence scope

V85 retains a Python research model and evidence concerning observed native coefficients and encoded-byte parity. Those parity observations describe the compared inputs and outputs; they do not establish implementation behavior, timing, or performance on target hardware.

Any timing or throughput figures produced by a Python model are hypothetical estimates under its stated assumptions. They are not measurements of RTL, FPGA fabric, ESP32 firmware, transport, or display scanout. The retained evidence does not establish FPGA or ESP32 operation, physical 30-fps performance, sub-10-ms completion, or hardware timing closure. A baseline integrity pass only checks frozen tracked bytes and the prior artifact manifest; it is not a functional or performance verdict.

The frozen V84 baseline is `abc19dc8f24fd64875ce181aa9af7382e6e2af27`. `scripts/cu66-v85/verify_baseline.py` checks that this commit is an ancestor, that tracked paths retain their frozen bytes outside the V85 artifact directories, and that the V84 artifact manifest verifies. It invokes only the V84 manifest check; it does not rerun earlier campaigns or functional workflows.

The V85 artifact manifest is intended to cover files under `docs/cu66-v85`, `scripts/cu66-v85`, and `experiments/python-gamebub-v85`, excluding its own manifest and Python cache files. It records SHA-256 file integrity only. Generate the manifest after retained V85 artifacts are final, then verify it with the corresponding script.

## Selected native wire proof

The full run is retained at
`experiments/python-gamebub-v85/wire-attempts/20261106T130658877580Z-53860fda/results.json`.
Its four native receiver processes all exit 0 after 457 sources each. Every
received packet's full coefficient, canonical-picture, semantic-HUD,
rendered-RGB565, C2 root and C2 seal matches the frozen native expectations.
This receiver consumes the new residual grammar directly, rather than
re-encoding a legacy CU66 frame for the original complete-frame receiver.

The combined verifier independently reconstructs all 1,828 packet hashes and
complete byte counts from retained components without rerunning entropy
encoding. It also parses eight retained CS85 fixtures and their nested
headers/CRCs, binds source snapshots and binaries, and recomputes all wire-size
statistics and compatibility-budget counts. Create and repeat verification
both completed with observed exit code 0, captured in `evidence-audit.log`.
The immutable inputs describe four reset histories from one walkthrough family.

The residual component proof covers 114,263 independently decoded AB38 chunks
across four profiles, plus 22 encoder corner checks. The matched whole-plane
all-visible control uses the same encoder rule, but its component gain is not
the complete original-wire comparison. The combined summary's separate matched
envelope projection is byte accounting, not a receiver-qualified control run;
it must not be presented as a deployed bitrate improvement.

## Transaction and context evidence

The selected `protocol-tests.json` points to 23 actual native cases retained in
`protocol-attempts/20261106T130825097268Z-7c3ad48b/`. Each malformed test reaches
its expected rejection, retains the accepted key, accepts the valid delta and
handles identical replay. Recovery responses are bound to the full positive
run's native source 0/1 expectations. The tests used an earlier smoke-run
receiver binary with the exact same SHA-256 as the full run's binary. Missing
references, key recovery and changed stale packets are also covered.

Native per-context attribution qualifies every counter and coefficient plane
on all 457 sources. Prospective parallel scheduling covers **25 selected
sources, 300 schedules and 18 synthetic cases**, with two independently
reconstructed full witness DAGs. It is a standalone existing-bitstream model,
not full-corpus parallel latency, the re-encoded CS85 stream's timing, or an
integrated memory/display result. Shared fetch and arithmetic batching are
explicit model choices, including in its one-lane control.

## Retained development attempts

Initial component and receiver compilation failed indentation warnings promoted
to errors; their exact source/logs remain retained. The first wire smoke run
then stopped on a Python metadata-field mismatch after native decoding; fixing
the field access did not change the wire grammar or native receiver. That
failed run and a successful two-source smoke are separate from the selected
full proof. An earlier passing combined-verifier snapshot is also preserved
as unselected history after direct protocol-to-full-positive binding was added.
No failed or prefix-only run is counted as the complete native wire proof.

## Verify retained evidence

From the repository root, without rerunning encoding:

```sh
python3 scripts/cu66-v85/verify_baseline.py
python3 scripts/cu66-v85/verify_evidence.py --wire-report experiments/python-gamebub-v85/wire-attempts/20261106T130658877580Z-53860fda/results.json --output experiments/python-gamebub-v85/summary.json --verify-summary
python3 scripts/cu66-v85/bundle_manifest.py
```

`run_wire.py` performs a new actual encode-component framing/receiver campaign
and writes a new attempt; it compiles the independent receiver with the existing
`gamebub-cu66-v69-build` container. `test_receiver.py --wire-report PATH` writes
a new native protocol-test attempt using that report's binary and fixtures.
See [residual.md](residual.md) and [contexts.md](contexts.md) for native
collection and selected model details. CPU elapsed time is provenance, not
FPGA or ESP32 performance.

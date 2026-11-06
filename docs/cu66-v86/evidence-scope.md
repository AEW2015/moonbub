# V86 evidence scope

V86 investigates a compact packet and its mode-map/control-byte accounting, alongside native parity checks against the frozen decoder. Any parity result applies to the exact retained inputs, packet forms, and compared outputs; it does not demonstrate deployment behavior or hardware performance.

The context-stream work is a separate Python model. Its per-context observations and front-end timing are conditional on that model's assumptions and retained inputs. They are not measurements of the compact packet path, a full decoder, RTL, FPGA fabric, ESP32 firmware, transport, or display scanout. A model estimate inside the 33.33-ms frame period or below 10 ms does not establish either target on hardware.

No V86 evidence establishes integration with FPGA or ESP32, sustained physical 30-fps performance, sub-10-ms end-to-end completion, hardware timing closure, or bounded on-chip memory. Keep compact-packet byte/parity evidence separate from context-stream scheduling and timing claims.

The frozen V85 baseline is `4851b1efbd92b1f78ea98cd5db7f9b5e7d3ad0b0`. `scripts/cu66-v86/verify_baseline.py` checks that this commit is an ancestor, that tracked paths retain their frozen bytes outside the V86 artifact directories, and that the V85 artifact manifest verifies. It invokes only the V85 manifest check; it does not rerun prior campaigns or functional workflows. A pass is an integrity check only.

The V86 artifact manifest is intended to cover files under `docs/cu66-v86`, `scripts/cu66-v86`, and `experiments/python-gamebub-v86`, excluding its own manifest and Python cache files. It records SHA-256 file integrity only. Generate it after retained V86 artifacts are final, then verify it with the corresponding script.

## Qualified packet and protocol runs

The selected full compact-wire run is
`wire-attempts/20261106T135235884295Z-2a73a26a/results.json` under the V86
experiment directory. Six native receiver processes each completed 457 sources
with exit code 0. Every actual packet's coefficients, canonical pixels,
semantic HUD, rendered RGB565, C2 root and seal match native expectations.
This includes actual all-visible controls under the same compact envelope.
The earlier `wire-attempts/20261106T134936488174Z-233e30ae/` is a two-source
smoke run and is excluded from the complete 2,742-packet count.

The selected native protocol record is `protocol-tests.json`, pointing to
`protocol-attempts/20261106T135723125817Z-5c1df8e7/`. Thirty cases include
legacy-profile rejection, malformed/resealed data, cached-reference branch
coherence and late semantic HUD failure. The HUD construction has a valid
original-HUD positive companion, ensuring the rejected foreign HUD is not
merely paired with a malformed generated seal. The earlier 29-case passing
protocol run remains retained history, not an extra set of unique tests.

The combined verifier independently reconstructs every full packet SHA and
byte count without rerunning entropy encoding, parses ten retained fixtures,
checks native recovery/positive-companion responses, and binds all input,
archive, binary and component hashes. Create and repeat verification passed
with observed exit code 0, captured in `evidence-audit.log`. Its initial
relative-manifest-path preflight error is retained separately; the path fix
changed neither codec inputs nor packet results.

The independent `byte-audit.json` checks every V85-to-V86 inherited-map change
is exactly minus 148 bytes, group changes affect only map bodies, and actual
full matched controls and original-wire comparisons are counted separately.
All reported complete-packet totals include new header, map, quantizers,
directories, actual AB38 data, HUD and CRC. Link/network overhead is excluded
equally. No losing configuration or over-budget input was silently dropped.

## New-stream context and adaptive evidence

`contexts/index.json` qualifies 914 source/profile records and 7,432 actual
re-encoded chunks. The selected model session is
`contexts/model-sessions/20261106T134837375141Z-e85a111c/`: all four cohort
processes exited 0. Its 5,484 schedules cover all 457 sources at both chunk
profiles, LOW/HIGH assumptions and one/two/four arithmetic lanes. Independent
model verification reconstructs four full witness DAGs and all count/statistic
summaries. These are COPY-stream frontend models, excluding complete decoder,
pixel-memory/display and ESP32 timing.

The rate-only mixed-history run is separate from the frozen combined summary:
`adaptive/results.json` selects
`adaptive/attempts/20261106T140824748437Z-23b07c06/`. It constructs all six
candidate packets from offline encoded components, binds their hashes to the
full run, then validates 457 selected new packets and 457 exact replays in one
mixed-history session. These 914 receiver calls are only 457 content sources.
The independent `adaptive-audit.json` checks every choice, native/replay
response, source/binary/artifact hash, and all paired byte statistics. Its
all-visible choices do not inherit COPY-only frontend timing predictions.

All source histories are from one walkthrough family with four reset cohorts;
multiple encodings, model configurations and retries do not create new unique
gameplay frames or sustained-stream qualification. The new receiver still
buffers whole packets and coefficient arrays on the host. Its 2-MiB research
limit is not a hardware allocation; all-six compliance on this corpus does
not establish an all-content 49,152-byte bound.

## Verify retained evidence

From the repository root, without repeating the packet/model campaigns:

```sh
python3 scripts/cu66-v86/verify_baseline.py
python3 scripts/cu66-v86/verify_evidence.py --wire-report experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a/results.json --context-session experiments/python-gamebub-v86/contexts/model-sessions/20261106T134837375141Z-e85a111c --output experiments/python-gamebub-v86/summary.json --verify-summary
python3 scripts/cu66-v86/bundle_manifest.py
```

The independent byte/adaptive audit scripts regenerate their output reports;
their source and input pins are recorded in the selected JSON records. The
combined `--verify-summary` command compares retained evidence without replacing
its summary. See [maps-controls.md](maps-controls.md),
[contexts.md](contexts.md), [adaptive.md](adaptive.md) and
[wire-format.md](wire-format.md) for detailed grammar, collection and model
contracts. Host elapsed times are provenance, not FPGA frame-rate measurements.

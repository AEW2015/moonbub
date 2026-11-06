# CU66 V78 decoder to direct native scanout

## Objective and boundary

V78 integrates the FPGA compressed-frame receiver with direct-YUV caching,
conversion and continuous native LCD scanout. The integration contract is in
[`interface-contract.md`](interface-contract.md). Reuse the qualified bounded
V77 cache/converter and frozen V74 memory, V72 SDRAM and V70 LCD line buffers.
The receiver must validate canonical data and HUD writes, drain accepted memory
work, commit the immutable frame identity, and publish a leased presentation
descriptor. The display must retain reference, front and pending bank ownership
until the matching native presentation and drain permit retirement.

The integrated replay must feed actual compressed fixture packets to the FPGA
receiver and real HUD data through the guarded wide transfer/readback path. It
must compare RTL-produced canonical bytes, tags and full native rasters against
an independent native oracle. Predecoded canonical seeding and injected golden
references are excluded from this proof. Count packet release, actual
admission, validated-ready, canonical commit and processor COMMIT ACK, presented
identity, and complete correct rasters as distinct events. Report source IDs
separately from repeated refreshes. Continuous scanout and source switching
must use the same run without per-source reset or reseeding.

## Verdicts and limits

Functional correctness and performance are separate verdicts. A valid
functional PASS can coexist with a performance FAIL. Report measured
validated-ready latency and source cadence against the strict under-10-ms and
30-source-fps goals; modeled threshold failures are explicit FAIL results.
Do not infer target timing from simulation. The native HUD endpoint remains a
CPU endpoint with zero simulated latency, and no live ESP32 source is present.
These are open integration/performance limits, not FPGA receiver timing
measurements. Any system recovery not actually implemented and exercised stays
an open gate. Preserve memory/cache errors and underruns as visible failures.

## Frozen baseline

Run `python3 scripts/cu66-v78/verify_baseline.py` to verify the V77 122-file
bundle, the inherited V69–V76 baseline and V78's required ancestry from
`f6c2b50112fc3bb1db99b86aac0aec4d03483355`. The baseline pin also records
selected reusable V70/V72/V74/V77 RTL hashes. This is an integrity check only;
it makes no V78 functional, performance or hardware claim. V69–V77 sources and
evidence remain frozen. Keep unrelated marker-recovery artifacts outside the
V78 package.

## Evidence and package

The evidence audit must bind producer sources, logs, input identity and derived
results by hash, and independently check ownership, validation, commit/ACK,
presentation and raster correctness. It must verify that repeats retain the
same source identity, distinct source identities are actually produced, and
native refresh proceeds continuously through source changes. Its accepted
schema and exact checks are finalized against the retained producer outputs;
completion markers alone do not prove correctness. Keep performance failures
visible rather than weakening functional checks to conceal them.

After all V78 sources, evidence and documentation are final, write and verify
the package manifest:

```sh
python3 scripts/cu66-v78/bundle_manifest.py --write
python3 scripts/cu66-v78/bundle_manifest.py
```

The package includes only `docs/cu66-v78`, `scripts/cu66-v78`, and
`fpga/experiments/cu66-v78`; it excludes its own manifest and Python bytecode.
The manifest records file integrity, not a functional or performance verdict.

## Completed integration and next milestone

The receiver and continuous scanout are implemented. The integrated positive
bench uses actual RTL-produced canonical planes and stored references through
the real command-level SDRAM model, plus guarded native HUD writes/readback.
It checks every source against full-plane hashes and an independent complete
native-raster oracle. A separate directed campaign rejects a bad CRC, aborts
after observed canonical writes while the tile adapter is active, retains the
old correct raster, and accepts a valid retry without resetting scanout.

The recommended path and precise scope are in
[hardware-handoff.md](hardware-handoff.md). Fixed-arrival tests and their timing
analysis are retained separately from paced bootstrap diagnostics. Passing the
serial COMMIT-ACK service budget does not close sustained output throughput;
presentation has refresh quantization and can wait behind a prepared repeat.

Before extending to all 457 histories and the 1,800-source/60-second modeled
campaign, harden sticky error observations through idle/readiness/release waits
and final display drain; bound per-source full-raster progress; compute queue
occupancy from the actual admission schedule; and declare presentation jitter
limits. Keep fatal display/cache recovery open until a coordinated drain/reset
policy is exercised. No reset or rejected source may disappear from accounting.

For strict max-under-10-ms work, profile reference service and arbitration under
active scanout, then prototype bounded outstanding requests, next-tile prefetch
and row-aware command grouping while preserving original display deadlines and
bank leases. Do not infer a critical-path improvement by subtracting overlapping
wait/service counters or assuming a higher FPGA clock. Qualify target fit,
route/CDC and real processor/ESP32 service before the 18,000-source/600-second
physical goal. Preserve the established coded/native resolution throughout.

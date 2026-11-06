# V80 evidence audit

Run from the repository root:

```sh
python3 scripts/cu66-v80/verify_baseline.py
python3 scripts/cu66-v80/verify_evidence.py
```

The baseline verifier requires the V79 parent commit to be an ancestor, checks
selected V79 benchmark and prefetch source hashes plus archived prototype
sources, and pins the V78 system, V74 memory, and V72 SDRAM controller/model
inputs. It then runs the V79 baseline, bundle, and evidence verifiers. A baseline
pass establishes ancestry and integrity only.

The evidence verifier audits retained `cu80-integrated-prefetch-system-v1`
runs. It checks each attempt's source snapshot archive hash, verifies mutable
V80 source pins against that archive and frozen pins against the repository,
checks command-log hashes and exit status, and compares recorded executable
hashes with the binary check log. A completed failed attempt remains historical
evidence; an incomplete checkpoint remains pending until its runner finishes.

For completed system PASS runs, the audit checks frame identity and ownership,
fixed-30 source release order, packet/admission/validation/ACK arithmetic,
complete native raster bounds, canonical and HUD write counts, profile bins,
and modeled ACK/validated threshold flags. When a bounded event trace exists,
it also verifies the compressed and decompressed trace hashes and sizes, event
counts, and selected-frame bounds. It recomputes command acceptance gap
histograms from raw trace rows, checks per-frame plane/tile ownership for all
8,100 canonical write requests and retirements, and requires retirement before
ACK. Prefetch epoch completion must precede validated-ready; each enabled epoch
must show 32,400 actual client-3 SDRAM reads, 259,200 beats, 8,100 fills and
retirements, and matching P0 miss/row-read accounting. Keyframes launch no new prefetch epoch or client-3 reads/fills; their diagnostic
counters retain the preceding epoch rather than resetting. These functional checks do not combine the
modeled serial ACK budget with strict validated-under-10-ms.

Variant 0 is checked against the four-frame V79 cohort-0 transaction,
presentation, and summary fields. Latest bounded baseline/prefetch/overlap
pairs are tied to identical source identities and release cycles. Repeated
variant-1 controls are checked for identical simulated timing and transaction
counters. Mode 2 remains its own overlap experiment, including retained stream
observations. TAC=7 system results are audited separately. The audit verifies
the actual-system fault run for bad-CRC rejection, a normal accepted client-3
read coincident with external abort, drain and front-buffer retention, then
recovery. The pending-lookup condition is explicitly false, so this result does
not claim that corner. Three completed fault-bench failures and one main-system
functional failure remain archived with their source snapshots and log hashes.
Earlier CLI and lint failures are retained separately and are not PASS evidence.

The integration audit checks its seven directed cases. The memory audits check
actual SDRAM-model controller runs at `tAC=2 ns` and `7 ns`, and the four
release-on-snapshot overlap configurations. Observer unit cases are synthetic
unit evidence with no hardware fault injection.

The full mode-2 campaign contains four independent finite histories with 457
fixture sources. The auditor binds each cohort log to its result path and hash,
checks the terminal runner record, and independently audits every full-history
result. It also recomputes `comparison.json` metrics and the six-run bounded
trace analysis, including all 178,200 emitted tile rows and the command/tile
histogram artifacts.

In these simulator runs, 326 of 457 mode-2 sources meet the modeled serial
30-fps ACK budget; 0 of 457 meet strict validated-under-10-ms. Against the
retained V79 histories, the mode-2 validated-time deltas improve 273 sources
and regress 184 (median of paired per-source deltas `-0.05603 ms`, range `-16.45171` to `+0.37339 ms`).
Across the 457 sources, modeled validated time ranges from `12.45290 ms` to
`71.49397 ms`, with a median of `28.52827 ms`; V79 ranges from `12.41175 ms` to
`78.72296 ms`, with a median of `28.70237 ms`. These finite simulator
observations do not establish a hardware speedup, physical 30 fps, fitted
clock timing, or a continuous 60/600-second stream qualification. All results
retain `physical_fps_proven=0`; clock conversions assume 100 MHz and native HUD
CPU work consumes zero simulation time.

# V81 actual-system rejection, abort and retry test

The V81 fault runner forks the V80 directed campaign onto mode 3. It uses the
actual compressed decoder, wide reference path, shared P0 memory backend,
SDRAM controller/model, guarded CPU HUD endpoint and continuous native LCD
raster. It drives packet and ordinary external-abort inputs, without internal
force, canonical-memory seeding or reset between attempts.

The sequence accepts a valid key, rejects its following delta with bad CRC,
then retries that delta but aborts after observed partial canonical writes on
an accepted physical client-3 read edge. A final valid retry must pass full
canonical/HUD validation and a correct full native raster, including recovery
from a deliberately lost CPU commit ACK. The accepted old reference, HUD and
physical front must survive each rejected attempt and complete another full
correct raster. Both prefetch/wrapper ownership and raw backend work must drain
before the next admission.

The test first seeks a simultaneous pending receiver lookup, with a finite
fallback to a physical-read/abort coincidence alone. The actual observed
`pending_lookup_at_abort` field controls coverage claims; the test does not
claim the stronger coincidence merely because it searched for one. Aborted
endpoint releases are accounted separately from successful commits. A normal
aborted prefetch epoch pulses both done and aborted once, as in V80.

Run `python3 scripts/cu66-v81/run_system_fault.py` after producer sources are
frozen. It builds a separate mode-3 fault executable with one compiler job;
`--skip-build` replays only the matching immutable executable. Attempt directories
retain source snapshots, all fixture/source pins, command logs, executable
identity and explicit result status. This document describes the test contract;
actual coverage and PASS/FAIL are reported only by completed result artifacts.

These directed simulations do not establish exhaustive faults, physical fault
injection, fatal display/cache recovery, live ESP32 Wi-Fi/QSPI, target resource
fit, routed timing or CDC. Native CPU HUD/hash/control cost remains zero modeled
time.

## Completed mode-3 result

The first V81 attempt passed:
[`attempt-20261106T040240294641Z-cf17f346/results.json`](../../fpga/experiments/cu66-v81/system/faults/attempt-20261106T040240294641Z-cf17f346/results.json).
It accepted two sources and rejected two attempts with four actual endpoint
releases, zero underruns and zero black lines. The accepted raw physical read
coincided with external abort at cycle 4,791,465/address 542,928; the abort/drain
checkpoint recorded 18,624 canonical write words in total. The epoch emitted both terminal pulses once at
cycle 4,791,483, drained, preserved old reference/HUD/full raster, then accepted
the same valid delta as generation 4. Recovery completed two full rasters with
two CPU commit calls confirming lost-ACK reconciliation. The pending decoder
lookup condition was false, so no combined pending-lookup/read-accept/abort
coverage is claimed. An independent fault-evidence audit passed.

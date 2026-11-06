# V81 system evidence audit

Run `python3 scripts/cu66-v81/verify_evidence.py` after regenerating
`comparison.json` from the completed immutable attempt directories. A comparison
made before another case starts or finishes becomes stale; the auditor rejects
that mismatch instead of combining old selections with new checkpoints. Running
checkpoints have no terminal `wall_seconds` and remain unqualified evidence.
The four historical checkpoints named by the exact-path interruption note
`interrupted-campaigns/20261106T0420-interruption.json` are reported separately
from active or otherwise unclassified checkpoints. Their partial source counts
and absence of terminal `SYSTEM_PASS` are verified; they remain in the
comparison's complete unqualified-path list and never become completed results.

The auditor verifies source tarball hashes, archived mutable V81 bytes, all
frozen source/fixture pins, command-log identities and outcomes, executable
build/run SHA checks, unique terminal markers, exact JSON/log records and all
per-source canonical-write/HUD/raster health gates. The observer and its unit
proof must remain byte-identical to V79. Mode 2 is tied to the preserved V80
four-source controls; mode 3 is the new wide-block experiment. Paired runs must
share all producer pins and original packet releases.

Each trace is checked against its raw and compressed hashes, byte count,
selected source bounds and exact event counts. For every source, candidate
write request, actual backend completion and receiver retirement cover all
8,100 canonical tiles with a consistent candidate bank and causal ordering.
The 7,806 first offered lookups, accepted requests and responses must cover
exactly the fixed profile's non-hidden tile coordinates. Generation, bank,
plane, tile and captured block address remain paired; all four blocks of every
mode-3 tile must appear exactly once as raw request, accepted snapshot and
successful commit before tile publication. The cache epoch must complete before
validated-ready. Physical commands preserve owner generation zero (unknown);
coordinate/address matching within a source trace window is not represented as
authenticated raw-bus ownership.

Per-source command and path-event counts must agree with the raw trace and
logged `SYSTEM_COMMANDS`/`SYSTEM_PATH` rows. The auditor independently recomputes
selected-run latency, queue, finite cadence, ACK/strict-latency thresholds,
observed-pixel counts and comparisons. All path-analysis interval histograms are independently recomputed from the
per-tile and per-block trace chronology, including weighted median arithmetic.
It verifies exact V80 mode-2 controls,
bounded mode-2/mode-3 pair deltas and all available full-history comparisons.
A completed four-history campaign additionally binds all four child logs,
terminal runner records and independently audited result hashes. Separate
histories are never combined into a claim of one sustained stream.

The actual mode-3 fault result is audited separately: bad CRC must produce no
physical candidate write or prefetch read; partial-write abort must coincide
with an accepted physical client-3 read, drain without success, retain the old
reference/HUD/front and complete a correct old raster. The valid retry and
lost-ACK reconciliation must succeed. Observed chronology is checked without
hard-coding the old mode-2 cycle numbers. Pending-lookup coincidence coverage
follows the actual recorded boolean. Historical failed attempts retain their
snapshots and log identities and are never counted as PASS.

The auditor checks evidence consistency and the actual self-checking simulator
contract. It does not independently decode trace payload samples (the trace
contains coordinates/events, not all pixel data), prove RTL equivalence, or
establish physical timing, fit, CDC, ESP32 transport or CPU execution costs.
Functional correctness, modeled packet-complete-to-ACK budget, strict validated
latency and physical sustained throughput remain separate verdicts.

The profile audit binds all four bounded system inputs and their trace hashes,
independently checks every recorded physical-command predecessor gap, and
checks source metrics against the audited system records. The two read-only
diagnostic runs receive the same system audit, source/log/binary bindings,
exact original frame/timing/summary parity (excluding native CPU wall time and
trace-row count), raw profile-row equality and state-bin partition checks.
Address-cache hit screens and derived diagnostic labels remain analysis of
those bound inputs, not an independently implemented cache or stall proof.
The conditional service arithmetic is checked separately: 35,040 reads at
18 clocks and 35,040 writes at 16 clocks, less the final maximum predecessor
interval of 18 clocks, give 1,191,342 clocks or 11.91342 ms at the assumed
100 MHz. The condition is the frozen serialized bridge/controller with the
observed fixed no-hit traffic; this is neither formal proof nor physical timing
qualification.

The completed tile-reuse screen binds its native source snapshot, fixture
hashes, command logs, binary SHA and 457 source records. Equality-mask
population counts, per-frame hypothetical canonical-write elimination and
aggregate arithmetic are checked against the native log. This screen is
native-only; new mapping/protocol RTL, metadata traffic, reference-read
reduction and latency savings are not established by its counts.

Run `python3 scripts/cu66-v81/verify_residency_independent.py` to reproduce the
separate residency review. It imports neither the producer model nor the
prototype runner, executes no native collector, and reads the retained oracle
streams without changing them. Each invocation retains an immutable attempt
under `fpga/experiments/cu66-v81/residency-review/` with the exact verifier
bytes, input hashes, command record, log and terminal verdict.

That independent replay reconstructs all 457 native frames for both bank
selection schedules, checks each certificate/elision against actual retained
tile fingerprints, and checks the complete candidate frame at every commit.
It separately reproduces the 16 partial-frame and 15 late-authentication abort
events, surviving certificate invalidations, same-bank retries and their
recorded totals. It binds source snapshots, native packet/canonical/HUD/display
digests, prior exact-byte equality masks, and compressed/raw oracle hashes.
The 19 synthetic cases and 457 lost-ACK replays remain bound producer evidence;
this verifier does not independently reimplement those cases. Its writes are
abstract whole-tile mutations, so it establishes no partial-BL8-beat, RTL,
physical-traffic, latency, throughput or target-fit proof.

The final audit returned `V81_EVIDENCE_AUDIT_PASS` with exit code zero after all
four histories completed. It qualified nine completed system runs, including
the four-history campaign's 457 sources, and independently recomputed all 457
full-history comparisons. The four bounded cohort-0/cohort-3 mode-2/mode-3
traces and path histograms, two exact V80 mode-2 controls, two bounded pairs,
read-only profile evidence and actual mode-3 fault campaign also passed.
There were zero retained completed system/fault failures and zero active or
unclassified checkpoints. The four exact historical interruption checkpoints
remain unqualified; their partial progress is excluded from completed counts.
These four completed histories establish finite simulator correctness, not a
single sustained physical stream or the strict latency target.

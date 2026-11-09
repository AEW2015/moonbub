# Optional V114 optimized 100 MHz prepared-card audit

**PASS_V114_NATIVE_PREFLIGHT_AUDIT**. The independent
[audit](../../experiments/python-gamebub-v114/audit/optimized-100-preflight.json)
binds the exact [prepared card](../../experiments/python-gamebub-v114/optimized/prepared/v114-spatial-100-20261108T234933895200Z-049fab/preflight.json),
SHA-256 `392a6c40d77bc9f26a0f517aaaca8914298af5b776da8a339925dfcd97807a24`,
policy `b161b6289c49790a360f68819a5281d0ae0fa5966135a2c568ed3880e78b5947`
and native guard `3650a8e586cf36ee8554e5365da13de380184252ba45b99628864b1600919071`.
No native job, build, source/proof edit or hardware action was performed.

All 18 source snapshots and origins match the qualified optional B composition:
only top controller `9e6d2b88…` and scratch `332da205…` differ from V113.
The exact 10.000 ns XDC is read before fresh default synthesis; the clock and
waveform are checked afterward. Recipe copies, tooling, immutable image
`sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`,
Default opt/route, ExtraNetDelay_high placement, no separate phys-opt, and the
same part/method match the primary card. There are no timing exceptions, guessed
IO delays, retiming, bitstream or hardware commands. Actual timing remains unknown
until this candidate's own terminal route; primary A's negative result is separate.

The optimized functional qualification explicitly reuses completed certificates:
44 canonical profiles/42 directed checks and first-seed transport 12 profiles/two
retries from exact failed parent `50abb09c…`. That parent remains FAIL following
its PSI resource stop. Recovery receipt `ffdf5ea6…` newly executes only the
interrupted second transport seed: 12 profiles/two retries, zero new canonical
profiles/checks. Totals are 44/42 and 24/4. The same frozen-source executable and
input assets, completed artifact copies, parsed stdout, independent oracles and
canonical raw hashes are checked. No assertion is disabled and no partial failed
prefix becomes a completed certificate. The reversible public-command API adapter
still reconstructs the untouched 496-line original, with its additional pending
assertion and E+1 diagnostic fence explicitly recorded.

Focused controller/prefetch/inherited proofs and the extra actual full-top
[peer proof](../../experiments/python-gamebub-v114/control-peer/results.json)
are source/artifact pinned. The peer summary `2ed08310…` binds raw receipt
`d92267aa…`; both seeds pass eight directed cases and eight full canonical retries,
including real accepted read/write debt and queued replay. Its separate reversible
adapter corrects one private queue push/response expectation only during exact
registered matching-owner cancellation. It requires no refill traffic, exact
cancel deltas and empty canceled queue owners; synchronous replay-response binding
and independent physical service objects remain checked. Prepared complete child
fail-task poststates are explicitly distinct from naturally packet-triggered faults.
The shared canonical/transport harness is unchanged.

All six retained controls were hash-checked and reparsed at their declared clocks.
B100 must be assessed against 10 ns controls and the actual primary 10 ns result;
B125 remains an 8 ns comparison. The global ledger permits four initial
source-qualified trials and one fresh repeat of a positive result; this
composition allows two initial trials, with no failed-clock repeat. Root serializes
starts and limits all heavy work to two jobs. Each native job retains two CPUs/tool
threads, 8 GiB RAM with equal memory-plus-swap, a 3,600-second watchdog and host
available-memory/PSI/combined-use gates. Docker active-name checks are supplemental.

This is preflight readiness, not a routed clock, FPS, under-10-ms or board claim.
OOC external IO timing, complete production PCTL1/session, parent CDC/memory/panel
and publication qualification remain open.

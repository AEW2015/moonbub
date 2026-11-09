# V114 peer-fault physical-owner qualification

This separate verification campaign targets the registered producer kill while
the full optimized component owns an accepted scratch transaction or queued
synchronous replay response. It changes no production RTL, frozen focused proof,
or shared harness file. The composition is the actual 18-source optimized
variant: registered-admission top plus prepared scratch prefetch.

The bench uses a reversible peer-local derivative of the frozen API/clock-hook
base. Its value, tuple, held-offer, replay binding and accepted physical-owner
checks remain active on every tick. Faults are explicit verification
fixtures that prepare the actual inverse/reconstruction child error and pending
registers; they do not claim that valid packets naturally reach those errors.

The first retained attempt, `20261108T231912975317Z`, passed all six scratch
cases and six canonical retries, then rejected a private internal-cancel edge.
The old queue monitor assumes `queue_push == frame_read_rsp` whenever no
external reset/abort is asserted. A matching-owner registered peer kill also
cancels that queue: it suppresses a push while the previously registered replay
response is still visible. The peer-only derivation corrects exactly this one
assumption in that explicit local-cancel scope. Outside that scope the old check
still executes unchanged. The old response address/epoch/data binding check and
every other original assertion execute on every tick. Independent before/after
hooks require no queue push/pop, stage write or new replay request at the kill,
exact queued/pending cancellation-counter deltas from pre-edge owners, and an
empty canceled queue. No raw-clock bypass or shared-harness edit is used.

The next retained attempt, `20261108T232958214656Z`, reached the unchanged
200,000-edge drain watchdog after the same six scratch cases and retries.
Diagnostic `20261108T234045208670Z` reproduced that failure against the exact
failed model: inverse `running=1`, `fault=1`, `busy=1`, with every inverse bank,
accept/result/math owner empty; producer, reconstruction, queue and both actual
physical debt ledgers were idle. The fixture had set only error/fault registers.
That is not the actual RTL `fail()` poststate, which also clears `running` and
logical owners. The diagnostic remains explicitly a reproduced failure, not a
qualification pass or an RTL defect.

The corrected fixture prepares every assignment of each actual inverse and
reconstruction `fail(reason)` task, including the previous-fault qualification
of its pending pulse. A pinned injection contract retains the literal RTL task
text, state encodings, C++ body and immediate poststate assertions. Counters,
unowned payloads and physical scratch/reference ledgers remain exactly as those
tasks specify; the reference physical owner is never cleared by the fixture.
The watchdog, eight cases, eight complete retries and all checker scopes remain.

For each peer, three cases align a real accepted scratch reply before, with or
after the registered local kill. These cover two writes and four reads per seed.
They check the immediate public valid/ready mask, the retained RTL outstanding
ledger and independent external request tuple, rejected replacement admission,
the same-owner registered kill, exact one-response retirement and first-cause
retention when the other peer subsequently faults. Two additional cases inject
a peer fault with one queued byte and one pending synchronous replay response.
Each of the eight cases requires a complete clean canonical retry through the
unchanged independent goldens.

`scripts/cu66-v114/control-peer/qualify.py` freshly compiles the actual component
with assertions, fatal SV `-Wall`, owned C++ `-Werror` and one compiler worker.
It runs seeds 114401/114402 under the same bounded two-CPU/8-GiB/no-extra-swap
watchdogs and host memory-pressure gates. Every failed attempt is retained.
The selected pointer is `experiments/python-gamebub-v114/control-peer/results.json`.
Until that pointer and its raw receipt say `PASS`, the prepared test is not a
qualification result. This test adds no native timing or hardware claim.

Selected attempt `20261108T234159536090Z` passed both seeds. Each completed
eight directed cases, eight complete canonical retries, two accepted writes,
four accepted reads, two queued-replay cases, 14 complete fail-poststate
injections and eight checked local-cancel edges. Clock totals were
11,327,423/11,326,804. Every retry checked all 518,400 canonical pixels through
the original goldens and finished with no physical debt. Strict compilation
reported no warnings; maximum full-memory PSI avg10 was 0.00.

The raw receipt SHA-256 is
`d92267aabe0dc510eb51048c9d92f6a380fe3bfc6d568f201eaddd83e0a398ca`;
the summary SHA-256 is
`2ed08310978ee6f43e7563b41a8372df7843c6c7d1f1ea34d3fbaf72f079a0d2`.
`control-peer/source-review.json` rehashes all 52 sources and 60 retained
artifacts, matches every actual optimized 18-source path/hash, reverses the
single peer-only checker derivation, and compares the injected assignment
targets against every assignment in both actual RTL failure tasks. It also
checks the two real stdout verdicts and all 16 complete canonical retry rows.
The two earlier attempts and diagnostic remain failures with their original
source snapshots and logs. Production RTL and selected proof inputs are frozen.

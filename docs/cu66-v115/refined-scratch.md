# V115 refined scratch: local forwarded tile writes

The initial V115 routed 125-MHz sample is dominated by `read_band` paths into
scratch tile reset/enables; the owner-comparator hypothesis was absent from the
top-50 routed paths and is deferred. This candidate targets the measured tile
storage cone. The refined scratch focused suite has passed both seeds. No timing gain is
established until the exact qualified composition is freshly routed.

The source is `fpga/experiments/cu66-v115-refined-scratch/packed_scratch_v91g2.sv`,
SHA-256 `2b9dbaf7fb25d7fdc8219a69dc59588b4c1bb2e7da374c6edaf223a5c1ac52d1`.
Its reversible recipe recovers the frozen initial V115 scratch source
`559cb6d4…` exactly. Root reviewed the actual source and branch priority before
qualification. Controller states, tile validity/ownership, counters, public
eligibility, physical debt and the existing three-edge descriptor contract are
unchanged. All previous assertions remain enabled.

Only three payload write sites move: serial clear, validated non-raw DC extract,
and a matching AC head. They capture one 23-bit bank/index/value tuple plus an
initialized valid bit. On the next clock the previous tuple commits to private
`tile_payload`, through local bank/word enables. Every visible `tile` word
forwards the pending tuple on an address match. The visible value therefore
changes on the original edge, while broad read-band/state/error control reaches
only the small pending tuple rather than each payload register. Capacity is one
write per edge; a new write may replace the slot while the old one retires.

Payload retirement deliberately remains active during warm reset, matching abort,
response failure and drain. Its value was already visible before that edge, and
the old raw tile did not clear that value on a kill. Suppressing this last commit
would expose an older payload when the valid bit cleared. New event capture,
however, follows the exact original outer branch priority: cancellation, wrong or
unsolicited reply, DRAIN, prefetch-owned error, and overlap-write-owned error
suppress it. A matching error outside those earlier owner branches can still
reach an old case write; a blanket `!response_failure` guard would change that
raw behavior and is intentionally absent.

The focused comparison retains the complete initial suite against the frozen
V114 reference, including exactly three checked candidate-only descriptor
preparation edges. All original public/value/request/cache/raw/owner checks are
retained. It additionally compares **all 128 visible tile words** before and
after every paired edge, including inactive words. Original ready-bank stability
assertions still observe the forwarded tile view.

Additive checks include eight naturally reached pending zero/data writes, each
aborted or warm-reset before physical payload commit, across both tile modes.
Each must retain its complete raw value and execute a full same-object retry
against the original dense and memory-owner goldens. Separate declared private
storage fixtures exercise consecutive zero/data overwrites and both banks,
ready-bank held visibility, late matching-error write visibility, five earlier
priority guards, and drain-state retirement. Those fixtures do not claim packet
reachability or invent accepted physical requests. Actual physical-debt drain
remains covered by the unchanged original accepted-request hazard/owner cases.
The finite ledger requires events = physical commits + one pending tuple.

The first attempt `20261109T020546433507Z` is retained as FAIL. Every inherited
72 full transactions, 128 corrupt responses, four read-owner cases, 48 boundary
transactions, 12 pending-descriptor cancellations, 24 retries and 269 paired
admissions/807 preparation edges passed with the strengthened all-word comparison.
The failure then occurred in a new private fixture: it changed `state` but omitted
the redundant `busy_owned` poststate, correctly triggering the old busy-predicate
assertion. Only that fixture was corrected to set both state and its exact busy
predicate together; no production source, natural case or assertion was changed.
Fresh attempt `20261109T021637391746Z` subsequently passed both seeds,
115801 and 115802, including every additive storage/priority fixture.

Reproduce preparation without running:

```sh
python3 scripts/cu66-v115/refined-scratch/prepare.py
python3 scripts/cu66-v115/refined-scratch/verification.py
python3 scripts/cu66-v115/refined-scratch/qualify.py
```

Use `--run` only after a Root heavy-job grant. The established standalone
Verilator 5.020 backend retains assertions, fatal SV Wall, owned C++ Werror,
one compiler worker, two CPUs, an 8-GiB memory/combined-swap ceiling, RAM/PSI
gates and finite watchdogs. Every attempt retains source snapshots, commands,
logs and raw receipts. The selected pointer is
`experiments/python-gamebub-v115/refined/scratch/results.json`.
Full-component, peer fault, canonical/transport and native route checks remain
separate gates. This storage change does not establish hardware 30 fps or
validated under-10-ms complete decoding.

The second retained FAIL, `20261109T020805491580Z`, again completed the inherited
suite and natural pending-write cases, then caught another incomplete private
fixture: cache bytes had changed without their all-offset predecoded position
metadata. The new fixture now seeds cache positions through the frozen independent
C++ oracle, coherent legal-band head/cursor metadata and aligned addresses. It
also retains the exact busy predicate. `fixture-invariant-review.json` records
an upfront review of all relevant old and new assertions. No production write,
natural case, validity gate or assertion was changed for either repair.

The two immutable failed receipts kept the historical `actual_RTL_run=false`
completion flag even though their logs show actual RTL verdicts followed by a
runtime assertion. `failed-runtime-flag-history.json` pins both receipts and
logs and explains this evidence defect without editing them or converting FAIL
to PASS. The current runner records simulation start separately before dispatch,
so a later runtime failure retains actual-execution provenance.


Selected raw receipt SHA-256:
`24872d24dfc30f569c57d62d0b040b6bf9ff59ac97739fd2e5c76c8eb55f73ff`.
The selected summary SHA-256 is
`897a06e89e359744268d43fdd520ac0894b8d8d6cdb1f0adc6b2f7a0c7a6a13f`.
Each seed passed the complete inherited suite and all eight naturally reached
pending-write kills/full retries, nine private-storage events, five earlier
priority guards and two held-bank edges. The private edge log contains 18
observations, nine with a new event. Every checked paired edge compared all128
visible raw words. No new public edge or weakened old assertion was needed.
Strict compilation emitted no warnings; all launch gates were met and no
resource stop occurred. Runtime peak RAM/PSI samples are not retained by this
runner, so no peak-resource statistic is claimed.

`experiments/python-gamebub-v115/refined/scratch/source-review.json` separately
rehashes all 36 current and snapshot source pins and 47 retained artifact pins,
reverses the production recipe and all eight verification adapters, checks the
actual commands/verdicts/edge counts, and verifies both failed receipts and logs
remain unchanged. This is an independent calculation from the runner, performed
by the author, rather than an external design review. Production, verification
and selected proof files are frozen. Fresh complete-parent and native timing
qualification remains in progress outside this focused evidence.

# V113 independent composition and performance review

Status: **source composition, reporting and selected transport evidence PASS;
native timing remains a separate gate**. This read-only review launched no builds, simulations,
Vivado jobs or hardware actions and changed no source or reporting scripts.
Exact reviewed-file pins and recomputed component metrics are in the
[audit receipt](../../experiments/python-gamebub-v113/audit/composition-review.json).

The composition contains the actual 18 V112 source origins with exactly three
replacements: geometry `4eefd411…`, scratch `efc3e61…`, and inverse `c727e7a7…`.
All three recipes reproduce and reverse byte-for-byte; module interfaces are
unchanged. Each production hash matches its selected focused PASS receipt.
The other 15 origins and the original full-component oracle match their
retained pins. No V111 rejected header candidate is included.

Geometry and scratch retain exact focused public/invalid/debug/counter
contracts. Geometry's byte preparation at request E and final preparation at
E+1 precede the actual earliest successful Rice response consumption E+3;
zero-stream truncation consumes at E+2 without geometry. The independent
scalar/key assertions and original Count configuration guard remain. Scratch
retains all eight concrete phase encodings, low-two-bit count/band indices,
full phase-zero semantics and original error/physical-drain priorities. Its
selected strict actual-module and 800,192-comparison phase checks pass.

Inverse deliberately uses IV113.1 latency and diagnostic semantics. A complete
accepted tuple is registered before validation and commit; 64 actual word
commits precede bank readiness. Arithmetic reserves a result slot before
launch, then copies all 1,536 payload bits before making that result READY and
releasing its math bank. A held result retains ownership through residual 63
acceptance. Reset/start/cancel mask public readiness, offered valid and payload
writes while invalidating private owners. Coefficient/result payload registers
need no reset to become ineligible. Stale invalid payload/debug values are
permitted under IV113.1; old invalid-cycle equivalence is not asserted for the
whole new-latency composition.

A sequentially detected fault can coincide with a private write or an already
offered transfer at that edge; local owner invalidation masks subsequent
eligibility. This matches the explicit edge contract. Private flush does not
retire accepted external memory transactions. The unchanged full-component
oracle retains actual accepted-request ledgers and matching-response drain
checks across abort, reset, wrong tags, held output and retries. The enclosing
PCTL1 supervisor and unique external session ownership remain unimplemented.

No source-level timing improvement is inferred. Geometry still has private
remainder correction/quotient selection; scratch still shares zigzag/band
validation and selects an eight-way decision. Inverse retains frontier/bank
selection into ready, decoded bank/word enables, a 1,536-bit parallel-copy
enable, a 64:1 residual read and two-slot output/identity selection. Existing
top readiness, remote fault and cancellation joins remain. Actual routed
endpoints, fanout, utilization and clocks must decide the physical result.

The retained parent attempt `20261108T210733724256Z` completed two canonical
seeds: 44 case/profile rows and 42 original directed checks. I independently
rehash-checked both transcripts and compressed streams and recomputed both raw
canonical hashes against V112. The unchanged oracle checks coefficients,
dequantized values, residuals, metadata/order, held offers, errors, counters,
canonical pixels and real scratch/reference drains. The transport oracle's
five-edit clock-hook derivation also reverses exactly to that original bench.
The parent attempt's later adapter compile failed; its overall FAIL status is
retained. The selected successful adapter-only retry reuses those canonical
certificates and reports zero newly executed full-component profiles/checks.
Its two actual transport campaigns newly execute 24 successful case/profile
rows and four abort/reset retry checks in total. Both transport canonical raw
streams independently match V112, and all 39 selected source pins and 55
artifact pins match. The [final spatial audit](../../experiments/python-gamebub-v113/audit/spatial-final.json)
records the selected evidence and honest execution counts.

`performance.py` and `summarize.py` have no actionable defect in the reviewed
snapshots. Performance reporting refuses a non-PASS spatial selection, binds
both seed transcripts to artifact hashes, compares matching case/profile keys,
requires 518,400 accepted canonical samples, and excludes failed provisional
prefixes. Its 100/125-MHz conversions use correct cycles-per-millisecond
arithmetic and remain explicitly conditional. The candidate metric starts at
the first accepted component byte; earlier preload, host encoding, network,
firmware, QSPI and physical display work are outside that window.

The read-only recomputation of successful component rows gives:

| Service profile | Rows across two seeds | First accepted byte → local done, min / median / max cycles |
| --- | ---: | ---: |
| Deterministic fast service | 12 | 642,491 / 1,012,911 / 1,383,951 |
| Seeded bounded stalls | 12 | 1,760,941 / 2,085,462 / 2,464,059 |

These are fixed-corpus component observations. Profile 1 retains the same
service policy/seed but changed scheduling changes random draw times; it is
not an identical timed service replay. Even at an assumed 125 MHz, the fast
profile's maximum is 11.072 ms. Local done still lacks complete C2/HUD sealing
and publication, so these observations qualify neither complete decoding below
10 ms nor sustained hardware 30 fps. The standalone 16-tile benchmark also
records a zero fast-path regression alongside AC-heavy improvements; two
result slots and conditional lane budgets imply no uniform speedup.

The summary script compares only matching 10-ns or 8-ns controls, records
controls as reused, and separates best-WNS diagnostics from a positive fresh
repeat. Its system/firmware/publication/FPS/complete-decode flags remain false.
Its actual-V97 execution claim is downstream of the selected spatial PASS
gate. The [prepared 125-MHz card audit](spatial-125-audit.md) now passes for its exact
source/recipe/proof/image/8-ns input snapshot. Terminal timing is not established
by that preflight.

The selected spatial receipt is now `PASS_V113_SPATIAL_CANONICAL` at
`spatial/attempts/20261108T212355592057Z/receipt.json`. The generated
[performance report](../../experiments/python-gamebub-v113/performance.json)
was checked against every independently recomputed case window, cycle delta,
clock conversion and profile statistic above; all match. No mutable aggregate
`results.json` or root documentation is pinned as a source gate. No native
terminal result, bitstream or hardware performance is certified here.

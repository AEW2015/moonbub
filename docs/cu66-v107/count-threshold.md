# V107 packet-count ceilings: focused RTL qualification

The four-file candidate passes actual arithmetic, complete ingress capture and complete old/new controller qualification in both SYNC modes. Production, adapters, benches and runner are frozen. The selected [actual receipt](../../experiments/python-gamebub-v107/count-threshold/attempts/20261108T071008661895Z/results.json) has `status: PASS`, `actual_RTL_run: true`, SHA-256 `d40845dac7a440bf36552b8d55c78abe45e1f6b3d567e3f95322a97da8894a2a`. Existing qualified source files were not modified. Complete pixel-pipeline composition and any conditional native trial remain parent-owned gates; no full-route timing gain is claimed.

The proposed activation combines CDC's earlier header-prefix preparation with these three exact count-cap ceilings. The actual META route's [worst path](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/route-setup-paths.rpt:15) runs from `context_blocks_reg[2]` through `used_bytes`/`sum30` capacity/layout logic to scratch state: −3.146 ns slack, 13.000 ns data delay (4.359 logic / 8.641 route), twenty levels. Report SHA is `a911f46845cbd5d0ff9743b4f1f06f4add246e235a763c5cb9e7294c6b164979`. A separate [synthesis-estimate path](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/synth-setup-paths.rpt:15) explicitly traverses `begin_limit43`; report SHA is `ed22b7472c707337eee41e2bf7a0ca5057a146c3b681ba7a6e0e0e0cc38d4198`. The combined candidate therefore addresses both packet-count prefix and threshold terms. Any future result must not be attributed to an isolated ×43 rewrite.

## Exact base and candidate

The base is CDC's four-file `cu66-v107-plan-prefix` variant, now qualified in both synchronous and legacy controller configurations. Its prefix fields remain intact. [edit-recipe.json](../../fpga/experiments/cu66-v107-count-threshold/edit-recipe.json) reconstructs and reverses all four complete source bodies:

| Production file | Prefix base SHA | Threshold candidate SHA |
| --- | --- | --- |
| synchronous ingress | `f7e05105dc7b` | `079381563a11` |
| ingress wrapper | `83577ff72781` | `2c4a0ab1ba74` |
| child pipeline | `d00f774fd8c4` | `a5d8a86d4bcc` |
| packed scratch | `4d06f2c15b85` | `f0bab2ba60d2` |

The production files are under [`cu66-v107-count-threshold`](../../fpga/experiments/cu66-v107-count-threshold/). `scripts/cu66-v107/count_threshold.py --prepare` regenerates source/models/adapters, while `--run` executes bounded actual RTL qualification without modifying production sources. Neither mode starts a vendor tool. The inline generate block adds no source module: native closure remains eighteen files, using four source substitutions and no helper-module filename waiver.

Three new internal 32-bit fields, `meta_threshold1/2/3`, travel through the existing synchronous ingress, wrapper and child wiring into scratch's `begin_threshold1/2/3`. The child/external top ports and every old public field remain unchanged. Prefixes retain their modulo-32 semantics; thresholds are a separate exact unsigned-integer calculation. No threshold depends on blocks, epoch or a preselected error code.

## Exact integer identity and widths

For unsigned `n` in 0…2^32−1, unsigned `b` in 0…131071 and `d` in {5,15,43}:

`n > b*d` iff `b < ceil(n/d)`.

The largest live product is 131071×43=5,636,053, below 2^23, so the original 32-bit product cannot overflow. Thresholds remain 32 bits, including malformed high count values. Zero count has threshold zero. No `n+d-1` expression is used.

With `M=floor(2^32/d)`, `q0=(n*M)>>32` equals `floor(n/d)` or one less. Thus `r=n-q0*d` lies in 0…2d−1, and exact ceiling is `q0+(r!=0)+(r>d)`. In particular `r==d` adds one, not two. The final implementation selects a two-bit correction 0/1/2 before one 32-bit addition.

The [independent arithmetic review](../../experiments/python-gamebub-v107/count-threshold/arithmetic-review.json) records the integer argument and separate deterministic boundary/random checks. [preparation.json](../../experiments/python-gamebub-v107/count-threshold/preparation.json) pins that file's SHA and labels both results model-only. This is not formal RTL equivalence or exhaustive simulation of every 32-bit numerator.

Each reciprocal product is decomposed into four explicit unsigned 16×17 partial multiplications. The second operand's leading bit is zero for reciprocal halves; their products therefore fit 32 bits. Only the high sixteen bits of low×low are stored. The two cross products plus that carry fit 33 bits; their high seventeen bits feed the high-product sum. The resulting quotient fits 32 bits.

Two more 16×17 multiplication sites form `q0*d`. Its high partial needs only sixteen stored bits: `floor(q0/65536)*d <= floor(n/65536) <= 65535`. The low partial fits 32 bits, and their registered sum equals the full product because `q0*d<=n`. These deliberate truncations discard mathematically zero/irrelevant bits; they do not narrow the input count domain or silence warnings with dummy reads.

There are eighteen source multiplication sites requesting local `use_dsp="yes"` across the three pipes. Full-production DSP count, register inference, placement and timing remain unmeasured. A separately scoped extracted-wrapper mapping measurement is described below. All arithmetic payload stages are unreset and run unconditionally. Only eight validity bits plus one live bit per divisor reset on packet cancellation/context diversion. The cached 32-bit ceiling updates from registered validity, without a global reset on its payload.

## Existing-edge deadline

Each word captures on the exact prefix-eligible `F_HEADER FETCH_WAIT` edge for bytes 33/37/41. Eligibility preserves reset/start/abort, context error/done, response-valid and RAM epoch/address priority. The current `ram_data` supplies the high byte; the three lower bytes come from already fetched header bytes. The forwarded word is registered before multiplication.

| Edge after count capture | Registered work | Latest field's actual state |
| --- | --- | --- |
| E0 | complete forwarded count | WAIT41 |
| E1 | four reciprocal partial products; matching numerator | REQ42 |
| E2 | cross-product sum and low-product carry | WAIT42 |
| E3 | add carry and register high cross bits | REQ43 |
| E4 | quotient estimate | WAIT43 |
| E5 | two quotient×divisor partial products | REQ44 |
| E6 | product sum, numerator and quotient alignment | WAIT44 |
| E7 | remainder and matching quotient | REQ45 |
| E8 | corrected cached ceiling and live ownership | WAIT45 |
| E9 | unchanged header validation/count commit | HEADER |

The cache is ready after E8 for HEADER at E9 and the following RAW metadata offer. Nothing stalls for threshold readiness. An eight-bit validity delay associates the E8 commit with E0's captured word; numerator and quotient are explicitly transported alongside the arithmetic. A streaming model checks overlapping independent values, rather than assuming a count stays stable for eight cycles.

A cancellation can coincide with an old `valid[7]` commit: private cache data may still update on that edge, while validity/live ownership clears. That data is unowned. A new complete header overwrites every threshold before metadata can become valid again. Source review explicitly accepts this only under that ownership contract; the actual RTL proof must test flush/commit collisions and retries. No public old output is masked to accommodate it.

## Consumers and retained validation

Only these existing functional predicates change:

| Consumer | Original operand ownership | Change |
| --- | --- | --- |
| synchronous ingress DESCRIPTOR, bands 1…3 | `counts[band]` is committed once from the same fully fetched packet header | compare live `context_blocks` with that band's cached ceiling |
| scratch begin, three count caps | `begin_count1/2/3` are the unchanged packet metadata fields carrying matching thresholds | compare live `begin_blocks` with three ceilings |

The original synchronous descriptor-limit expressions remain solely as simulation identity-assertion references. The old scratch `begin_limit43` likewise remains a simulation reference. They have no functional qualifier use under synthesis; no false path or clock relaxation removes them.

Everything else remains unchanged: CRC before header checks; header block-count mismatch; RAW's exact zero-count requirements; descriptor length/bits/k bounds and their error order; zero-count descriptor checks; epoch-staleness priority; block zero/max guards; scratch capacity; descriptor readback/count mismatch checks; all counts copied into scratch; and every context decoder event-count/position bound. The generic context module accepts independent callers, so its `event_count > start_limit` guard is not replaced by a packet-cache assumption. This remaining live multiply can become a later timing cone and still needs measurement.

For `SYNC_STAGING=0`, the wrapper computes `count/d + (count%d!=0)` directly from the actual legacy `meta_count` outputs. Its internal legacy ingress keeps all original descriptor guards. This fallback is exact and cycle-preserving, with no legacy timing optimization claim. Both wrapper configurations require actual paired regression.

Old unowned counts are retained/reset on exactly their original edges. New sideband values are meaningful only for their owned metadata; their private contents after reset, failed header or cancellation are unspecified. At owned metadata, new assertions check all three ceilings, live validity and held stability. Scratch asserts the complete incoming ceiling/count invariant on every begin handshake. Prepared contexts must initialize/derive matching sidebands rather than claim arbitrary unreachable cache bits are valid.

## Finite model results and remaining actual proof

The first source-reverse audit failed because a short replacement token was ambiguous; it failed before arithmetic modeling or RTL execution. That attempt is retained in `preparation/003`. Earlier source preparations with direct capture-to-multiply and wider unused storage are retained in `001/002`; `004` preserves the initial passing model before adding explicit collision counters. Those preparation steps launched no simulator; the separately granted actual qualification is recorded below.

The current preparation passes 1,966,080 boundary/extreme predicate checks covering every 17-bit block value for all three divisors, plus 300,000 seeded full-32-bit random pairs. It separately emulates each registered arithmetic stage, checking 90,027 streaming clocks, variable captures, 909 flushes, alignment and bounded eight-entry ownership. Independent division/remainder computes the expected result; it does not reuse the reciprocal formula as its oracle.

The header schedule model checks 4,096 completed prepared headers, 3,072 abandoned headers followed by full retries, 69,632 held metadata edges and 2,048 flush/commit collisions. Its exact relative timeline is capture edge 83, cache commit edge 91, HEADER edge 92. Random high-count headers in this model establish arithmetic/scheduling invariants only; they are not claimed valid RAW packets. Real valid RAW packets must retain their zero counts and actual ninety-three-edge fetch/HEADER path in RTL.

The actual focused proof described below exercises the inline production pipeline with full 17-bit boundary counts, full-32-bit extremes/randoms and streaming alignment; runs the complete old/new production ingress capture probes with current-byte forwarding and all original owner/priority assertions; tests real earliest RAW metadata, held offers, capture and commit cancellations, and retries; and pairs all four complete controllers in both synchronous and legacy modes with every existing public/debug/counter/golden comparison retained. Prepared high-count metadata must be explicitly populated with coherent ceiling ownership. The six inherited expected foreign-response assertion rejections remain rejection tests, not recovery proof.

Parent canonical/fresh pixel-pipeline equality and separately authorized fixed-10-ns native synthesis/place/route follow those functional gates. The new count-word→partial-product paths, live block→threshold comparator, prefix/capacity path, generic context guards, WE fanout and slice pressure can still miss timing. No frequency, latency or frame-rate improvement is promised by this preparation.

## Actual focused results

Attempt `20261108T070931247917Z` is retained FAIL: strict compilation rejected five unnamed generate branches in the synthetic arithmetic wrapper before RTL execution. The wrapper branches were named explicitly, without suppressing warnings. All four production sources stayed byte-identical.

Attempt `20261108T071008661895Z` passed zero-Verilator-warning compilation and all actual phases at seeds 109101/109102. It includes no source-only/preparation count in its actual PASS totals:

| Actual phase | Combined result |
| --- | ---: |
| Arithmetic block clock edges | 4,592,318 |
| Full-17-bit block boundary count cases | 3,932,160 |
| Full-width random numerator cases | 600,000 |
| Explicit extreme cases | 78 |
| Live block predicate checks, before/after clocks | 27,553,908 |
| Arithmetic flush/cache-write collisions | 450 |
| Complete paired ingress capture edges | 47,576 |
| Positive prepared capture/priority cases | 3,456 |
| Prepared high-32-bit metadata owners | 256 |
| Real RAW packets, exact 93-edge fetch/HEADER schedule | 14 |
| Explicit commit/abort followed by real retry | 6 |
| Capture-edge abort/restart cases | 6 |
| Actual ingress cache writes / flush collisions | 1,206 / 10 |
| Held ingress metadata edges | 4,590 |
| Expected original foreign-response assertion rejections | 6 |
| Complete four-body paired public edges | 31,856,723 |
| Golden packet/configuration profiles | 160 |
| Golden dense coefficient comparisons | 18,007,552 |
| Inherited directed checks / staging checks | 206 / 18 |
| Paired-controller held metadata edges | 8,840 |

The four-body edge counts are SYNC1: 7,982,473 and 7,983,108; SYNC0: 7,945,823 and 7,945,319. Every inherited public, invalid/debug, counter, memory-service, state and golden comparison remains active. New threshold/prefix owner checks run at metadata. The arithmetic probe uses the exact production generate block with synthetic byte plumbing; it does not stand in for the separate complete ingress or four-controller tests.

The independent complete-ingress cache tracker checks actual captured numerators, current-byte forwarding, every due-E8 cache write, ownership/live bits, held cache and flush collisions. It explicitly populates prepared metadata only after eight post-capture clocks. Real RAW packets retain the original 93-edge path, even after abort/commit collisions and fresh retries. All six foreign epoch/address tests still terminate at the original `stale staging response` assertion, with capture disabled; they provide no post-rejection recovery claim. Only the intentionally unowned new payload contract differs, and no old public output comparison is masked.

The [offline audit](../../experiments/python-gamebub-v107/count-threshold/audit.json) rechecks 35 source hashes, 82 artifacts, all four reversible recipes, eight lossless adapters and the exact extracted production arithmetic block. It independently replays all 47,576 retained capture CSV rows, including 1,206 ceiling cache writes and ten abort/commit collisions. It also records the four post-run executable hashes. This audit adds no RTL execution counts.

All heavy commands were sequential in one lane, using isolated 8 GiB containers, one compiler, split output, strict `-Wall --assert` and C++ `-Wall -Wextra -Werror`, with no added warning suppression. The full production compiles took 305.6, 321.6 and 320.6 seconds under their 600-second caps; no compile continuation was required. Every failed/superseded preparation and the initial strict wrapper failure remains retained. The frozen source recipe's original preparation-status label is historical metadata; the selected actual receipt above is the qualification gate.

## Separately scoped native-unit observation

The parent-authorized [extracted-wrapper native evidence](../../experiments/python-gamebub-v107/count-threshold/native-unit/evidence-index.json) uses the frozen arithmetic wrapper, not the complete ingress/decoder. It reports sixteen DSPs after legal synthesis sharing: fourteen with PREG=1 and two with AREG=1/BREG=0/MREG=0/PREG=0. The two PREG=0 sites remain explicit mapped evidence; no all-output-PREG claim is made. All DSP resets and 469 payload-FF reset pins are grounded. Seven reset-bearing fabric registers were independently attributed to validity/reset-mask control. These observations are separate from the behavioral unit result.

Synthetic byte broadcasting permits cross-pipe sharing and SRL inference that need not occur in full ingress, where the lower bytes of the three fields differ. Consequently these mapped resources and positive synthesis-only timing do not predict full-production resource use, routing, parent frequency or frame latency. Production sources stay frozen; the parent owns the exact complete pixel-canonical comparison and any combined native activation.

## Complete pixel decoder composition

The source-pinned combined variant adds these four threshold/prefix bodies to
the qualified META/TABLES/private-reset decoder. The complete fresh-candidate
comparison passes both retained control seeds, **44 case-profile runs and
42 directed checks**, requiring exact stdout, public cycles, events and canonical
pixel bytes. The actual elastic control is reused and not recounted.

Receipt: [full canonical comparison](../../experiments/python-gamebub-v107/threshold-pipeline/results.json).
The native source-map gate requires exactly the same 17 RTL bodies plus include
header; strict simulation splits the admission helper bytes losslessly into
correctly named compile files. No assertion or golden comparison was removed.

The measured META parent route is retained with its original negative slack.
The [eighth-source activation](../../experiments/python-gamebub-v107/coordination/threshold-native-activation.json)
binds that routed path, the actual extracted-unit mapping receipt and this full
canonical proof. The [native comparison](vendor-comparison.md) records the final
fixed-10-ns result; source/function qualification alone is not timing closure.

# V90: absolute-cap policy, exhaustive timing oracle and review preparation

V90 tests whether a host policy can choose better actual CS88 representations
using decoder and memory work. It preserves the existing quantized 720×480
picture, native format and addressed alias layout. It also prepares the next
literature review; the review itself is not claimed complete.

## Full-corpus work-aware proxy

The experiment evaluates all **457 sources × eight whole-plane masks = 3,656
actual candidates**. Each mask selects AB38 or BR88 independently for Y, Cb
and Cr. Actual observed primitive totals, complete packet bytes and the frozen
alias memory accounts supply the features. The LOW/HIGH proxy formula was
frozen before the exhaustive timing results were available.

The proxy serializes selected resource-work terms into a ranking score. It is
not a completion-time estimator: it overcounts overlap and omits dependencies
and some work. A separate necessary-work floor is retained and is not called
a sufficient deadline test. See [formula, assumptions and audits](policy.md).

Both cost settings choose all BR88 on 456 sources and a mixed fallback on the
one oversized source. All 457 packets fit **49,152 bytes**. Each full proxy
history totals 8,319,065 bytes, with a maximum packet of 48,744 bytes. There
are 914 per-cost selections, but only 457 distinct chosen packets; identical
LOW/HIGH choices do not add content coverage.

## Exhaustive selected-source timing

Four selected sources × eight masks × LOW/HIGH costs give **64 distinct causal
schedules**, with aliases enabled. The oracle minimizes actual modeled decode
cycles, then complete bytes and mask, subject to the absolute packet limit.
It is an offline exhaustive comparator, not a live encoder or measured FPGA.

| Source / costs | Earlier 15% policy | Exact absolute-cap choice |
|---|---:|---:|
| C0/f0 key, LOW | 7.29471 ms | 7.17692 ms |
| C0/f0 key, HIGH | 10.08595 ms | 8.12490 ms |
| C3/f50 hard source, LOW | 10.80892 ms | 10.80320 ms |
| C3/f50 hard source, HIGH | 12.30751 ms | 12.29713 ms |

The key's best packet uses Y-only Rice, mask 1, at 29,941 bytes. It fits the
absolute cap but exceeds the old relative 15% allowance. The hard source also
prefers mask 1, at 47,674 bytes, and still misses 10 ms. Cold/cheap LOW cases
prefer mask 0; eliminating all feedback is not always the fastest choice.

The proxy matches the oracle mask on 0/4 LOW and 1/4 HIGH source cases, but its
maximum timing regret is only **19.74 µs LOW / 10.38 µs HIGH** on this selected
set. This supports testing a simple policy further, not generalizing its
accuracy to every frame or target. Four of all 64 cases pass the necessary
10-ms work floor but miss modeled completion, demonstrating the floor's limit.

All schedules pass independent graph/resource/credit checks. Sixteen full
retained DAGs pass re-audit. Thirty-two old policy-row comparisons match V89,
representing **22 unique prior cases**, rather than 32 independent controls.
See [all exhaustive-model results and limits](exact.md).

## Fresh native selection qualification

Four complete native histories run proxy LOW/HIGH and exact-four-source
overrides with proxy fallback elsewhere. They pass **1,828 accepted packet
calls plus 1,828 exact replays**, matching qualified coefficients, canonical
pixels, semantic HUD, RGB565 display, content root and frame seal. All four
receiver processes exit zero and all accepted packets fit 49,152 bytes.

Only eight source/cost choices are exact-oracle overrides. The other frames in
those histories use the proxy; this is not an exhaustive 457-frame oracle or
new distinct gameplay. Existing CS88 bytes are reconstructed from previously
qualified AB38/BR88 components and quantizer state, with no new image loss.

The native receiver is frozen CS88 C++ code. Native execution is a correctness
oracle, not hardware decode timing. Both encodings are prepared offline; live
host candidate-generation cost and finite ESP32 transport remain unmeasured.

## After V90: review before the next codec change

The next step is the [literature-review brief](literature-review-prep.md), with
nine screened primary-source seeds, an explicit search/selection protocol,
review questions driven by these results and a fair HEVC/AV1 comparison
contract. A [source log](literature-review-source-log.json) distinguishes
metadata/abstract screening from full reading, and an
[extraction matrix](literature-review-matrix.csv) is ready for the review.

Prioritize bounded parser architectures, dependency-aware policy decisions,
memory/descriptor/display costs and table/state overhead. Preserve the exact
raw-source, quality, byte-accounting and latency-fence conditions before
ranking a method or claiming that a published throughput transfers to Game Bub.

**Hardware 30 fps and complete validated decoding under 10 ms remain open.**
The exact times cover four selected sources under assumed costs and 100 MHz.
Physical ports/controller, HUD semantics, continuous display and ESP32 ingress
are unqualified. The unchanged corpus is one walkthrough family in four reset
histories. No FPGA RTL, deployed firmware or HEVC/AV1 superiority result is
introduced here.

- [Combined audited results](../../experiments/python-gamebub-v90/summary.json)
- [Full-corpus policy audit](../../experiments/python-gamebub-v90/policy/verification.json)
- [Exact model audit](../../experiments/python-gamebub-v90/exact/verification.json)
- [Native packet and replay results](../../experiments/python-gamebub-v90/native/results.json)

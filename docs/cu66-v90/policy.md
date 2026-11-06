# Absolute-cap resource-score policy and exact timing comparison

The new policy considers all eight actual AB38/BR88 whole-plane combinations
for each of 457 sources. It uses the negotiated **49,152-byte absolute packet
limit**, without the old 5%/15% relative-overhead restriction. These are existing
CS88 bytes and quantized output, not a new codec profile.

## Actual-work interface

`policy/data.py` joins the native BR88 canonical work arrays from V89 and the
frozen native AB38 arrays from V86. The AB38 rows gain a zero `plain_bits` field;
their other counts are unchanged. An arbitrary mask selects the corresponding
plane from one actual array or the other. Complete bytes and packet hashes come
from the independently reconstructed V88 candidate corpus.

`iter_masks(masks=range(8), only=...)` yields a list of frame dictionaries per
source. It includes shared/four-context tile work, native identities, actual
mask, packet/work SHA, full wire bytes, metadata bytes and cap eligibility.
The current corpus has exactly one residual chunk for each plane. This is not
support for arbitrary fragmented/chunk layouts inferred from a bit mask.

The full policy campaign uses exact per-plane totals rather than expanding all
eight full tile arrays into Python dictionaries. Mask 0 and 7 totals are
independently checked against all 914 native AB38/BR88 endpoint observation
records. Synthetic tests independently verify packed row/field layout and
plane boundaries; the producer also matches actual V88 feedback, Rice-bit,
renormalization and chunk-CRC totals on every mixture.

## Frozen scoring rule

The model was frozen before the exhaustive four-source timing results became
available. Its LOW/HIGH primitive weights are the same explicit assumptions
used in V89, including one/two cycles per plain bit. No coefficients were fitted
to the later exact results.

For each candidate, the score is:

```text
outer CRC + metadata scans
+ decoder memory-busy work
+ actual inner fetch work
+ max(ceil(total context compute / 2), longest ordered context compute)
+ emissions
```

This serializes component work for ranking. It overcounts some overlap and
omits dependency/port details. **It is not a completion-time estimate or a
certified upper/lower bound.** Decoder memory traffic is fixed across the
entropy masks for the same source, so this term does not itself discriminate
between those masks. The policy does not model their different memory/compute
interleavings.

A separate necessary-work floor is reported using the maximum of resource
work, with the admission prefix applied only to resources that start after
metadata. The tree/hash floor remains outside that prefix. A floor above
10 ms rules out that deadline under the priced graph assumptions; a floor
below it is insufficient to establish success. The rule is not a physical
hardware lower bound.

The selector minimizes score among cap-eligible candidates, then complete
bytes, then the lower mask. There is always a qualified AB38 fallback on this
corpus; a future source with no eligible candidate is explicitly rejected by
the selector rather than silently overflowing the target limit.

## Full-corpus result

All **3,656 candidate feature records and 914 LOW/HIGH selection records** pass
the independent saved-row arithmetic/cap/tie/source audit. Both cost settings
choose all-BR88 mask 7 on 456 sources and mask 6 on the one source whose all-BR88
packet is oversized. Consequently the two cost settings choose identical
packets on this corpus: 457 distinct chosen bytestrings, not 914 distinct
content frames.

Each policy totals **8,319,065 complete bytes**, maximum 48,744 bytes, with
457/457 fitting the absolute limit. The necessary work floor is strictly below
10 ms on 420 LOW sources and 362 HIGH sources. Those counts are **not full-
corpus decoder timing successes**. The host prepares both entropy encodings
offline; candidate-generation cost, live encoding rate and ESP32 execution
remain unmeasured.

## Four-source exhaustive comparison

The separate exact study schedules all eight masks under LOW/HIGH assumptions
with aliases enabled: 64 schedules on four selected sources. The offline oracle
minimizes actual conditional graph completion, then packet bytes, then mask.
It is an exhaustive research oracle on those inputs, not a live host policy.

| Comparison | LOW | HIGH |
|---|---:|---:|
| Proxy exactly matches oracle | 0/4 | 1/4 |
| Maximum proxy regret | 19.74 µs | 10.38 µs |
| Proxy sources actually below 10 ms | 3/4 | 3/4 |
| Oracle sources actually below 10 ms | 3/4 | 3/4 |

The key source's oracle is mask 1 (Rice only on Y). HIGH timing is 8.12490 ms,
versus 8.13162 ms for the proxy and 10.08595 ms for the old 15%-overhead policy.
The absolute cap permits the useful Y switch that the relative budget blocks.
For two inexpensive LOW cases, the oracle instead retains mask 0, avoiding
extra bytes when parsing is not on the limiting path.

The difficult C3/f50 source remains outside the target even at the oracle:
**10.80320 ms LOW / 12.29713 ms HIGH**, versus proxy 10.80892/12.30751 ms.
Across all 64 exact rows, every necessary floor is conservative, but four
rows pass its 10-ms necessary condition while actual modeled completion fails.
The proxy score has no false-under-10 classifications in these 64 rows, which
does not calibrate it or generalize beyond this small selected set.

These results support a timing/interleaving-aware selector rather than a
feedback-only or resource-floor policy. They do not demonstrate sustained
hardware 30 fps or complete validated decoding under 10 ms. The constant
sentinel, physical RAM/controller/display behavior, HUD semantics and ESP32
transport remain outside this timing comparison.

- [Policy results](../../experiments/python-gamebub-v90/policy/results.json)
- [Independent feature/selection audit](../../experiments/python-gamebub-v90/policy/verification.json)
- [Exact comparison](../../experiments/python-gamebub-v90/policy/exact-comparison.json)
- [Contract tests](../../experiments/python-gamebub-v90/policy/tests.json)

```sh
python3 scripts/cu66-v90/prototype_policy.py
python3 experiments/python-gamebub-v90/policy/test_policy.py
python3 experiments/python-gamebub-v90/policy/verify.py
python3 experiments/python-gamebub-v90/policy/compare_exact.py
```

An initial test script had a syntax typo; its failed receipt is retained.
The corrected 18 contract checks pass. Production data/scoring code was
unchanged by that test correction and by the later exact comparison.

# Exhaustive selected-source timing oracle

V90 evaluates all eight existing CS88 whole-plane AB38/BR88 masks on each of
four previously qualified sources. It uses the actual per-tile/context
observations, complete candidate bytes and addressed on-chip alias layout in
the same bounded causal graph as V89. The two parser/arithmetic servers,
consumer-held credits, transforms, descriptor operations and C2 publication
dependencies remain intact.

Each source is evaluated under LOW/HIGH costs, with aliases enabled:
**4 sources × 8 masks × 2 cost tables = 64 distinct schedules**. This is an
offline exhaustive experiment, not a live host encoder or a full-corpus timing
qualification. The constants-sentinel prototype is not included.

## Conditional oracle

The oracle filters candidates to complete packet sizes at most 49,152 bytes,
then chooses the earliest modeled decoder publication. Ties prefer fewer
complete bytes and then the lower mask. A mask bit selects plain BR88 for its
plane: bit 0 is Y, bit 1 Cb, bit 2 Cr. Mask 0 uses AB38 throughout; mask 1
switches only Y; mask 7 uses BR88 throughout.

| Selected source | Costs | Best mask | Packet bytes | Best conditional ms | Prior 15% policy ms |
|---|---|---:|---:|---:|---:|
| C0/f0 key | LOW | 1 | 29,941 | 7.17692 | 7.29471 |
| C0/f0 key | HIGH | 1 | 29,941 | 8.12490 | 10.08595 |
| C0/f1 | LOW | 0 | 18,607 | 8.82684 | 8.84658 |
| C0/f1 | HIGH | 1 | 19,589 | 9.25790 | 9.25810 |
| C0/f3 | LOW | 0 | 14,523 | 7.92931 | 7.93900 |
| C0/f3 | HIGH | 7 | 15,088 | 8.26246 | 8.26246 |
| C3/f50 hard source | LOW | 1 | 47,674 | 10.80320 | 10.80892 |
| C3/f50 hard source | HIGH | 1 | 47,674 | 12.29713 | 12.30751 |

The key's useful Y-only switch exceeds the old relative 15% allowance but fits
the absolute packet limit. Its HIGH model result drops from 10.08595 to
8.12490 ms. This identifies a constraint of the relative budget; it does not
establish a physical under-10-ms decoder.

For the cold and cheap LOW cases, keeping AB38 is best. For the hard source,
Y-only Rice gives a small gain beyond the prior all-Rice choice, but both LOW
and HIGH still exceed 10 ms. More plain decoding is not always the fastest
complete path: fetch costs and backend dependencies still affect the result.

## Actual work and controls

The new arbitrary-mask reader composes actual frozen AB38 and BR88 plane work,
without scaling counters or estimating one coding mode from another. Every
candidate's byte count and SHA match V88's independently reconstructed packet
set. Work hashes cover the entire canonical shared/four-context observation
array. Each schedule uses those counts to reprice its original producer tasks
before the frozen alias transformation adds actual data and descriptor work.

Every schedule passes the frozen independent DAG auditor: dependency ordering,
resource capacities, context order, finite staging, group ownership and full
publication ancestry are checked. All 32 prior V89 alias-policy row comparisons
match exactly, including packet, work and timeline hashes. Those comparisons
represent **22 unique source/mask/cost cases**, because some policies selected
the same mask; they are not 32 new content cases.

Sixteen complete endpoint DAG/timeline witnesses (mask 0 and mask 7 for every
source/cost) are retained and independently re-audited. Other schedules retain
their in-process independent audits and timeline hashes. The separate audit
rebuilds all 32 actual observation arrays, all producer work totals, the exact
cap-constrained argmins and the unchanged V89 comparisons.

## Assumptions and handoff

LOW/HIGH use the same hypothetical primitive costs as V89, including one/two
cycles per plain bit plus symbol/event costs. Dequantization, inverse and
reconstruction retain nominal 64-cycle costs; BL8 reads/writes use 18/16 cycles;
all milliseconds assume 100 MHz. These are sensitivity inputs, not RTL clock
measurements or physical bounds.

Input is fully buffered at release. Decoder publication is separate from the
later full-base-YUV gather. HUD semantics, physical port/controller behavior,
continuous display, host candidate-generation time and ESP32 transport remain
unqualified. The exhaustive oracle can examine all candidates offline; the
full-corpus proxy selector is evaluated separately and is not this oracle.

The [oracle selections](../../experiments/python-gamebub-v90/exact/oracle-selections.json)
provide the eight selected source/cost packets for fresh native qualification.
Their conditional timing is not a runtime guarantee. Hardware 30 fps and full
validated decoding under 10 ms remain open.

- [Selected results and all oracle values](../../experiments/python-gamebub-v90/exact/results.json)
- [Independent work, control and stored-DAG verification](../../experiments/python-gamebub-v90/exact/verification.json)

```sh
python3 scripts/cu66-v90/prototype_exact.py
python3 experiments/python-gamebub-v90/exact/verify.py
```

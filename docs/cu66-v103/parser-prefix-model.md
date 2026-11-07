# V103 parser prefix model

**Status: PASS — Python combinational model only.**

This artifact advances the V103 rank 1 prefix-network hypothesis without changing the geometry candidates or measured native sources. It models the existing `br88_rice_elastic.sv` scan and an aligned-window leading-zero formulation, then compares `zeros`, `found_one`, `prefix_empty`, `needed`, `take_bits`, and `can_step`.

## Coverage

| Check | Count |
|---|---:|
| Distinct prefix words across windows 0–15 | 65535 |
| Word / representative availability pairs | 704475 |
| Model comparisons (parallel and serial modes) | 1548910 |
| Random full-width reservoir comparisons over every window and availability 0–64 | 133120 |
| Random lower-tail-bit comparisons | 6840 |

The total prefix-word count is 65,535: one empty-width word plus all 65,534 words for widths 1–15. Exhaustive prefix words are tested at representative availability values including 0, values below the window, the window boundary, and larger refill capacities. Full-width deterministic random reservoirs (seed `0x103A11CE`) cover every availability value 0–64 for each window in both modes. Lower tail bits are flipped independently to check that the selected prefix is unaffected.

## Boundary observations

- Empty windows observed: 8338 combinational comparisons.
- Short all-zero unterminated-prefix combinations with enough bits: 4446.
- Fifteen-zero parallel escape-boundary combinations: 57489.
- Leading one at first/last prefix position: 704168 / 8706 comparisons.
- Parallel cases where available bits are fewer than window bits: 269794.

Named edge vectors are also retained in the JSON receipt, including empty, short-zero, 15-zero, first-one, last-one, and unavailable-tail prefixes.

## Result and limits

The two Python combinational formulations matched on every enumerated input. The input and result streams are represented by SHA-256 digests in the JSON receipt; no expanded trace is written. This supports only the next isolated RTL extraction experiment. It does not establish RTL equivalence, full parser behavior, suffix or error-path behavior, a latency change, LUT reduction, synthesis gain, routed timing, or performance.

Source SHA-256: `f10846002fc007d4e5c25133fa425aa34ea492ff2738aeedd6aa5de7252acd47`

Model script SHA-256: `5115b5e15f6fd149dfae14e0389cd51b8cafd13f315be3e1be7955183062b20d`

Enumerated input SHA-256: `69271895cf784590b7edd6dfb4b2780bc1e5ce85709969d80232ece144acacd3`

Enumerated result SHA-256: `629c0e5dbbec8fdae11373bc97a19a66518ccfbcee659966f4c28069a0e0cbbd`

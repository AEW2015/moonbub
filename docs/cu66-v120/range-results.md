# V120 isolated range qualification results

The complete fresh ingress-and-caller suite passes after the verification adapter correction below. An independent terminal audit passed **346 checks**, including current and consumed source hashes, all 100 retained artifact hashes, actual compile-input hashes, exact current V119 reference ancestry, raw terminal records, strict compile flags and every original oracle. The selected receipt is `experiments/python-gamebub-v120/range/attempts/20261109T183959919230Z/receipt.json`; its selector is `experiments/python-gamebub-v120/range/results.json`.

The production candidate remains SHA256 `82f6e3be050d0848e0d9e29439ac31a1a78e981f3a5b9f74f2b6180925c6a2e4`: only the complete signed16 range prefix and its verification assertion were added. All original production assertion blocks remain byte-for-byte. Six production/caller reference adapters were independently matched against the actual V119 18-source map, including the capacity-aware packet wrapper, V116b control and V119 scratch.

## Observed functional results

Each ingress seed retains all 259 successful legacy packets, 84 cancellation retries, 6,272 initial descriptor contexts, 21,860 ready descriptor contexts and 1,920 ceil-byte boundary contexts. All original terminal dictionaries, including observed clocks, exactly match the immutable V117-bytecount controls. The current-reference public pair is active on every clock; no edge is skipped.

| Ingress seed | Legacy public-pair clock edges | Actual synchronous requests | Matching responses | Canceled read owners |
| --- | ---: | ---: | ---: | ---: |
| 117901 | 29,633,007 | 2,256,431 | 2,256,398 | 33 |
| 117902 | 29,631,442 | 2,256,431 | 2,256,398 | 33 |

Each seed additionally checks:

| Added contract | Measured executions per seed |
| --- | ---: |
| Complete signed16 prepared RAW predicate domain | 65,536 bit patterns: 4,097 accepted, 61,439 rejected |
| Natural first/last-coefficient boundary packets | 36: 20 valid completions and 16 reason-5 rejections |
| Natural fetched-RAW-owner cancel/reset/start cases | 27 |
| Clean nonreset retries | 67 |
| Explicit stable-output hold edges | 364 |
| CRC-before-RAW-error priority | 2 |
| Header-before-RAW-error priority | 2 |
| Natural synchronous reads/responses | 18,394 / 18,394, with no terminal pending debt |

The exhaustive domain is repeated in two seeds but still contains 65,536 distinct values. Those cases are explicitly prepared predicate owners, not natural frames. The separate natural packets pass the real CRC/header/metadata/RAM/RAW path; invalid values never transfer and preserve the first error-5 edge and prior valid prefix. Natural cancellation is applied to a coefficient actually fetched from the packet; the inherited suites separately retain pending-read cancellation and drain cases.

Both current-caller seeds pass 40 corpus case/profile records each and 4,501,888 independent dense-coefficient comparisons each: 9,003,776 comparisons total. Each retains 56 directed checks, 18 preparation cancellation checks and nine synchronous-staging checks, including accepted physical debt/drain/replacement and final acceptance fences. Their summary dictionaries also match the historical V117-bytecount summaries. More importantly, the actual paired caller reference uses current V119 sources and retains every old public/telemetry and private pending-tuple check against the candidate on the same edges. These are coefficient-packet fixtures, not distinct complete gameplay frames.

## Preserved failed attempt and correction

Attempt `20261109T182832622843Z` remains an overall FAIL with both ingress seeds passing and no completed caller run. Its caller compile stopped under strict warnings because the reference packet-wrapper adapter had been generated from the older V91h wrapper, which lacks nine prefix/threshold/capacity ports. The log retains nine `PINMISSING` warnings and nine `PINNOTFOUND` errors. This was a testbench interface adaptation error.

The correction regenerated only `verification/br88_packet_ingress_v91h_reference.sv` from V119’s exact `cu66-v108-capacity` source with module-name substitutions, and updated its reversible manifest entry. Production RTL, runner and pinned `range.md` were unchanged across repair. The failed source/compile snapshots remain intact. The complete fresh suite was then rebuilt and rerun successfully; no warning, assertion or oracle was suppressed.

The audit is [range-terminal.json](../../experiments/python-gamebub-v120/audit/range-terminal.json). The selected full PASS makes this candidate eligible for the separate complete-component, transport, parent and native timing gates. Behavioral Verilator results establish no routed clock, CDC correctness, sustained hardware 30 fps or hardware decoding under 10 ms.

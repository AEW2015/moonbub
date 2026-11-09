# V118 Game Bub timing study

**100 MHz internal component timing passes both fresh routed runs. The 125 MHz target remains open.**

| Fresh RTL route | Setup WNS | Setup failures | Hold / pulse failures | Routing errors |
| --- | ---: | ---: | ---: | ---: |
| 100 MHz initial | +0.061 ns | 0 | 0 / 0 | 0 |
| 100 MHz identical-source repeat | +0.061 ns | 0 | 0 / 0 | 0 |
| 125 MHz | −1.499 ns | 12,667 | 0 / 0 | 0 |

The runs use Vivado 2026.1, `xc7a100tcsg324-1`, the fixed synthesis/place/route method, and the actual 10 ns or 8 ns clock loaded before synthesis. All have zero unconstrained internal endpoints. This qualifies the measured out-of-context component at 100 MHz; external I/O and the complete parent are outside that qualification. The positive margin is small.

V118 adds owned residual capture/validation/commit stages, four 128-bit canonical-copy beats, and six registered per-band scratch decision bits. It retains two canonical owners and adds no tile payload buffer. Strict RTL tests and independent audits passed:

- 48 complete canonical records matched independent goldens: 24,883,200 bytes.
- 1,306,584 successful accepted events preserved values, metadata and per-stage order.
- Peer-fault recovery completed 28 full canonical retries. Copy-beat cancellation, malformed residuals, physical reference debt and reachable response cases passed.
- All 4,100 recorded parent hash-job digests were independently reproduced.

| Guarded parent service | Last accepted outer byte → validated commit, cycles | Conditional 125 MHz | Conditional 100 MHz |
| --- | ---: | ---: | ---: |
| Byte, fast | 3,704,705 | 29.638 ms | 37.047 ms |
| Byte, stalled | 9,484,147 | 75.873 ms | 94.841 ms |
| Row, fast | 1,145,104 | 9.161 ms | 11.451 ms |
| Row, stalled | 1,553,197 | 12.426 ms | 15.532 ms |

These are measured RTL cycles under a finite abstract memory service and one key-frame/recovery fixture. The milliseconds assume the listed parent clock; they are not measured hardware latency. The fast row case costs 1.6485% more cycles than V117, compared with 7.0% more in the isolated reconstruction key case. Random stalled service interacts with the changed schedule, so its small improvement is not a controlled speedup claim.

A separate Python prototype passed 1,036,720 arithmetic checks for replacing the source's 32-bit nonce overflow guard with a high-bit reduction and small carry. It has no RTL integration or timing result.

**Sustained hardware 30 fps and validated under-10-ms decoding remain open.** The fast row case exceeds 10 ms at 100 MHz, and the stalled case exceeds it even at hypothetical 125 MHz. Complete-parent timing, real memory/CDC/display integration and production Sunshine/ESP32 integration remain to be verified.

The current 125 MHz worst path is raw-mode input validation, with additional independent admission/cache and reference-control failures. The next coordinated cuts are source-bound in the plan below. No second source composition was selected; the dormant replay candidate is unqualified and unintegrated.

- [Hardware-development handoff](handoff.md)
- [Routed timing and mapping](native-results.md)
- [Next coordinated timing work](native-mapping-next.md), [input chronology](input-validation-proposal.md), [admission/owner candidates](admission-owner-next.md)
- [Functional](functional-results.md), [reconstruction](reconstruct-results.md), [scratch](scratch-results.md), [parent](parent-results.md), [response](response-tests.md) and [Python arithmetic](nonce-model.md) results
- [Plan](plan.md), [reproduction](reproduce.md), [machine-readable results](../../experiments/python-gamebub-v118/results.json)

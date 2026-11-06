# V89: actual Rice work coupled to alias addressing

V89 joins the real BR88 decoder observations with the addressed alias layout in
one bounded causal schedule. It also prototypes a fixed-profile constant-tile
descriptor separately. The CS88 bitstreams and existing quantized 720×480 image
are unchanged; this iteration adds no new wire profile or deployed firmware.

## Actual input work

The new native observer validates **457 sources, 1,371 BR88 chunks and
86,444,480 coefficient values**. It records actual fetches, bit reads, symbols,
AC lookahead, events and emissions per canonical tile and four contexts. No
old feedback counters are scaled into new Rice timing predictions.

The full Rice path has 37,656,819 plain bit reads, 11,435,381 Rice symbols and
5,042,343 AC events. It has zero adaptive decisions, renormalizations or
probability initialization. Those remaining parsing operations are charged;
removing feedback does not make decoding free.

Independent checks cover **all 2,285 mixed-policy observation records** and the
16 selected public-interface arrays. Eighteen native attribution tests cover
lookahead, raw fallback, escaped symbols, DC reset and exact work counts.
See [observations and fetch conventions](observations.md).

## Joint decoder model

Four selected content sources × four actual packet policies × LOW/HIGH costs
× alias off/on give **64 schedules**. Ten unchanged frozen controls match
exactly. All schedules pass independent in-process graph/resource/credit
audits; 15 retained complete DAGs pass a separate re-audit.

The same graph contains actual selected entropy work, complete CS88 packet
scans, bounded coefficient consumers, dequant/inverse/reconstruction, alias
data accesses, descriptor ports, C2 hashing and publication. A full base-YUV
gather follows publication as a separate fence.

For C3/f50, the previously difficult source, with aliases enabled:

| Assumed costs | AB38 control | 15% byte-budget policy |
|---|---:|---:|
| LOW | 11.26378 ms | 10.80892 ms |
| HIGH | 17.12268 ms | 12.30751 ms |

This is a joint result, not an addition of V88's independent speedups. It still
misses 10 ms on that source. Some other selections regress slightly: the key's
LOW time increases from 7.29135 to 7.29471 ms and its HIGH time from 10.07923
to 10.08595 ms. The 5% policy also slightly worsens the hard source. Fewer
feedback operations do not guarantee lower complete latency when extra fetch
work or another engine limits progress.

LOW/HIGH are hypothetical sensitivity costs, including one/two cycles per
plain bit. The model retains two parser/arithmetic servers, nominal 64-cycle
dequant/inverse/reconstruction stages, 18/16-cycle read/write BL8 service and
an assumed 100 MHz. These are not measured FPGA cycles or physical bounds.
See [all joint-model assumptions and results](joint.md).

## Separate constant-descriptor prototype

At the 294 positions in the fixed hidden-tile profile, descriptor 3 generates
CONST128. At visible positions it remains INVALID. All descriptor accesses
are retained, while constant pixel stores and gathers become explicit
generation events. The candidate map remains unpublished until validation.

All 457 sources reproduce exact native tiles and content root/seal. The trace
removes **537,432 writes and 537,432 gather reads** over the corpus, with
8,598,912 logical constant bytes per consumer explicitly counted. Twenty
contract checks and 1,024 symbolic updates test publication, invalid values,
partial candidates, abort and held scanout.

The on-chip descriptor case's maximum decoder memory-busy work falls from
9.99088 to 9.80272 ms, and total memory work through base gathering from 15.82288
to 15.42304 ms. **These are service-work reductions, not decode latencies.**
Generator ports and scheduling remain unpriced. Physical address windows are
unchanged; unused slots do not prove a smaller RAM allocation. This separate
change is not included in the joint timing table above.

See [the constant profile, traffic and failure checks](constants.md).

## What this establishes next

The custom codec now has measured encoding alternatives, actual decoder-work
traces and a joined memory/consumer model. The next host policy should minimize
validated decode/fetch cost under the real packet and queue limits, rather
than use feedback count as its deadline proxy. Add the constant generator and
physical port constraints to that model, then calibrate it in RTL.

**Sustained hardware 30 fps and complete validated decoding under 10 ms remain
open.** HUD semantic work, physical controller/ports, continuous display and
ESP32/transport execution are still unqualified. The 64 timings cover four
selected sources; the 457-frame observation corpus is one walkthrough family
in four reset histories. Neither is a distinct-source sustained hardware test
or proof of HEVC/AV1 superiority. The all-BR88 policy remains diagnostic because
one source in the complete corpus exceeds 49,152 bytes.

- [Next experiment and implementation plan](next-steps.md)
- [Combined evidence](../../experiments/python-gamebub-v89/summary.json)
- [Independent observation audit](../../experiments/python-gamebub-v89/observations/verification.json)
- [Independent joint-model audit](../../experiments/python-gamebub-v89/joint/verification.json)

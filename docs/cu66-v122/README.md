# V122: prepared admission bounds and memory-service study

The new admission bounds pipeline passes focused, full decoder/transport,
physical-debt peer and byte/row parent checks with **zero public-cycle change**.
The qualified V120 100 MHz Source B remains byte-identical to its published
source pin. **The new candidate fails 125 MHz timing and is not promoted.**

The [routed result](timing-results.md) is WNS −1.949 ns, TNS −4,597.575 ns and
11,866 setup failures, worse than V121's −1.347 ns/9,407 failures. The targeted
admission cursor/state family improves by 1.097 ns to −0.250 ns and the new bounds
stages have positive slack, but the global worst is RAW-mode → scratch state.
All 722 independent evidence checks pass; timing remains a separate FAIL.

## What changed

The [new admission source](../../fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv)
prepares cursor/length arithmetic and its validity predicates on existing
word-read edges, then consumes them on the original decision edges. It preserves
full64 length arithmetic, separately wrapped uint32 number bounds, first-fault
priority and cancellation behavior. The V121 prepared request queue and every
other selected source stay unchanged. Payload has no blanket reset; verification
binds every actual consume to the fresh preparation owner and phase.

See the frozen [design](bounds-design.md) and [verification contract](verification-plan.md),
the [executed functional results](functional-results.md), and
[reproduction commands](reproduce.md). Source, proof, recipe and report hashes
identify each selected attempt; unsuccessful focused attempts remain retained.

## Memory budget

The [retained trace audit](stall-baseline.md) corrects transaction granularity:
the row fixture performs **70,080 eight-byte requests**, writing 560,640 bytes
over its abstract 16-bit service model. It is not 560,640 independent byte
transactions. Phase counts and overlapping wait conditions cannot be summed
as independent latency causes.

The stalled row fixture still takes **1,553,197 cycles**, conditionally 12.425576 ms
at an assumed complete-parent 125 MHz clock. Strictly below 10 ms requires
**303,198 fewer cycles**. Removing its entire 193,865-cycle validation tail
would still leave reconstruction at 10.874656 ms. The 100 MHz projections for
the fast/stalled rows are 11.451040/15.531970 ms.

The [burst sensitivity](../../experiments/python-gamebub-v122/memory-study/burst-sensitivity.json)
tests twenty analytical scenarios. Under its explicit idealized assumptions,
32-byte bursts need at least 48.10% of saved service edges to reduce post-input
latency. This is a hypothesis for selecting a fresh controller experiment;
neither the RTL memory controller nor measured parent cycles change here.
See [the memory implementation plan](memory-next.md) for the required address,
wait-owner, write-ACK, validation, scanout and refresh measurements.

The [new trace validator](wait-trace.md) passes 17 synthetic cases plus seven
independent boundary cases, including accepted-write debt before decode-start.
It is a schema prerequisite, not actual RTL instrumentation or a calibrated
controller. The full V122 [machine result](../../experiments/python-gamebub-v122/results.json)
links the selected proofs, native report, checkpoint queries and memory studies.

## Next work and hardware scope

The [next timing experiments](next-timing.md) separate plane-start guard
preparation from wide-stage enable simplification and keep other RAW/context/
kill families visible. Select changes using the actual routed paths, then run
the same independent functional gates and fixed-recipe native comparison.

Continue remote hardware work using the
[qualified 100 MHz Source B handoff](../cu66-v120/handoff.md).
Component timing, complete-parent timing, validated decoding below 10 ms and
sustained distinct hardware 30 fps remain separate gates. No board was contacted
or programmed, no complete board image was produced, and no Sunshine/ESP32
production endpoint changed in this iteration. The production parent still
uses JPEG/MSV1 pending negotiated custom-codec integration.

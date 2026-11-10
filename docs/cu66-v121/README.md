# V121: refill request timing repair

**The targeted request path is fixed at 125 MHz; the complete component still
fails 125 MHz timing.** All four functional stages pass with exact Source B
public cycles. No new clock or hardware milestone is qualified.

The [machine results](../../experiments/python-gamebub-v121/results.json) bind
the source, functional proofs, independent audits, fresh native run and separate
checkpoint queries. See [timing results](timing-results.md),
[functional results](functional-results.md) and [reproduction](reproduce.md).

## Measured improvement

Same part, tool image, 8 ns target and implementation recipe; only the selected
refill queue source changes from V120 Source B.

| Routed metric | Source B125 | V121 |
| --- | ---: | ---: |
| Worst setup slack | −1.517 ns | **−1.347 ns** |
| Total negative slack | −3,931.934 ns | **−3,248.192 ns** |
| Failing setup endpoints | 10,524 | **9,407** |
| Hold slack / failures | +0.082 ns / 0 | +0.069 ns / 0 |
| Pulse-width slack / failures | +2.750 ns / 0 | +2.750 ns / 0 |
| Unconstrained internal endpoints / routing errors | 0 / 0 | 0 / 0 |
| Issued-counter → admission RAM enable | −1.517 ns | **+0.303 ns** |
| Prepared-address → admission RAM enable | Not present | **+0.581 ns** |

The original request family gains **1.820 ns**. Global WNS improves by 0.170 ns,
absolute TNS falls 17.39%, and setup-failing endpoints fall 10.61%. This is a
local timing fix with a measured overall improvement, not complete timing closure.

The new global worst is admission `cursor_reg[1]` → `state_reg[0]_rep/D`:
9.232 ns data delay, 14 logic levels including eight CARRY4s. RAW, context and
kill families also still have failing paths. The independent terminal audit
passes **606 integrity checks** while explicitly reporting design timing FAIL.

## Change and verification

The [new queue](../../fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv)
prepares the full32 next request address on existing start/accepted-request
edges. It holds through stalls and preserves original wrap, reset/cancel,
response-owner, error and credit behavior. Zero public cycles are added.

Mapped synth and routed checkpoints contain 32 prepared-address FFs, zero old
offset FFs and 32 issued FFs. The original B125 has 32 offset and 32 issued FFs.
Global routed CARRY4 usage stays **4,198**: arithmetic is relocated, not removed
globally. No KEEP/DONT_TOUCH constraint forces the new register into existence.

Focused queue, complete decoder/actual transport, physical-debt peer and four
byte/row parent runs all pass. Independent comparison rehashes the actual
value/event/canonical/hash streams against Source B. These are finite repeated
golden/profile fixtures, not sustained distinct gameplay. The small collection,
preflight and observation-wrapper failures are preserved and explained in the
linked reports; no functional oracle was weakened.

## Hardware and product goals

Keep the [qualified V120 100 MHz Source B handoff](../cu66-v120/handoff.md) for
the remote hardware team. Its 18 original source/include files remain unchanged
and pinned to `69c0f145`. This V121 candidate has no qualified 125 MHz handoff or
board bitstream. A negative initial route is not rerun unchanged as a positive
fresh repeat.

Row-service fixtures remain 1,145,104/1,553,197 final-input-byte → validated-commit
cycles. At an assumed complete-parent 125 MHz these project to
9.160832/12.425576 ms. The stalled profile still needs **303,198 fewer cycles**
to be strictly below 10 ms, and the complete parent clock is unqualified.
Production custom-codec endpoints, physical memory service, sustained hardware
30 fps and validated hardware <10 ms remain open.

## Next bounded experiment

Target admission cursor/bounds preparation before state decoding, using actual
owned word-load edges. Inspect all current cursor/chunk-end arithmetic and
preserve its full-width overflow, generic-caller and first-fault semantics.
If extra pipeline stages are necessary, declare and verify a new latency
contract while retaining the exact-cycle control.

Continue RAW/context/kill timing checks and the V122 memory/stall attribution
work in parallel. More DSP lanes alone cannot fix the current admission
control path. Follow the [V121–V125 roadmap](../gamebub-v121-v125-spatial-literature-review.md)
and preserve the separate clock, latency and physical frame-rate gates.

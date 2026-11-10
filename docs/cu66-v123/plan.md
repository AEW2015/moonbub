# V123: spatial ordering preparation and complete-component timing

**Measured outcome:** [V123 results](README.md) pass all functional gates with
exact V122 public cycles. The fresh 125 MHz run improves WNS to −1.086 ns and
TNS to −1,709.649 ns, but still has 6,724 setup failures and is not promoted.
The rank-mask all-endpoint family has +0.159 ns slack; RAW and owner-return
families remain negative. Python rank and causal overlap prototypes are retained;
actual parent overlap, calibrated service and the roadmap's strict latency and
hardware frame-rate exits remain open.

V122 passes all four functional stages with exact cycles, but its fresh 125 MHz
route fails at −1.949 ns WNS / −4597.575 ns TNS / 11,866 setup endpoints. Its targeted
admission family improves to−0.250 ns; the new global worst is RAW-mode to
scratch state, 18 levels and 9.896 ns data delay. Qualified 100 MHz Source B stays
byte-identical to its original 18-source pin.

## Bounded implementation experiment

Use frozen V122 as the declared exact-cycle control. Change only the selected
scratch alias: precompute a 64-entry raster-rank threshold mask on the original
APPEND edge. Consume its selected bit in parallel with full-width high/block
ordering comparisons on the original INGEST edge. Preserve generic full32
ordering, all phases and RAW values, first-fault priority, response/abort debt,
speculative-bank capture and every previous assertion and independent oracle.
No new public cycles, protocol bits, codec quality/rate change or endpoint
firmware change are intended. V122 admission and V121 refill preparation remain
selected and unchanged.

The focused generic/actual-caller pair must retain inherited tests and add
independent mask/full32 boundary/cancellation cases. Prepared-domain high-bit
fixtures need real APPEND preparation and must be labeled separately from
natural packets. An independent Python arithmetic model supplies additional
finite-domain evidence, not RTL equivalence or timing proof.

Freeze source and proof inputs, run fresh complete decoder/actual V97 transport,
physical-debt peer and byte/row parent stages, then independently compare raw
outputs, events, canonical pixels, HUD/C2 root/seal and public cycles with V122.
Only a passing four-stage source-bound index permits fresh native timing.

## Timing and qualification gates

Reuse the V120 core Tcl/report/8 ns clock recipe byte-for-byte, clock before
fresh RTL synthesis on xc7a100tcsg324-1, pinned Vivado 2026.1/build6511674 image.
No clock relaxation, false/multicycle paths, guessed board delays, directive
sweep or checkpoint-based implementation. Compare every setup/hold/pulse,
coverage/routing metric and fresh methodology report with V122 and retained
historical controls. A positive initial result requires a separate identical
source/tool/core-recipe fresh repeat; a negative source is not rerouted unchanged.

Independent read-only checkpoint queries compare RAW/scratch state, all endpoints
from the mask/previous-position families and mapped register widths, plus the
unchanged admission/refill paths. Query success is not clock qualification.
Actual route evidence controls promotion, including any global regression.

## Spatial compute and validation-overlap milestone

This ordering mask is an application-specific spatial decomposition of a
control/validation cone. It does not itself overlap inverse compute or validation,
shorten the parent cycle count, or complete all V123 roadmap exits. Develop the
next overlap experiment from actual producer/request/ACK/hash/fence traces with
finite owned result slots. Do not expand aggregate counters into invented edge
traces or subtract overlapping phases as independent savings.

The existing row fixtures remain 1,145,104/1,553,197 post-input→validated-commit
cycles until a changed parent actually measures otherwise. At an assumed 125 MHz
these are 9.160832/12.425576 ms; strict <10 ms requires at most 1,249,999 cycles.
The stalled profile still needs 303,198 fewer cycles. Complete-parent/board
clocks, real ESP32 Wi-Fi/QSPI/memory service, sustained distinct hardware 30 fps
and validated hardware decode <10 ms remain separate open milestones.

## Resources and preservation

At most two heavy jobs globally; each 2 CPUs/8 GiB RAM and 8 GiB RAM-plus-swap with
available-RAM/PSI/combined-usage guards and finite watchdogs. No added swap and
no requirement to empty cold swap. Preserve all prior sources/proofs/receipts
and unrelated marker-recovery files and their size/hash/mtime. No board contact,
complete board bitstream or installed Sunshine interruption is part of this run.

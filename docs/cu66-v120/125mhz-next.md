# Continuing the 125 MHz implementation

Keep the remote 100 MHz handoff pinned while experimenting on a separate source composition. The completed V120 A125 route fails at −1.847 ns; its [independent path audit](native125-mapping.md) identifies admission validation and tile-address/control travel as the main measured problem. Component timing closure, complete-parent timing, sustained hardware frame rate and validated decode latency are separate gates.

## Current bounded repair

Source B combines Source A's range prefix with the [admission header-total equality preparation](admission-match.md). It changes the measured header-total comparison cone while keeping every ordinary public cycle and first-fault priority. The address-writer and context-terminal prototypes are not selected into B.

Require the fresh focused proof, actual complete-component/transport decode, physical-debt/cancellation/retry proof and guarded byte/row parent before routing B at 8 ns. Keep the original recipe and clock-before-synthesis method. Compare WNS, TNS, failing endpoints, hold/pulse margins, internal coverage and routing, plus the actual retained equality register/carry path. A moved worst path or fewer carry cells is useful diagnostic evidence, not a timing pass. A positive result needs a separate fresh repeat of exactly that source/tool/core recipe.

## Next changes, selected from the next actual route

1. **Admission control.** If other full-width header predicates still gate tile/coordinate initialization, prepare the remaining decision during existing header phases, including last-byte forwarding and the original ordered error code. Preserve full32 fields and full35 overflow behavior. Prove ownership and cancellation before using any cached predicate.
2. **Tile and active-cell storage.** The A125 tile-to-active-cell path has long physical travel through address selection and a large write-enable cone. Explore a canonical local write address/data/enable owner, then a registered memory stage if required. Maintain single-write behavior, write ACK/drain ownership, exact coordinate/reference addressing and read-during-write semantics; verify whether block RAM is actually inferred and whether the complete design still fits.
3. **Remaining control families.** Revisit the parser kill-to-storage enables, RAW-mode/scratch validation and context position arithmetic only where the new routed reports retain critical paths. Keep immediate logical cancellation separate from accepted physical work that must drain. Prepare phase-local payloads without resetting datapaths unnecessarily; do not delay cancellation, mask physical responses or add false paths to make reports pass.
4. **Explicit pipeline latency if existing edges are insufficient.** A separately declared next composition may add registered control or memory stages and a revised latency contract. Preserve accepted values/order, error priority, backpressure and cancellation with independent scoreboards. Keep the old exact-cycle control as a control; add and verify an explicit new latency model rather than silently weakening it. A small added pipeline delay may be preferable to retaining a failing 8 ns combinational cone.
5. **Complete-top measurement.** After component closure, route the actual board parent with clocks, CDC/reset, QSPI, SDRAM and scanout. Attach calibrated per-frame logs from the remote system before claiming hardware frequency, 30 fps or sub-10-ms decoding.

## Frame and latency budgets

The existing row fixtures require 1,145,104 fast and 1,553,197 bounded-stall cycles from final input byte to validated commit. Their public schedule is unchanged by the current timing repairs:

| Assumed complete-parent clock | Fast fixture | Bounded-stall fixture | Strict under-10-ms cycle limit |
| --- | ---: | ---: | ---: |
| 100 MHz | 11.45104 ms | 15.53197 ms | fewer than 1,000,000 |
| 125 MHz | 9.160832 ms | 12.425576 ms | fewer than 1,250,000 |

At 125 MHz, the fast fixture fits the arithmetic latency budget, but the stalled fixture still needs at least 303,198 fewer cycles to be strictly below 10 ms. At 100 MHz those reductions are at least 145,105 and 553,198 cycles. Clock closure alone cannot remove these service/cycle costs. Optimize measured memory stalls, row joining, validation overlap and reconstruction throughput while retaining finite ownership and complete validation.

These are conditional calculations. The complete parent has not been routed at either clock, physical service is not calibrated, and these recovery fixtures are not sustained distinct gameplay frames. A 30 fps source leaves 33.333 ms per frame for the complete real pipeline, including work outside this measurement fence.

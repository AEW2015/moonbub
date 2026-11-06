# V79 monitored full-history qualification

The goals remain sustained **30 distinct source-fps**, followed by a strict
maximum **ingress-complete → validated FPGA decode below 10 ms**, at the
established resolution. V78's 30-source finite replay is the frozen baseline:
all sources display correctly, but validated decode is 14.09–29.11 ms and the
finite display cadence is 29.49 source-fps. Neither physical goal is complete.

## This iteration

1. Reuse the exact V78 decoder/direct-display hardware, controller model and
   independent native pixel/canonical oracle. Change verification only.
2. Retain display errors, memory-error counters and underruns after every
   evaluation, through release/readiness waits and final drain. Give every
   committed source an explicit bounded full-raster obligation.
3. Compute finite-queue occupancy throughout the original fixed release
   schedule, including admission waits; separate waiting and in-service work.
   Keep ingress-complete timestamps unchanged when work waits.
4. Test the monitor's rejection behavior separately with synthetic observation
   snapshots. Those tests qualify the checker, not hardware fault recovery.
5. Replay all four available histories: 119, 119, 119 and 100 distinct sources,
   totaling 457. Each history gets one initial reset; no source within a
   history gets a reset, predecoded canonical seed or injected reference data.
   Independent cohort resets do not constitute one continuous 457-source run.
6. Use actual memory counters and a bounded Python service study to select
   the next implementable memory optimization toward 10 ms. Distinguish exact
   traffic arithmetic, controller evidence and analytic counterfactuals.
7. Audit source/input/log identity, all requested IDs, queue arithmetic,
   validated/ACK/presentation/raster timings and every reported failure.
   Keep functional and performance verdicts separate.

## Execution and boundaries

Build once with one build job in the existing bounded container, then use up
to four independent read-only runtime workers sharing the immutable executable.
Record command wall time separately from simulated cycles. Preserve failed
attempts and their input/source versions before changing any checker.

The fixed input schedule is a model of complete immutable packets; it is not
live ESP32 transport or proof of ESP32 queue capacity. Native HUD processing,
hashing and control still have zero simulated CPU cost. The memory clock is
assumed, not routed Fmax. No bitstream, device fit, CDC or electrical signoff is
inferred from these runs.

Fatal scanout/cache recovery remains a separate open implementation gate.
Stronger error detection does not implement automatic recovery. After full
history coverage, the next sustained simulation gate remains 1,800 distinct
sources over 60 seconds, then the 18,000-source/600-second physical goal with
live transport, processor service and synchronized measurements.

## Completed results and next controlled experiment

All 457 retained history sources now pass the actual-controller/direct-display
regression with zero display errors or underruns. The nine observer tests and
nine standalone prefetch groups pass. The paired original V78 fields remain
unchanged. The Python studies qualify traffic accounting, bounded dependency
models and six injective physical layouts; they do not qualify a speedup.

The timing target stays open: the full corpus validates in 12.41–78.72 ms,
0/457 meet strict under-10-ms, and 136/457 miss the serial ACK budget. Combat
retains up to three packets, requiring 144 KiB in an illustrative fixed-slot
endpoint pool before other firmware costs. Keep these failures in the baseline.

Next, integrate the separate two-slot prefetch experiment through a held
retirement shim, authenticated candidate-to-reference bank translation and
global lease/drain tracking. Capture per-client command and per-tile ready
events before changing memory ordering or physical layout. Run matched-arrival,
matched-phase baseline/prefetch comparisons through the actual SDRAM controller
and repeat all histories. A response FIFO alone does not implement lookahead.

Then test command/bridge grouping against the measured event chronology. The
current controller's idealized non-display command work already approaches
10 ms before LCD/refresh/compute; deeper queues alone are not established as a
solution. Keep default physical layout until controlled RTL comparisons support
a change; the grouped-layout model has no universal winner. Bound long-run
oracle storage and collect a genuinely longer source corpus for the 60-second
gate rather than relabeling repeated frames as new source evidence.

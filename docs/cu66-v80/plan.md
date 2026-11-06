# V80 actual-controller reference-prefetch integration

Keep V69–V79 source and evidence immutable. The goals remain 30 distinct
source-fps, then a strict maximum ingress-complete → validated decode below
10 ms, at the established coded/native resolution. V79 passed all 457 history
sources but validated in 12.41–78.72 ms; neither performance milestone is closed.

## Integration and controls

1. Integrate the two-slot generation/bank/plane/tile reference window through
   actual V74 bridge/V72 controller transactions, retaining native canonical,
   hash, HUD readback and full-raster checks.
2. Authenticate candidate writes/completions, translate candidate-bank identity
   to the immutable reference-bank lease only after authentication, and hold
   write completion until the associated reference slot retires. Preserve
   accepted lookup cancellation and physical-read drain through abort/fault.
3. Keep an exact legacy path as mode 0. Measure the conservative integrated
   prefetch as mode 1 before proposing an optimization.
4. Test a controlled mode 2 that releases the P0 bridge owner after a captured
   128-bit snapshot, while independently retaining the eight-beat stream and
   lease. Prevent a later stream completion from releasing a newer write owner.
   Preserve held-data stability and block a second snapshot until drain.
5. Record actual controller command/client/address chronology and per-tile
   request/response/write/fill events. Distinguish accepted physical commands
   from cache requests and from completions crossing measurement boundaries.
6. Compare identical immutable releases, resets, clocks and fixture identities.
   Preserve queue time and adverse timing results. Only a completed canonical
   and raster replay qualifies a performance observation.
7. After bounded paired tests and both memory corners, run the selected
   candidate through all 457 sources in four independent continuous histories.
   Report each history separately; do not manufacture one continuous stream.

## Verification and publication

Use strict lint, bounded self-checking components, the V79 sticky observer and
explicit per-generation raster obligations. Every attempt retains its result,
exact mutable-source snapshot, frozen-source/input hashes and command/log
digests. Preserve failed attempts and their diagnosis. Completion pulses must
be captured as events rather than expected to remain high through later ACK.

Performance remains distinct from correctness. A model of 100 MHz, instantaneous
native CPU HUD/control and immutable fixture packets is not routed target timing,
ESP32 transport or physical throughput. Counterfactual blocked cycles are not
recoverable latency without matched measurement. Keep sustained 60 s/600 s gates,
target implementation and fatal display recovery open until actually qualified.

## Next acceptance sequence

1. Use mode 2 as the experimental comparison for a separately versioned wide
   128-bit fill interface. Preserve the legacy control and all source releases.
   Add first-valid lookup, snapshot, block-commit and backend-write-done trace
   events before attributing latency to a specific stage.
2. Prove block ordering, held-data stability, exactly-once completion, slot
   ownership and bank drain in component tests, including abort on response
   acceptance and concurrent candidate writes. Test both SDRAM timing corners.
3. Repeat paired actual-controller compressed decode, canonical/HUD readback,
   full native display and reject/abort/retry tests. Run all four existing
   histories without per-source reset. Reject changes that merely shift delay
   into the admission queue or weaken display, hash or ownership checks.
4. If that comparison improves end-to-end validated latency, use measured
   decode/hash/store/controller stage observations to select the next pipeline
   change. Keep arithmetic acceleration and memory service as separate measured
   experiments; do not extrapolate a theoretical per-block saving to a frame.
5. Qualify at least 1,800 distinct source updates over 60 continuous modeled
   seconds with original timestamps and bounded queue/drop accounting. Repeated
   rasters, reset-separated histories and replaying the same few sources do not
   satisfy this gate. Keep CPU HUD/control cost and ESP32 Wi-Fi/QSPI transport
   explicit rather than treating the present zero-time model as a measurement.
6. Finish target synthesis, fit, timing and CDC checks on the exact FPGA, then
   qualify 18,000 source updates over 600 physical seconds, including transport,
   input and recovery behavior. Report all late/lost/rejected sources and the
   maximum packet-complete-to-validated latency. Close the strict under-10-ms
   goal only when every required sample passes; retain a separate decoder-only
   execution measurement for diagnosis.

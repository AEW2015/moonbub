# From the joined model to a deadline-aware application codec

1. **Replace the feedback-count policy with a measured cost policy.** Evaluate
   actual candidate bytes, parse arrivals, memory dependencies and publication
   cost. The existing relative 5%/15% budgets can block a useful large-chunk
   switch or spend bytes without a latency gain. Use the negotiated absolute
   packet limit plus finite transport/queue budgets, and charge live host
   candidate-generation cost. Retain the current policies as controls.
2. **Extend joined timing beyond the four selected sources.** Use all 457 actual
   mixed observations, then add distinct content and scene transitions. Compare
   source by source under identical resource assumptions, including regressions.
   Multiple policies and reset histories are not additional gameplay coverage.
3. **Integrate the constant sentinel with real consumer ports.** The fixed-profile
   state/address proof is complete, but generator bytes are not free cycles.
   Schedule constant production, hash consumption and base/display emission;
   preserve INVALID at visible positions and validation before publication.
   Keep map accesses, leases, failed-write drain and physical layout explicit.
4. **Test finer entropy choices using real bytes.** Whole-plane chunk choices
   are coarse. Prototype per-context AB38/Rice selection with explicit method
   tags, actual re-encoding, strict native parsing and identical coefficients.
   Price metadata, byte fetches and scheduling before assuming it improves a
   key frame or the oversized all-Rice case. This is a proposed experiment,
   not a format already implemented by CS88.
5. **Calibrate parser and transform hardware.** Measure bit-reader/word-window
   parsing, bounded leading-zero extraction, stalls and resource fit. Compare
   real cycles against the observed symbols and causal graph. Then choose DSP
   allocation for dequantization and inverse transforms; the current 64-cycle
   stages and assumed 100 MHz remain unmeasured inputs.
6. **Close the display and ESP32 boundaries.** Add HUD entropy/semantic hashing,
   real RAM ports, row/refresh/direction behavior, continuous line deadlines,
   YUV-to-RGB565 composition and finite Wi-Fi/QSPI queues. Separate fully
   received input, validated publication and displayed-frame fences. Negotiate
   CS88 and buffer limits; retransmit exact selected bytes and test recovery.

The milestones remain 1,800 distinct accepted/displayed frames over 60 seconds
at fixed 30-fps releases, followed by 18,000 over 600 seconds on hardware with
zero detected underruns. Complete validated decoding must then be strictly
under 10 ms on every qualified source. Current selected conditional timings
close neither physical milestone.

# Next application-specific codec and implementation work

The next useful improvement is a decoder architecture that preserves the
current picture while reducing real memory work. Metadata compression is now
measured on complete native packets, and context parallelism is tested with
downstream backpressure. Neither closes the hardware latency milestone.

1. **Integrate tile aliases into the actual command trace.** Start from V87's
   three-slot functional layout and add descriptor validity/version state,
   reference/scanout leases, failed-write drain and atomic publication. Generate
   data and metadata reads/writes from this layout on every source. Keep the
   frozen residency trace as a control. Do not substitute the dense-comparator
   write saving or the memory study's counterfactual for this measurement.
2. **Close the missing coupled-model work.** Price operation-map expansion,
   quantizer parsing/cache access, HUD entropy and semantic hashing, actual
   COPY/CONST transfer ports and reconstruction arithmetic. Include indirect
   scanout, refresh/row/direction behavior and continuous phase. The current
   20% reservation is a sensitivity input, not an LCD trace. Keep first-byte,
   fully received packet, validated publication and displayed-frame fences
   separate.
3. **Calibrate a two-lane RTL microarchitecture.** Implement shared fetch,
   ordered context state, bounded rendezvous and consumer-held credits. Compare
   cycle traces with the causal Python graph, including consumer stalls.
   Measure probability feedback/multiply/renormalization, dequant and inverse
   arithmetic before choosing DSP count or pipeline depth. Achievable clock,
   RAM ports and fit must be reported; assumed 100 MHz and 64-cycle stages are
   not measurements.
4. **Treat CS87 as a negotiated research profile.** Implement its variable
   quantizer grammar and accepted-state cache on the target, preserving
   transactional rejection/replay. The sender must cache decoded quantizers,
   including defined omitted values, rather than assume its original full map
   was stored. Track changing-quantizer and incompressible fallback cases;
   stable quantizers in this corpus do not imply the same saving on every game.
5. **Make host policy aware of actual decoding and transport.** Retain fixed
   COPY and matched all-visible controls. Measure their actual entropy work,
   complete packet bytes, host encoding time and finite buffer needs. Then
   choose representations under a combined byte/decode-deadline policy. The
   all-visible CS87 packets have native parity but no coupled timing claim.
   If calibrated arithmetic feedback dominates, prototype selective bounded
   Rice/raw bypass for costly residual chunks. Actually re-encode those chunks,
   price the extra complete-packet bytes and verify native reconstruction;
   deleting their old arithmetic counters would not prove a new codec result.
6. **Replay finite ESP32 Wi-Fi/QSPI queues.** Include fragmented parsing,
   GUI/input concurrency, stalls, loss, duplicates and bounded recovery. Use
   exact selected bytes for retransmission. The host receiver's 2-MiB cap and
   whole-frame buffers are not a target allocation.

Keep the milestones unchanged: **1,800 distinct accepted frames over 60 seconds
at fixed 30-fps releases**, then 18,000 over 600 seconds on hardware, with exact
displayed identities/content and zero detected underruns. After that, validate
the complete defined decoder strictly below 10 ms on every qualified source.
Multiple configurations, reset histories and repeats of the current 457-source
walkthrough do not substitute for those distinct-source sustained runs.

Application specialization here means preserving unchanged tile storage,
reusing stable quantizer state, keeping HUD/content semantics explicit and
matching parallel arithmetic to bounded memory consumers. It does not mean
claiming a standard HEVC/AV1 decoder has been implemented or outperformed.

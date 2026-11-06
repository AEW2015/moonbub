# Next application-specific codec experiment

V88 supplies actual alternative entropy bytes and addressed alias traffic.
The next iteration should join those two measured inputs, rather than combine
their separate headline savings as if they were one implementation.

1. **Observe actual BR88 scheduling work.** Trace plain bit extraction, bounded
   unary/remainder symbols, zero-run lookahead, coefficient emission and fetch
   boundaries per tile/context. Include AB38/BR88 switching and raw fallback.
   Verify every coefficient against the native oracle. Feed those arrivals into
   the consumer-held credit graph; do not scale or subtract old AB38 timings.
2. **Join entropy policy and alias layout.** Keep complete CS88 packet budgets,
   actual physical data accesses, descriptor accesses, candidate/scanout leases,
   provisional store fences and dirty C2 group reads in one causal schedule.
   Preserve a frozen control and compare source by source. Account for the
   non-COPY writes that the old bank-residency layout sometimes elided.
3. **Choose and validate descriptor storage.** On-chip maps, a small word cache
   and uncached external maps have materially different traffic. Include map
   ownership, packed-word updates, cache misses/evictions, validity and response
   drain. A logical map budget is not a physical BRAM/port fit result.
   Evaluate a CONST128 descriptor sentinel as a separate native-verified
   comparator: the fourth two-bit code could generate known constant tiles
   instead of storing them. It must preserve hash/display bytes and lease
   semantics; do not remove those stores from V88's measured trace by assumption.
4. **Model the actual display deadline.** Current full-base YUV gather work is
   separate from decoder publication. Add continuous line deadlines, finite
   gather buffers, YUV-to-RGB565/HUD composition, output timing, refresh and
   controller row/direction effects. Keep fully received input, validated
   publication and displayed output timestamps distinct.
5. **Calibrate the simpler entropy decoder in RTL.** Compare a bounded bit
   reader with a word-window/leading-zero implementation using the same actual
   traces. Measure frequency, storage and stalls before claiming one symbol per
   cycle. Use the reduced feedback logic to evaluate DSP allocation for
   dequantization/inverse transforms. Include admission and abort tests.
6. **Make a live host/ESP32 policy.** Measure generating both candidates,
   packet assembly, queue memory and host encoding time. Replace the offline
   feedback-count objective with measured decode/fetch cost under the actual
   Wi-Fi/QSPI envelope. Negotiate CS88 and the target packet limit; preserve
   exact chosen bytes for retransmission. All-BR88 already exceeds 49,152 bytes
   on one current source, so a bounded fallback policy is required.

After these inputs are qualified, compare against HEVC/AV1 on identical source
frames, quality targets and transport conditions. Current exact reconstruction
is relative to the existing quantized picture, not the original game framebuffer.

The milestones stay **1,800 distinct accepted/displayed frames over 60 seconds
at fixed 30-fps releases**, then 18,000 over 600 seconds on hardware with no
detected underruns. Complete validated decoding must subsequently be strictly
under 10 ms for every qualified source. Multiple encodings of the current
457-source walkthrough family and conditional Python schedules close neither
milestone.

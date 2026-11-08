# Next experiments after V113

Keep the CS88 q16/all-BR88 wire profile, 720×480 canvas and 49,152-byte cap
fixed while separating execution improvements from coding changes. The JPEG
production path remains a separately qualified control.

V113's frozen candidate has three local changes and two physical result slots.
Its component scoreboards and the actual forwarding/decoder test are useful
prerequisites, but neither closes the complete Sunshine/ESP32/QSPI/display
path. Do not promote an OOC timing result to that claim.

1. Make the failed timing gate the prerequisite for the next coding experiment.
   The routed 100-MHz worst path is inverse fault-pending state to ingress
   fetch-index enable; the 125-MHz path is inverse acceptance state to ingress
   prepared-request-address enable. Cut the cross-module command/readiness
   dependency with a bounded owned reservation/command stage. Preserve immediate
   public kill masking and accepted physical drains. Pipeline the whole tuple
   and epoch, not only data or a cancel flag. The source fault net's fanout is
   one; blind duplication or MAX_FANOUT is not a demonstrated remedy for this
   multi-net cone. Keep old sources and proofs as controls. See the terminal
   audits and the [control-cut proposal](next-control-cut.md).
2. Check mapped DSP48E1 registers, inferred RAM, control sets and fanout before
   expanding compute lanes. Reset ownership/valid state; retain reset-free
   payload only where the owner/commit proof prevents stale reads. No timing
   exceptions should hide a functional same-cycle dependency. The routed
   component already occupies over 91% of slices. All 44 RAMB primitives have
   their optional output registers disabled; investigate coherent registered
   RAM lookup stages and packed quotient/remainder ROM words under a proven
   latency/valid contract. The synthesis-only prefetch path remains a secondary
   candidate, not the final routed worst path.
3. Implement a two-lane experiment only after establishing real scheduling and
   memory-port service. The V113 1/2/4-lane ledger is a bound, not an instantiated
   or routed multi-lane decoder. Coefficient intake and the consumer already
   impose shared limits. Measure resource, clock, stalls and worst-case frame
   service together.
4. Follow V114's coding candidates using restartable bounded chunks, explicit
   entropy contexts, sparse residual modes and exact HUD blocks. Compare bytes,
   quality, worst-case decoding work and memory traffic against unchanged CS88;
   retain useful bounded temporal prediction. Hardware parallelism does not
   require removing inter-frame prediction.
5. Complete the harness's missing executable boundaries: shared native custom
   encoder/packetizer, ESP32 firmware and GP-SPI/DMA, timed QSPI serialization,
   parent ownership/drains, C2/HUD validation and scanout publication. Add
   sustained distinct-frame/deadline campaigns under one time authority before
   hardware validation of 30 fps and complete decoding below 10 ms.

Conditional conversions of bench cycles at 100/125 MHz are planning data.
Actual routed setup/hold, full-parent CDC/I/O timing and hardware measurements
remain separate evidence gates.

# V21 independent audit checklist

## Hardware claims still unproved after v20

- No FPGA decoder RTL has been implemented or replayed for the v20 arithmetic, parser, HUD delta, or receiver-cache path. Python/C references and vectors are software conformance evidence only.
- No target synthesis/place-and-route evidence establishes LUT/FF/BRAM/DSP use, Fmax, timing margin, physical memory mapping, or bank/cache capacity and arbitration.
- No board evidence establishes memory-controller service under refresh/contention, physical read-drain behavior, line deadlines, scanout order, underflow recovery, or display publication safety.
- No native host/ESP32/FPGA endpoint integration establishes negotiated profile/reset/rekey, DMA/heap/QSPI/RF service, real loss/reconnect behavior, or sustained gameplay cadence.
- No calibrated, fresh long-play hardware run establishes 30 distinct presented frames/s, frame age/gaps, quality/HUD coverage, input/audio coexistence, or fault recovery. The v20 30-ID/s rate is a goal; Python replay/service and bitrate projections are not a hardware 30-fps result.
- Any v21 ACK-driven display-cache reuse, cache identity/generation, invalidation, or read-drain ordering remains a proposed software protocol unless independently implemented and measured on the target.

## V21 audit criteria

- **Bounds and framing:** enforce all declared dimensions, coordinates, counts, lengths, integer ranges, complete-frame cap, and bounded retry/attempt counts before allocation, indexing, or decode. Reject malformed, truncated, oversized, duplicate, and out-of-range records atomically.
- **Byte accounting:** independently recompute exact complete-frame and wire-byte totals from retained serialized artifacts, including headers, patch/delta metadata, CRC/trailers, and any ACK/control messages included by the report. Recompute baseline-vs-delta savings from matched frames; distinguish payload, complete packet, and projected-rate denominators. Check cap admission per frame and aggregate arithmetic.
- **Cache identity and ACK semantics:** key entries by the full declared stream/session epoch, frame/region identity, generation/version, and content identity as applicable. An ACK may authorize reuse only for the exact generation/content the receiver has validated and committed; receipt, decode, display, and physical read drain must not be conflated. Verify duplicate, stale, wrong-identity, reordered, and delayed ACKs cannot authorize incorrect reuse or release a live owner.
- **Loss and reset:** exercise lost delta, lost ACK, duplicate/reordered messages, receiver cache eviction/corruption, sender retry, epoch reset/rekey, and reconnect. Require bounded invalidation/recovery, no stale-cache reuse, no partial display commit, and a full refresh/key path when cache agreement is uncertain.
- **Read-drain/publication:** verify reused or replaced display storage remains owned until all readers/scanout/DMA have drained; reset/abort invalidates private work before publication or acknowledgment. Test delayed drain and reset at each transaction phase.
- **YUV reference separation:** prove exact HUD/display deltas affect only display composition. They must not alter reconstructed YUV samples, predictor identity, canonical tag, or reference-bank publication. Compare retained YUV/reference outputs independently from RGB565 display output.
- **Evidence scope:** bind results to exact source pins, fixture hashes, commands, and retained logs. Label synthetic/model cases as such. Do not make a 30-fps, hardware throughput, resource-fit, or board-readiness claim from the Python experiment.

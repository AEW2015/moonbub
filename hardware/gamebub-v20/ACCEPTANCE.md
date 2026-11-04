# v20 implementation acceptance gates

Record tool versions, source commit, command, seed, vector index hash, actual
part/board revision, constraints and result artifacts for every hardware run.
Keep component correctness, resource fit, timing and gameplay qualification as
separate gates. Never convert a planning rate into a measured result.

| Gate | Required evidence |
| --- | --- |
| A0: source and fixture integrity | `verify_prototype_v20.py` passes from an isolated checkout with matching paired host handoff |
| A1: inverse arithmetic | Every retained native/DC/random/edge block matches int32 residual words and both rounding boundaries; invalid input cannot mutate output |
| A2: stream behavior | RTL replay with stalls, reset/abort at each phase, short/extra blocks and no dropped/duplicated output; no overflow at legal width extremes |
| A3: entropy/parser | Complete AR03, GM01/SR01/CP02 and patch fixtures match decoded coefficients/YUV/display; length/CRC/route/geometry negatives reject before publication |
| A4: compact storage/tagging | All uint8 bank samples round-trip; canonical int16 SHA256[:16] matches every vector; tile reorder/duplicate/truncate/stall/abort cannot publish stale or partial state |
| A5: frame and packet ownership | FG19 and PC18 tests preserve exact owner identity under loss, replay, wrong reply kind/slot, partial ingress and delayed decode; no fabricated credits |
| A6: native encoder policy | Every accepted mandatory-profile frame contains all requested regions and fits 49,152 bytes; all losing work paid; impossible coverage rejects the frame |
| A7: resources and memory | Actual mapped banks/address ranges, all local buffers/control/cache state, synthesis resources, controller service, arbitration/refresh and contention recorded |
| A8: clocks and scanout | Constrained implementation timing passes; actual 480×800 scan order, full clean epochs, line deadlines, underflow and recovery verified |
| A9: calibrated endpoint service | Measured host encode/attempt distribution, ESP RX/CRC/copy/DMA/heap, QSPI FIFO credits, radio batching/RTT/loss and controls bound the selected operating point |
| A10: user experience | Fresh long gameplay at requested geometry/rate, unique decoded/presented IDs, frame age/gaps, quality/HUD coverage, input/audio and fault recovery recorded |

For ready/valid interfaces, a transaction advances only on valid AND ready.
Hold data and its owner/block/plane/stripe identity stable during stalls. Reset
or abort must invalidate private work before any bank/pointer/ACK publication.
Do not discard a buffer still owned by a reader or in-flight packet/DMA.

The scalar C oracle passes A1 host tests; it does not satisfy A2 or mapped hardware
gates. Python fixtures support the remaining tests but do not replace RTL,
implementation reports or board measurements. A0 is a handoff integrity check,
not a product-ready verdict. A6 preserves all requested HUD words by accepting a
background-quality tradeoff; record that loss explicitly. The current custom
pipeline remains experimental until the applicable gates pass.

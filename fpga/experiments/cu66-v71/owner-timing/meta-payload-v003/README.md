# Metadata payload capture v003

This isolated successor derives from sealed meta-payload-v002 and therefore from actual selected receiver 7991bfc59ddf2942080185196b103e9af0b72b94857460f5570b92d035bd71d3. It moves all 417 metadata payload bits into a separate same-edge capture block: HUD tag, canonical tag, HUD offset/length, frame/reference IDs, key flag and parsed timestamp.

The four start-cleared fields retain their original reset values and clear only on the exact original validated IDLE start. Invalid generation or packet length holds previous payload. Metadata capture uses the previously proven meta_fire && !fatal_non_hud guard. Start clear and metadata capture are proven mutually exclusive, so the sequential ordering adds no behavior. Parsed timestamp uses the original clock_count value on the original edge. Global fatal/error/state priorities and the complete event/diagnostic suffix are unchanged.

The formal abstraction removes only parser/base/bank child implementations, promoting all 88 child output signals to arbitrary inputs alongside all 64 original inputs. Owner initial state is arbitrary; only a verifier reset_seen bit is initialized. Following an actual reset edge, unbounded temporal induction proves the original accepted-start predicate equals the new clear predicate, the metadata guards agree, the metadata/HUD invariant holds, and all 417 payload bits equal a literal original-guard shadow at every edge. No valid-start or child protocol assumptions are imposed. This is two-state RTL equivalence on reachable post-reset histories, not SEU/four-state/PVT/MTBF qualification.

The generic optimized FF-enable graph shows zero current HUD-tag bits in all eight moved payload enable cones. This structurally removes the false metadata CE dependency, without exceptions or new cycles. Device setup/hold is not measured here. The event ring and other true global fatal consumers remain separate work.

Native qualification uses the actual selected validpipe system, qualified SDRAM pin model and actual native semantic HUD implementation. Entire parent and candidate KEY/P/P and control/failure/144-word-DIAG snapshot logs must match byte-for-byte, including timestamps, pixels, canonical/HUD goldens, denied writes, abort drain and error71. Native CPU is outside virtual HDL time; no ESP32/SPI/network/hardware throughput is claimed.

No selected source, firmware, constraints, image, hardware or prior evidence was modified. Production source is frozen at SHA-256 1b3be7c9779d4c5c61712c177173a235f1ddbb68737f7687059789325b510f32.

# Prepared parser-stage + CE full-system KEY/P replay

Not compiled or run. Root authorization is required before launching the prepared compile/Rust/run steps.

Two production RTL changes versus selected V028: existing CE receiver and the new validation parser. The other selected RTL files retain exact hashes. The executed source list contains exactly one parser, its new SHA; the old parser source path is absent. A test-only wrapper counter witnesses state19 and the C++ server requires exactly two visits. No production ports were changed.

Use unchanged V55 Rust/native DLL, original KEY/P packets and independent prequalified canonical/raster/HUD goldens. The old CE replay remains untouched. No malformed, stale or recovery injection is inherited from focused tests; this replay itself covers the positive pair only.

Model assumptions: direct CSR8 cycles, core100MHz, modeled yield100us, explicit Prepare200ms, native virtual CPU timing0, accelerated SDRAM powerup20/refresh750, zero-initialized model. No physical SPI/SDK/radio/heap-fragmentation/SDF throughput claim. Front banks0/1 only; bank2 untested.

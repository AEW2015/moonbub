# CE-factored RTL: actual V55 Rust, original KEY/P controls

Both the unchanged zero-start memory model and the separately witnessed deterministic-poison memory model pass the original KEY/P pair through actual V55 Rust/native/RTL/SDRAM/HBU/scanout. Each verifies42,240HUDwords and691,200video pixels plus all candidate canonical bytes. See each REPORT.md and result.json. This is not hardware, new12/HU25 replay coverage, stale/error injection, or routed timing signoff.

The only productionRTL change is the independently checked HUD request-eligibility predicate. Poison adds only model startup fill and runtime witness, not production logic, clocks or real init commands. Both retain8cycle CSR,100us modeled yields,200ms modeled Prepare, accelerated20/750init/refresh and known-front bank0/1 checks. Bank2 and physical memory margins remain unqualified.

Raw canonical/raster/reference payloads are deterministic gzip. preservation.json binds stored and expanded hashes/sizes; expand to a NEW workspace with final.gz removed before using original comparison scripts. Original commands/bindings retain their historical C:/moon paths. Simulator/compiler objects, hostexecutables and nativeDLLs are excluded; exact source and selected images are preserved separately. This candidate's implementation status must be checked independently before any BIT/hardware selection.

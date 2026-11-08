# CE + parser-stage actual-Rust new 12 replay: PASS

The finite twelve-frame replay passed. Read REPORT.md, result.json and layout-v2/comparison.json for the authoritative outcome and limitations. The exact new parser was exercised twelve times; all canonical, video and HUD output matched independent goldens.

Two production RTL modules differ versus selected V028: the reviewed CE receiver and parser validation-state split. Source hashes, actual executed source list, native/Rust provenance and test-only witness are bound in bindings.json. The old parser path is excluded. Three actual included headers are separately bound and checked after completion.

This is positive functional composition, not physical throughput, a two-minute video, live streaming, fault-recovery qualification, routed timing or hardware readiness. Model timing includes an explicit 200 ms Prepare service and 100 us polling yield, with directCSR8 cycles at 100 MHz and accelerated SDRAM init 20/refresh 750. Physical thread yield has no fixed sleep. Target heap fragmentation and stack are not modeled.

Original pre-run notes and the corrected historical source-label binding are retained in preparation-history. No simulation retry, hardware, Vivado, network transmission, commit or push occurred here. The separate original KEY/P gate is preserved independently.

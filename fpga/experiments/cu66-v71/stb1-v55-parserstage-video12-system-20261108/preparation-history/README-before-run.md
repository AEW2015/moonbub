# Prepared CE + parser-stage actual-Rust new12 replay

This folder has not been compiled or simulated. Launch requires successful original KEY/P replay and root review of prelaunch-binding.json.

It uses exact V55 Rust/native with the reviewed CE receiver and parser state19 split. Two production modules differ versus selected V028; all remaining selected RTL remains unchanged. The simulation-only wrapper counts visits to actual hierarchical system_core.receiver.parser.state==19. The C++ server requires exactly twelve visits. The executed source list contains the candidate parser once and excludes its old source path.

The twelve packet bytes and corrected independent tile-major layout-v2/goldens (48 files) match the prior qualified new12 baseline. The old erroneous planar bank oracle is not selected or copied here. Independent proof, native receipt and frozen-Python receipt are retained; no output from this DUT is used to derive goldens. Fixtures span 0.367 seconds of local source content, not 120 seconds or live video. Frames0–8 use HX33 and9–11 use HU25, with P9 referencing8.

No prior full-system result is inherited. The new positive run must compare canonical front-bank bytes, complete composed raster and HUD write/readback against independent goldens, and record all accepted/presented/rejected/underrun counters. No malformed/stale/recovery fault is injected. Front banks0/1 are expected; bank2 remains uncovered.

Modeling stays core100MHz/CSR8 cycles, yield100us (physical thread yield has no fixed sleep), explicit Prepare200ms, native CPU virtual timer0, accelerated SDRAM init20/refresh750 and default zero model memory. No physical SPI/SDK/radio/fragmentation/SDF/throughput claim is made. Fresh Windows/WSL/output paths are asserted absent of old executable destinations; readonly original oracle/source references remain intentionally pinned.

After authorization, run compile.py, compile-rust.py, run.py and finalize.py in order. run.py is bounded to4200seconds and does not retry. Do not run the retained prepare_tiled_goldens.py merely to reproduce the test; its historical independent-proof inputs are already frozen and selected goldens hash-checked.

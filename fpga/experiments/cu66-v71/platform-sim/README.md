# Actual v35 core to CU71 RTL platform co-simulation

Functional control/data gate **PASS**; clean display/cadence gate **FAIL**.

The exact sealed v35 Rust local driver and actual bounded native HU endpoint execute on Windows. A persistent binary RPC link forwards its numerical CSR read/write operations to a Verilated CU71 local-control component wired to the actual CU71 burst system, parser/decoder, canonical reference storage, portrait painter, LCD and checked SDRAM command/DQ model. Both original flash key0/P1 packets are uploaded through the real CSR staging path. The request/ticket and native processor operations are not replaced by a fake successful peer.

Results:2accepted,2qualified presentationACKs,0rejected;42,240completed HUDwordwrites and42,240actual SDRAMword comparisons with the native sealed candidates. Both canonical accepted tags and accepted/front IDs match the original packets. There were1,313LCDunderruns, so descriptorACKs must not be reported as complete clean game frames or30fps acceptance.

The run executed73,760,880modeled memory clocks,1,249,368READcommands,2,142,720writebeats(includingmaskedbeats)and97,234refreshes. These are diagnostic schedule counts, not physical throughput. Memory period10,000ps, readphase274.5degrees and panelhalfperiod17,029ps match the existing system runner. The exact frozen fast checked model retains flight/access/hold0.757/2.223/2.223ns and the disclosed1ps Verilator monitor scheduling compatibility variant. This is two-state simulation, not independent X/PVT or routed timing proof.

Each CSR adapter call advances8memory clocks; a SDK yield advances1,000clocks. These are selected functional adapter delays, not measured SPI/ESP32 service. Native HU CPU execution occurs outside HDL time; report CPUvalues0must not be interpreted as fast decoding. Physical SPI/QSPI endpoint and busCDC, vendorPLLs/jitter, FreeRTOS locks/task scheduling and target CPU/heap/stack are outside this test. Numerical CSR/tag byte order and actual hardware ownership/memory flow are exercised.

The Linux environment has no Rust compiler, so the sealed Windows Rust core is used directly with a persistent WSL binary pipe to the CABI RTL backend. Verilator messages go to a separate stderr transcript; binary replies include a request sequence. Original production modules and v35 source/image files remain unchanged. No hardware or serial action occurred.

Reproduce with `python C:/mb70/scripts/cu66-v71/platform-sim/run.py --output <new-unique-directory>`. The build uses Verilator -j2. Evidence is in evidence/integration01: source-freeze.json, scope.json, execution.json, integration.log, rtl-stderr.log, result.json and audit.json. audit.json binds the selected sources/tools and post-verifies all693existing sealed v35 artifact hashes. Compiler primitive/width warnings are retained; no zero-warning claim is made.

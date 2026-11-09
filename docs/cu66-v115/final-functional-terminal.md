# V115 selected functional evidence audit

Read-only independent audit; no builds, simulations, hardware, or frozen-input changes. Machine-readable pins and per-proof details are in [final-functional-terminal.json](../../experiments/python-gamebub-v115/audit/final-functional-terminal.json).

All eight selected records passed their hash and selector checks: inverse, refined scratch, final ingress, owner focus, final spatial composition, final control peer, final LIVE parent, and JPEG wire. The audit rehashed 290 current-source/snapshot bindings and 367 artifact pins. The initial inverse proof is reused and rehashed, not rerun.

The final main and transport results contain 76 canonical rows total (24 main, 24 transport, 28 peer), representing 39,398,400 canonical Y/Cb/Cr byte samples (YUV420, not RGB pixels). Each selected main/transport seed output was byte-exact against the frozen V113 output; all 28 peer retry payloads matched the frozen V113 vector payloads. The selected final spatial and peer runs report 44 main case profiles, 42 directed checks, 24 successful transport profiles, four abort/reset retries, and 28 peer retries across two seeds.

The selected LIVE receipt passed with two profiles: each reports 560,640 acknowledged writes matching 560,640 requests, 1,025 hash jobs, and one wrong ACK drained before a clean retry. Canonical, accepted, C2/HUD, seal, and abstract-publication checks passed. This is component-model evidence: no ESP32 execution, physical SDRAM, RGB LCD, sustained hardware 30 fps, or fully validated decode under 10 ms is established.

The separate JPEG endpoint test passed four frames and 1,382,400 RGB pixels across two phases, including its CRC/reset-retry cases. It uses a C-model-related golden and is not connected to the custom CS88 transport; it is not an independent decoder oracle.

**Result:** `PASS_FINAL_SELECTED_FUNCTIONAL_EVIDENCE_AUDIT`, with no hash, selector, or comparison mismatches. Custom CS88-to-QSPI integration, Sunshine host serialization and negotiated-stream integration, and ESP32 CPU/Rust execution remain open. The auditor authored report-only flow documentation, not production RTL, implementation logic, or test benches.

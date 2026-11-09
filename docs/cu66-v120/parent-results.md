# V120 live terminal results

The selected V120 live-guard terminal passed actual Verilator RTL runs for byte and row variants at profiles 0 and 1 (seeds 116701 and 116702). The raw receipt, source snapshots, alias origins, and artifacts are independently audited in [live-terminal.json](../../experiments/python-gamebub-v120/audit/live-terminal.json).

All four runs match the six corresponding V119 terminal dictionaries (live case, fences, service, verdict, spatial pipeline, and parent guard) and raw accepted/canonical TSV, event, and hash streams byte-for-byte. Their modeled cycles also match V119 exactly: byte/profile 0 3,938,310 total edges (3,704,705 last-outer-to-commit); byte/profile 1 9,737,801 (9,484,147); row/profile 0 1,378,719 (1,145,104); row/profile 1 1,807,173 (1,553,197). Canonical producer, request, successful ACK, and hash counts are each 518,400; HUD request, ACK, and hash counts are each 42,240. The independently unpacked `actual_001` bytes match the pinned canonical golden and accepted bytes match actual bytes.

Each terminal checks 33,384 raw local reads and responses, with zero raw pending or revoked responses. Physical responses are not masked; the parent guard shows one private residual handshake and one fault-gap edge, with zero private local reads and zero private gap responses. The selected scope models abstract publication and finite service. It does not establish physical SDRAM behavior, routed full-parent timing, ESP32 execution, hardware 30 fps, or sub-10 ms decode.

The two prepared-card audit outputs passed their checks. They explicitly reuse native qualification and budget logic, so they are second-pass preflight audits rather than independent qualification implementations.

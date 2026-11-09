# V120 B parent terminal results

The selected B parent passed four actual Verilator runs: byte service at profiles 0/1 (seeds 116701/116702) and row service at profiles 0/1. The independently audited receipt and source/artifact bindings are in [B-parent-terminal.json](../../experiments/python-gamebub-v120/audit/B-parent-terminal.json).

For each run, the six terminal dictionaries and raw accepted/canonical TSV, event, and hash streams match V119 byte-for-byte. Modeled last-outer-to-commit cycles are unchanged: byte 3,704,705/9,484,147 and row 1,145,104/1,553,197. Canonical accepted, request, ACK, producer, and hash bytes are 518,400 per run; HUD request, ACK, and hash bytes are 42,240. The canonical root, seal, and HUD digest match the independently pinned V119 outputs.

The parent guard records 33,384 raw local reads and responses per run, zero raw pending or revoked responses, and no masking of physical responses. Row service is abstract modeled service, not physical SDRAM. This terminal makes no board-clock, full-parent timing, hardware FPS, or hardware latency claim.

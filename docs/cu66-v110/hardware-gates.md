# V110 hardware gates and integration prerequisites

The development plan defines two hardware acceptance gates. First demonstrate
1,800 distinct 720×480 frames over 60 seconds, then 18,000 over 600 seconds at
fixed 30-Hz source releases. Include real Wi-Fi/QSPI/UI/audio/input contention,
intended displayed identity, pixel/HUD integrity, bounded queues and zero
scanout underruns. These hardware runs are pending; no simulation result passes
them.

After the frame-rate gate, every qualified packet-complete → validated-publication
sample must be strictly below 10 ms. Include entropy decode, reconstruction,
actual memory waits, content/reference/HUD/hash checks and safe ownership
publication. Report min, median, p95, p99, maximum and worst frame identities;
an average-only result does not pass. This gate is OPEN. Existing V109 counters
are simulation-cycle proxies, and most cases exceed the strict one-million-cycle
reference at an assumed 100 MHz; they are not calibrated hardware milliseconds.

## Immediate production prerequisites

1. Integrate CU66/CS88 packet/profile negotiation, bounded compressed-byte
   ingress, error recovery and JPEG fallback into the production parent.
2. Define reference/generation ownership, pixel conversion, memory-write drain,
   validated publication and panel-visible frame identity as explicit contracts.
3. Add calibrated, epoch-tagged timestamps and per-cause queue/stall counters
   from packet completion through validated publication.
4. Constrain and qualify the actual parent clocks, board I/O, generated clocks,
   CDC/reset paths, SDRAM service and display deadlines; prove complete-top
   parity, bounded service and zero scanout underruns.

The current production parent still uses JPEG. Component or OOC timing, RTL
simulation, source exports and Verilator checks may inform these steps but cannot
claim complete-parent timing, sustained hardware 30 fps or strict validated
decode below 10 ms. Hardware testing is performed elsewhere, so both product
gates remain open until their required device evidence is attached.

The normative acceptance text is in the
[development plan](../gamebub-v91-v110-development-plan.md#product-milestone-gates)
and the [V109 parent integration inventory](../cu66-v109/integration-gaps.md).

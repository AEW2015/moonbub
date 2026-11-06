# Real SDRAM-controller row gate

`row_to_sdram.sv` accepts one tagged eight-byte candidate row and issues four
actual 16-bit single-word requests through the existing SDRAM controller. It
holds each physical word until the controller has become non-idle and returned
to idle; the controller does not expose a write response. A row response is
therefore available only after all four real word writes retire, or after the
currently accepted word retires following cancellation. No simulated fixed-delay
ACK stands in for this path.

The logical bank maps directly to SDRAM bank bits 23:22, with byte offset / 2
in the low bits. Candidate banks 0–2 each use only their bottom 560,640 bytes;
bank 3, zero epochs, unaligned rows and out-of-aperture rows reject without
issuing a word write. The row payload is little-endian: word 0 is bits 15:0,
then bits 31:16, 47:32 and 63:48.

Warm `reset` and `cancel` stop unaccepted word offers, retain an accepted word
until idle retirement, then emit a matching error response. Error here means
canceled or invalid logical work; the physical controller has no error-report
input, so this is not SDRAM fault detection. A response already offered after
physical drain remains immutable, including success/error, across later warm
kill. Its caller must discard the completed transaction if it canceled it.
`power_on_reset` also resets the controller and requires external quiescence;
it is not an escape from an outstanding physical owner.

## Controller derivative

The original `fpga/rtl/moonshine_sdram.sv` remains unchanged. Strict Verilator
lint found four pre-existing diagnostics: two 16-to-32-bit comparison contexts,
a 32-to-16-bit power-up assignment and one unused constant name. The mechanically
regenerated `controller/moonshine_sdram.sv` changes only these explicit casts and
removes the unused `WRITE_WAIT=11` name. Other state values remain explicit and
unchanged. `controller-derivation.json` records every exact replacement and
both source hashes. No controller timing or command algorithm was optimized.

The supplemental Icarus run compiles the frozen original and the strict derivative
against the same unit harness and compares every JSON event. It establishes
observable trace identity for that bounded Tac2/seed case, not formal equivalence.
The Icarus compile logs retain normal simulation-assertion synthesis-context
warnings. Primary Verilator builds use `--assert -Wall` without warning suppression.

## Pin model and timing

The timed SV harness instantiates the actual controller and a functional SDRAM
pin model with a 100-MHz command clock, 279-degree (7.75-ns) read capture clock,
4-ns forwarded-clock flight and 2-ns/7-ns tAC cases. Model drive values use
continuous net delays, preserving the tAC behavior under Verilator `--timing`.
Memory is initialized to `(word_address & 65535) ^ 0x5a3c`; this is declared
external-device initial state. There are no backdoor DUT memory writes.

The model checks active/precharge/refresh state, tRP/tRCD/tRAS/tWR recovery,
BL8/CAS3/write-single mode, write masks and contention. It records every
non-NOP command and actual pin write data; scheduled read-drive words and actual
controller read responses are separate events, so a shifted or repeated beat
cannot satisfy the 32 exact raw read checks. It is a bounded behavioral model,
not vendor SDRAM timing/PVT signoff or physical board evidence.

## Evidence scope

Each unit corner runs 20 checks: four SDRAM banks with distinct read bursts,
exact four-word row writes, row hits/misses, candidate-bank aperture edges,
64 seeded row payloads, refresh, cancel/reset before issue and after each of
four accepted words, blocked replacement, held success responses, invalid rows
and retry. Optional Tac2 replay consumes all 140,160 retained actual key/delta
candidate-row requests and adds one check. Each native logical response remains
bound to its source epoch/token/bank/address.

The native replay is actual candidate traffic from prior RTL output. It is not
a live entropy/inverse/reconstruction/HUD/hash/scanout join to this controller.
The counter/timestamp fence includes the bridge and testbench client schedule;
its clocks must not be added to an earlier full-path number or called hardware
frame rate. Byte requests and neighbor-preserving byte RMW are not implemented.
Shared scratch/reference/scanout arbitration, actual GUI/ESP32 transport, mapped
frequency and sustained 30 fps / complete under-10-ms decoding remain open.

## Reproduce

```sh
python3 fpga/experiments/cu66-v91l-sdram/generate_controller.py
python3 scripts/cu66-v91l-sdram/run_controller.py --seed 912301
python3 scripts/cu66-v91l-sdram/run_controller.py --seed 912302
python3 fpga/experiments/cu66-v91l-sdram/verify_original_equivalence.py
```

Use the established `gamebub-cu66-v69-build` container. Verilator timed builds
use C++20 coroutines, strict assertions/warnings and two compiler jobs. The
runner retains source/input snapshots, commands, tool versions, original logs,
compressed event streams and all failed/superseded attempts. JSONL logs include
normal simulator finish lines outside JSON; the explicit `TEST_PASS` verdict
and successful tool exit are both required.

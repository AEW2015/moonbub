# v91l real-controller write scheduling experiment

This experiment compares the frozen v91l row bridge and strict-width SDRAM controller with a separate same-open-row write pipeline. Both variants use the same timed pin model, unit stimulus and native row fixture. The frozen files under `../cu66-v91l-sdram/` are never edited or selected through a runtime timing flag.

Run the complete matched comparison from the repository root:

```sh
python3 scripts/cu66-v91l-writepipe/run_comparison.py
```

Use `--unit-only --seed 912301` for the four-build directed regression. Default full runs compile control and writepipe separately at tAC 2 ns and 7 ns. Each build runs seeds 912301 and 912302. The two tAC 2 ns variants replay the same 140,160 native 8-byte rows for each seed; tAC 7 ns runs the directed checks without native replay. Every compile uses Verilator `--binary --timing --assert -Wall -DSIMULATION -j 2` and C++20 `-Wall -Wextra -Werror`, without warning waivers.

## Controller change

`generate_controller.py` verifies the strict baseline SHA and reproduces the optimized controller with exactly two replacements, retained in `controller-derivation.json`:

1. `request_ready` may assert while the current write is in `RW_CMD`, only if the following request is another write to the same bank and row, reset is inactive and the refresh counter remains below its original budget.
2. At that handshake the current registered address/data still drives the current physical WRITE; the following address/data is latched for the next cycle and the controller remains in `RW_CMD`. When no following word is accepted, the original `wait_cycles(3, IDLE)` recovery remains.

The MRS remains `0x233`: BL8 reads, CAS 3, single-location writes. This is **not** a change to burst-write mode. The output-register/ODDR alignment, read clock and capture path, initialization, PRE/ACT sequence, refresh mechanism and final write recovery are unchanged. There is no accelerated read turnaround or crossing-bank/row queue. The external bridge bounds the stream to four aligned words; the controller is not a general four-entry FIFO.

## Ownership and cancellation

The new row bridge retains one logical 8-byte request, feeds up to four x16 word requests and records at most four accepted credits. It never acknowledges the logical row until every accepted word has passed the controller's physical idle/recovery fence. `count_words_retired` retires the row's accepted prefix together at that fence. The controller monitor separately records any earlier physically drained cohorts, including a refresh split.

Warm reset and cancel stop new word handshakes immediately; they do not reset the SDRAM controller or discard accepted words. An accepted prefix can therefore remain in memory after an error response. Cancellation does not provide rollback. A prefix which already physically drained during an input stall still completes through the fence. Response identity/error remain immutable once offered, even through subsequent reset/cancel and response backpressure. Cold reset is permitted only without physical ownership.

The candidate aperture, mapping and invalid-request rules remain the prior interface: candidate banks 0–2, aligned 8-byte rows through byte offset 560632; word address `(bank << 22) | (byte_address >> 1)`. Raw compatibility probes separately test all four physical banks and exact eight-word BL8 reads.

## Verification and evidence

The common harness adds a four-credit request/idle monitor to the prior pin harness. Directed checks cover raw BL8 read compatibility, physical row hits/misses, candidate aperture edges, seeded distinct payloads, refresh, cancel/reset after zero/one/two/three/four accepted words, replacement blocking, held success/error responses, cancellation after a physically drained stalled prefix, wrong-bank/row/read follow rejection and refresh-budget backpressure/recovery.

The functional SDRAM pin model samples actual emitted pins after the prior 4 ns forwarded-clock flight and checks tRCD, tRP, tRAS, tWR, tRFC, MRS, DQM, ownership of active rows and DQ contention. It explicitly checks one-clock tCCD spacing. Read data propagates with the selected tAC rather than direct testbench substitution. Physical address/DQ for every WRITE is compared with the accepted word stream; retirement must follow its physical command. The independent audit adds further command timing and row/ownership checks.

`attempts/<UTC-and-id>/` retains source/input snapshots, strict compile logs, simulation JSONL gzip files, source/artifact SHA-256 values and the per-mode report. Failures are retained. `results.json` selects the latest attempt, including failures; use its `selected_report` to locate immutable attempt evidence. Early exploratory logs are retained separately and do not substitute for the complete comparison.

Native replay measures **candidate-memory writes only**, using precomputed request traffic. It does not run a decoder, ESP32 Wi-Fi/QSPI model, SDRAM scanout, simultaneous reference reads, shared-memory traffic or live host join. Any 100 MHz time is modeled cycles divided by the fixed modeled clock, not a measured or routed FPGA frequency. Hardware sustained 30 fps and end-to-end or full-frame under-10-ms decode validation remain open.

## Retained comparison result

`attempts/20261107T000322915745Z-1793dc80/results.json` passed all eight variant/seed/tAC modes. Each native mode completed 140,160 rows plus 92 directed logical requests, with 560,999 physical writes, 561,003 accepted/retired controller requests and 32 exact read responses. Each native mode passed 26 named checks; each unit-only tAC 7 ns mode passed 25.

| Native candidate write window | Frozen control | Write pipeline | Speedup |
| --- | ---: | ---: | ---: |
| Key frame, 70,080 rows | 2,562,150 cycles / 25.62150 ms | 1,271,369 cycles / 12.71369 ms | 2.01527× |
| Delta frame, 70,080 rows | 2,561,984 cycles / 25.61984 ms | 1,271,364 cycles / 12.71364 ms | 2.01515× |

Times use the fixed modeled 100 MHz clock. Both seeds reproduced these windows. Seeds vary the directed random payload/address checks; the native workload is intentionally the same fixture, not two different native clips. These results show a candidate-write scheduling improvement; they do not establish full decode time. The write window alone remains above 10 ms in this workload.

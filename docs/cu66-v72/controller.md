# V72 masked BL8 SDRAM controller

`cu72_sdram_controller` changes the memory mode from read-BL8/write-single to
read-BL8/write-BL8, CAS3 (`MRS=0x033`). It retains the four open-row records,
bounded refresh schedule, explicit precharge/activate waits, read retiming and
physical ODDR/IOBUF data/tri-state structure from the frozen v70 controller.
This is a functional-model prototype; the physical sampling phase remains a
board timing assumption rather than a new routed result.

## Request and completion contract

One request transfers on `request_valid && request_ready`. Both `request_ready`
and `idle` are combinationally false whenever reset is asserted, including
between clock edges while the previous state is IDLE. The caller supplies
an eight-word-aligned 24-bit physical x16 address. The upper adapter must reject
unsupported, unaligned or out-of-allocation accesses; the simulation controller
also asserts alignment. The low-level controller does not implement a recoverable
request-error response.

| Signal | Contract |
| --- | --- |
| `request_write` | 1 for write, 0 for read |
| `request_address[23:0]` | Eight-word-aligned physical word address |
| `request_burst_data[127:0]` | Word `i` in bits `16*i +: 16`; captured at handshake |
| `request_byte_enable[15:0]` | Bit `2*i` enables word `i`'s low byte, bit `2*i+1` enables its high byte |
| `response_valid`, `response_data[15:0]` | Eight consecutive read response words; no read-response backpressure port |
| `idle` | No transaction remains active; after a write this follows all eight bus beats and final write recovery |

Byte-enable 1 means write. SDRAM DQM uses the inverse sense. A fully masked
burst still occupies eight bus beats and must satisfy recovery from its last
beat. A single-word fallback therefore uses one masked BL8 request; efficient
writers should submit full or half bursts rather than repeatedly use fallback.

Requests latch address, all eight words and all byte enables at acceptance.
Changing their input values after acceptance cannot alter the transaction.
Once accepted, a write drains without cancellation. A reset flushes controller
and model activity but can leave an already-written candidate prefix in memory;
all higher ownership/admission adapters must reset coherently and prevent that
partial candidate from becoming accepted output.

## Checked model and counters

`cu72_sdram_model` has a full 16,777,216 x16-word / 32 MiB array and models one
selected chip. It checks mode, aligned bursts, open rows, tRCD/tRP/tRAS/tWR,
refresh/tRFC and MRS recovery. It accepts eight write beats with per-byte DQM,
updates only enabled bytes, and applies tWR from the final beat even if masked.
It is not a vendor memory model or electrical timing signoff.

The model preserves `mem`, `rows`, `device_clock`, `writes`, `reads`, `acts`,
`pres` and `refreshes`. `writes` counts words with at least one active byte;
`reads` counts read commands. `write_commands` and `write_bus_beats` distinguish
command and physical bus costs. `last_write_address[23:0]` and
`last_write_data[15:0]` describe the actual most recent active word update,
including the preserved byte in a partially masked word. A fully masked write
leaves those event fields unchanged. Reset clears model counters and active
protocol state, while preserving memory contents.

## Evidence

Run:

```sh
python3 scripts/cu66-v72/run_controller.py
```

All eight executions pass: Verilator 5.020 and Icarus 12, tAC of 2 ns and 7 ns,
and payload seeds 7201 and 7202. Both simulators produce identical terminal
counts for each seed/corner:

- 2,478 checks; 195 completed write bursts and 212 read bursts.
- Eight mask cases: low/high four words, alternating low/high bytes, first/last
  individual bytes, fully masked and fully enabled.
- Adjacent-block sentinel preservation, row boundaries, all four physical banks
  and the last aligned physical burst at `0xfffff8`.
- Input mutation after acceptance and 172 held-request clocks, including a
  request held through initialization.
- 34 observed refresh commands across the campaign, including reinitializations.
- Nine reset-prefix probes: reset after exactly 0 through 8 observed write beats,
  readback of the preserved prefix, no orphan response, and a fresh successful
  write/read following every reset.

An additional reset-edge probe asserts reset with a valid request while the
controller is idle. It checks immediate and clocked ready/idle suppression,
unchanged preexisting memory, and fresh write/read recovery. The final leaf
therefore covers nine write-prefix resets plus one idle reset-edge probe.

Each run ends normally after 10,698 modeled memory clocks. That total includes
idle refresh observation and repeated reset/reinitialization; it is not a frame
or sustained-transfer throughput benchmark. `controller/results.json` records
all command lines, exit codes, source hashes and transcript hashes.

`build-first-unused-trace.log` retains the first strict lint failure: the new
trace outputs were initially unobserved by the bench. The final bench checks
both active-write trace contents and fully masked trace preservation.
`unused-seed-return.log` retains an initial seed-coverage failure caught by the
runner (a request for seed 7202 printed 7201); the final bench requires the
`SEED` plusarg and all eight qualified transcripts report the requested seed.
Neither intermediate transcript is qualified evidence.

No full-system frame rate, target FPGA fit/Fmax, physical SDRAM timing, CDC or
under-10-ms target decoding is established by this controller campaign.

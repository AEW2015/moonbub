# V70 canonical and display memory subsystem

This directory implements real memory clients over the conservative SDR SDRAM
controller, with a checked 32 MiB command model. It does not source reference
pixels from native goldens. Production RTL and all v69 files are unchanged.

`cu70_memory_system.sv` combines:

- `cu70_tile_memory.sv`: generation/bank/plane/tile-identified 64-byte canonical
  reads and writes, packed two u8 samples per x16 word. A request holds one tile
  lease until its held response is consumed or accepted operations drain.
- `cu70_word_bridge.sv`: round-robin tile/auxiliary arbitration with independent
  eight-word read caches. Read misses issue actual aligned BL8 commands. A
  matching write invalidates either client's aliasing cache. Writes are single
  SDRAM word operations and acknowledge only after controller recovery.
- `cu70_sdram_controller.sv`: a local derivative of the existing production
  controller with only module naming, explicit parameter sizing and one unused
  state-symbol cleanup. `controller-origin.json` pins/checks those exact text
  transformations. This is not an equivalence or timing result.

`API.md` records exact interfaces. `cu70_memory_sim.sv` combines the same RTL
with `cu70_sdram_model.sv` for a simulation top without external SDRAM pins.
It exposes command counters and has a simulation-only 20-cycle power-up
parameter default. The hardware subsystem defaults to 20,000 power-up cycles
and `REFRESH_CYCLES=750`. The simulation clocks use a 10 ns memory period,
279-degree read clock, 4 ns modeled forwarded-clock flight and 2/7 ns read-data
access corners. These are declared model conditions, not achieved FPGA Fmax,
board pin budgets or a vendor memory/electrical signoff.

## Shared memory map

`generate_map.py` emits the JSON, SV include and C++ header from one description.
All public addresses are x16 words; JSON also records exact byte addresses.
Three canonical regions occupy different SDRAM internal banks, with three HUD
regions, two RGB565 buffers, two compressed allocations and a high-address
diagnostic region. Total allocated data is 3,381,760 bytes within one mapped
32 MiB chip. Allocations have at least 32 bytes of guard space and BL8-aligned
ends. The second schematic SDRAM chip is deliberately not selected.

The model has all 16,777,216 x16 words; it does not truncate addresses to the
old 2 MiB array. Auxiliary requests outside allocated regions are rejected
without issuing a controller command. A request to physical word `0xffffff`
is tested. No scratchpad, array or declared region is an FPGA BRAM-fit claim.

Canonical layout is planar row-major Y/Cb/Cr, u8 packed little-endian into x16.
The Y plane starts at word offset0, Cb at172800 and Cr at216000. Each luma row
is360 words and each chroma row180 words. An eight-pixel tile row consumes four
words. BL8 reads may fetch four extra neighboring samples; the cache selects
only the requested word. The initial writer uses32 individual word commands
per complete tile. This first adapter supports full x16 writes; it does not
claim an odd-byte mask/RMW or programmed write-burst implementation.

## Abort and completion rules

Read/write responses are held stable until ready. A write response is physical
controller completion/recovery, not FIFO acceptance. `abort_i` cancels the
canonical transaction and `aux_abort_i` cancels the auxiliary transaction;
accepted controller operations still finish. An aborted partial tile can have
provisional words in its candidate bank, but no successful tile response is
exposed. The global owner must retain bank leases and discard that candidate.

**Coordinate upstream drain semantics:** v69 base decode waits for a normal
accepted reference response while it drains. If it is aborted, either let this
adapter complete normally or provide a separate matched cancel/flush protocol.
Do not simultaneously cancel the memory response and wait for that canceled
response to arrive. Reset assumes a shared adapter/owner flush; the model clears
protocol state on reset but preserves memory contents.

## Retained qualification

Run from any directory with the dedicated tools container available:

```sh
python3 fpga/experiments/cu66-v70/memory/run_regression.py
```

Final `results.json` and `regression.log` record eight passing runs:

- Icarus12 and Verilator5.020, seeds7001/7002/7003 at tAC2 ns;
- both simulators again at tAC7 ns, seed7001, with identical cycle and command
  summaries to the nominal run;
- 227 canonical tile transactions and3,695 scalar auxiliary transactions per
  run, including independent scalar physical-address readback for each tile;
- 43 abort probes per run: before/after each of0..32 accepted canonical write
  words, after each of1..8 accepted canonical read bursts, and auxiliary read
  and write drain; subsequent clean write/read recovery;
- simultaneous canonical and auxiliary clients, held-result backpressure,
  four SDRAM internal banks, row/page boundaries, top physical address,
  forbidden allocation/guard accesses, cached sequential reads and cross-client
  alias invalidation;
- actual ACT/PRE/RD/WR/REF/MRS commands, refresh during work and idle, and model
  assertions for tRP/tRCD/tRAS/tWR/tRFC/tMRD and bounded refresh deferral.

Seed7001 completes114,154 modeled memory clocks, with4,230 writes,1,894 read
commands,1,640ACT,1,631PRE and151refresh commands; maximum observed auxiliary
response wait is33 clocks in this component workload. The other two seeds
vary sampled tile positions and agree between simulators. The testbench has a
watchdog and explicit `MEMORY_PASS`; the runner requires both PASS and normal
exit and checks source stability. `--Wall` diagnostics are fatal; only
`BLKSEQ` is disabled for procedural verification-model/bench style.

This is component and command-model evidence. It is not a full457-frame CU66
receiver run, continuous physical LCD result, accurate full-device timing
model, physical bus proof, target resource fit or hardware30fps result. The
native golden comparison, frame owner, HUD/global commit, actual LCD/CDC and
full packet cadence remain separate integration gates.

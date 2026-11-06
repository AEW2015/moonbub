# V91l row writes through the real SDRAM controller

The row-to-word bridge now runs against the existing SDRAM controller's actual
command state machine and a timed pin-level memory model. One eight-byte request
becomes four little-endian 16-bit writes. A completion is offered only after the
last accepted word has drained through the controller's idle recovery. This
replaces the candidate-write response assumption for this standalone gate; it
is **not yet the live decoder/controller/shared-memory integration**.

See the [independent audit](../../experiments/python-gamebub-v91l-sdram/audit.json),
[summary](../../experiments/python-gamebub-v91l-sdram/summary.json),
[source-backed native fixture](../../experiments/python-gamebub-v91l-sdram/traffic-results.json)
and [Python controller contract](controller-contract.md).

## Results and exact timing boundary

Two strict Verilator seeds pass the unit campaign at both modeled SDRAM data
access delays, 2 ns and 7 ns. Each unit corner has 20 check entries, 352 physical
word writes, 32 exact BL8 read responses, and 356 accepted/retired controller
operations. The 2-ns corner additionally replays the actual earlier native key
and delta candidate traffic: 140,160 row requests and 560,640 native word writes
per seed. Its extra replay check makes 21 entries at that corner.

The independent checker replays actual command/address/data pin events, controller
read captures, request ownership, completion timing and cancellation prefixes.
All four complete native bank images across the two seeds match their earlier
560,640-byte accepted-bank goldens. The checker also rejects six deliberately
corrupted trace variants. These checks are simulation evidence, not formal proof.

| Replayed frame | Accepted row requests | Actual word writes | First request → last response cycles | Simulated time at 10 ns/clock |
|---|---:|---:|---:|---:|
| c0/f0 key, bank 0 | 70,080 | 280,320 | 2,561,979 | 25.61979 ms |
| c0/f1 delta, bank 1 | 70,080 | 280,320 | 2,562,092 | 25.62092 ms |

The native request schedule and these fences match across both seeds; seeded
unit payloads differ. These are **candidate-memory write replay fences**. The
source bytes were already reconstructed and HUD-decoded in the earlier live
experiment. No current entropy/IDCT/HUD/hash/publication RTL or processor work
runs inside this fence. Input transport, reference reads, scratch traffic,
conversion, scanout and arbitration are absent. Do not add this time to an older
component fence or convert it into a claim of hardware frame rate.

The result exposes an actual bottleneck rather than a new speedup: the current
controller waits after every single-word write, and raster physical placement
causes frequent row changes. Each 2-ns run records 89,033 ACT commands including
unit traffic. Even the earlier best-case source-FSM write-work bound is 1,681,920
clocks per candidate bank; at a hypothetical 100 MHz that is 16.8192 ms before
row changes and other work. Controller scheduling and placement therefore need
further measurement before a complete under-10-ms target can be achieved.

## Controller, timing model and bounded equivalence

The original [moonshine_sdram.sv](../../fpga/rtl/moonshine_sdram.sv) remains
unchanged. A mechanically generated strict derivative makes four edits: two
explicit 32-bit comparison casts, one explicit 16-bit assignment cast, and
removal of the unused `WRITE_WAIT` name without changing other state values.
Its ports, write-single mode, BL8 reads, command schedule and waits remain the
same. The [derivation record](../../fpga/experiments/cu66-v91l-sdram/controller-derivation.json)
pins both files and the exact replacements. A supplemental Icarus run compares
the original and derivative using the same 20-check 2-ns unit harness and obtains
identical complete observable JSON traces. This is bounded behavioral comparison,
not exhaustive equivalence, synthesis mapping, CDC or timing signoff.

The main qualification uses Verilator 5.020 `--binary --timing --assert -Wall`
and strict C++20 compiler warnings. It models a 10-ns system clock, 4-ns forwarded
clock flight, 7.75-ns read capture phase, and separate 2-/7-ns memory data delays.
The SDRAM model checks selected command spacings and functional contents; it is
not a vendor/PVT electrical model or board measurement.

Early lint runs caught the original width/unused diagnostics and testbench
procedural-delay issues. The latter were rewritten as raw procedural values
with continuous net delays rather than suppressing `INITIALDLY`: the tagged
[Verilator warning documentation](https://raw.githubusercontent.com/verilator/verilator/v5.020/docs/guide/warnings.rst)
explains that ignoring it can remove intended delays. Timed builds use the
[C++20 timing flow](https://raw.githubusercontent.com/verilator/verilator/v5.020/docs/guide/languages.rst).
The first simulation caught a bench address error in an eight-word write loop;
the corrected loop and all failed diagnostics/attempts remain retained.

## Mapping and ownership

Candidate bank IDs map directly to SDRAM bank bits `[23:22]`; the byte offset
becomes a word offset. The row starts on an eight-byte boundary and cannot
cross the 560,640-byte candidate extent.

```text
physical_word = (candidate_bank << 22) | (byte_offset >> 1) | word_index
word_index = 0..3
```

Banks 0, 1 and 2 are accepted; bank 3 is reserved at this interface. Each hardware
bank has an 8-MiB aperture, of which this design uses the bottom 560,640 bytes.
The three candidate extents occupy 1,681,920 actual data bytes within 24 MiB of
reserved apertures. This avoids putting all frame owners in hardware bank 0,
but concurrent-bank speedup has not been measured. Only the controller's first
32-MiB chip is selected; this does not enable the second chip.

Warm cancellation or reset stops further word issue but retains any accepted
physical word until it drains. Already written candidate words remain modified;
there is no physical rollback. The bridge then offers a cancellation completion.
A response already offered after physical drain stays immutable through later
cancel/reset and backpressure; the caller discards it if its logical epoch was
canceled. Cold power reset requires quiescent physical ownership. A competing
replacement offer cannot reuse the bridge before response consumption.

`rsp_error` reports cancellation or invalid input. The underlying controller has
no write-error or write-ACK port; this gate does not detect silent memory faults.
Likewise, the bridge knows bounded bank IDs, not accepted/reference/front roles.
Its caller must grant a provisional bank and preserve the existing transaction
ownership checks. This standalone replay does not commit or present a frame.

## Write-locality candidates for the next experiment

The separate [layout study](../../experiments/python-gamebub-v91l-sdram/layout-results.json)
replays all 140,160 source-backed eight-byte requests through three proposed
physical address maps. It verifies byte-address injectivity, inverse reconstruction,
row alignment and all four x16 word addresses. The root summary independently
checks all 420,480 transformed requests against the original fixture and mapping
formulas. The current RTL remains raster-mapped.

| Physical placement | Ideal ACTs across two frames | Allocated bytes per bank | Extra padding |
|---|---:|---:|---:|
| Raster control | 82,478 | 560,640 | 0 |
| 8×8 tile-major | 1,096 | 560,640 | 0 |
| 16×8 microtile | 1,104 | 564,480 | 3,840 |

These are closed-first-row, write-only locality counts that ignore refresh and
command timing. They are not the measured 89,033 ACTs from the controller run,
which includes refresh and unit traffic, and are not frame-time savings. The
microtile candidate pads each 360-wide chroma plane to 368 physical columns and
places HUD bytes after the padded canonical extent. Both candidates preserve
all intended data, but neither is promoted to RTL.

Tile-major storage can improve native write and reference locality while changing
the physical reads needed by raster conversion and display. In particular, 16-byte
logical reads can cross tile boundaries, and 360-byte chroma rows interact with
16-byte alignment. The next comparison must include exact read/gather/scanout
schedules and masks as well as write traffic; a favorable write-only count is
insufficient for selection.

## Remaining work

1. Compare raster, tile-major and small microtile placement using exact writes,
   reference reads and scanout/conversion accesses. A write-locality model alone
   cannot promote a layout that increases read or display cost.
2. Qualify faster word-command scheduling or supported burst writes against the
   selected SDRAM part's timing requirements, preserving refresh and recovery.
   Keep the new row bridge and controller as controls.
3. Connect scratch, reference, candidate, conversion and display requests to one
   finite physical service and measure the actual live decoder path. The byte
   control still needs implemented neighbor-preserving RMW/masking; its Python
   model is not RTL support. HUD decode/overlay and ESP32 execution remain open.
4. Retain hardware sustained 30 fps and complete validated decoding below 10 ms
   as unfulfilled physical milestones, with V100–V110 mapping/route/test gates.

## Reproduce

Use `gamebub-cu66-v69-build`. Native replay is enabled by default; `--unit-only`
performs only the bounded probes and does not qualify the native gate.

```sh
python3 fpga/experiments/cu66-v91l-sdram/generate_controller.py
python3 experiments/python-gamebub-v91l-sdram/model.py
python3 experiments/python-gamebub-v91l-sdram/traffic.py
python3 experiments/python-gamebub-v91l-sdram/layout_study.py
python3 scripts/cu66-v91l-sdram/run_controller.py --seed 912301
python3 scripts/cu66-v91l-sdram/run_controller.py --seed 912302
python3 experiments/python-gamebub-v91l-sdram/verify_results.py
python3 fpga/experiments/cu66-v91l-sdram/verify_original_equivalence.py
python3 scripts/cu66-v91l-sdram/summarize.py
```

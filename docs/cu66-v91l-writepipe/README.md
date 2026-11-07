# V91l: four-word write pipeline and read-aware memory layout

The SDRAM write path now has a matched, separately compiled optimization candidate: feed four x16 single-word writes from one bounded eight-byte row without recovering between every word. Recover after the final word, then acknowledge the row. The frozen controller and bridge remain the control. This is a standalone candidate-memory gate; it does not join the live decoder, hash/publication logic or all memory clients yet.

The parallel Python work compares physical layouts using the actual native write order and delta-reference requests, plus explicitly derived converter reads. A further byte-exact next-row retention model addresses the conversion overfetch of 8×8 storage. Both placement and retention remain Python candidates.

See the [qualified summary](../../experiments/python-gamebub-v91l-writepipe/summary.json), [independent RTL audit](../../experiments/python-gamebub-v91l-writepipe/audit.json), [root layout cross-check](../../experiments/python-gamebub-v91l-writepipe/model-crosscheck.json), [timing contract](timing-contract.md), [layout contract](layout-read-contract.md), and [row-retention proposal](rowpair-cache.md).

## Matched write-only simulation

| Source-backed candidate frame | Frozen controller + bridge | Four-word pipeline | Cycle reduction |
|---|---:|---:|---:|
| Native key, 70,080 row requests | 2,562,150 cycles / 25.62150 ms | 1,271,369 cycles / 12.71369 ms | 50.38% |
| Native delta, 70,080 row requests | 2,561,984 cycles / 25.61984 ms | 1,271,364 cycles / 12.71364 ms | 50.38% |

Times assume the same **10-ns source clock**. Each window starts at the first actual accepted native row and ends at its frame's last matching physically drained response. Both seeds reproduce the windows. Each frame writes 560,640 bytes through 280,320 physical x16 WRITE commands. Seeded unit data differ; native source traffic is fixed.

This measures writes of previously decoded candidate bytes. It includes bridge scheduling, controller row commands, recovery and refresh. It excludes current entropy/inverse/reconstruction, native HUD preparation, C2/HUD/seal hashing, publication, input transport, reference/scratch reads, conversion, display scanout and contention between those clients. **12.71 ms is not validated frame decoding latency and does not satisfy the complete under-10-ms target.** No new achieved clock or hardware FPS is claimed.

The strict campaign has two variants × two seeds × two modeled read delays (2/7 ns). All eight modes complete 25 directed unit checks; each 2-ns mode adds a full two-frame replay check. Across the matrix, 204 check entries, 256 captured read words, eight exact native bank images, 560,640 native row requests and 2,242,560 native physical word writes are independently reconciled. The 7-ns modes are unit campaigns, not full native replays. Thirty-two deliberate trace corruptions are rejected by the checker.

## What changed

The [controller derivation](../../fpga/experiments/cu66-v91l-writepipe/controller-derivation.json) records two scheduling replacements from the frozen strict controller. In write-command state, accept one next word only if it is another write to the same bank and open row and the refresh budget remains available. Current command/address/DQ outputs use the previous registered request while the next one is latched. Otherwise retain the original final `wait_cycles(3, IDLE)` recovery. MRS stays `0x233`: single-word writes and BL8 reads. Read sampling, initialization and PRE/ACT/refresh behavior are retained.

The bridge retains one logical row and at most four accepted physical words. It does not overlap logical rows or add a frame buffer. Its accepted-minus-retired count may include a prefix already physically idle during a stall; that conservative accounting is cleared only by the row's final idle fence. Every accepted word appears once at the pins before retirement, and every response follows complete drain. Warm cancellation stops new issue and preserves exactly the accepted prefix; previously modified candidate words are not rolled back. Held success and cancellation responses remain immutable under reset/cancel and backpressure. Bank-role/lease authorization and publication remain the caller's responsibility.

The controller has no physical-error port. An error completion means cancellation or an invalid request; it does not detect silent SDRAM faults. Only the first 32-MiB chip is enabled, as in the frozen controller. Bank mapping and candidate extent remain unchanged and raster-mapped in the timed RTL.

The [manufacturer timing receipt](timing-source.json) supports one-clock column-command spacing. Selected tRP/tRCD/tRAS/tRC/tRRD/tCCD/tWR/tRFC requirements are checked against pin traces. This is a timed functional model, not vendor/PVT electrical simulation, SDF timing, FPGA resource/route signoff or board testing. Consecutive writes particularly require fresh routed command/data setup and hold analysis.

## Placement and converter results

The root independently verifies all 420,480 native request mappings, all six complete canonical-plus-HUD inverse bank images, 23,418 reference-tile gathers and 97,200 converter requests across three layouts. The data remain exact, including chroma edges and microtile padding. The converter order below is a declared full-once plane schedule; retained converter events do not provide individual read addresses.

| Layout | Ideal write ACTs, two frames | BL8 reads, one delta-reference phase | BL8 reads, one derived conversion | Extra allocation/bank |
|---|---:|---:|---:|---:|
| Raster | 82,478 | 62,448 | 32,400 | 0 |
| Tile8×8, discard unused rows | 1,096 | 31,224 | 64,800 | 0 |
| Micro16×8 | 1,104 | 62,448 | 37,920 | 3,840 bytes |
| Tile8×8 + proposed row retention | 1,096, same placement model | 31,224, same reference model | **32,400** | Proposed 752 on-chip data bytes |

The last row combines separately verified Python components; it is not one timed shared-service run. The first column excludes refresh and command costs. Phase counts cannot be converted into frame time or added to the write-only timing table. A simple tile layout is insufficient by itself: its reference reads improve while independent conversion reads worsen. The [row-retention model](rowpair-cache.md) restores exact-once conversion reads with at most 728 observed pending bytes, using a proposed 720-byte next-row RAM plus 16-byte physical scratch and 16-byte logical response. Tags/control and existing converter storage are additional. Integrating the real chroma-prefill schedule remains required.

## Next work and unchanged milestones

1. Preserve these controls and implement tile8×8 physical translation as a separate static timed-controller comparison. Include HUD placement, aligned burst gather, lease validation, cancellation and refresh; measure native writes plus actual reference/conversion consumers.
2. Implement the bounded row-retention reader and compare against independent gathers. Handle immutable bank generations, backpressure and invalidation. Adapt to actual chroma prefill, then compare the complete existing RGB565 oracle.
3. Join live supported BR88 reconstruction, validation/publication and all scratch/reference/candidate/conversion/scanout traffic on one finite x16 service. Implement byte-control masking/RMW before claiming a physical byte-versus-row comparison. RTL HUD decode/overlay and mixed-entropy fallback remain open.
4. Run fixed 30-Hz source cadence with distinct frame identities and all service costs. Sustained hardware 30 fps and complete validated FPGA decoding below 10 ms remain open; V100–V110 retain exact-device mapping, placement, routing, I/O/CDC timing and hardware qualification.

Codec syntax, encode rate/quality, Sunshine and ESP32 firmware are unchanged. These measurements do not update HEVC/AV1 coding comparisons or qualify ESP32 transport timing.

## Reproduce and retained diagnostics

Use the existing `gamebub-cu66-v69-build` container (Verilator 5.020, GCC 13.3.0). The default runner compiles frozen control and candidate at both selected read-delay corners, then runs both seeds; `--unit-only` cannot qualify native replay.

```sh
python3 scripts/cu66-v91l-writepipe/run_comparison.py
python3 experiments/python-gamebub-v91l-writepipe/verify_results.py
python3 experiments/python-gamebub-v91l-writepipe/layout_reads.py --check
python3 experiments/python-gamebub-v91l-writepipe/rowpair_cache.py --check
python3 scripts/cu66-v91l-writepipe/summarize.py
```

The runner snapshots every source/input and command, records exit codes/tool versions and compresses raw traces with SHA-256 receipts. Main builds use `--binary --timing --assert -Wall`, C++20 `-Wall -Wextra -Werror`, and two compile jobs. No warnings/assertions are disabled. Standalone Verilator remains the established backend. The simulation workflow requires explicit contracts, finite watchdogs, retained diagnostics and fresh-source rebuilds; it supplies no hardware proof.

Early lint caught a bench-only unused signal; it was logged rather than waived, then incorporated into the kill receipt. A later directed held-error test initially blocked the logical request before acceptance. That bench deadlock was stopped, its source/trace/exit 143 retained, and the hold moved after the logical handshake. The successful matched campaign was rebuilt from the corrected snapshot. Failed attempts are historical diagnostics and are not qualification inputs.

# V48/V027 HUD/QSPI throughput audit

Read-only audit, 2026-11-07. V027 remains unchanged. No RTL build, FPGA write, timing-constraint change or hardware experiment was performed by this audit.

## Result and measured budget

The local V48/V027 cached12 trial passed twelve accepted/presented frames and253,440 actual HUD-word comparisons. That establishes bounded functionality, not30fps. Evidence: `C:/moon/dev/evidence/v48-v027-local-20261107-run01/trial01/export.raw` (complete43-record DY45 export).

| Retained ordinal | Native Prepare CPU | HUD write phase | Full HUD readback/compare phase |
|---|---:|---:|---:|
|9|212.382ms|291.388ms|275.783ms|
|10|196.723ms|289.892ms|322.480ms|
|11|124.060ms|291.166ms|276.801ms|

All phase differences above use receiver timestamps on the same device. Native9 CPU value is from its retained native row; write/readback are differences between valid/write_done/readback_done. These are enclosing firmware phase times, **not isolated SDRAM service or SPI wire times**. Each write/readback phase includes native READ, software packing/comparison, mailbox setup/polling, status checks, SPI driver/lock overhead and FPGA work.

Write throughput is approximately0.145MB/s for42,240bytes. Full readback is0.131–0.153MB/s. Either phase alone exceeds the33.333ms frame interval by about9×. Native Prepare alone exceeds it by3.7–6.4× for these retained frames. Even perfect transfer batching would therefore leave another independent CPU/codec bottleneck before30fps.

## Exact selected sources

Selected FPGA source root is `C:/moon/dev/dy71-v027-20261107-v001/inputs`; selected identity/top/part are documented by adjacent `selection.json`: V027, USERCODE4459373f, DY71 ABI00020000, xc7a100tcsg324-1. The selected `source-freeze.json` SHA values were rechecked against these files:

| Relative FPGA source | SHA256 |
|---|---|
|`fpga/experiments/cu66-v71/hud-bulk-v025/dy71_hud_bulk_v025.sv`|`217193256187f57f0003f43ccb57cf7b0d93a268b717f12a7aa074487f3d7457`|
|`fpga/experiments/cu66-v71/hud-bulk-v025/dy71_local_control_bulk_v025.sv`|`87f4b32d0d9c15c2b398f48255d710426362039f18ebf1b41a88c26fb63c3e4d`|
|`fpga/experiments/cu66-v71/hud-bulk-v025/cu71_bus_cdc_bulk_v025.sv`|`9425958a151f7fd4cd4ed4eb3c9e13ae365e0b594d566e67c506f584a4c86988`|
|`fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v003/moonshine_qspi_endpoint.sv`|`8cd2237217d079452581234e5f2d60073be3b9e78ee2f26d62a90ac84203baf0`|
|`fpga/experiments/cu66-v71/bridge-cache-special-v021/cu71_word_bridge_cache_v021.sv`|`0a0b3e23ddee64762ec661197c0ff11914c0534b443d8b88822f26f30f05a03e`|
|`fpga/experiments/cu66-v71/result-admission-system-v023/cu71_system_final_v023.sv`|`84c3397ee80704dfc7df2f1b80e9e8bc0d46d71fb12fc6fbbef93c6a998ca50f`|

Firmware root for line references below is `C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107` (`F`). Its native decoding remains the V47 largest-first implementation. FPGA line references below are relative to the selected inputs above (`R`).

## HBU1 is already a512-byte payload window

The12-u32 limit is the **mailbox metadata run**, not the HUD payload. `F/handheld/src/cu66/local_usb.rs:28–35` batches at most12 metadata words into48bytes, preserving mailbox register bounds. Its separate bulk payload methods at45–52 batch up to128u32 (512bytes) in one SPI call to0xe0000400.

`R/.../hud-bulk-v025/dy71_hud_bulk_v025.sv:26` accepts at most256u16 per block. Payload scratch is0x400–0x5ff, held in two RAMB18E1 instances (lines45–58), low/high halves of128 packed words. HBU1 magic/version are48425531/00010000 at0x600/604. This is already the intended packed bulk path; replacing12-word metadata calls with larger metadata writes alone cannot accelerate the payload by an order of magnitude.

For each block, firmware `network_driver.rs:161–176`:

1. Checks owner state and requests up to256 words from native HC70 op3.
2. Packs two u16 into each u32.
3. Sends mailbox op22 (setup), carrying identity/bank/ticket plus offset/count/readmode.
4. Writes512bytes of payload for write mode; then op23 runs the block. For read mode, op23 runs first, then payload is read.
5. Waits for sequence-matching mailbox completion, checks returned completed count, and reads four HBU status registers (flags/count/span/ticket).

There are83 blocks per full HUD (82×256+128 words). Each direction therefore performs166 mailbox commands,83 payload transfers,332 scalar HBU-status reads and83 owner checks, plus idle checks, metadata updates and mailbox polls. In the usual steady full-block case with one changed offset and a single completion poll per command, this is around13 SPI transactions/block, roughly1,079 per direction. First-block metadata/tag changes and extra polling add more. This is an explanatory transaction model, not a measured per-phase count; the current export retains only whole-run I/O totals.

The mailbox implementation (`dy71_local_control_bulk_v025.sv:160–172,199–201`) snapshots12 fields at the start doorbell0x24, accepts a strictly newer sequence, routes22 to setup and23 to run, and completes op23 only after the bulk engine's done. Firmware `network_driver.rs:45–55` already coalesces contiguous changed metadata and reads ack/status/data together. The four status reads after each block are still separate calls.

## Firmware READ work precedes every transfer block

**First priority is the ABI-compatible native READ optimization, before another FPGA build.** `F/native/endpoint.hpp:34–37` handles HC70 op3 by iterating every word in every candidate patch, even when the caller requests only256 words:

`for(each patch) for(each word) { if(index in requested range) copy; ++index; }`

Each direction calls it83 times, so one full HUD write traverses1,752,960 candidate words; full readback repeats that traversal. Only21,120 words are requested in each direction. The readback loop re-fetches the same expected native words before comparing actual SDRAM contents.

An isolated endpoint change can skip nonintersecting patches and copy only the intersection, reducing traversal from O(total_HUD_words) to O(patch_count+requested_words). It preserves op3 bytes, bounds, CRC, tag/state/identity checks and all external write/drain authority; it requires no allocation or FPGA change. The source-level iteration reduction is roughly83× across one direction; **that is not a predicted83× phase speedup**, because SPI/mailbox/SDRAM/CRC/packing time remains. Root has assigned an isolated V50 experiment for this change; do not mix it with a window/clock/SDRAM change in its first comparison.

Useful ABI-compatible follow-ups, after that result:

- Add bounded phase aggregates for native READ CPU time, SPI payload time, mailbox completion wait, status checks, transactions and bytes. Retain maxima/counts rather than logging per transaction.
- Read the contiguous HBU status span0x608–0x618 in one existing auto-increment SPI read (five u32, ignoring0x60c if not needed), then validate the same flags/count/span/ticket. This could replace four scalar transactions without dropping checks. It requires proving the window remains stable after done; current single-owner command flow provides that intended stability, but pin-level tests must verify it.
- Keep the original full-readback path as a diagnostic control. Do not silently skip actual verification, fabricate drain ACKs or relabel ingress acceptance as presentation.

## Compressed ingress dominates whole-run transaction count

`F/handheld/src/cu66/network_driver.rs:116–137` still stages the compressed CU66 packet one u32 at a time. Each word needs at least a credit read0x00c, a write0x100 and a stored-count read0x104, with more polls as needed.

The twelve actual packet sizes total175,275bytes, yielding43,821 four-byte staging iterations. This implies **at least131,463 SPI transactions** for packet-word staging alone. The observed complete trial reports161,030 total QSPI transactions: this minimum is81.6% of that total. It is a count comparison, not81.6% of elapsed time. Larger transfers have different per-call and wire costs.

Thus improving only HUD output/readback cannot deliver full-path30fps. A later compressed-ingress block/FIFO contract must replace per-word host round trips while retaining exact stored-prefix, byte count, whole-packet CRC and seal/activate rules. DYN1 network framing itself need not change for a purely local FPGA staging improvement.

## Real FPGA back-end serialization

HBU engine `dy71_hud_bulk_v025.sv:18,60–94` is FETCH→ISSUE→DRAIN for **one16-bit AUX word**. It waits for each response before moving to the next. Increasing the scratch window reduces mailbox overhead but does not change this word-level service path.

`cu71_system_final_v023.sv:130–188` rechecks live generation/frame/bank, sequential HUD address and active ownership; its AUX arbiter also admits one request and waits for its response. This is intentional safety/authority, not a free-running DMA queue.

The memory system connects AUX to p1 (`metadata-baseline-v022/cu71_memory_system_cache_v022.sv:109–110`). `cu71_word_bridge_cache_v021.sv:51–89` has a read cache for p1; scalar writes are masked physical BL8 transactions, preserving only one16-bit word per transaction. Consecutive HUD reads may hit the eight-word cache, while writes still issue masked bursts one word at a time. Genuine128-bit HUD writes could reduce physical write commands from21,120 to2,640, but require a new checked burst path, not just a larger payload BRAM.

CDC (`cu71_bus_cdc_bulk_v025.sv:12–68`) already has a64-entry44-bit asynchronous write queue and a read snapshot mailbox; reads drain earlier writes before sampling, include a settling cycle for BRAM, and return through a toggle handshake. The QSPI endpoint pipelines the next CSR read while shifting the current word (`moonshine_qspi_endpoint.sv:193–204`). These are selected implementations, not assumed single-word-only SPI hardware.

## Bandwidth ceilings, not forecasts

`F/handheld/src/device/drivers/fpga/mod.rs:40,260–300` caps this path at16MHz and uses quad address/data, an8-bit single-lane command, and eight dummy bytes on reads. Adapter calls explicitly use that cap. Device setup offers16MHz (`device/mod.rs:522`); actual physical SCLK for this trial was not separately measured in the retained export.

At nominal16MHz quad, raw payload ceiling is8MB/s.42,240bytes alone therefore require at least5.28ms of data clocks; write plus external readback require10.56ms before headers, dummy cycles, command polls, gaps, SDRAM waits and CPU work. For a512-byte write, command8+address8+payload1,024=1,040 SCLK cycles,65us at16MHz; read adds16 dummy cycles, about66us.83 such payload transactions are around5.4–5.5ms of clocks each direction, far below the measured~291ms enclosing phases.

At30fps, full HUD write+external readback payload is2.5344MB/s; adding the fixture mean compressed packet contributes about0.438MB/s, total~2.973MB/s before protocol overhead. Raw wire capacity could accommodate that total with efficient transfers, but the actual per-word/per-block handshakes and native work cannot currently do so. Raising the SPI clock is not the first fix and is not authorized by these arithmetic ceilings.

## Versioned design after the measured firmware-only result

If software READ/status batching leaves transfer dominant, create a separate **HBU2 capability/version**, preserve HBU1/V027 as fallback, and agree its local ABI before firmware/hardware testing. Suggested concrete first scope:

- Two1KiB payload banks (512u16 each), explicit free/ready/busy/completed credits; setup binds generation/frame/reference/bank/ticket/offset/count/direction and monotonic sequence. Never overwrite an active bank; reject stale/short/duplicate/out-of-order payloads deterministically.
- Accept one entire payload bank with one queued SPI transaction, then ring one descriptor doorbell; overlap filling the next bank with draining the current bank. Bound total queued descriptors and expose overflow as a sticky counted error, not silent loss.
- Convert eight contiguous u16 into actual128-bit SDRAM requests with full byte masks, retaining exact completed-word count only on real downstream response/drain. Maintain original per-frame HUD bounds and lease/abort/generation checks across queued work. Enlarging BRAM alone is insufficient.
- Apply an analogous independently identified block-ingress capability to compressed staging, e.g.512–1,024byte accepted chunks with exact stored-prefix/CRC progress. Credit reports must mean actual reserved storage, not arbitrary SPI queue availability. Preserve DYN1/MSV1 separation and native/FPGA ownership.
- Only consider replacing external full HUD readback with a negotiated FPGA proof computed over **actual completed SDRAM readback**, including all21,120words and canonical HUD rectangle/tag serialization. Returning expected tags, CRC of the incoming payload, completed counts alone or a read-free ACK is insufficient. A CRC-only proof is a different integrity contract and must not be silently treated as the existing native HUD tag proof.

A streaming-DMA variant can later enlarge transfers further, but first qualify bounded double-buffered banks and true memory bursts. Neither constitutes a30fps claim until native Prepare and downstream decode/presentation concurrency are also measured.

## Simulation and implementation gates

1. Native READ: exhaustive requested spans/boundaries/zero count/invalid range/opcode/reference/generation, byte-exact reply/CRC and no allocator-stat drift; all12 golden HUDs plus broader corpus. Compare CPU and phase aggregates on unchanged V027.
2. Existing ABI status batching: pin-level QSPI auto-increment reads across0x608–618 at selected16MHz, random clock phase and CDC backlog; old/new checks must return identical snapshot outcomes without dropping authority checks.
3. HBU2 unit tests: bank credits, setup/load/run races, unaligned/odd/final counts, partial payload, abort during asserted request, late/duplicate responses, stale tickets/generation, overflow and reset while a transfer is pending. Requests remain stable until accepted and all accepted responses drain before failure completion.
4. Memory tests: BL8 address/mask/odd-tail correctness, non-HUD accesses denied, completed counts only after real drain, randomized SDRAM/refresh latency and simultaneous LCD/cache traffic. Compare every actual written/read word, not just counters.
5. System tests: real ESP driver command schedule through selected QSPI/CDC RTL and actual memory model; KEY/P reference authority, presentation commit boundaries, injected mismatch/recovery, no fabricated software ACKs. Measure cycles, transfer occupancy, QSPI bytes/transactions and LCD starvation bounds separately.
6. Timing: V027 routed setup+0.019ns/hold+0.012ns (`timing-summary.rpt:139–145`) has little margin. New wide-data muxes, credits and descriptor comparisons must use synchronous BRAM, registered arbitration/identity cuts, bounded fanout and correct Gray/toggle CDC. Keep memory/pixel clocks and existing constraints unless a real hardware specification demands a change. Require routed setup/hold, DRC, CDC, physical pin-level simulation and exact source/image hashes for the new selected design. Never add false/multicycle paths to hide functional crossings.

Next action is the isolated native READ experiment and instrumentation on unchanged V027. A new full bitstream should follow evidence of the remaining transfer bottleneck, not precede that inexpensive separation.

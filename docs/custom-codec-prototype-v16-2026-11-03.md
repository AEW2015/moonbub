# Iteration 16: implementation contracts, refresh and memory service

This iteration moves the application-specific codec toward a reproducible native
and FPGA implementation. It preserves 720×480 coded / 720×405 active game content
and the 30 fps target. It adds complete interoperability vectors, actual-packet
operation/memory budgets, measured GM refresh comparisons and bounded publication
tag ordering. These are Python prototypes; no native encoder/decoder, synthesized
FPGA implementation or physical 30 fps qualification is supplied.

## Portable codec contract

The [golden-vector pack](../experiments/python-game-golden-vectors-study/README.md)
contains ten complete AR02 frames in three deterministic synthetic cohorts:
GM key/P/promotion/bank-1-P/forced-refresh, actually selected exact SR lifecycle,
and a full 720×480 SR+UI key. It retains twelve real GF02 datagrams, exact AF02
feedback, canonical reconstructed YUV bank arrays/tags, original source arrays,
scale maps and display RGB565. Eighty-four content-addressed objects occupy
89,759 stored bytes. Offline zlib object packaging is not video compression.

Ten negative wire vectors exercise eight receiver and two feedback failures:
outer/patch CRC, truncation, overlapping UI, wrong stored/reference tags,
unsupported dispatch and feedback binding. Failure must preserve semantic
publication state and reader ownership; the valid ACK must remain applicable
after a feedback rejection. Seven tests pass, including abort/retry, real chunk
reordering/duplication/corruption and UI-independent reference identity.

This is a bounded reference contract for implementation teams. Matching it is not
an independent decoder, comprehensive fuzzing or proof on every legal bitstream.
The full-resolution synthetic packet is intentionally small and has a small UI
patch; it establishes geometry and exactness, not gameplay compression/FPS.
The separate refresh/budget studies exercise all four 21,120-word UI regions.

## Periodic refresh remains a bottleneck

V15's periodic-refresh case used exact SR, so v16 reruns **GM + all four exact
UI regions** to isolate a simpler profile. Six runs reuse the same 180 distinct
native frames from the earlier v15 regression window; this is not new held-out
validation. Every run charges fresh Python service costs.

| Policy | Strict / eventual presentations | Distinct images in five modeled seconds | Modeled IDs/s |
| --- | ---: | ---: | ---: |
| Initial key only | 174 / 177 | 149 | 29.8 |
| Regular full refresh every 30 IDs | 158 / 160 | 133 | 26.6 |
| Same regular control repeated | 160 / 162 | 134 | 26.8 |
| Coarser refresh-key background, every 30 | 161 / 163 | 135 | 27.0 |
| Coarser refresh-key background, every 60 | 168 / 171 | 144 | 28.8 |
| Coarser refresh-key background, every 90 | 172 / 174 | 146 | 29.2 |

All decoded frames retain 21,120 exact original RGB565 UI words, zero mismatch.
The five-second window is [500,5500) ms; counts are checked against both distinct
native source and decoded image hashes. The six cases contain 1,080 scheduled
captures and take 122.68 seconds of host execution, distinct from virtual time.

Changing only refresh-key background quantization 16→32 makes five same-input,
independent keys **16.07% smaller**: complete bodies total 152,754→128,210 bytes.
Initial-key/P maps retain background 16 and priority blocks retain scale 8.
Keeping that map is not an identical priority-RGB or original-source error bound:
chroma interpolation and subsequent prediction histories can differ. On common
decoded IDs the active source RGB565 MSE increases by 0.3719. UI has its separate
original-word exactness contract.

This key-only saving is not a net-wire gain: coarse-30 sends more total wire
bytes here, with different admitted IDs and future P residuals. Its small cadence
advantage is close to control repeat variability. Longer intervals trade recovery
age for fewer interruptions; none proves robust 30 fps. The initial-only repeat
at 29.8 also shows the limited margin behind v15's conditional 30.0 result.
Lost refresh chunks/ACKs safely trigger independent key retries; the original
staged-publication, expiry precedence, lease and physical-drain rules remain.
[Refresh study](../experiments/python-game-refresh-v16-study/README.md): 16 tests.

## Actual coefficient work versus memory traffic

The [decoder budget](../experiments/python-game-decoder-budget-study/README.md)
reparses eighteen complete actual packets, including native key/promotion/P GM
and exact-SR packets with all four UI patches. Nineteen traces include one
explicitly analytical dense stress conjunction, not an admitted dense packet.
There are 57 conditional budgets, 52 clock/issue-lane sweeps and seven tests.

A native ordinary P contains 1,512 general inverse blocks. Exact SR reduces its
complete packet from 15,047 to 14,953 bytes without changing coefficient work.
The chosen fixed inverse requires 1,024 MAC operations per general block plus
64 dequantization multiplications. Issue lanes are hypothetical arithmetic
capacity, not demonstrated DSP48 counts. Entropy bits/cycle, CRC issue, paired
Cb/Cr output-position rate and SHA service are explicit assumptions.

| Full-resolution trace | Nominal planning ms | Optimistic planning ms |
| --- | ---: | ---: |
| Native GM ordinary P | 47.600 | 20.780 |
| Native promoted P | 69.724 | 37.227 |
| Analytical all-general promoted P | 82.681 | 44.675 |

Nominal assumes 100 MHz, eight MAC issue lanes, 16-byte bursts with read15/write13
cycles, four entropy bits/cycle, two sample/paired-chroma positions per cycle
and 3% refresh. Optimistic assumes sixteen issue lanes, eight entropy bits/cycle,
four sample/paired-chroma positions per cycle, hypothetical read8/write8 and
1% refresh. Both reserve independent 800×480 RGB565 panel
scanout at 60 Hz: 46.08 MB/s. The local 13/15-cycle handshake observations are
not physical board goodput; 8/8 is hypothetical. The model serializes compute
stages and uses residual average memory service, not a worst-case line scheduler.
Passing its average frame budget cannot establish a scanline deadline or timing.

Full-frame scratch/reference/display allocation is **5,042,080 bytes (4.809 MiB)**,
including three full 800×480 panel buffers. This exceeds the current 2 MiB
functional-model window, not the board's advertised physical memory. Qualify a
larger implemented address range and actual arbitration before claiming fit;
chip-1/SRAM support is not assumed. Scratch reduction alone cannot fit three
full panel buffers into that window.

The small gain from adding issue lanes points toward traffic and publication
work. Canonical SHA input is 1,036,804 bytes per full key/promotion (dimensions
plus int16 YUV). Packed8-bit reference memory still needs a 518,400-byte reread
for the unfused hash pass. A streaming parser, reconstruction/color fusion and
inline canonical hashing are concrete candidates, with explicit ordering,
chroma buffering, late-error and publication constraints.

## Bounded inline-tag experiment

The [inline-tag study](../experiments/python-game-inline-tag-study/README.md)
accepts tile-ordered Y/Cb/Cr and hashes canonical plane-row order through one
reused eight-row int16 stripe. Twenty cases match the original reference tag
exactly, including ten golden frames, six native packet decodes and four seeded
canonical-YUV cases with partial edges. All eight full-resolution cases use
**11,520 bytes** of stripe storage. The canonical SHA input remains 1,036,804 bytes.
Eight tests cover endian conversion, shape/range, strict order, duplicate/extra/
truncated input, finalize-only visibility and no retained producer tile.

The producer is simulated from already decoded full planes; this is an ordering
and bounded-scratch proof, not an implemented fused decoder or measured memory
saving. Conditional removal of only the packed8 publication reread changes native
promotion planning 69.724→60.691 ms nominal and 37.227→33.815 ms optimistic.
Even the latter remains above 33.333 ms. SHA work is unchanged. A future native/RTL
producer must preserve canonical order, backpressure and late-error atomic bank
publication; the helper's finalized hash alone does not validate an AR02 packet.

## ESP32 coverage boundary

The existing finite codec model bounds transaction/frame ownership but does not
emulate ESP32-S3 CPU, FreeRTOS, Wi-Fi/lwIP scheduling, heap fragmentation or actual
SPI DMA service. Its assumed 8 Mb/s links and 160 Mb/s QSPI are not qualified
ESP32 goodput. The two GF02 reassembly slots belong to the receiver/FPGA model,
not a demonstrated ESP32 allocation.

The inspected firmware snapshot implements **MSV1 JPEG**, not AR02/GF02. It uses
ordered 1,024-byte chunks through one 1,065-byte internal DMA buffer; recorded
configuration is 240 MHz with PSRAM disabled. The compiled UDP mailbox has six
entries. The streaming worker has a 16 KiB stack and shares the FPGA/device lock
with UI/input. CRC is bitwise; per-chunk register/identity checks and driver calls
are additional work. The 40 MHz quad-write setting is a raw clock ceiling, not
sustained forwarding throughput. Its current frame-bytes-remaining credit check
does not establish free clock-crossing FIFO capacity.

The [ESP32 gateway study](../experiments/python-game-esp32-gateway-study/README.md)
adds 32 principal scenarios, 20 link/burst cases and three RAM-reservation cases,
with eleven tests. CPU cycles, driver latency, radio delivery bursts and FIFO
service remain explicit assumptions; it is neither ISA/Renode emulation nor a
joint capture/codec/ESP32/FPGA simulation. Actual admitted AR02 frame sizes are
reframed in an MSV1-shaped hypothetical port, not forwarded by current firmware.

| Same initial-only size trace | Strict / eventual gateway frames | Mailbox drops |
| --- | ---: | ---: |
| Nominal paced 8 Mb/s | 176 / 177 | 0 |
| Conservative CPU/service assumptions | 69 / 69 | 379 |
| Nearly simultaneous bursts of eight | 0 / 0 | 460 |
| Periodic device-lock contention plus 100 ms abort sensitivity | 97 / 98 | 1,484 |

There are 177 admitted frames spanning 180 capture IDs/six seconds. Gateway
completion is not decoded/displayed FPS; original encode completion times are
not integrated here. The nominal trace needs 6.019856 Mb/s IP/UDP service and
reaches 43.547 ms maximum gateway completion age. The modeled no-contention
mean packet-service payload ceiling is 17.123 Mb/s, excluding frame-control and
failure costs; it is not measured goodput. The raw quad rate of 160 Mb/s omits
CPU, CRC, copies, polling, DMA/driver and contention costs.

A distinct cap stress sends sixty hypothetical 49,152-byte frames at 30 Hz. With
1,024-byte chunks, 40-byte framing headers and 28 IP/UDP bytes, it needs
**12.57984 Mb/s** before Wi-Fi airtime/retransmission overhead. At assumed 8 Mb/s,
only 38/60 complete within the two-second capture horizon; eventual delivery
finishes after 3.1455 seconds, with up to 1.179 seconds of age. The cap is a
maximum legal size, not a sustainable average target at that link rate.

The firmware's abort loop can retry for about 100 ms. The model distinguishes a
failed fresh begin (no active transfer, no abort) from a failed active forward.
A read-only review found and corrected that distinction before final source pins.
Transport queue drain is separate from incomplete active protocol state; the
500 ms idle-frame timeout is not simulated. True-FIFO waiting is a hypothetical
new credit contract and may move overflow upstream into UDP. Host pacing and
end-to-end bounded admission need testing alongside faster CRC/driver service.

Illustrative RAM reserves total 275,545 bytes. Assumed available internal budgets
of 256/320/384 KiB give negative/positive margins, but neither those budgets nor
largest DMA block/heap fragmentation are measured. Network payload reserves may
alias and double-count. No PSRAM or all-free 512 KiB pool is credited; all fit/
physical-throughput flags remain false. Calibrate packet/CRC cost distributions,
lock/abort timing, heap watermarks, DMA largest block, stack high-water marks,
mailbox/pbuf drops and actual FIFO occupancy on the remote system before an
ESP32 end-to-end 30 fps claim.

## Next implementation gates

1. **Freeze the AR02 subset and conformance rules.** Use the stored packet/bank/UI/
   feedback vectors as a common contract for host, ESP32 and FPGA teams. Negotiate
   this experimental dialect separately; installed JPEG/GM01/standard Moonlight
   peers cannot consume it. Keep GM + recent references + exact UI as the first
   profile; exact SR is optional until native rate/CPU costs justify it.
2. **Qualify the ESP32 gateway before an end-to-end rate claim.** Implement the
   negotiated forwarding protocol, bounded queues and real FIFO credit semantics.
   Measure concurrent RX/QSPI packet cost, Wi-Fi burst/drop statistics, UI/input
   contention, DMA-capable free heap/largest block and task stack high-water marks.
   Calibrate the gateway model; a Python cycle allowance is not an ESP32 emulator.
3. **Port bounded integer decode to native code.** Match canonical YUV, tag, UI and
   negative-state behavior on the stored bytes. Expand vectors to dense, partial,
   cap-boundary and loss/reordering cases. Count parser stalls, widths/rounding,
   memory allocation and callback ownership before mapping DSPs.
4. **Prototype streaming memory service.** Replace full-frame coefficient scratch
   with bounded block/stripe FIFOs. Test inline tag ordering and fuse only passes
   whose dependencies and late-failure atomicity are proven. Add a burst/scanline
   scheduler with refresh, row/chip changes, turnaround, maximum stalls, FIFO
   watermarks and display deadlines. Average bandwidth alone is insufficient.
5. **Design bank-local or sliced refresh.** Full-key drains remain costly even with
   smaller keys. Specify which pixels/references are valid, how slices publish,
   how feedback binds them and how loss recovers before measuring cadence. A
   longer refresh interval is not an equivalent recovery guarantee.
6. **Validate application-specific decisions on fresh gameplay.** Reused regression
   frames cannot validate tuned policy. Compare the same source IDs and UI coverage,
   quality/noise, latency tails, complete wire bytes, recovery and target memory.
   Preserve full resolution rather than using fewer distinct frames as an FPS win.

## Retained verification

The five study suites record **49 passing tests**, plus independent audit guards.
Each retained verifier checks source snapshots and recomputes packet, ordering,
queue or budget evidence. The audit reads the actual results and keeps missing
inputs pending. `docs/prototype-v16-provenance.json` inventories the new snapshot,
frozen v15 source hashes, source media hashes and paired Sunshine documentation.

```sh
python experiments/verify_prototype_v16.py
```

Use the project NumPy/Pillow/PyAV environment. This checks retained evidence and
conditional model replay; it does not regenerate measured host performance or
run hardware. Portable packet/ordering/budget replay does not require external
video bytes. When source media are available the aggregate also hashes them;
otherwise it explicitly reports missing files without claiming that recheck.

The branch pair is `handoff/gamebub-app-codec-v16-20261103`. Read-only evidence
checks and a source inventory accompany this report. New source snapshot pins
include conservative dependency/ancestry files and are not counts of exclusively
executed code. Host measurements use offline precompressed sources and assumed
8 Mb/s links, 160 Mb/s QSPI, 10 ms feedback and 60 Hz vblank; live acquisition,
shared native CPU, actual target memory/RF/QSPI and physical 30 fps remain open.

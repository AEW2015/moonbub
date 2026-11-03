# SDRAM-resident compressed-bank feasibility model

This is an **address and bandwidth study**, not an SDRAM-backed JPEG
implementation. It uses the existing RTL's dimensions and an isolated
controller handshake test. It does not measure the physical SDRAM, Game Bub,
Wi-Fi or FPS, and does not prove timing, fit, absence of underrun, or 30 fps.

## Proposed address map

The project uses **16-bit word addresses**. The existing functional SDRAM
model allocates `mem[0:1048575]` (1,048,576 words, 2 MiB); this is a model
bound, not a verified size or address map for the fitted physical memory. The
LCD RTL uses framebuffer bases `0x000000` and `0x080000` words. Conservatively
reserving the full 480×800 RGB565 raster in each buffer, the following two
**256 KiB** JPEG slots fit the model's gaps without overlapping those regions:

| Region | Start word | End word, exclusive | Bytes |
| --- | ---: | ---: | ---: |
| Framebuffer 0, full raster reserved | `0x000000` | `0x05dc00` | 768,000 |
| JPEG bank 0 | `0x060000` | `0x080000` | 262,144 |
| Framebuffer 1, full raster reserved | `0x080000` | `0x0ddc00` | 768,000 |
| JPEG bank 1 | `0x0e0000` | `0x100000` | 262,144 |

`layout()` checks every pair for overlap and checks the one-million-word model
limit; it rejects a bank only 16 bytes larger. The slots preserve the present
protocol's 256 KiB maximum, unlike the separate 48 KiB BRAM candidate. The
actual fitted chip, capacity, wiring, address decoding and aliases have not
been established; a physical map cannot be accepted on this arithmetic alone.
The model assumes all these locations are safe for this design's exclusive
use and does not account for other cores or firmware sharing the SDRAM.

All four regions have address bits `[23:22] == 0`, the SDRAM bank field in the
current controller. They therefore contend in the **same modeled SDRAM bank**
and can trigger row precharge/activate when arbitration changes clients. This
is a material risk, not four independent memory channels. Other physical-bank
layouts may be possible only with verified chip geometry and an appropriately
extended model/controller; changing addresses does not itself permit concurrent
transactions in the current single-request FSM.

## Workload and optimistic controller budget

At 100 MHz, a 16-bit SDR bus has a theoretical payload ceiling of **200 MB/s**
(decimal MB), before any commands, refresh or turnaround. A BL8 request moves
16 payload bytes. The RTL's LCD raster is 480×800, but it fetches only the 720
canvas rows (40–759); the outer rows are black. At the existing modeled/routed
clock arithmetic, ~65.076 Hz, that is 720×480×2×65.076 = **44.981 MB/s**
of scanout reads. Writing 720×480 RGB565 at 30 distinct frames/s adds
**20.736 MB/s**. Each JPEG is written to SDRAM once and read once; this study
pads each transfer to 16 bytes. For a 29,337-byte JPEG, those two directions
add **1.761 MB/s** combined. This accounting assumes each new frame is fully
decoded and presented and continuous error-free canvas scanout; no hardware
transfer rate has been measured here.

The isolated Verilator test applies repeated requests to each unmodified
controller RTL, with its normal 100 MHz cycle scale. It first requests the
**same open row**, then alternates rows 0 and 1 in the same bank. It checks
12 ACT, 12 WRITE and 12 READ commands per controller, and measures consecutive
`request_ready && request_valid` acceptances. It observes these spacings:

| Controller RTL | Access | Single write | BL8 write | BL8 read |
| --- | --- | ---: | ---: | ---: |
| Current baseline `moonshine_sdram` | Same open row | 6 cycles | unsupported | 15 cycles |
| Current baseline `moonshine_sdram` | Alternate same-bank row | 14 cycles | unsupported | 23 cycles |
| Experimental `moonshine_sdram_burst` | Same open row | not modeled here | 13 cycles | 15 cycles |
| Experimental `moonshine_sdram_burst` | Alternate same-bank row | not modeled here | 21 cycles | 23 cycles |

The test samples four write gaps and five read gaps per mode and controller.
The first request's row activation is excluded, `REFRESH_CYCLES` is changed to
60,000 to avoid a refresh during the short sample, and no actual SDRAM device or
read data is connected. The controller accepts one request only in IDLE, so
these costs describe serialized request spacing; they are **not overlappable
service slots**. The test does not measure write/read transitions, external
timing, memory data, a real arbiter, variable traffic or refresh. The production
controller does not support BL8 writes; using the burst row implies a separate
unimplemented compressed-ingress client and the experimental burst controller.

Substituting those row-hit spacings as idealized costs for *every* request gives
the following total cycle demands. Baseline-style rows use single-word writes
for both pixels and JPEG staging; burst rows assume full BL8 writes for both.
These scenarios require the proposed staging path to exist; neither implements
it. The sample sizes are from the local [capacity profile](../capacity-profile/README.md),
not a bound for arbitrary games or JPEG settings.

| JPEG bytes/frame | Payload MB/s | Baseline-style scalar writes | Experimental BL8 writes |
| ---: | ---: | ---: | ---: |
| 29,337, one sample's p95 | 67.477 | 107.84% | 60.56% |
| 33,324, another sample's maximum | 67.716 | 108.31% | 60.77% |
| 262,144, protocol cap | 81.445 | 135.34% | 72.78% |

Percentages are **arithmetic controller cycles demanded divided by 100 million
cycles/s**, not measured utilization. Because the baseline-style scenario
exceeds 100% even using the sampled optimistic row-hit spacings, that particular
continuous workload cannot be serviced by that serialized cost model. A value
below 100% does **not** prove feasibility: row changes, refresh, arbitration,
read/write turnaround and lost bus slots must be added, and an average cannot
guarantee a scanline deadline. Results depend on refresh, compression size,
frame rate, burst packing, controller revision and the assumed service costs.
The scenario JSON also computes a deliberately extreme **every-request row
switch** using the measured testbench gaps. It is not a trace of actual memory
accesses: consecutive requests within a real LCD line tend to hit the same row,
while switching between scanout, frame writes and JPEG regions can force row
changes. The real mix and scheduling must be measured in an integrated test.

Each fetched canvas line takes 60 BL8 reads. The 15-cycle row-hit spacing alone
would account for roughly 900 controller cycles or **9 µs** per line; the
baseline modeled LCD line period is about **18.43 µs**. This is an optimistic
service comparison, not a proven per-line deadline. The two line buffers,
prefetch/CDC handshake, 480-word line completion, prioritized scan requests,
refresh, decoder backpressure and interference from staged JPEG reads/writes
must all be modeled together. Payload data rate alone hides these short-term
stall and FIFO-underflow risks.

## Required implementation work

* Integrate an arbiter with bounded scanout priority and fairness for both JPEG
  staging and decoder writes; test bursts, row changes, refresh, read/write
  turnarounds, full FIFOs, and worst-case scanline phase. Current arbiter knows
  only line reads and pixel writes. The experimental burst path does not itself
  implement this compressed-data client or general abort recovery.
* Verify SDRAM geometry/address aliases on the actual board, and reserve the
  ranges consistently across all masters. Validate board electrical timing,
  the memory part's refresh and burst rules, and final FPGA implementation.
* Pack ingress into aligned bursts, define last-burst padding and byte strobes,
  keep CRC/length over the actual JPEG bytes, reject oversize before issuing a
  write, and ensure the decoder never consumes padding as valid stream data.
* Hold bank generation and frame metadata until writes actually drain and CRC
  passes; prevent stale/cross-epoch writes or outstanding reads from surviving
  bank reuse. Define QSPI/CDC credits, abort/NACK acknowledgment, reset and
  display publication ordering. The current RAM assumptions and
  [`../tagged-gateway-rtl/`](../tagged-gateway-rtl/README.md) do not establish
  this physical drain contract.
* Add SDRAM data traffic to a cross-checked Verilator test with real scanout,
  bounded queues and adverse burst timing, then run target synthesis/place/
  route and hardware instrumentation before asserting performance.

## Reproduce

With Python 3, Verilator 5.x and a C++ compiler, set `BUILD_DIR` to a new empty
scratch directory and run `./run.sh`. It verifies source hashes, runs six
Python arithmetic/bounds tests, emits twelve scenario JSON records, and runs
the isolated controller handshake bench. The observed run is
`/home/lori/gamebub-tools/sdram-storage-model-v2/`; compact evidence is in
`results/`. `python3 model.py --help` exposes JPEG size, bank cap, refresh and
video rates, and per-request costs for what-if analysis. These are supplied
inputs and cannot establish a service guarantee.

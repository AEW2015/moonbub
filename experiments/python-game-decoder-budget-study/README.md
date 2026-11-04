# Conditional AR02 decoder cycle and memory budget

This Python study converts **actual decoded coefficient traces** into explicit
arithmetic, storage and service budgets for a future native/FPGA decoder. It
keeps 720×480 coded video and 720×405 active native content. It does not implement
RTL, synthesize DSPs, prove timing/line deadlines or measure target 30 fps.

## Inputs and checks

`benchmark.py` creates 18 admitted AR02 packets: GM/exact modes each encode
key → promoted P → ordinary P at 64×48 and 720×480 deterministic synthetic
geometry, plus the same sequence for three native Mass Effect frames selected
at four seconds. Native frames are offline PyAV RGB, Pillow BOX to 720×405 and
black letterbox rows 37/38; quantization is uniform scale 16. This is not the
v15 finite model's complete ROI/reference scheduling and is not a live source.
The complete bytes/hex, packet hashes, decoded coefficient classifications and
source media hash/PTS are retained. `verify.py` reparses every actual packet to
rederive its trace; it does not trust precomputed counts alone.

A nineteenth analytical all-general-block promoted-P case combines 8,100 general
8×8 blocks with a 49,152-byte maximum input. It is **not an encoded/admitted packet**
and does not imply that dense noise or all such blocks compress under the cap.
It is a stress conjunction for arithmetic/capacity planning, not a complete
worst-case legal bitstream timing proof. There are 57 primary service scenarios
and 52 bounded clock/issue-lane sweeps. Seven self-checking tests pass, covering
counts, traffic, storage, saturation and monotonic service assumptions.

The actual full-resolution native ordinary P selects SR01 at 14,953 bytes versus
GM01's 15,047, with identical coefficient work. All six native packets select
21,120 exact UI words. Its three planes have zero/DC/general counts
(3,407/577/1,416), (1,281/30/39), (1,235/58/57). The native promoted P has
1,581 general blocks; ordinary P has 1,512. This anchors the budget beyond smooth
synthetic fixtures without generalizing three frames to all gameplay.

## Arithmetic and scheduling assumptions

The frozen inverse is two 8×8×8 Q14 matrix passes: **1,024 multiply-accumulates per
general block**. Dequantization adds 64 multiplications. A DC-only block uses one
dequantization multiply and two Q14 multiplies; all-zero residual skips both.
The analytical dense canvas therefore has 8,294,400 inverse MAC operations plus
518,400 dequantization multiplications. RGB conversion has four multiplications
per output pixel; reconstruction, bilinear chroma output and RGB565 packing have
separate assumed sample issue rates. Zero/DC bypass does not remove prediction,
clipping, color, packing or display traffic.

Entropy budgets count all selected plane payload bits at an assumed bits/cycle;
they do not implement Rice-token scheduling, variable-length worst cases or a
hardware parser. CRC work counts outer, inner, nested CP02 and patch protected
bytes; SR headers do not invent another CRC. Publication SHA receives canonical
`<HH dimensions>` plus little-endian **int16** YUV, exactly 1,036,804 bytes at full
resolution. The hypothetical reference memory is packed **8-bit**, so its tag
pass physically reads 518,400 bytes then widens samples for hashing. Python
reference arrays themselves are int16 and use twice the packed storage.

`budget.py` adds deliberately serialized modeled entropy, inverse/dequant,
reconstruction, upsampling, RGB matrix/pack, UI, SHA and CRC stage cycles. MAC
lanes represent hypothetical arithmetic issue capacity, **not a demonstrated
one-lane/one-DSP48 implementation**. Signed width, rounding, clipping, stalls,
RAM ports, coefficient supply, FIFO depths and actual DSP mapping remain gates.
The inverse pipeline latency is an explicit assumption per general block.
A roofline `max(compute,memory)` ceiling is reported separately and is never used
as the serialized frame estimate or presented as a throughput proof.

## Shared memory, scanout and results

The candidate stores packed YUV banks, a private reconstruction, full-frame
coefficient scratch, compressed ingress and RGB565 display frames externally.
It reads reconstructed YUV for color, and performs a separate publication-tag
read for keys/promotions. Four decoded UI patches and two chroma-row buffers are
local; UI is muxed before the single RGB565 write, so it adds no second external
RGB overwrite. Staging writes/reads every compressed packet once each. There
is no assumed free reference copy, a second independent SDRAM bus, or direct
ESP32-addressable FPGA SRAM.

Scanout is independent of video cadence. The scenario uses the prototype's
800×480 landscape-equivalent panel at 60 Hz, **46.08 MB/s** RGB565 payload. Actual
panel orientation/clocks still need board confirmation. Bursts round each scan
line. At 100 MHz, 16-byte bursts and read15/write13 cycles with 3% refresh,
scanout reserves 43.2 million cycles/s and background receives 53.8 million.
Background frame service uses a fair residual **average** allocation. Arbitration,
refresh collisions, row changes, queue tails, turnarounds, CDC and per-line
watermark deadlines are not simulated; average feasibility does not prove them.

| Full-resolution trace | Nominal modeled frame ms | Optimistic modeled frame ms |
| --- | ---: | ---: |
| Native GM ordinary P | 47.600 | 20.780 |
| Native exact SR ordinary P | 47.583 | 20.766 |
| Native promoted P (GM/exact same choice) | 69.724 | 37.227 |
| Analytical all-general promoted P | 82.681 | 44.675 |

Nominal is 100 MHz/8 MAC issue lanes/4 entropy bits per cycle/2 sample lanes,
read15/write13 BL8 and 3% refresh. Optimistic is 100 MHz/16 MAC issue lanes/8
entropy bits per cycle/4 sample lanes, hypothetical read8/write8 BL8 and 1%
refresh. Both use an assumed 80-cycle SHA compression block and 16 inverse
pipeline cycles per general block. The 50 MHz, read23/write21, 5% refresh scenario
cannot serve the assumed scanout alone. Those 13/15 and 21/23 serialized burst
intervals come from local short RTL handshake tests described in the external
memory audit; they are not physical board goodput. Hypothetical 8/8 is not measured.

The clock sweep changes the shared compute/memory clock while holding burst
cycle and all other assumptions fixed. With nominal service and eight issue
lanes, native ordinary P first fits the serialized 33.333 ms average budget at
127 MHz, promotion at 175 MHz. With sixteen lanes, those become 123/170 MHz;
the analytical dense case first fits at 191 MHz. These are search results in
1 MHz steps over 50–200 MHz, **not clocks the FPGA/SDRAM can run**. The small gain
from doubling lanes highlights memory/publication service rather than proving
more DSPs will solve the bottleneck. No burst maximum-stall contract is supplied.

## Capacity and next implementation gate

The explicit candidate allocation is **5,042,080 bytes (4.809 MiB)**:

| Allocation | Bytes |
| --- | ---: |
| Two packed8-bit YUV reference banks | 1,036,800 |
| Three full 800×480 RGB565 panel buffers | 2,304,000 |
| Two maximum AR02 ingress slots | 98,304 |
| Private reconstructed YUV | 518,400 |
| Full-frame int16 coefficient scratch | 1,036,800 |
| Four decoded UI patches | 42,240 |
| Two chroma rows | 1,440 |
| Metadata reserve | 4,096 |

This exceeds the current **2 MiB functional memory-model window**; that window
is not the board's total SDRAM capacity. Officially advertised 64 MiB spans two
shared-bus chips; the current streaming controller selects chip 0 and neither
chip-1 nor SRAM is assumed implemented/qualified. The advertised 512 KiB SRAM
cannot hold these frame pools. Allocation is not a BRAM fit result; vendor IP,
CDC FIFOs, control state, descriptor alignment and additional implementation
buffers remain outside this illustrative total. BRAM is already heavily occupied
in the routed JPEG baseline, so local patch/row buffers need real packing/fit.

A streaming coefficient parser could replace the 1,036,800-byte full-frame
coefficient scratch with bounded block/strip FIFOs. Fusing reconstruction/color
and inline publication hashing can avoid the full YUV color/tag rereads, provided
chroma row/halo buffering, exact canonical hash order, late failure and atomic
bank publication are preserved. These are **next candidates**, not savings already
credited here. Three physical panel buffers alone exceed the 2 MiB model window;
reducing scratch does not remove the need to qualify a larger address range or
prove safe role aliasing.

Next build a bounded burst/line scheduler driven by these packet traces, with
actual row/chip/turnaround/refresh/stall sequences and buffer ownership. Port
integer reconstruction to native/RTL golden vectors, verify widths/rounding,
then measure parser/inverse/color/SHA stalls and synthesize resource/timing.
Only then choose a production clock, DSP allocation and memory layout.

```sh
python -m unittest -v test_budget.py
python verify.py          # retained packets, counts, source pins and budget replay
python benchmark.py      # regenerates evidence; external native clip required
```

Use the project NumPy/Pillow/PyAV environment. Sources are pinned by relative
repository paths. External media bytes are not redistributed; retained packet
trace verification does not require media. No existing v15 sources or artifacts
were modified.

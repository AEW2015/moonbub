# V99 measured results and candidate decision

The current CU66 path now accepts fresh RGB and produces genuine CU66/GU66
packets. Every one of **360 candidates** passes unchanged Python and native
receivers with exact canonical, fixed-HUD and complete RGB565 output. The
native campaign also passes **3,948 atomic rejection/recovery trials**.
The independent source/packet ledger audit passes 10,510 checks, and a separate
pixel auditor recomputes every active/ROI error from actual native output.
Seven bounded fresh-encoder unit tests pass.

## Research candidate

Select **CS88/all-BR88, uniform q16**, with the existing V91-compatible mode
and quantizer subset. Native-general minimum metadata initially used 23 P
run-map packets and uniform key quantizers that the RTL subset rejects.
The selected attempt therefore forces key map 0/P grouped map 3 and QM87
key run-map 2/P accepted-cache 6. All 360 selected packets have those fields;
the candidate does not depend on silently widening the RTL parser.

The CS88 native receiver matches all fresh coefficients, canonical planes,
HUD words, RGB565, C2 roots and seals. An independent Python BR88 reader and
separate frame/C2 parser verify **186,624,000 coefficients in 2,916,000 dense
blocks**, all 360 complete packets and their content commitments. A validly
re-encoded late coefficient mutation passes inner/outer CRCs but fails the
content root; the old accepted frame remains and the good P frame recovers.

| Scope | Frames | Complete bytes | Largest packet | Cap outcome |
|---|---:|---:|---:|---|
| Fresh CU66, q8/q16/q32 | 360 | 4,057,806 | Within 49,152 B throughout | 360/360 |
| Selected-grammar CS88, all three diagnostic scales | 360 | 4,429,435 | 49,654 B | 359/360; one q8 history fails the complete cap gate |
| Frozen q16 CS88 candidate | 120 | 1,426,431 | 36,119 B | All four 30-frame histories fit |

The q8 oversize is the new combat sample's frame 25. Its later native diagnostic
frames use that accepted oversized reference and therefore are not an admitted
production history. Cap eligibility is assessed for each complete causal
history, including any skipped upstream inputs. q8 is not the default.
The q16 cap result covers these samples, not every possible future game frame.

BR88 replaces adaptive entropy feedback with bounded plain Rice decoding and
matches the already-developed RTL direction. q16 CS88 costs 136,103 more bytes
than the same-pixel CU66 q16 control across these four sequences. That overhead
also includes the different complete wrappers, C2 commitments and metadata;
it is not an isolated entropy penalty or a measured FPGA speedup. No custom
HEVC/AV1 superiority is claimed.

## New supplied combat sample

The source is 1280×720 H.264 at 60 fps. Every second native frame produces a
30-fps selected sequence, aspect-fitted to 720×405 inside a 720×480 canvas.
Every method uses the same retained RGB samples. CS88 reconstructs exactly
the CU66 target pixels, including the source-exact fixed HUD patches.

| Profile | Complete bytes / 30 frames | Mbps at selected 30-Hz cadence | Active / geometric ROI PSNR dB | Largest packet |
|---|---:|---:|---:|---:|
| CU66 q8 | 913,421 | 7.307 | 35.73 / 35.23 | 43,619 B |
| CS88 q8 diagnostic | 997,992 | 7.984 | 35.73 / 35.23 | 49,654 B; exceeds cap |
| CU66 q16 | 672,514 | 5.380 | 34.72 / 34.29 | 31,838 B |
| CS88 q16 candidate | 723,414 | 5.787 | 34.72 / 34.29 | 36,119 B |
| CU66 q32 | 516,471 | 4.132 | 33.17 / 32.89 | 24,097 B |
| CS88 q32 diagnostic | 546,556 | 4.372 | 33.17 / 32.89 | 28,199 B |

Rates count full elementary packets, including their headers/CRCs, but exclude
UDP/QSPI/FEC/retries/ACK traffic. Multiplying bytes by source cadence is not
measured link throughput or displayed FPS. PSNR is a pixel-error diagnostic;
game ROIs have no verified HUD semantics and do not establish readability.
V98's standard-codec results remain software anchors on these exact inputs.

## CPU decoding and the direct sender

CU66's native C++ receive-to-published-RGB565 samples are **7.690–12.397 ms**,
median **8.503 ms**, mean **8.825 ms**, p95 **10.592 ms**. This includes its
actual decode, integrity checks and presentation construction, excluding
packet reads, golden checks, output writes and transport. It is one unpaced
sample per frame on this shared CPU. These are **CU66 CPU timings**, not selected
CS88 timing, physical FPGA timing or a validated under-10-ms result.

The direct sender computes fresh transforms, q16 coefficients, exact HUD,
BR88, C2 root/seal and complete packets without creating the diagnostic
AB38/CS38/CU66 control. All **120 produced packets are byte-identical** to the
selected CS88 q16 controls and receive actual independent native ACKs before
reference/root/cache advancement. An additional **32-frame synthetic control**
passes key 0, key 30 and P31→30, including key quantizer reset and C2 history.

| Direct sender case | RGB-to-packet median ms | HUD phase median ms |
|---|---:|---:|
| Earlier 2600 window | 182.96 | 148.92 |
| Earlier combat window | 99.68 | 54.10 |
| New Legendary Edition combat | 269.74 | 221.60 |
| Synthetic motion/cut | 112.80 | 75.79 |

The overall 120-frame packet-ready range is **84.53–303.53 ms**, with median
157.92 ms. Native ACK/verification, golden rendering/hashing and artifact I/O
are outside this sender fence; native BR88 helper encode/self-check and Docker
stdio IPC are inside it. The direct path is a real fresh-input prototype, but
it is still much slower than the 33.33-ms frame period. The next host task is a
native in-process HUD/transform/BR88/C2 encoder, tested against these exact
packet and pixel goldens. Do not count the Python path as a 30-fps sender.

## RTL-facing handoff and open milestones

The new-user q16 key/P export independently decodes actual BR88, reconstructs
signed dequant/residual values and checks all 518,400 normalized sample bytes
per frame. It supplies three case rows including a late-CRC fixture and 17,887
transform rows for the existing testbench contract. This is a bounded golden
bundle; no fresh RTL simulation or routed design was run here.

V99 freezes a **research candidate and reproducible evidence**, with production
JPEG kept as the fallback. Complete live RTL producer/HUD/C2/shared-display
integration, an actual ESP32/QSPI adapter, original held-out captures, native
host throughput and physical memory/port budgets remain open. V100–V110 must
establish mapping/P&R/timing and actual complete-system qualification. Both
physical 30 fps and strictly under-10-ms validated FPGA decoding remain open.

# Candidate paths to 30 displayed fps

## Status and priority

30 displayed fps is not established. Start with the existing JPEG path because
it already has a receiver/FPGA decoder, while improving SDRAM writes and the
ESP32/FPGA transport. In parallel, investigate MPEG-2 I/P as a higher-quality
per-bit alternative, not as a currently usable bitstream. H.264 is a useful
host benchmark but a complete compatible Game Bub FPGA decoder and memory fit
have not been demonstrated. GBD1 is a custom research codec with no complete
FPGA packet decoder. None of these formats eliminates the need for adequate
framebuffer write and scanout bandwidth.

The test target is 720×480 coded pixels, 30 unique displayed frames/s. The
samples below letterbox 16:9 content at 720×405 inside that raster. Thirty FPS
is a cadence, not an end-to-end latency guarantee. The LCD can continue
refreshing while an old video frame remains on screen: count new frame IDs at
actual scanout swaps.

## Existing evidence: quality versus burst

Two precompressed Mass Effect scenes, 90 frames each at 30 fps, were encoded
in software at approximately 4 Mb/s average, with 15-frame I/P GOPs for H.264
and MPEG-2 and all-intra MJPEG. Combat and movement JPEG achieved RGB PSNR
39.26 and 37.02 dB versus the already-compressed resized source; MPEG-2 gave
41.38 and 41.07 dB at 3.96 and **4.62** Mb/s respectively. These are not
matched-quality, the movement MPEG-2 rate is 15.6% above target, and PSNR is not
a judgement of perceptual game quality. The FFmpeg MJPEG output is not verified
compatible with the production receiver's restricted JPEG syntax.

A new offline FIFO replay sends the measured picture sizes at ideal constant
payload service rates. All pictures arrive exactly every 33.333 ms, all are
queued, none are dropped, and no protocol overhead, Wi-Fi loss, ESP32 work,
FPGA work, encoder timing, or presentation scheduling is included. These
numbers are time from modeled frame availability to end of ideal serialization,
not end-to-end latency. The 33.333 ms cutoff is an illustrative per-picture
service deadline; later completion does not by itself establish display loss.

| Scene | Codec | Actual average | Ideal service | Pictures above 33.33 ms | Maximum service + queue |
| --- | --- | ---: | ---: | ---: | ---: |
| Combat | MJPEG | 3.94 Mb/s | 8 Mb/s | 0/90 | 26.3 ms |
| Combat | MPEG-2 | 3.96 Mb/s | 8 Mb/s | 7/90 | 49.4 ms |
| Combat | H.264 | 3.93 Mb/s | 8 Mb/s | 5/90 | 67.4 ms |
| Movement | MJPEG | 4.11 Mb/s | 8 Mb/s | 0/90 | 21.0 ms |
| Movement | MPEG-2 | 4.62 Mb/s | 8 Mb/s | 8/90 | 48.5 ms |
| Movement | H.264 | 4.15 Mb/s | 8 Mb/s | 6/90 | 54.9 ms |

These ideal rates are hypothetical, not a measured device capacity or a
recommended Wi-Fi setting. A larger keyframe can queue several following frames;
use bounded peak rate, buffer/credit accounting, and frame-age limits rather
than selecting from average bitrate. Dropping an independent JPEG frame is
straightforward; inter-frame formats need reference-aware recovery. Samples are
short, not lossless native gameplay or a stress test.

Reproduce the queue model with `python3 fpga/experiments/throughput30/replay-deadlines.py`.
The adjacent JSON records the measured frame sizes and source-stream SHA-256
hashes; video files are not redistributed. The script also compares 12 Mb/s.

## Game Bub-specific optimizations to prototype

1. **FPGA memory first:** convert the existing grouped 8×8 transpose output
   into genuine SDRAM burst writes, with ping-pong tile buffers, safe refresh,
   scanout arbitration and atomic back-buffer publication. The current tested
   transpose issues single writes and takes 53.10 ms/frame alongside scanout;
   33.33 ms requires at least a further 1.59× write-path improvement in that
   simplified replay, plus margin for the omitted workloads. Validate every
   pixel, stalls, refresh, frame boundaries and actual Artix-7 timing.
2. **Pipeline the ESP32:** keep a fixed-size DMA-capable receive/transfer pool;
   overlap Wi-Fi reception and QSPI transfer; provide synchronized FPGA FIFO
   credits, sticky overflow counts, sequence/integrity checks, deadlines and
   a bounded frame-age policy. Measure concurrent ingress and QSPI goodput on
   the real device; a remaining-frame-byte counter is not a FIFO credit.
3. **Optimize JPEG for this display:** retain independently decodable frames
   and 4:2:0 where supported, use host bitrate/quality control plus a peak
   frame cap, and test native 720×480 against 360×240 decoded and scaled by
   FPGA. The low-resolution option reduces decoded pixels fourfold but needs
   a tested scaler and will reduce detail. Both are comparisons, not proven
   working profiles.
4. **Experiment: JPEG tile updates:** send changed tiles using the receiver's
   reconstructed reference, with bounded tile age and periodic refresh. An
   earlier small software experiment saved little in one movement scene and
   more in a quieter scene; fast full-screen motion can remove the benefit.
   Coherent double-buffer updates, frame IDs, loss recovery and extra SDRAM
   copying/bandwidth must be modeled before claiming speedup. Existing protocol
   and decoder do not support this method.
5. **Research MPEG-2 I/P with DSP IDCT:** lower rates at useful quality in the
   offline tests make it worth considering. Its motion/reference reads and
   decoder integration compete with scanout for memory, and its full decoder
   has no proven fit or timing in this design. Protect keyframes, bound packet
   bursts, and specify loss recovery. CPU/GPU encoding cost on the actual
   Windows host must be measured; do not assume RTX 2070 NVENC offers MPEG-2.

Prove the result with sustained representative game footage and concurrent
capture, encode, Wi-Fi, ESP32/QSPI, FPGA decode, SDRAM and LCD scanout. Report
new displayed frame IDs per second, frame age, p95/p99 latency, dropped frames,
FIFO overflow, SDRAM/scanout underruns and audio/input behavior. Preserve the
existing physical fixtures and their measured limitations as independent data.

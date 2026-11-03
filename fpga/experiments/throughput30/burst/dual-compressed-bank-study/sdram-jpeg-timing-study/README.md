# One-frame modeled SDRAM staging and display timing

This is **observational instrumentation of one bounded synthetic fixture** in
the existing [`sdram-jpeg-full-study`](../sdram-jpeg-full-study/README.md)
simulation. It does not change the original study's sources or control/data
path. The testbench supplies JPEG bytes directly to the experimental writer;
the full staged image is checked in the functional SDRAM model and passed via
the experimental reader to the actual JPEG decoder and LCD RTL. It is not a
physical measurement, end-to-end input latency or sustained-FPS proof.

The instrumentation samples handshake and completion signals on the test's
100 MHz model clock. Durations below are differences between model-cycle event
timestamps; signals registered by the RTL are observed by the monitor on the
following sampling edge. `results/timing.json` retains absolute model cycles
and the definitions used by `analyze.py`.

| Observed interval, one 26,991-byte frame | Model cycles | At assumed 100 MHz |
| --- | ---: | ---: |
| Writer BEGIN accepted → modeled shared-path drain | 63,963 | 0.640 ms |
| First → last testbench input byte accepted | 63,947 | 0.639 ms |
| Last BL8 write accepted → modeled drain | 14 | 0.00014 ms |
| SDRAM reader start → last compressed word accepted by decoder | 2,224,310 | 22.243 ms |
| Reader start → last decoded pixel accepted | 2,230,953 | 22.310 ms |
| First → last decoded pixel accepted | 2,227,149 | 22.271 ms |
| Last decoded pixel accepted → modeled presentation | 660,461 | 6.605 ms |
| Writer BEGIN accepted → modeled presentation | 2,955,385 | 29.554 ms |

These intervals **overlap** and should not be added. For example, decoding and
pixel output overlap SDRAM reads. The last-pixel-to-presentation interval
includes the modeled output drain and wait for a display boundary; it is not a
pure display phase measurement. Presentation is an internal buffer swap, not
the moment the entire panel has emitted the new image.

The testbench's byte source is idealized and much faster than any measured
ESP32 or Wi-Fi path: 26,991 bytes accepted over about 0.639 ms is roughly
42.2 MB/s in this model. Its direct predecode SDRAM comparison is testbench
logic, **not RTL CRC or a production commit**. The reported timing omits host
capture and encoding, packet transmission, Wi-Fi, ESP32, real QSPI, physical
memory, actual panel output and input-to-photon latency. It reflects one
synthetic JPEG, one phase, this arbiter and one functional memory model; it is
not a bound or a claim that a game streams in 29.554 ms or at 30 fps.

The instrumented run preserved the full study's two exact C/framebuffer checks,
modeled LCD canvas scans, zero-new-underrun check and predecode-corruption
negative control. Its two output dump hashes match the uninstrumented run
(`c087e502623218aa8be0669aab3e634d9b6d22fff6b59bfceee8f5c8322de3f0`
and `af13aa217140470bfd6d1ea3270d826b51d0a50fc9c0532c01d19e1aa19490de`).
The C reference shares algorithms with the RTL and is not an independent JPEG
decoder. The stored evidence records only the instrumented result; dump hashes
were separately compared against the existing uninstrumented scratch run.

Set `BUILD_DIR` to a new empty scratch directory, `JPEG0` and `JPEG1` to the
same hash-pinned `0000.jpg` and `0002.jpg` fixtures used by the full study, and
run `./run.sh` with Verilator 5.x, Python/Pillow and a C++ compiler. It checks
source manifests, tests the timing-log parser against missing and out-of-order
events, generates the instrumented bench without editing the original,
executes the positive and negative full-study tests, and parses its single
timing record. The full recorded output is
`/home/lori/gamebub-tools/sdram-jpeg-timing-v1/`; compact logs and parsed output
are in `results/`.

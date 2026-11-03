# Live emulator guest → QSPI/CDC → dual banks → modeled display

This isolated experiment connects the existing ESP32-S3 emulated guest and
its actual Rust receiver to the experimental QSPI endpoint, credit FIFO,
test-only MMIO adapter, two 48 KiB compressed banks, word reader, guarded JPEG
decoder, functional SDRAM and LCD canvas scoreboard. The live bridge uses one
bounded event at a time; socket waits freeze Verilator logical time. There is no
shared emulator/RTL clock or calibrated CPU, radio or QSPI timing.

The clean, corrupt, recovery sequence passed: frame 0 was committed, decoded,
checked against the related C model and scanned; the corrupted final packet of
frame 1 was rejected by the actual guest receiver, which emitted ABORT after
25,600 accepted bytes; the test confirmed that frame 0's front framebuffer,
front identity, write count and output remained intact. Frame 2 was then
committed, decoded, scanned and checked against its own C model; the previous
front framebuffer was also preserved during recovery. Both completed frames
had 345,600 exact RGB565 pixels. The event auditor checked all 84 guest-emitted
event hashes and ACKs against the pinned fixture packet trace. The LCD
scoreboard checked full displayed canvases for order, identity and exact data.
There were no modeled FIFO overflows or post-warmup LCD underruns.

The testbench's bus adapter is not production firmware. It implements only
metadata `0x14`–`0x20`, begin/abort/commit `0x24`, data `0x100`, and the
CDC-draining byte/commit count fences `0x28` and `0x2c`. Metadata and data
writes honor conservative FIFO credits; each data chunk is fenced before the
next. The bench verifies event ID, sequence, bounds and CRC, and acknowledges a
commit only after display publication and a full scan. This policy deliberately
serializes work; it is a functional correctness test, not a real-time schedule.
The guest's corruption scenario is an injected malformed final datagram, not a
measured radio-loss pattern.

To reproduce, set `BUILD_DIR` to an empty scratch directory and run `build.sh`
with Verilator 5.x, make and a C++ compiler. It checks `sources.sha256` before
compilation. Then invoke the existing host wrapper
`../../esp-emulator-study/live-bridge/run-multi.py` with its documented seven
arguments: new work directory, esp-emu executable, guest ELF, flash image,
fixture trace, the new `obj/Vtb_live_multiframe`, and fixture directory. The
recorded artifacts came from `/home/lori/gamebub-tools/live-dual-build-v3/` and
`/home/lori/gamebub-tools/live-dual-run-v3/`; the wrapper pins guest, flash,
trace and fixture hashes, audits event hashes, and performs C-model comparisons.
Small logs and comparison summaries are in `results/`.

This test does not validate physical CDC/metastability, QSPI electrical timing,
FPGA fit, actual panel timing, target firmware integration, Wi-Fi performance,
or 30 fps. It does not modify the earlier single-bank live evidence.

The existing live wrapper binds TCP `127.0.0.1:15536` and guest-forwarding UDP
`127.0.0.1:15533`; it has no listener-side `SO_REUSEADDR`. Back-to-back runs
can fail with `EADDRINUSE` even after the listener exits if the OS retains a
server-side TCP connection in TIME_WAIT. Check `ss -tan '( sport = :15536 or
dport = :15536 )'` and `ss -lun '( sport = :15533 )'`; wait for TIME_WAIT to
expire before retrying in a fresh work directory. The expiration is controlled
by the host OS and is commonly around a minute, but is not guaranteed. If an
active listener or UDP owner remains, identify it before retrying. A new bind
option could be used in a separate adapter, but changing the existing adapter
would invalidate the established source/evidence hashes; this test retains it.

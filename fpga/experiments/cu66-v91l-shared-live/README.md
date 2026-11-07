# Live commit and RGB through shared timed SDRAM

`shared_live.sv` instantiates the frozen `cs88_rows_v91l` live producer, frozen burst `canonical_rgb565_tiled`, and the new shared physical service. Candidate requests and responses are internal RTL wires exposed as observation ports. The C++ bench does not drive candidate ready, ACK validity, ACK identity, ACK error, or memory payload.

Each native `c0/f0` key and `c0/f1` delta reconstructs all 518400 canonical bytes through the live BR88 parser and inverse path. Canonical/HUD candidate rows pass through the actual tiled row writer, unchanged SDRAM controller, and timed functional pin memory. Only real matching physical row responses update the C++ accepted-reference mirror. Actual ACK-backed bytes then feed the RTL validator, including all 1025 SHA jobs. RGB conversion begins after validated commit and reads the same physical memory through the actual BL8 reader, controller, and pins. There is no native frame, canonical, or pixel preload.

The two frames run serially: live write and validated publication, then physical RGB conversion, then the next live frame. The separate shared-service campaign exercises simultaneous writer/reader offers and physical cancellation/drain. This live campaign does not claim concurrency, a complete physical live service, full RTL HUD handling, hardware timing, or 30 fps.

The finite frozen C++ scratch and reference endpoints remain at explicit profile 0. The reference endpoint reads only the mirror of actual ACK-backed candidate writes. Delta qcache preload uses captured RTL registered lookup responses from the previously validated frame. Native C++ HUD decoding occurs before each start. Golden canonical/HUD/RGB fixtures only check outputs; they never populate physical memory or the accepted-reference mirror.

Generate wrappers and run:

```sh
python3 fpga/experiments/cu66-v91l-shared-live/make_wrapper.py
python3 fpga/experiments/cu66-v91l-shared-live/make_bench.py
python3 scripts/cu66-v91l-shared-live/run_test.py
```

The default grid uses seeds 912801/912802 and tAC 2/7 ns. Builds use `gamebub-cu66-v69-build`, Verilator `--timing --assert -Wall --timescale 1ns/1ps`, C++20 `-Wall -Wextra -Werror`, and `-j2`. Delayed events advance through every pending time slot, following the established burst timed bench. Native frame, event-loop, RGB, parser, and drain watchdogs are finite.

Each attempt preserves source snapshots and SHA-256 inputs, tool versions, exact commands and failures. Receipts contain original 32-byte candidate request/ACK/hash-delivery records; actual RTL SHA job digests; accepted canonical/HUD/qcache exports; SV controller requests, captures, ownership/fences and pin writes/reads; native start/commit and RGB start/frame/row events; and complete 691200-byte RGB565 files. The 32-byte bus format remains `<BBBBIIIIQI`: kind, profile, bank, bytes, fid, epoch, token, raster address, little-endian payload, cycle.

The original logical wrong-ACK, partial-error, abort/reset drain, metadata/HUD rejection, and publication-fence tests remain unchanged in `cu66-v91l-rows/tb_compare.cpp` and `scripts/cu66-v91l-rows/run_comparison.py`, with the existing qualified baseline receipts. They are separately qualified logical control tests; their C++ fault injection is not presented as physical service fault coverage. The new live bench retains the real vblank/scanout publication fences. Physical service reset/cancel/drain and contention are covered in the separate new shared-service experiment.

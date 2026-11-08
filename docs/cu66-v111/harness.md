# V111 executed harness baseline and trace capture

The fresh functional baseline **passed**. An emulated ESP32-S3 receiver test
application accepted 26 actual MSV1 datagrams (26,159 compressed bytes), emitted
28 ordered events acknowledged by the experimental QSPI/CDC RTL, and committed
one 720×480 JPEG frame. All **345,600 RGB565 pixels** match the previously
qualified related C oracle exactly. This is JPEG/receiver-core functional
integration; Sunshine, full target firmware and synchronized timing remain open.

The [selected summary](../../experiments/python-gamebub-v111/harness/results.json)
binds [attempt 20261108T182424178254Z](../../experiments/python-gamebub-v111/harness/attempts/20261108T182424178254Z/receipt.json),
SHA `b0f42b9ff83be4231fff9bb9cb64f31c73429d91ee2866f05ded4d1c1dfed216`.
Its 33 legacy RTL/DPI input hashes match the frozen published manifest. RTL and
the corrected C model were compiled fresh; the guest ELF/flash were reused with
explicit hashes. The Docker image is content-pinned, and every participant ran
inside one allocation capped at two CPUs, 8 GiB memory=swap, no additional swap,
with network restricted to its isolated loopback/user-network model. Available
host RAM stayed above 21.44 GiB and memory PSI full avg10 was zero.

## Actual execution and limits

| Item | Executed evidence | Scope still open |
| --- | --- | --- |
| ESP32-S3 guest | ROM/bootloader/app startup, IDF 5.4.3, actual unchanged Rust receiver, frame CRC and byte checks | Full production UI/USB/storage worker; silicon cycle accuracy |
| Network | Actual loopback UDP into the guest's synthetic AP/network path | Real RF behavior, capacity and service calibration |
| FPGA | Fresh Verilator build of experimental credit QSPI/CDC, JPEG decoder, finite burst-memory/LCD bench; exact frame comparison | CS88 integration, full operational parent and physical timing |
| QSPI | SV drives actual endpoint pins from received guest event bytes and observes credit/commit responses | Guest GP-SPI registers, DMA descriptors and completion IRQs |
| Source timing | Host monotonic arrival stamps and raw RTL counters are retained separately | A common emulator/RTL clock or valid end-to-end latency |
| Host encoder | Separate Python MSV1 packetizer capture is executed below | Actual Sunshine/custom native backend execution |

The old builder deliberately uses `--assert -Wno-fatal`; **43 legacy compile
warnings** are retained. This is not promoted to the stricter warning-free
custom-decoder qualification. The C oracle shares algorithmic sources with the
JPEG RTL and is not an independent standard-codec conformance implementation.

The test guest embeds the synthetic image as an oracle. Accepted payload bytes
still come from received UDP datagrams, but the image prevents any production
SRAM footprint claim. PSRAM is disabled. The guest reports a 240-MHz CPU
configuration; this does not calibrate emulator instructions against real CPU
cycles. The bridge is stop-and-wait with one event in flight and at most 1,039
event bytes. Its blocking socket calls freeze FPGA time, so neither its wall
duration nor counters establish system FPS or input-to-display latency.

Raw testbench counters are `commit_cycle=2411982`, `present_cycle=4610042`,
with 434 credit reads. Publication/presentation and validation endpoints differ;
do not convert those counters into the strict under-10-ms product result.

## Reproduce

With the retained input paths listed in the script, run:

```sh
python3 scripts/cu66-v111/harness/baseline.py
```

It creates a new source snapshot and external build directory, checks all old
source/input hashes, captures emulator/compiler versions, compiles fresh RTL
and the existing corrected color oracle, then executes the emulated guest,
event audit and exact comparison under bounded watchdogs. Binaries, flash and
framebuffer dumps remain external; small logs, source snapshots and receipts
are retained. Old source/experiments are not edited.

The [first attempt](../../experiments/python-gamebub-v111/harness/attempts/20261108T182049120186Z/receipt.json)
is retained as **FAIL**. Its guest/adapter/RTL completed, but the final original
comparison command failed because the tool image lacks Pillow. Investigation
also found the first runner had selected the uncorrected vendor color main
instead of the already-published corrected oracle used by this baseline. No
DUT or existing golden was changed to resolve that mistake.

The successful attempt compiles the existing
`host/evidence/jpeg-c-model-fixed-color-main.cpp` and its existing source. A
single explicit wrapper-expression substitution invokes the new strict
stdlib-P6 comparator, retaining the original success tests and exact RGB565
arithmetic. The [diagnosis](../../experiments/python-gamebub-v111/harness/diagnostics/first-comparison-dependency/results.json)
records the original Pillow and new P6 readers returning identical numerical
fields against the historical correct PPM and fresh RTL dump. The freshly
compiled corrected oracle's PPM is also byte-identical to that historical PPM.
There is no tolerance relaxation or candidate-derived expected image.

## Host datagram trace utility

[trace.py](../../scripts/cu66-v111/harness/trace.py) records real loopback UDP
datagrams with their bytes, SHA-256 and host-monotonic arrival timestamps. It
validates format/bounds, offsets, ownership, complete-frame CRC and clock-domain
labels. It cannot attest an arbitrary external producer as Sunshine. The
implemented producer kinds deliberately distinguish the actual Python
packetizer from an unattested external capture; timing-qualified flags stay
false.

```sh
python3 scripts/cu66-v111/harness/trace_probe.py
python3 scripts/cu66-v111/harness/trace.py validate PATH_TO_CAPTURE_JSON
```

The [executed trace probe](../../experiments/python-gamebub-v111/harness/trace-results.json)
sent the unchanged `host/moonshine/protocol.py` packetizer's actual output
through UDP: 26 datagrams, 26,159 compressed payload bytes and **27,199
application-datagram bytes** (UDP payloads, including 1,040 bytes of MSV1
headers). The frozen trace field `wire_bytes` uses that application-level unit;
it excludes UDP/IP, link-layer and RF overhead. The
[byte-accounting receipt](../../experiments/python-gamebub-v111/harness/trace-accounting.json)
records those counts. An assumed unfragmented IPv4/UDP header charge would add
728 bytes; those network headers were not captured. All captured payload
bytes reconstruct the expected synthetic JPEG. Five controls reject a corrupt
payload, missing first packet, duplicate first packet, backward timestamp and
wrong clock domain. These are byte-integrity/clock-label checks, not a simulated
link-rate or Sunshine encoder benchmark.

## Capability and guest-build provenance

The [capability/provenance audit](../../experiments/python-gamebub-v111/harness/capability-provenance.json)
rehashes selected sources/artifacts, compares retained guest-source copies to
the current committed receiver/test application, and binds the exact emulator
binary and ELF compiler metadata.

The executable is Espressif `esp-emu 0.51.0`, SHA
`8df332148be34f0271d03d8cebf9f5ef0f67e95cee41e826b5b3f999e9047937`.
Its CLI advertises GDB CPU single-stepping. No dedicated external time-quantum
flag was found by the recorded help probe, and no controlled-time API was
exercised. This is not proof that no source-level API could be implemented.
The local release is binary-only; a pinned source-level scheduling and GP-SPI
inventory remains work for the synchronized bridge.

The reused guest ELF identifies **Rust 1.93.0-nightly** in `.comment`; the
currently installed `esp` compiler identifies **1.97.0-nightly**. Both are
recorded rather than falsely attributing the old guest to today's compiler.
Exact guest rebuild reproduction remains open. Recover the matching toolchain
or build a new explicitly versioned guest and rerun the tests. Current
Cargo/target/IDF configuration files are pinned as observations, not an
attestation that today's dependency tree produced the old ELF.

The next harness work is a tested time coordinator, actual guest GP-SPI/DMA
transactions, full production boot/memory accounting, and an actual isolated
Sunshine encoder backend. This V111 baseline does not close any of those gaps,
hardware 30 fps, or validated decode below 10 ms.

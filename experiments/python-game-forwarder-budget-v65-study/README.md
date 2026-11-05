# Forwarder byte and timing budget audit (v65)

**The audited firmware and FPGA path are JPEG-only; CS38 is not deployable through them today.** This study applies actual retained CS38 byte sizes to a hypothetical transport budget. It does not execute ESP32 instructions, simulate RF, change firmware or prove 30 fps. A matching negotiated codec/backend and FPGA decoder would still be required.

## Actual source constraints

The read-only audit covers [Rust protocol](../../firmware/handheld/src/streaming/protocol.rs), [streaming task](../../firmware/handheld/src/streaming/mod.rs), [actual FPGA driver](../../firmware/handheld/src/device/drivers/fpga/mod.rs), [driver-rate configuration](../../firmware/handheld/src/device/mod.rs), [canonical host packetizer](../../host/moonshine/protocol.py) and [current JPEG core](../../fpga/rtl/moonshine_core.sv).

| Constraint | Audited value and scope |
| --- | --- |
| MSV1 header | 40 bytes; version 1/codec 1 restricted JPEG |
| Fragment payload | up to 1024 bytes; canonical host default fills 1024 except tail |
| Accepted logical frame | 1..262144 bytes (256 KiB); not an ESP32 full-frame allocation |
| Runtime packet DMA | **1065 bytes** =40+1024+1, internal DMA-capable heap |
| Programming DMA scratch | 16 KiB inside `ensure_core`, before the session packet buffer exists |
| Streaming thread stack | separate 16 KiB declaration, not measured stack use or DMA |
| Payload write request | maximum 40 MHz, first configured driver no faster than requested |
| Configured rates | 40/20/16/10 MHz; actual pin clock/dividers/stalls unmeasured |
| Status reads | maximum 16 MHz; forward calls identity(two reads)+credit(one read) per fragment |
| Compatibility | Rust parser accepts codec1; begin checks JPEG feature; RTL instantiates `jpeg_core` |

The parser checks MSV1 metadata/CRC; it does not classify the JPEG payload. Mislabeling CS38 bytes as codec1 could forward bytes and receive a completion ACK, but would not create a valid JPEG or a supported FPGA decoder path. The unsupported-CS38 flags describe codec capability, not a payload-magic rejection test.

The runtime DMA buffer, programming scratch and stack are different scopes. Their sizes do not establish total ESP32 SRAM use. Wi-Fi/lwIP/socket queues, SPI descriptors/bounce buffers, other tasks, heap and target state layout remain unmeasured. The extra runtime byte lets packet-length validation reject a datagram beyond the permitted 1064 bytes.

The successful task path is blocking receive→parse/software CRC→begin on SOF→device access/identity/credit→blocking QSPI→stats→commit/reply on EOF→yield. `Device::try_lock` or credit failure drops/aborts rather than creating a free wait queue. The 500 ms frame timeout, 20 ms socket read timeout, recovery, feedback/heartbeat, UI contention and periodic statistics are not execution-time measurements. A socket timeout is not charged as a fixed per-packet delay here.

## Actual 457-frame corpus, nominal 30 fps requirements

Every byte count comes from actual archived binary-qual-v40 CS38 packets, with stored/raw hashes, outer CRC, ID and complete length verified. These include the existing CS38/HUD/binding bytes. They were not received by the audited firmware. Each is hypothetically packetized in full 1024-byte payloads except the tail.

| Cohort | Frames | Mean payload B | Max payload B | Mean fragments | Max fragments | Mean data L3 Mbps at30 | Max frame-equivalent L3 Mbps at30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 119 | 17328.48 | 27063 | 17.412 | 27 | 4.44299 | 6.93576 |
| mass-effect-4500 | 119 | 20371.58 | 38504 | 20.378 | 38 | 5.22175 | 9.86112 |
| mass-effect-1600 | 119 | 3907.82 | 16249 | 4.269 | 16 | 1.00755 | 4.16088 |
| mass-effect-combat | 100 | 30027.85 | 44032 | 29.830 | 43 | 7.69351 | 11.26944 |

Across 457 frames, mean payload is 17405.08 B and mean fragment count 17.479. Payload range 2093–44032 B produces 3–43 fragments. IPv4/UDP data-only L3 bytes are

`N = ceil(B/1024)`

`L3 = B + N × (40 MSV1  +20 IPv4  +8 UDP)`

At nominal 30 fps, the weighted corpus mean is **4.46248 Mbps**, with a maximum frame-equivalent requirement of **11.26944 Mbps**. The mean is not enough to guarantee the largest frame meets a 33.333 ms latency window. These are byte-rate requirements, not measured RF goodput; MAC/PHY, ACKs, retries, encryption/FEC, contention and other traffic are excluded. Actual source PTS are not being replayed as an RF/scheduling trace.

The current 32 B completion feedback adds at least 60 IPv4/UDP bytes per successful frame in the reverse direction (14.4 kbps at 30 fps), plus heartbeat/input/error messages. It is excluded from the data-only figures. A received-frame ACK is not proof of FPGA decode or presentation.

## QSPI phase lower bound and unmeasured work allowance

With the audited rate list and 40 MHz request, the declared driver selection is 40 MHz. The lower-clock scenarios are explicit sensitivity assumptions, not observed runtime fallback.

The firmware strips the 40 B transport header before forwarding. The driver sends an 8-bit single-line command, 32-bit quad address and quad payload:

`clocks per fragment =8 +32/4 +8p/4 =16 +2p`

`total phase clocks =16N +2B`

At an assumed effective 40 MHz, these phases alone take **0.87725 ms mean /2.2188 ms worst** for this corpus. Chip-select/setup, driver/SDK, lock, MMIO and scheduling costs are not included in that lower bound. The full data+address+command time is modeled; headers do not cross QSPI.

With an explicitly assumed other-stage reserve R, the maximum **amortized combined unmodeled successful-frame allowance** per fragment is

`(1e6/30 − QSPI_phase_us − R) / N`

For the largest corpus frame (44032 B, 43 fragments), this upper envelope is 723.59 µs/fragment with R=0, 607.31 µs with R=5 ms, and 491.04 µs with R=10 ms. The allowance must cover receive/CRC/SDK/locks/status-MMIO/yield/jitter and frame-level work amortized across fragments. It is not an observed CPU time or a guarantee for individual calls.

R=0 is a maximum residual envelope, not a claim that FPGA decode, memory/display publication, host encoding or transport queues are free. The 5/10 ms reserves are illustrations, not measured stage costs. Current JPEG decode/publication readiness must be measured as part of the real pipeline. Other overlaps or serialized dependencies require an actual pipeline trace.

## Explicit assumption sweeps

Each row assumes the stated combined unknown cost per fragment. At 40 MHz, the number of modeled deadline misses among 457 frames is:

| Assumed unknown µs/fragment | Reserve 0 ms | Reserve 5 ms | Reserve 10 ms |
| --- | ---: | ---: | ---: |
| 25 | 0 | 0 | 0 |
| 100 | 0 | 0 | 0 |
| 500 | 0 | 0 | 4 |
| 1000 | 96 | 123 | 141 |

At 1 ms/fragment, 96 frames miss even with no other-stage reserve. At 500 µs and an assumed 10 ms reserve, four miss; the worst modeled margin is −385.47 µs. The four source records are combat IDs 48/50/52/72 (43944/44032/43234/43087 payload bytes), each 43 fragments. These are unsupported-CS38 source records for the audit, not instructions to send them to the JPEG-only endpoint. The complete 48-scenario grid also includes 20/16/10 MHz alternatives. Every miss retains its source ID, exact rational used time and negative margin. No miss is removed to manufacture a 30 fps result.

Software CRC has eight source-level bit rounds per payload byte. Their count is archived; compiled instructions, cycles, acceleration and real ESP32 execution time are not inferred. Status-MMIO reads and clean begin/commit transactions are audited but remain inside the unknown allowance, avoiding double subtraction.

The protocol maximum 256 KiB is a separate boundary case, not the corpus maximum. It uses 256 fragments and a 40 MHz QSPI phase lower bound of 13.2096 ms, leaving only 78.61 µs/fragment before any other-stage reserve. Protocol acceptance does not establish a realtime operating point.

## Hypothetical shorter headers

The 16/8 B alternatives below are unimplemented byte-count illustrations, not complete replacement formats preserving all existing fields or compatibility. Header reduction benefits every codec using that transport. It changes only the modeled network cost here; payload QSPI/CRC work and assumed CPU costs remain unchanged.

| Header bytes | Corpus data L3 bytes | Mean nominal L3 Mbps | Reduction from 40 B header |
| --- | ---: | ---: | ---: |
| 40 | 8,497,307 | 4.46248 | 0.000% |
| 16 | 8,305,595 | 4.36180 | 2.256% |
| 8 | 8,241,691 | 4.32824 | 3.008% |

## Hardware-team measurements required

Measure actual pin clock/phase gaps and complete SPI transaction times; compiled protocol parsing/CRC; begin/commit and per-fragment identity/credit MMIO; lock-busy/drop rates; task wake/yield and UI contention; RF/UDP arrival goodput, bursts, losses and queues; and FPGA decode/DRAM/publication/scanout time. Record successful frame IDs alongside received, decoded and displayed counters. Measure end-to-end timing with a valid clock basis; host capture timestamps alone do not synchronize ESP32/FPGA clocks.

Use those observations to replace the assumed costs/reserves and evaluate complete-frame latency and unique displayed-frame throughput. This audit supplies measurement thresholds and current source constraints, not firmware support, ISA simulation, SRAM-fit or RF/FPS proof.

Six independent tests and the complete audit pass: 457 payloads, 7988 canonical-host fragments, 1371 header scenarios, 5484 exact residual thresholds, all 48 sweeps and 1685 retained negative-margin misses, with all 12 source pins valid. Independent verification also checks the codec-label/backend distinction, inclusive zero-margin boundary and allocation scopes.

Three producer tests pass for fragment boundaries/exact ceiling arithmetic/MAX rejection, header-only network deltas and exact QSPI phase math/negative margins, and actual Rust allocation/backend scope checks. All source files are pinned read-only; no firmware or FPGA file was edited.

```sh
cd experiments/python-game-forwarder-budget-v65-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

The independent audit additionally checked the pinned esp-idf-hal 0.45.2 semantics for single-line `Operation::Write` versus explicit quad `WriteWithWidth` against its [upstream SPI source](https://raw.githubusercontent.com/esp-rs/esp-idf-hal/v0.45.2/src/spi.rs). This supports the phase arithmetic and supplies no measured pin-clock or execution-time result.

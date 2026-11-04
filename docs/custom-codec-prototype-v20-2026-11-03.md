# Iteration 20: hardware-development handoff

V20 is ready for **hardware/software development and offline conformance testing**.
It preserves 720×480 coded / 720×405 active content and the 30-ID/s goal. The kit
supplies executable references, golden data, wire contracts, team prompts and
acceptance gates. A full FPGA decoder, native negotiated endpoint, bitstream and
sustained physical 30 fps are still open implementation work.

Use the paired `handoff/gamebub-app-codec-v20-20261103` branches. Begin at
[hardware/gamebub-v20](../hardware/gamebub-v20/README.md), its
[task prompts](../hardware/gamebub-v20/TASKS.md) and
[acceptance gates](../hardware/gamebub-v20/ACCEPTANCE.md).

## Delivered implementation references

| Component | Concrete result | Practical limit |
| --- | --- | --- |
| Mandatory HUD encoder policy | All 96 accepted outputs carry all 21,120 requested original RGB565 words within 49,152 B | More background loss and paid retries on complex footage |
| Reconstruction-fed canonical tags | All 16 real AR03 decisions match tags/YUV/display; 9 generated IT20 streams | Conditional service/storage model, not SHA RTL or fitted resources |
| Portable C11 inverse | 101,667 blocks /6,506,688 residual samples exact, UBSan enabled | Scalar host golden reference, not ESP32/RTL throughput |
| Hardware contract bundle | Byte offsets, generated C constants, 1,725 serialized FG19 messages, actual epoch-1 AR03/AF03 example | Capability negotiation/reset and endpoint implementation remain open |

All 34 tests pass: 10 mandatory-policy, 15 inline reconstruction, 5 C/ABI and 4 audit
tests. Independent retained verifiers and hash-bound analyses pass. The aggregate
checker is `python experiments/verify_prototype_v20.py`; it replays conformance,
not timed gameplay benchmarks. Source snapshots conservatively include inherited
artifacts, not exclusively executed code. Prior branches stay frozen.

## Mandatory HUD budgeting fixes the coverage gap

The [mandatory-HUD study](../experiments/python-game-mandatory-hud-study/README.md)
prepares/caches and validates every requested exact display patch before base
selection. It reserves the complete framed patch bytes, then tries at most four
legal ROI/background maps: 8/16, 8/32, 16/32 and 32/32. The actual outer AR03 cap is
authoritative. Failed maps pay real build/discard work without burning identity
or publishing a bank. If no map fits, the whole frame is rejected.

Four cases replay 48 frames from each of two existing 1280×720 precompressed clips,
baseline and mandatory: 192 decisions / 96 source acquisitions. These are reused
regression windows at 29.88 fps, not fresh long footage or live acquisition. The
native sequence uses real AR03/AF03 references, keys/promotions/refresh and actual
decoded packets; it is not a source-clock throughput experiment.

| Scene /policy | Full requested HUD | Mean active expanded-RGB565 channel MSE | Complete packet bytes |
| --- | ---: | ---: | ---: |
| 2600 baseline |48/48 |14.4290 |988,011 |
| 2600 mandatory |48/48 |14.4290 |988,011 |
| 7200 baseline |34/48 |27.0335 |2,103,725 |
| 7200 mandatory |48/48 |34.0921 |2,116,013 |

Primary outputs remain byte/pixel-identical. The complex scene needs 23 paid
losing builds: 25 frames accept 8/16, 23 accept 8/32, with maximum complete size 48,898 B.
Rejected builds cost 579.30 ms in the recorded Python run; patch preparation costs
358.66 ms for that mandatory case. Those are host-work measurements, not achievable
frame rates. Bytes rise 0.584% while requested HUD coverage becomes complete.

Quality is traded for coverage: MSE is RGB-channel error after RGB565 expansion,
not packed-word arithmetic. Adapted keys/promotions also change later prediction
history. Only source IDs 0 and 24 retain matched reference history in the complex
comparison; their mean MSE changes 27.8746→42.8716. Do not attribute the whole
same-source mean delta purely to entropy coding or claim a lossless base image.

Tests cover all-attempt failure/reuse of the uncommitted ID, stale commit,
callback/source failures and preservation of pre-existing external source leases.
Twenty isolated golden fixtures retain actual packets, pre-banks, YUV, display
and AF03 bytes (109 objects,8,085,364 stored bytes). Each P packet must use its
stated predictor identity/tag/bytes. Twenty CRC-negative replays reject atomically.
Baseline partial-patch vectors are valid general AR03 grammar controls; they do
not satisfy the proposed mandatory profile. Native peers must negotiate the
requested region list and validate its coverage. AR03 syntax itself is unchanged.

## Inline tags remove bank rereads without changing reference identity

The [inline reconstruction study](../experiments/python-game-inline-reconstruction-study/README.md)
runs actual sparse inverse/reconstruction stripe by stripe. Every newly clipped
uint8 tile enters the tagger before its external-output write. It never traverses
a finished output plane as the tag input. One compact stripe reorders 8×8 tiles
into canonical Y/Cb/Cr raster rows; a little-endian int16 row feeds SHA256 after
the little-endian width/height prefix. Canonical SHA256[:16] remains unchanged.

All 16 packets /97,308 blocks /6,227,712 residual samples /6,224,472 reconstructed
YUV samples /253,440 selected UI words match frozen vectors. Twelve native
cohort decisions reuse six source acquisitions, plus four small controls.
Ten decisions are eligible publications; six ordinary decisions expose no
publication tag. Functional private-tag checks on all vectors are an oracle;
ordinary runtime P frames need no reference publication hash. Packet CRC/length,
patch validation, all tiles, expected tag and digest finalization precede publication.

Tests cover negative rounding, partial tiles, ordering, duplicate/truncated input,
stalls, abort and expected-tag mismatch. Nine generated IT20 streams occupy 567,504
compressed bytes. IT20 is an offline tile fixture, not a new runtime codec.

| Matched conditional service at 100 MB/s hash rate | Mean native frame service |
| --- | ---: |
| Compact YUV8 plus serial tag reread |67.6298 ms |
| Reconstruction-fed inline tag |62.8622 ms |

The 7.05% planning improvement removes 4,147,200 physical native compact-bank reread
bytes across eight eligible native decisions. Copy/expansion, hash backpressure,
SHA padding and finalization are paid in both matched designs. Tag-ready,
write-drained bank-publication and RGB display-ready times are distinct.

Tagger arrays use 7,200 B at 720 pixels: one 8-row uint8 stripe and one int16 row.
The conservative whole local plan adds these arrays and 192 B assumed SHA/control
state to v19, reaching 107,504 B; it does not claim buffer reuse or full decoder heap.
Hashlib/Python oracle/export arrays and external banks are excluded. All native
cases in all five conditional profiles still miss 33.33 ms. Memory bandwidth,
clock/hash service, cache/preflight and average scanout reservation remain
assumptions; physical portrait line deadlines, area and Fmax are unproved.

## Hardware kit contents and exact arithmetic

The portable scalar C kernel validates legal dequantized input before changing
output, uses no heap and preserves both floor((sum+8192)/16384) boundaries.
Golden arrays retain int32 residuals, including extremes above int16 range.
The 101,667 blocks comprise 97,308 actual AR03 blocks, 4,097 exhaustive DC values
at quantizer 255, 256 seeded legal operand-domain random blocks and six signed
edge patterns. Exact C work totals/classifications also match the Python oracle.
Four invalid-input checks leave output/work unchanged.

Compilation used GCC 13.3 in the existing Gamebub development container, followed
by native Linux-host execution with statically linked UBSan. This verifies C
conformance, not embedded instruction timing. Legal numeric bounds are 20-bit
dequantized input, 22-bit intermediate and 38-bit biased accumulators; a 40-bit
planning accumulator and multiplier decomposition still need RTL mapping.

`golden-index.json`, compressed int32 arrays, `export_mem.py` and a signed-edge
`.mem` smoke set let the RTL team start immediately. `wire-contract.json` and
`gb_wire.h` define offsets/endian order; never cast a packed C structure.
AR03's header is 61 bytes, its CRC is after the variable body, and 65 bytes is
the total fixed envelope overhead. GF03 header 31 + token 16 + payload 1008 gives
1055-byte UDP data packets. PC18/QC18/FG19/AF03 sizes are 29/28/36/43 bytes before
28-byte IPv 4/UDP overhead. Serialized FG19 histories preserve intentional loss
flags and model times; they are not radio captures.

The host branch carries byte-identical wire/development JSON and native-port
instructions. The hardware kit's `handoff-index.json` binds the kernel, contracts
and two study manifests. Host, ESP32 and FPGA teams have separate copyable task
prompts, with whole-frame grants, packet credits and decoded publication kept
separate. Existing MSV 1 JPEG endpoints do not implement this custom profile.

## A remaining bandwidth gate

At 30 scheduled frames/s, arithmetic projection from complete mandatory packets is:

| Scene | Mean complete bytes/frame | AR03 body rate | Forward GF03/token/IP/UDP rate |
| --- | ---: | ---: | ---: |
| 2600 |20,583.56 |4.940 Mb/s |5.316 Mb/s |
| 7200 |44,083.60 |10.580 Mb/s |11.376 Mb/s |

The projection excludes FG19, reverse credits/AF03, Wi-Fi airtime/retries and
capture/input/audio. The old assumed 8 Mb/s link cannot carry the complex case at
30 fps. A 49,152-byte frame cap is not a sustainable-rate guarantee.

## Next development order

1. Port and simulate the exact inverse and compact reconstruction/tag modules
   against the C/IT20/packet vectors, including stalls, reset and illegal input.
2. Join mandatory candidate admission with FG19 and native host encoding; share
   valid forward-analysis work between bounded map attempts without hiding costs.
3. Implement negotiated profile/reset/recovery, true FIFO/backpressure and mapped
   bank ownership before continuous use. Preserve the working JPEG baseline.
4. Measure actual host/ESP32 CPU/heap/DMA/QSPI/RF and FPGA memory/scanout/resource/
   timing gates. Use fresh long gameplay, unique IDs, gaps/age and full HUD coverage.
5. Revisit acknowledged receiver display-cache reuse/deltas to reduce static HUD
   bandwidth while keeping it separate from YUV prediction. Existing host byte
   caching saves work but still transmits patches. Any receiver reuse needs exact
   patch identity/generation, loss, refresh and reset semantics; it is not v20 code.
6. Study pre-granted capacity leases and smaller compressed refill caches with
   explicit generation and shared-memory arbitration. Neither is implemented here.

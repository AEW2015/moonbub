# Iteration 22: joint video/HUD transactions and optimal gap spans

V22 implements a synchronous Python whole-frame transaction, then independently
tests a smaller exact HUD coding grammar. It preserves **720×480 coded /720×405
active** and the 30-ID/s goal. The existing v20 hardware kit remains frozen;
this study supplies no new installed endpoint, RTL or physical frame-rate proof.
All **37 tests pass**: 21 joint-transaction, 10 gap-span and 6 independent-audit
tests. Source-pinned retained verifiers and the complete-byte analyzer pass.

## Whole-frame admission and publication now execute together

The joint sender prepares HC21 on a private bookkeeping fork, then builds actual
patch-free AR03 candidates with bounded legal maps. It counts every byte of the
base, HC21 sidecar and 57-byte CB21 pair binding against 49,152 bytes. The adaptive
order is ROI/background 8/16, 8/32, 16/32, 32/32. Every actual losing map/build and
discard is paid. Metadata forks share immutable bank arrays rather than deep-copy
their contents.

Reject, discard, expired deadline and build failure leave issued video identity,
HUD generation, confirmed banks and pending publications unchanged. Accepted work
holds its exact source lease until commit/discard. Commit validates the owned
candidate and both semantic component states, then swaps the logical state tuple.

The receiver validates and privately decodes both components. Neither visible
image, published bank nor ACK changes during prepare. An explicit write-drain
event **and** a presentation/vblank event are required before one logical tuple
publishes the matching base, HUD and RGB565 display. These calls are injected
functional permissions, not real DMA fences, memory barriers, CDC or panel timing.
Malformed fixed-profile geometry rejects before private reconstruction.

JA22 acknowledges the whole pair and embeds the exact AF03 plus HA21. Its
134 bytes include a 33-byte header, 43-byte AF03, 54-byte HA21 and final four-byte
CRC. A wrong/mixed half, body digest, epoch or identity cannot independently
advance video or HUD state. Exact last-pair retry returns the same ACK without
presenting another frame. Sender stop-and-wait remains; no free extra concurrency
or unknown credits are assumed. CRC/SHA tags provide consistency, not authentication.

Owned source/destination readers survive metadata forks and prevent overwrite.
Tests cover readers arriving after prepare, duplicate releases, token exhaustion,
invalidated component state, abort and deadline boundaries. Array read-only flags
are a trusted local API contract, not a security boundary against code deliberately
reenabling NumPy write access. Local reset still requires drained ownership;
reset negotiation and one-sided reboot recovery remain unimplemented.

## Actual sequential native-source campaign

Four cases reuse 96 distinct acquired source frames from the same two existing
48-frame Mass Effect windows, giving **192 actual joint decisions**. All commit,
retain all four requested HUD regions and remain within the complete cap.
Footage is precompressed 29.88 fps, not live capture at 30 distinct frames/s.

| Window /policy | Complete pair bytes | Mean active RGB565 channel MSE | Fine/coarse selected frames |
| --- | ---: | ---: | ---: |
| 2600 /fixed v20 profile trace |934,451 |14.4290 |48 /0 |
| 2600 /adaptive |934,451 |14.4290 |48 /0 |
| 7200 /fixed v20 profile trace |2,017,112 |34.0921 |25 /23 |
| 7200 /adaptive |2,072,408 |31.0812 |34 /14 |

"Fine/coarse" here means ROI8/background16 versus ROI8/background32. The complex
adaptive policy spends **2.74% more bytes** for **8.83% lower mean squared error**
and nine more fine-background frames. This is a rate/quality tradeoff, not a
compression-efficiency gain at equal quality. Later reference histories diverge;
matched-reference source IDs 0–32 have MSE 37.8212→33.5091. Error is measured after
expanding RGB565 channels over the 720×405 active area, not packed-word arithmetic
or a human gameplay/legibility score. HUD words remain exact in both policies.

The fixed control deliberately replays v20's stored selected-map trace to preserve
its image and reference history. It omits the old controller's search work. It
is an image/byte control, **not a deployable causal selector or fair timing
baseline**. Only the adaptive case exercises current complete-size selection;
its complex sequence pays 14 losing builds. No host speedup is inferred by
comparing fixed/adaptive wall times.

The retained verifier replays all 192 complete packet/ACK sequences from empty
banks, compares 4,055,040 original HUD words, canonical hashes for 99,532,800 YUV
samples and output hashes covering 66,355,200 display words. These last counts are
sequence hash consistency checks, not lossless original full-frame pixels.
Twenty retained-source quality checks independently recompute the pixel errors;
ten fixed-control images also match v20's full golden display words directly.
It repeats 192 CRC negatives and 384 write/vblank-gate failures without publication.

## HD22: minimum-byte row-span partition

HD21 splits every contiguous nonzero XOR run. HD22 merges runs separated by one
or two zero words: a six-byte extra span header costs more than transmitting two
bytes per zero word. Gaps of three words tie and canonically split; larger gaps
split. With this grammar, independently selecting each gap gives a minimum-byte
partition for the row. Exhaustive tests enumerate every partition of 2,036 small
masks. This is optimal **within this span grammar**, not an optimal general codec.

HD22 has its own magic/grammar, the same 50-byte framing cost, RAW/COPY fallbacks,
geometry/reference/content tags and CRC. Decoding permits interior zero XOR words
but rejects noncanonical endpoints/order/short-gap splits. Both actual delta
candidates and the existing full-patch compressor are paid in the benchmark;
the smallest complete encoded patch wins. Source and ACKed RGB565 cache histories
are held identical to v21, independently of video-base policy.

| Native window | V21 selected HUD bytes | HD22 with same cache overhead | Additional HUD saving |
| --- | ---: | ---: | ---: |
| 2600 |442,450 |427,966 |3.27% |
| 7200 |1,023,067 |981,385 |4.07% |

All 528 patch decisions /132 updates independently scalar-decode 2,787,840 words
exactly. Static, sparse-change and noise controls show **no additional byte gain**
over v21 after the real full-patch fallback; they remain separate from gameplay.
Seven portable goldens retain 26,880 words and seven CRC negatives.

Fewer headers also send extra zero operands. On matched selected-span cases,
2600 removes 3,657 headers while adding 4,916 zero words; 7200 removes 9,249 headers
while adding 12,096 zero words. Logical decoder work, hash/copy traffic and actual
native/RTL costs still need measurement. This is not a DSP throughput result.

## Keep actual replay and integration projections separate

The joint model currently dispatches **HC21/HD21**, not HD22. The following
analysis substitutes independently tested HD22 patch sizes into the fixed-image
joint rows, assuming the same 83-byte cache envelope, 57-byte binding and no new
dispatch overhead. It is a complete-byte projection, not actual HD22 joint replay.

| Window | Actual fixed joint bytes | Projected HD22 joint bytes | Complete saving | Projected forward Mb/s at30 |
| --- | ---: | ---: | ---: | ---: |
| 2600 |934,451 |919,967 |1.55% |4.9804 |
| 7200 |2,017,112 |1,975,430 |2.07% |10.6515 |

Projected complex maximum is 48,477 bytes, versus 49,022 for current joint HC21.
A new negotiated dispatch may add bytes and must be tested as real packets.
The projection charges GF03/token/IP/UDP fragments, two forward and three reverse
FG19 controls, one PC18 per fragment and the actual 134+28-byte JA22. Current
fixed joint forward/reverse projections are 5.0596/0.3560 Mb/s (2600) and
10.8757/0.6621 Mb/s (7200). Adaptive complex forward is 11.1731 Mb/s.

These are 30-ID/s arithmetic projections, excluding queries/retries, Wi-Fi airtime,
capture, audio and input. JA22 is nine bytes more than separate AF03/HA21 datagrams
when each carries IPv4/UDP overhead. There is no integrated gateway or RF schedule.

## Memory and timing limits

The Python reference uses int16 YUV banks: two retained banks reach 2,073,600 bytes.
Two published HUD banks use 84,480 bytes and the visible RGB565 display uses
691,200 bytes. A private decoded YUV set is 1,036,800 bytes; on stored frames those
same arrays later become a retained bank. Do not add postpublication counters as
independent allocations. Before publication, new private display/HUD staging can
coexist with old visible state. RGB intermediates, coefficients, packets, hashes
and caller objects are additional. Named array counts are neither a total Python
heap peak nor a mapped target memory plan. Logical pointer sharing does not grant
extra SDRAM ports or eliminate physical storage/reader lifetimes.

Keep v20's compact uint8/tag architecture for the native FPGA port, then budget
actual external-memory ranges, staging and arbitration. ESP32 code still must
forward bounded fragments without taking on these complete video/HUD banks.
No ESP32 instruction/DMA/SRAM, RF/QSPI service, FPGA resource/Fmax, scanline or
physical 30-fps proof is supplied. Python timing includes actual controller work;
diagnostic hashes/quality/export and offline acquisition are outside service clocks.

## Next application-specific development

1. Implement a new HC22 dispatch carrying the actual HD22 bytes, then replay the
   whole joint packet/ACK stream. Retain HD21/legacy/JPEG controls and count every
   new negotiation/dispatch byte. Preserve exact display tags and video-bank isolation.
2. Share source prediction and forward-transform analysis across bounded map
   attempts. The adaptive complex sequence currently repeats 14 losing builds;
   do not optimize by hiding that cost. Require identical selected packets,
   reconstruction, ownership and rejection behavior against this reference.
3. Add explicit negotiated capabilities/reset/rekey and one-sided reboot/lost
   reset recovery. The tuple transaction and local resets are a laboratory model.
4. Model a bounded pipelined bank-generation scheme to reduce stop-and-wait RTT,
   with explicit extra storage, read drain and frame/packet/cache/reference credits.
   Include true single-worker/DMA/FIFO and shared-memory contention before rate claims.
5. Port the stable inverse/parser/span/cache ownership kernels to native/RTL and
   prove stalls, abort/reset, mapped memory, write fences and atomic display epochs.
   Measure long fresh gameplay with unique presented IDs, frame age/gaps, quality,
   input/audio and fault recovery before claiming sustained 30 fps.

Run `python experiments/verify_prototype_v22.py`. Component instructions and data
are in [joint transactions](../experiments/python-game-joint-commit-study/README.md)
and [HD22 gap spans](../experiments/python-game-gap-span-study/README.md).

# Iteration 21: acknowledged display-cache deltas

V21 advances the application-specific codec by treating the exact HUD as a
separate acknowledged display layer. It keeps **720×480 coded /720×405 active**,
the v20 video-base bytes and reference histories, and the requested 30-ID/s goal.
It does not replace the frozen v20 hardware-development handoff or install a new
native endpoint. This branch is a Python study and integration specification.

## Measured byte results

The same two 48-frame Mass Effect regression windows are used, with 96 source
acquisitions. They are previously compressed 29.88-fps footage, not fresh or
held-out live 30-fps captures. All four requested HUD regions total 21,120 RGB565
words/update. The main game image remains lossy exactly as in the v20 mandatory
policy; the new HUD mechanism adds no image loss.

| Native source window | Existing HUD bytes | HC21 HUD bytes | HUD saving | Complete bytes including new binding | Complete saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2600 |498,746 |442,450 |11.29% |988,011 →934,451 |5.42% |
| 7200 |1,124,704 |1,023,067 |9.04% |2,116,013 →2,017,112 |4.67% |

The complete comparison includes a 57-byte CB21 binding container for each
frame. Raw HC21-only substitution figures of 5.70% and 4.80% omit that container
and must not be presented as the complete-frame result. CB21 is an actual
serialized **offline fixture format**, not implemented endpoint carriage.

All 96 accounted native pairs fit 49,152 bytes; the complex maximum is **49,022
bytes**, leaving only 130 bytes of cap headroom. Whole-pair admission still needs
integration with the candidate/commit controller. These results do not guarantee
that unseen frames, new metadata or recovery traffic fit.

The encoder tries the actual existing full patch compressor and actual HD21
delta for each region, paying both before selecting the smaller complete patch.
In 384 native patch decisions it chooses 265 legacy full patches, 117 XOR-span
patches and only two COPY patches. The game HUD is not assumed static. There is
no future-frame or decoded-quality oracle in mode selection.

Separate 12-frame synthetic controls give 56.80% HC21 HUD savings for static
patches and 47.84% for small changes. Random noise **regresses 0.158%** because
the existing full-patch fallback wins but HC21 adds metadata. Do not report the
synthetic static result as measured gameplay compression.

## Functional evidence

- HD21 has RAW, COPY and bounded changed-row XOR spans. Complete overhead is
  50 bytes, including geometry, exact reference/current SHA256[:16] and CRC.
  It uses canonical little-endian RGB565 words. Six retained goldens independently
  reconstruct 36,481 words; fourteen component tests include 60 seeded roundtrips.
- HC21 wraps exactly four regions, with a 79-byte header and four-byte CRC.
  It binds epoch, frame, generation, destination, exact reference identity and
  whole-HUD content. HA21 is 54 bytes and binds the precise outstanding packet.
  Across 96 native and 36 synthetic decisions, **2,787,840 HUD words** match and
  132 corrupt updates reject before publication. Fifteen tests cover loss, retry,
  wrong/stale ACKs, reset, reference/tag mismatch and reader ownership.
- Ten v20 mandatory goldens decode through an actual patch-free/resealed AR03
  receiver and separate HC21 receiver. All **3,456,000 full-display RGB565 words**
  and **5,184,000 reconstructed YUV samples** match v20. Canonical YUV predictor
  tags remain unchanged. The AF03 packet must bind the new AR03 body CRC.
  Ten repaired-outer-CRC component-binding negatives reject. Seven composition
  tests cover stripping, pairing, cap admission and rate arithmetic.

The composition vectors use exact retained precondition YUV banks; they are
isolated video-packet tests, not ten self-contained stream frames. Their separate
HC21 decisions form two five-update cache sequences. An independent audit checks
the frozen artifacts, byte arithmetic and all three retained verifiers. All
**41 tests pass**: 14 patch, 15 cache, 7 composition and 5 independent-audit tests.

## Ownership, loss and memory

HC21 is bounded stop-and-wait. The sender references only a fully ACKed immutable
cache bank and keeps exactly one unresolved packet. A lost packet/ACK cannot
advance its reference. An exact retry is idempotent; conflicting or stale bytes
reject. Eight live unique reader descriptors protect two alternating banks;
duplicate release cannot drain another owner. A 32-bit token counter fails
closed on exhaustion until a later local epoch reset.

Receiver pixel storage is **84,480 bytes for two banks +42,240 bytes for atomic
staging =126,720 bytes**, before parser/delta scratch, packet bytes, descriptors,
hash state and allocator overhead. Python makes additional bounded arrays and
copies. This is a storage plan, not measured embedded heap or fitted FPGA RAM.
Sender confirmed+pending pixels peak at 84,480 bytes, plus the existing full-patch
selector cache (up to 69,690 bytes on native cases), pending wire bytes and scratch.
The noisy synthetic selector cache reaches 84,592 bytes.

Place prospective persistent HUD storage in explicitly mapped FPGA external
memory. The ESP32 should forward bounded fragments rather than own full HUD
banks. Neither placement nor the ESP32 memory/DMA behavior is implemented here.
Do not subtract this state from v20's local plan by assuming undocumented reuse.

The receiver's synchronous validated object assignment is not DMA completion,
atomic video/HUD presentation or scanout timing. Reset tests call both local
endpoints explicitly; they do not implement reset negotiation/rekey, one-sided
reboot recovery or a lost-reset handshake.

## Bandwidth and latency remain gates

The following 30-ID/s projections include GF03/token/IP/UDP fragmentation and
two forward/three reverse FG19 controls per proposed frame. Reverse accounting
also includes one PC18 per fragment, AF03 and the new HA21. It assumes future
single-frame carriage of CB21; existing GF03 peers do not accept it.

| Window | Forward old →new Mb/s | Reverse old →new Mb/s |
| --- | ---: | ---: |
| 2600 |5.3469 →5.0596 |0.3490 →0.3538 |
| 7200 |11.4065 →10.8757 |0.6679 →0.6599 |

These forward baselines exceed the v20 data-only 5.316/11.376 figures because
the two FG19 forward controls are now included. Retries, queries, Wi-Fi airtime,
capture, input and audio remain excluded. There is no RF/ESP32 ISA emulation.

An optimistic network-only stop-and-wait sweep allows complete overlap between
forward/reverse directions and adds an assumed minimum feedback delay. It still
exposes important necessary conditions on the complex window:

| Assumed symmetric link /minimum delay | Frames satisfying network-only 33.33 ms bound |
| --- | ---: |
| 8 Mb/s /0 ms |0/48 |
| 12 Mb/s /0 ms |41/48 |
| 12 Mb/s /5 ms |10/48 |
| 16 Mb/s /5 ms |48/48 |
| 16 Mb/s /15 ms |0/48 |
| 24 Mb/s /15 ms |48/48 |

A passed bound leaves zero evidence of CPU, QSPI, decoder or display feasibility.
It is not a recommended physical link rate. The last two passing worst cases
leave little time even before those services. V20's modeled decoder profiles
still miss 33.33 ms; this HUD optimization does not accelerate their inverse
transform or remove the need to map and measure the hardware pipeline.

Actual Python HC21 mean encode/decode component costs are 11.34/1.51 ms (2600)
and 10.71/2.36 ms (7200), excluding video-base work, offline source acquisition,
correctness/export work and transport. All competing modes are paid. These are
host measurements on this run, not native endpoint or FPGA throughput.

## Progression to the application-specific codec

1. Keep the working JPEG path and frozen v20 inverse/tag/reference contracts.
   Use v20 hardware vectors for the residual decoder/DSP pipeline.
2. Integrate separate **prepare/admit/commit** for a complete video+HUD candidate.
   HC21's standalone prepare currently consumes a component identity and cannot
   substitute for whole-frame admission. Reserve actual binding and ACK costs.
3. Add private decode plus atomic joint publication: the matching video and HUD
   become visible together only after both validate and memory writes drain.
   Lost HUD data must not display a falsely current HUD over a newer base.
4. Implement capability negotiation, one-sided reset/rekey and explicit cache
   refresh. Keep HA21 display-cache confirmation distinct from AF03 YUV-reference
   confirmation, FG19 frame capacity and PC18 fragment permits.
5. Prototype a bounded pipelined cache-credit alternative only after ownership
   is proven; stop-and-wait adds a feedback gate every frame. Measure how many
   bank generations can remain live rather than assuming free concurrency.
6. On fresh gameplay, compare exact tile COPY/XOR, gap-aware span packing and
   acknowledged region refresh against the frozen full-patch fallback. Report
   total framing, memory reads/writes, worst-case CPU, frame age and recovery.
   Do not choose defaults from these reused windows alone.
7. Port the fixed arithmetic and parser to native/RTL; prove stalls/reset/CDC,
   external-memory arbitration, portrait scanout and mapped resource/timing fit.
   Then calibrate simultaneous ESP32 Wi-Fi/QSPI/input and long gameplay.

The application-specific gain here is exact UI reuse with its own lifetime and
feedback. The video-base decoder remains the v20 custom transform profile. This
study supplies no HEVC/AV1 decoder, new DSP fit, bitstream or physical 30-fps proof.

See [integration tasks](v21-display-cache-integration.md),
[patch codec](../experiments/python-game-hud-delta-study/README.md),
[cache campaign](../experiments/python-game-hud-cache-study/README.md) and
[composition/budget method](../experiments/python-game-display-compose-study/README.md).
Run `python experiments/verify_prototype_v21.py` for retained verification.

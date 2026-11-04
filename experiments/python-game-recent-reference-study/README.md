# AR01: bounded acknowledged reconstructed-P references

This Python-only experiment preserves the 720×480 coded canvas, native
720×405 active game content and 30 fps product requirement. It introduces a
separate AR01 frame / AF01 feedback dialect around frozen GM01 transform,
quantization and CP02 entropy bytes. No installed Sunshine mode, ESP32 firmware,
FPGA decoder, HEVC/AV1 compatibility or target frame rate is provided.

## Reference rules

Bank 0 holds the immutable acknowledged reconstructed key. Bank 1 may hold one
explicitly promoted reconstructed P frame. A normal P uses bank 1 only after an
exact content-bound publication ACK; otherwise it uses bank 0. Every reference
has an epoch, frame ID and a 128-bit reconstructed-content tag. Display RGB and
UI patches never enter the YUV predictor.

This first implementation is deliberately conservative: a key or promotion
requires **all sender pending transactions and read leases to drain**. A pending
key or promotion blocks all further preparation until feedback or a drained
expiry. Normal P transactions can overlap up to the configured window (three in
the benchmark). Thus it does not assume two banks permit arbitrary concurrent
reference replacement. More flexible bank-specific draining remains future work.

Preparing a promotion reconstructs its quantized P candidate and computes its
stored-content tag as **paid sender preparation**, including rejected candidates.
No expected-image oracle supplies that reconstruction for free. Complete cap
admission occurs before pending state, frame identity or bank reservations commit.
On accepted promotion, sender bank 1 becomes reserved/unselectable. Lost or
uncertain promotion feedback leaves bank 1 unselectable after expiry; it cannot
reuse an old bank-1 ID that the receiver may have overwritten. Bank-0 fallback
continues, and a later explicit promotion can recover. Expired key feedback
requires a new key. Ordinary P ACKs only release credits.

The receiver fully validates outer/base syntax, reference identity and reconstructed
publication tag before committing a bank. `begin()` retains an owned read lease
and private output; `complete()` releases the reader, publishes the destination,
advances decoded identity and emits AF01. `abort()` releases ownership without
publication. External read leases prevent destination overwrite. There is one
active decode and a bounded number of leases. Reordered/replayed older frames
are rejected atomically; general out-of-order display is not implemented.

Transport integration must defer sender expiry/reclamation until physical wire,
ingress, decode and feedback readers drain. These Python leases prove logical
ownership, not physical DMA/CDC timing or a remote-drain protocol by themselves.

## Wire contract

AR01 uses little-endian `HEADER = <4sBBIIBBI16s16sI` (56 bytes), followed by a
complete GM01 packet and a four-byte outer CRC32. The fields are magic `AR01`,
version 1, flags, epoch, frame ID, source bank, destination bank, source reference
ID, source tag, stored-result tag and inner byte length. Outer overhead is 60
bytes. Full cap is 49,152 bytes including both headers/CRCs and all inner bytes.

- Key flag 1: no source bank (255), no reference ID (`0xffffffff`), zero source
  tag, destination bank 0 and a nonzero stored-result tag. Key commit clears bank 1.
- Promotion flag 2: source bank 0 or 1, exact earlier reference ID/tag, destination
  bank 1 and the reconstructed result tag.
- Ordinary P flag 0: exact source bank/ID/tag, no destination (255) and zero
  stored-result tag. GM01's inner reference ID must match the outer reference.

The canonical reference tag is the first 16 bytes of SHA-256 over little-endian
`<HH width,height>` followed by C-order Y, Cb and Cr **little-endian int16** planes.
The decoded samples are in 0–255, but this Python protocol explicitly hashes the
two-byte canonical representation. Native implementations must reproduce it.

AF01 is `<4sBBIIIBI16s>` (39 bytes) plus CRC32, totaling 43 bytes. It contains
magic/version/status, epoch, frame ID, **outer AR01 body CRC excluding its footer**,
stored bank, stored frame ID and stored tag. ACK status 1 for a key/promotion must
match the actual published bank/frame/tag. Ordinary ACK and NACK status 2 use no
stored bank/ID and zero tag. The feedback CRC is separate from its frame-content
CRC field. An inner GM01 CRC cannot acknowledge the outer AR01 body. These CRCs
and hashes identify data; they are not authentication.

`identity(..., decode=False)` validates envelope/base headers, map, exact lengths
and CRCs for routing. It deliberately does not certify coefficient entropy or
successful reconstruction. The receiver pays full frozen parsing during `begin()`.

## Retained results

The campaign completed 924 actual packet attempts and 916 independent decodes
in 76.15 seconds of host wall time. Native inputs are 300 source IDs (two short
60-frame windows and 180 held-out images) repeated across three independent
profiles, hence 900 native packet attempts rather than 900 unique acquisitions.
The short windows contain 32 and 60 distinct RGB hashes; the held-out window has
180 distinct hashes. The remaining 24 attempts are two separately labeled
synthetic noise/recovery runs with eight paid cap rejections.

| Source | Raw GM01 mean bytes | AR01 immutable mean bytes | AR01 recent-8 mean bytes | AR immutable → recent active PSNR |
| --- | ---: | ---: | ---: | ---: |
| Combat, 60 IDs | 8,802 | 8,862 | 6,635 (−25.1%) | 34.020 → 34.031 dB |
| Second, 60 IDs | 12,026 | 12,086 | 8,730 (−27.8%) | 35.203 → 35.215 dB |
| Held-out second, 180 IDs | 12,283 | 12,343 | 8,798 (−28.7%) | 35.207 → 35.203 dB |

Percent changes compare the **same AR01 envelope**. Raw GM versus AR01 immutable
has exactly the 60-byte overhead and identical inner packet bytes/pixels on all
300 native inputs. All 900 native attempts fit the complete cap. Recent-reference
outputs are independently verified but are not required to be identical to the
immutable control. Their small PSNR changes demonstrate that fixed maps do not
guarantee identical distortion. These limited source windows are not a general
compression ratio or long-drift qualification.

| Source | Mean preparation, immutable → recent | Mean receive, immutable → recent | Mean full prepare + receive + feedback |
| --- | ---: | ---: | ---: |
| Combat | 19.90 → 20.27 ms | 21.10 → 18.51 ms | 41.01 → 38.79 ms |
| Second | 19.68 → 19.86 ms | 24.12 → 20.76 ms | 43.81 → 40.63 ms |
| Held-out second | 19.82 → 19.93 ms | 24.48 → 20.98 ms | 44.31 → 40.92 ms |

These preparation means include reconstructed promotion output and hash work;
seven, seven and 21 P frames are promoted in the native runs. There is one further
synthetic promotion. A cheaper residual/entropy stream reduces observed receive
work, while preparing a promoted reference adds sender reconstruction work. The
full-service column is a serial sum of measured host calls, **not** a reciprocal
FPS claim or a target pipeline schedule. Profile order rotates, but host load and
warm caches remain uncontrolled.

At 720×480, one logical 8-bit YUV420 frame contains 518,400 bytes. One actual
int16 representation here occupies 1,036,800 bytes; two retained reference banks
occupy 2,073,600 bytes per peer. Over the 180-frame held-out recent run, logical
sender reconstruction writes rise from 3,110,400 to 13,996,800 bytes because
promoted P frames must be reconstructed, and canonical tag input rises from
6,220,824 to 27,993,708 bytes. All 180 receiver outputs are reconstructed in both
arms, totaling 93,312,000 logical output bytes. The extra bank and promotion work
are real protocol costs, not omitted FPGA resources. Scratch and all other host
allocations remain outside those retained-bank figures.

Twelve tests and the read-only retained verifier pass with 13 executed-source
bindings. These are immediate-feedback algorithm results. See the parent's
separate ownership study for finite transport; its outcomes cannot be predicted
by dividing these byte counts or serial host times.

## API

```python
enc = recent_codec.Encoder(epoch=1, window=3, frame_cap=49152)
rx = recent_codec.Receiver(epoch=1, frame_cap=49152)

if enc.can_prepare(force_key=False, promote=True):
    decision = enc.prepare(rgb, frame_id, scale_map=quant_map, promote=True)
    if decision.accepted:
        task = rx.begin(decision.packet)  # parsing/reconstruction, read pin held
        displayed_rgb, info, ack = rx.complete(task)  # publication + real AF01
        enc.ack(ack)
```

`acquire(slot)` / `release(lease)` are owned physical-reader oracle hooks.
`expire(frame_id)` is a sender operation that the transport must invoke only after
its readers drain. `expected_hash(frame_id)` is an independent verification-only
reconstruction, excluded from timed preparation; required promotion reconstruction
already ran inside `prepare()`.

## Evidence and reproduction

Twelve tests pass: key/P/promotion/refresh reconstruction; inner-byte equality
with immutable GM; paid cap rejection without commit; P credit/promotion drain;
owned leases; begin/complete/abort publication; lost promotion/key ACK recovery;
outer/session/published-reference feedback binding; corruption/reference/tag
atomic rejection with failed work accounting; replay/reorder/foreign completion;
and resource bounds.

The retained benchmark compares frozen GM01 with an explicit cap-before-commit
candidate path, AR01 with immutable-key prediction (fair wrapper overhead), and
AR01 promoting every eight capture IDs. Keys occur every 30 IDs. It uses two
60-native-frame windows from one second, a 180-frame held-out window from four
seconds and separate 720×480 noise/recovery controls. This is immediate-feedback
algorithm evidence, not finite network/credit cadence. The parent's separate
ownership study evaluates transport scheduling.

All accepted packets are independently decoded, compared with expected RGB
hashes, and every retained sender/receiver YUV bank is checked sample for sample.
Full packet/inner hashes, reference IDs/tags, state snapshots, active/priority/
background MSE/PSNR and actual service times are retained. Priority rectangles
are declared test regions, not verified game HUD locations. GM/AR immutable
outputs match exactly. Recent-reference distortion can differ despite identical
quantizer maps; compare quality as well as bytes. This standalone metric compares
the original RGB888 source against RGB565-expanded decoded output. The separate
SR01 and finite-reference quality tables quantize both source and output to
RGB565 first; their MSE/PSNR values are not directly interchangeable with this table.

Preparation includes source conversion, transforms, candidate entropy, complete
packet framing and key/promotion reconstruction/tag work. Receive includes full
validation, reconstruction, color and AF01 construction. Sender AF01 parsing and
publication are separately timed. Map construction, offline file extraction/
resize, expected-image oracles, hashes/quality and bank comparisons are outside
service clocks. Profile order rotates per source ID; host load remains uncontrolled.
Sources are related precompressed 25/29.88 fps footage with duplicate content,
not live native 30-distinct-fps acquisition.

Counters ending in `reference_read_bytes` / `reconstruction_write_bytes` denote
logical **8-bit YUV420 payload** amounts. The accompanying `*_array_bytes` count
one-pass amounts for the actual int16 arrays. `tag_read_bytes` includes four
dimension bytes plus canonical int16 planes. Failed publication checks and aborted
decodes keep their work charged. These amounts exclude internal transform,
prediction, RGB, hash-copy and allocator traffic; they are not measured bandwidth.

Two retained banks are bounded, but pending promotion output, active decoded YUV,
RGB, coefficients, predictions, source arrays and temporary old/new overlap are
additional storage. Recorded retained-bank array high-water is not peak memory,
BRAM/SDRAM fit or proof of a two-buffer physical implementation.

```sh
python -m unittest -v test_recent_codec.py
python verify.py                  # read-only retained evidence checks
python benchmark.py > run.log 2>&1 # regenerates timings; external media required
```

Use `/home/lori/gamebub-streaming-prototype/.venv/bin/python` in the supplied
environment. `results.json` pins executed sources and external media; the parent
manifest pins the documentation and complete retained snapshot.

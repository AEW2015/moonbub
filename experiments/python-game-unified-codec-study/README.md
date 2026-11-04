# AR02/AF02: one residual/reference/display envelope

This Python codec preserves **720×480 coded video**, 720×405 active native game
content and the 30 fps product target. Unlike v14's separate studies, AR02 carries
selected GM01/SR01 residuals and optional HP01/HR01 exact display patches in one
content-bound frame. Two acknowledged reconstructed YUV banks use the overlapped
promotion/key-bank-continuity policy. No installed Sunshine mode, ESP32 decoder,
FPGA implementation or physical frame-rate proof is supplied.

## Coding and admission

Each preparation performs one prediction/analysis and three forward transforms.
The GM candidate supplies the quantized coefficients. In `exact` mode, those same
coefficients feed SR's zero/DC/full-block syntax; already serialized GM dense CP02
payloads are reused byte for byte. The alternative split map/DC/full-block stream
is actually serialized, and every losing candidate is paid. The chooser compares
the complete inner packet including all plane headers and CRC. Ties choose GM.
Thus SR's dense-only header penalty cannot increase the selected base packet.

`gm` evaluates only GM. `prune2`/`prune4` evaluate GM and a bounded pruned SR
candidate. Pruning runs only on P frames, pays actual inverse/error comparisons
and preserves scale-8 priority blocks plus the frozen bilinear chroma halo.
The error bound is against quantized GM under **the same selected reference**,
not the original source or a different reference history. GM fallback is exact;
choosing pruned SR is explicitly lossy. No future source or quality oracle selects
the live mode. Keys are never pruned.

After choosing the smaller base, the optional UI plugin receives the remaining
complete-frame byte budget. It can admit up to four priority patches. The core
validates every returned patch and its actual current source RGB565 words before
committing pending state. The final 49,152-byte cap includes every header, length
prefix and CRC. A faulty callback that ignores the budget still cannot commit
an over-cap frame. Callback failure or cap rejection changes no bank reservation,
frame identity or pending credit. Valid UI-cache data may remain cached on the PC.

The minimum guarantee is for the **base inner**, not a comparison of complete
outer packets with different UI coverage. A smaller base can admit more exact UI
pixels and therefore produce a larger but higher-coverage final frame. Retained
rows record selected regions/pixels and every attempted candidate.

## References, display and feedback

Bank 0 holds the acknowledged key; bank 1 holds a tagged reconstructed P. Only
confirmed bank/frame/tag identities can predict a frame. A bank-1 replacement
waits for its pending consumers and read leases, while key-bank consumers may
continue. During drain or uncertain promotion, new P frames use bank 0. Full keys
drain all consumers. Lost publication feedback leaves bank 1 unusable and permits
key-bank continuity; stale or mismatched AF02 cannot resurrect it.

Preparing a key/promotion reconstructs the **selected** GM/SR YUV and hashes it
as paid encoder work. Reference tags never hash patched display RGB. Encoder and
receiver use the same exact zero/DC inverse bypass in every coding mode, so SR
is not credited with that unrelated decoder optimization.

Receiver `begin()` validates all outer/inner syntax and every UI patch before
acquiring a source lease or returning a private reconstruction. `complete()` alone
publishes a destination bank, advances decoded identity and emits AF02. `abort()`
releases the owned lease without publication. Exact source RGB565 patches affect
only returned display pixels. When patches exist, the display follows the existing
RGB565-expanded contract; otherwise base RGB888 is preserved. Neither patching nor
display quantization modifies the reconstructed YUV bank.

The surrounding finite model must retain physical ingress/read owners and stage
publication through paid completion. These single-threaded Python APIs do not
prove native concurrent memory service or transport-drain signaling.

## AR02 and AF02 wire contract

AR02 uses `<4sBBIIBBI16s16sIBI`, a 61-byte little-endian header, then a complete
GM01 or SR01 packet, the patch section and a four-byte outer CRC32. Fields are
magic `AR02`, version 2, reference flags, epoch, frame ID, source bank, destination
bank, source reference ID, source tag, stored-result tag, inner byte length,
patch count and patch-section byte length. Base envelope overhead is 65 bytes.
The validated inner magic identifies GM01 or SR01; unsupported dispatch is rejected.

Reference flags remain 0 ordinary P, 1 key and 2 promoted P. Key uses no source
bank/ID/tag and stores bank 0. Promotion names the exact source and stores bank 1.
Ordinary P has no destination/result tag. Inner epoch/frame/reference/key identity
must match the outer identity, and vectors remain zero. Inner SR prune flags are
separate from the outer reference flags. Each patch is a little-endian u32 byte
length followed by a complete HP01/HR01 packet. Count is at most four, exact
lengths and non-overlap are mandatory, and the outer CRC covers all UI bytes.

AF02 is the 39-byte `<4sBBIIIBI16s>` header plus CRC32, totaling 43 bytes. Magic is
`AF02`, version 2. It binds epoch/frame and the **outermost AR02 body CRC**, plus
the actually stored bank/frame/tag for key/promotion ACK. Ordinary ACK/NACK carries
no stored publication. An AF01 or an ACK covering only the GM/SR inner is rejected.
Canonical YUV tags are the first 16 SHA-256 bytes over `<HH width,height>` and
C-order Y/Cb/Cr little-endian int16 samples. CRCs/tags are identity checks, not
authentication or a negotiated installed peer mode.

`identity(decode=False)` validates framing, base headers/maps/lengths and CRC for
routing. It does not certify coefficient entropy or UI payload decoding. Receiver
`begin()` pays the complete chosen parser and all patch validation before publish.

## Retained component results

The campaign has 328 source/cohort IDs and **1,020 actual decisions**: 900 native
base decisions, 48 native UI-key decisions and 72 synthetic decisions. There are
1,002 admissions and 18 paid synthetic noise rejections, completed in 111.42 seconds
of host wall time. Profiles run in rotating order, with uncontrolled host load.
The two related source clips are precompressed 25/29.88 fps footage, not live
30 Hz capture. Repeated profiles/cohorts are not independent unique acquisitions.

| Native base window | GM-only mean bytes | Exact GM/SR minimum | Prune-4 policy |
| --- | ---: | ---: | ---: |
| Combat, 60 IDs | 6,640.30 | 6,326.15 | 5,455.87 |
| Second, 60 IDs | 8,734.90 | 8,646.27 | 7,453.28 |
| Held-out second, 180 IDs | 8,803.23 | 8,727.29 | 7,650.80 |

Exact inner selection saves 4.73%, 1.01% and 0.86% respectively. On the second
and held-out windows it selects raw GM for 20/60 and 64/180 frames, avoiding the
old SR header regression. All 300 native GM/exact controls have identical source
IDs, current reference bank/ID/tag, base/display RGB hashes and source-quality
metrics. Every one of 45 stored key/P tags is identically observed as the next
P's selected source; the supplemental unit also compares cross-profile YUV arrays.
[matched-exact.json](matched-exact.json) and `analyze.py --check` preserve that
independent retained-data comparison without changing any timed source.

| Native base / policy | Complete preparation | Complete receive |
| --- | ---: | ---: |
| Combat GM / exact / prune-4 | 21.74 / 23.41 / 33.22 ms | 16.05 / 13.82 / 9.22 ms |
| Second GM / exact / prune-4 | 19.74 / 22.50 / 32.95 ms | 18.45 / 17.24 / 11.66 ms |
| Held-out GM / exact / prune-4 | 19.70 / 22.63 / 33.33 ms | 18.88 / 17.67 / 12.29 ms |

Exact selection adds real host work despite sharing analysis and dense CP02
payloads. Pruning saves more bits and receive work but pays substantial host
inverse/error checking; complete service is not universally faster. Source active
RGB565 MSE for GM→prune-4 is 20.597→19.705, 14.773→16.058 and 14.560→15.813.
Prediction history can differ after pruned promotion. Same-reference local error
bounds do not imply equal source distortion or a universal quality improvement.
Metrics quantize both source and decoded output to RGB565.

There are 84 UI attempts and 75 admissions, including nine noisy UI rejections.
All admitted UI rows select 21,120 original-source words, totaling **1,584,000
exact checked RGB565 words**. Native UI-key combat mean frames are
34,257.12→34,084.38 bytes for GM→exact; second-source UI keys both use 27,542.38
bytes due to GM fallback. Those keys are never pruned. Synthetic temporal UI
rows additionally exercise actual pruned P bodies and overlay/reference separation.
No source-word mismatch is found. Configured rectangles are declared priorities,
not independently confirmed real game HUD locations.

All 10 tests pass: dispatch/shared analysis/whole-inner fallback, key/P/promotion
and refresh reconstruction, partial geometry, pruning/halo bounds, UI source
word/tag independence, malformed UI atomicity, final-cap rejection, every feedback
binding, leases/lost-ACK fallback and supplemental cross-profile YUV exactness.
The nine original tests and all timed sources remain byte-identical to their
recorded pins; the extra unit and analysis are explicitly untimed additions.

## Reproduction and limits

```sh
python -m unittest -v test_unified_codec.py test_exact_reference.py
python verify.py                       # retained numerical/source checks
python analyze.py --check              # cross-profile exactness and stored tags
python benchmark.py > run.log 2>&1     # regenerate timings; external media required
```

Use the project study virtual environment. Preparation includes UI callback,
validation, losing candidates and promotion reconstruction/tag work. Receive
includes chosen parsing, reconstruction, base hash, display patching and AF02
construction; encoder feedback application is measured separately. Maps, source
BOX/offline acquisition, expected-image oracles, comparison hashes and quality
metrics are outside these component clocks. The finite study charges its own
preprocessing and transport and must not simply add these averages.

Two retained reference banks exclude pending promotion reconstruction, GM/SR
coefficient candidates, raw transforms, prediction/RGB output, UI/source/cache and
packet-copy storage. This is not peak physical memory or FPGA resource proof.
These component immediate-feedback results do not measure GF02 queues, RF/QSPI,
SDRAM/CDC, native execution, display hardware or sustained physical 30 fps.

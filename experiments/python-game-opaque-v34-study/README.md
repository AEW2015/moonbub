# Opaque-HUD source formation, causal custom and native comparison

The requested full Y/Cb/Cr rectangle mask is **not visibly equivalent** with
the frozen color conversion: all 96 source frames change visible RGB565 words
outside the exact HUD (546–934 words/frame). Even 2x2 alignment does not prevent
this. The chroma upsampler interpolates from the right and below, so a rectangle's
first chroma row and column affect RGB just above and left of that rectangle.
Every source retains this negative result and the full-mask input hash.

The tested safe variant sets all Y samples inside the four exact HUD rectangles
to 128 and sets Cb/Cr interior samples to 128 **while preserving each rectangle's
first chroma row and column**. No plane sample outside a rectangle changes.
All 96 sources pass both exact RGB8 equality outside the rectangles and exact
RGB565 equality after the opaque HUD overlays. This is a host source-formation
change; the decoder syntax and picture dimensions stay unchanged.

The safe source mask yields a modest byte/quality tradeoff in the causal custom
controller. Its quality becomes slightly worse relative to the original-source
control; visible equivalence before lossy coding does not imply equal
reconstruction after transform coding and changed reference histories.

| 48-frame scene | Original CP34/HX33 control bytes | Masked CP34/HX33 bytes | Saving | Original MSE | Masked MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mass-effect-2600` | 441,224 | 426,409 | 14,815 (3.36%) | 14.386886 | 14.565884 |
| `mass-effect-7200` | 1,068,678 | 1,036,896 | 31,782 (2.97%) | 26.303889 | 26.572316 |

MSE rises 1.24% and 1.02%, respectively. Every metric compares against the
**original RGB source after exact HUD overlay**, never against a masked target.
All selected complete custom frames fit 49,152 bytes; maxima are 24,502 and
42,376 bytes. The comparison uses actual root `controller-v34` control packets,
with the same HX33 HUD and 60-byte binding. Earlier v33 HU25 complete totals are
retained only as historical fields; they cannot establish masking savings.
The baseline accounting was corrected after encoding without changing any
produced packet, native AU, reconstruction, quality metric or causal history.

Same-processed native encoders remain substantially smaller at better quality.
These are exact frozen standard-v24 low-delay PyAV settings, with actual
access units, extradata once at frame 0, the same actual HX33 bytes, and a
60-byte binding cost per frame:

| Scene | Safe masked input codec | Quality parameter | Complete accounted bytes | Original-source MSE |
| --- | --- | ---: | ---: | ---: |
| 2600 | HEVC/libx265 | 32 | 239,942 | 11.526840 |
| 2600 | AV1/libsvtav1 | 48 | 222,522 | 12.487713 |
| 7200 | HEVC/libx265 | 28 | 606,337 | 22.048210 |
| 7200 | AV1/libsvtav1 | 38 | 592,829 | 20.222133 |

Twelve full native runs retain the original and masked anchor per codec/scene,
plus both masked quality settings (HEVC 28/32, AV1 38/48). The stronger bracket
already meets or exceeds custom quality, so no additional settings were needed.
On scene 7200 the weaker masked HEVC32/AV148 settings have MSE 30.1270/30.6340
and do not match custom quality; they are retained and labelled accordingly.
Original versus masked anchor bytes are HEVC32 238,738→239,942 and AV148
222,451→222,522 on scene2600, and HEVC28 606,532→606,337 and AV138
601,387→592,829 on scene7200. Masking therefore does not uniformly help native
codecs either. There is no bitrate-parity claim.

All 576 native AUs decode with exact PTS/DTS 0..47, keys 0/24, one AU emitted
per input call and one immediate decoder output per AU, with no flush-only
packets or frames. Options, library versions, encode/decode calls, timings,
actual AU/extradata archives, metrics and hashes are retained. The 60-byte
native binding is cost accounting; these are not native CP34 packets or a
Gamebub HEVC/AV1 hardware decoder implementation.

The custom cohort uses unchanged shared incumbent/strict-band encoders,
zero and half32 motion choices, and strict selection at background 16 then 32.
All 376 candidates are actually serialized, scored against original RGB,
bound to HX33, archived, and replayed. Keys are 0/24. Each scene maintains its
own previously accepted **masked reconstruction** as the next reference.
Selected GM27 pictures travel in actual CP34/HX33 packets through the root
atomic receiver and produce exact JA34 ACKs. Invalid or missing HUD cannot
publish the base. The test corrupts an inner HUD while repairing the outer CRC
and SHA, verifies rejection without state change, and then accepts the valid
masked key packet.

Mask formation copies 518,400 logical eight-bit samples per source and writes
30,712 constants: 21,120 Y plus 9,592 chroma. The common Python source uses
int16 arrays, so each source and additional masked-plane set occupies
1,036,800 array bytes, versus 518,400 logical uint8 bytes. The mask adds no
decoder format/state bytes and does not eliminate picture processing for the
covered pixels. Source masks, equivalence proofs, fixture conversion, archive
IO and HUD preparation are excluded from encoder policy clocks. The measured
custom policy means are about 227.37 and 320.59 ms/frame, including all paid
analysis, shared encodes, metrics and binding. `offline_mask_cost.json` retains
one separately timed postcampaign mask-only sample per source, including
copies/stores, so its cost remains visible without mixing it into those clocks.
Native call timings similarly exclude source preparation and archive work.
No end-to-end 30fps, RSS, physical memory, FPGA fit or hardware claim follows.

Offline decoded coefficient analysis directly measures inverse shortcut
opportunities. Every frame still has exactly 8,100 8x8 coefficient blocks:

| Scene and cohort | Zero blocks | DC-only blocks | General blocks |
| --- | ---: | ---: | ---: |
| 2600 original | 319,767 | 18,217 | 50,816 |
| 2600 masked | 327,084 | 16,734 | 44,982 |
| 7200 original | 246,345 | 21,397 | 121,058 |
| 7200 masked | 257,017 | 20,332 | 111,451 |

Replaying the frozen two-bank inverse-component dependency model gives mean
6.20048→6.08656 ms and 7.39291→7.23460 ms **if an unclosed 100 MHz clock is
assumed**. This model excludes entropy, reference reads, color conversion,
HUD, CRC, transport and display. It is offline analysis outside encoder clocks,
not a native frame-rate estimate or new hardware result. Per-frame counts,
cycles and schedule source hash are in `offline_coefficients.json`.

`results.json` retains source/producer pins, both complete causal cases, every
attempt, source and masked hashes, full-mask negatives, source-quality metrics,
native runs, and accounting scope. Replay/test files are excluded from the
mid-campaign producer-stability assertion so a verifier repair does not require
encoding again; final full pins include them. Recorded metadata distinguishes
the original numeric producers from the final accounting/replay changes.
`verify.py` independently checks all 96 visible-source equivalences and causal
histories, every 376 actual custom candidate, all ACKs and original-source
metrics, root-control same-HUD accounting, and all 576 native AU decodes. It
also reproduces 1,555,200 selected/control coefficient classifications. Two
tests cover the chroma-border failure/safe support, input ownership and invalid
geometry, plus atomic rejection of malformed/missing HUD.

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY experiments/python-game-opaque-v34-study/benchmark.py
$PY -m unittest discover -s experiments/python-game-opaque-v34-study -p test_model.py -v
$PY experiments/python-game-opaque-v34-study/verify.py
```

# V41 combat peak-rate controls: the coarse-grid gap closes

This targeted follow-up tests 21 native encoder configurations on exactly the
same 100 combat canvases, common YUV420 input and exact HX33 HUD bytes as v40.
Every actual access unit is retained and independently redecoded. All 21 points
succeed as low-delay encodes; eight have at least one complete-frame cap failure.
There are 2,100 additional actual native access units, not 2,100 new source frames.

The source is precompressed 25-fps low-resolution combat footage upscaled to the
fixed 720×480 canvas. Nominal encoder timestamps are 1/30; original timestamps
remain attached. This does not establish distinct 30-fps capture or hardware FPS.

## Measured settings and explicit quality gates

All points retain frozen v24 single-thread x265 ultrafast / SVT-AV1 preset8,
lookahead0, B0, keys24 and full-range color settings. The experiment adds:

* HEVC CRF22/24/26 × VBV buffer160/200/240 kbits at maxrate4000 kbps, init1.
* AV1 CRF34/37 × mbr3000/4000/5000 kbps, mbr-overshoot-pct0.
* AV1 CBR3000/4000/5000 kbps × buffer40/60 ms with equal initial/optimal size.

The [x265 CLI documentation](https://x265.readthedocs.io/en/stable/cli.html)
defines the paired VBV buffer/maxrate controls. The
[SVT-AV1 parameter reference](https://github.com/AOMediaCodec/SVT-AV1/blob/main/Docs/Parameters.md)
documents capped CRF, CBR and buffer parameters. These are requested encoder
settings, not a proof of a per-frame packet bound. The installed backend consumed
all options; actual complete packet sizes determine admission. The tested AV1
capped-CRF requests produce identical bytes for each CRF across all three mbr
values and retain cap failures; no useful effect is claimed for those controls.

Complete bytes charge actual AU + actual selected HX33 +80 modeled binding bytes
+ actual extradata on frame0. The same display converter and original RGB565 error
metric apply to every native output. The 80-byte native binding is accounting,
not an implemented native wire extension. Both encode and decode must emit the
current frame immediately; no frames appear only at flush.

| Setting | Total complete bytes | Mean active MSE | Peak frame MSE | Max packet | Cap failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| Custom CS38 | 3,002,785 | 29.3515 | 35.0413 | 44,032 | 0 |
| HEVC CRF24, VBV160 | 2,098,348 | 27.5797 | 37.9845 | 40,122 | 0 |
| HEVC CRF22, VBV160 | 2,362,563 | 23.9478 | 33.1654 | 40,122 | 0 |
| AV1 CBR3000, buffer40 | 2,025,584 | 25.8078 | 40.9632 | 39,559 | 0 |
| AV1 CBR4000, buffer40 | 2,302,669 | 21.7033 | 33.1352 | 45,038 | 0 |
| AV1 CBR5000, buffer40 | 2,564,186 | 19.2493 | 28.6682 | 49,132 | 0 |

The lower-byte mean-quality winners do not satisfy the peak-error gate. HEVC
CRF22/VBV160 uses 21.3209% fewer complete bytes than custom and has no worse SSE
on **every one of the 100 frames**, while fitting the cap. Thus the coarse-grid
combat gap does not establish custom compression superiority, even under the
strong every-frame quality gate. No tested AV1 point passes that every-frame gate;
its CBR4000 point passes mean and peak. These are measured, targeted sampled points,
not exhaustive optimized encoder frontiers or equal-FPGA-resource comparisons.

The most aggressive passing AV1 case has only 20 bytes cap margin; that is not a
safe production margin or a guarantee on other content. All passing and failing
settings are archived rather than selecting only a favorable example.

## Replay

```sh
python benchmark.py             # regenerates all actual encodes
python verify.py                # independent AU decode and accounting, no encode
python ../compare_native_cap_v41.py --check
```

The verifier checks source pins, source formation, all HUD words, every decoded
hash/error, actual lengths/caps, frame/key ordering, immediate output and summary
totals. This is dataset qualification of existing native codecs, not a new codec
unit-test suite. No Sunshine installation, ESP32 firmware, FPGA RTL or physical
board is changed. The useful application-specific work remains bounded decoder
cost and memory, exact UI treatment and end-to-end latency; lower bits than HEVC
or AV1 have not been demonstrated.

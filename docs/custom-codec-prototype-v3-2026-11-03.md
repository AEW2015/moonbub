# Custom codec iteration3: coefficients, compressed stripes and motion

This preserves iteration3. [Iteration4](custom-codec-prototype-v4-2026-11-03.md)
couples actual re-encoding to capture/ACK timing and evaluates bounded overlap
and quality backoff, including failures absent from these short packet tests.

This continues the [codec plan](codec-development-audit-plan.md) and
[previous prototype report](custom-codec-prototype-progress-2026-11-03.md).
It implements the three next software steps: better coefficient coding,
byte-driven stripe reconstruction and reconstructed-reference prediction.
These are executable Python formats/models, not installed Sunshine modes,
ESP32 firmware, FPGA decoders, target-fit evidence or physical FPS results.

## Results

| Step | New evidence | Outcome |
| --- | --- | --- |
| DC/AC contexts | [CP02/FT02](../experiments/python-coefficient-study/README.md),144 exact-pixel frame roundtrips | 19–52.4% fewer wire bytes than FT01; independent JPEG still wins rate/quality |
| Compressed stripe decoder | [SS01](../experiments/python-stripe-study/README.md),48 actual-byte decodes, arbitrary chunking and late-CRC rejection | Exact FT01 pixels;23,040 bytes retained sample payload, with other workspace counted separately |
| Temporal/global motion | [MT02](../experiments/python-motion-study/README.md), actual packets, committed references and epoch-bound ACKs | Promising temporal sample rates below JPEG; no real-time/network proof |
| Feedback capacity | Serial stop-and-wait length-trace schedule | Feedback/serialization can reduce cadence; this schedule is not MT02 playback |

There are **34 new passing tests**: seven coefficient, seven stripe, and
twenty motion/corpus/feedback tests. They include invalid-input/fault cases.
Normal MT02 profiles reconstruct1,080 packets exactly to the host golden;
four fault campaigns additionally commit112 of120 attempts and recover to
their final ID29. Failed/lost data are counted rather than accepted as video.

## Independent coding and byte-driven stripes

CP02 separates row-reset DC differences from AC coefficients, with bounded
Rice codes, three AC frequency contexts, EOB/ZRL tokens, RAW fallback, exact
counts and CRC. Its coefficient helper supports whole planes or stripe
regions. The largest positive DC delta4096 is handled without escape overflow.
Arithmetic, quantization and reconstructed RGB remain identical to FT01.

On exactly12 matching frames per primary window at scale16, FT02 improves
combat from9.754 to7.542 Mb/s and the second clip from7.599 to4.307 Mb/s.
JPEG q50 is5.969/3.540 Mb/s at nearly equal PSNR. All144 sampled FT02 frames
fit48 KiB, maximum39,427 bytes; general RAW fallback still exceeds256 KiB.

SS01 sends Cb/Cr before the corresponding16 luma rows. Receiving the next
chroma region provides bilinear lookahead and permits the previous Y stripe
to emit. It stages at most one bounded compressed region, validates each
region's CRC/order, and keeps provisional output confined to a caller-owned
back buffer. Only explicit `finish()` after the complete frame CRC commits.
Corruption after every provisional row was emitted still cannot commit.

The actual retained decoded-sample peak is23,040 bytes, **not** the earlier
18,000-byte oracle. Separate maximum coefficient arrays are23,040 bytes and
int64 IDCT input92,160 bytes; other Python temporaries/copies, output stripe
and full provisional framebuffer are separately disclosed. The largest actual
compressed staging in these samples is3,651 bytes; the declared RAW region
bound is23,070 bytes plus its saved header. This is not a23 KiB total decoder
or a target BRAM utilization report.

Extra region headers/CRCs/context resets cost rate: primary SS01 scale16 is
8.323/5.153 Mb/s at the same frozen pixels. It has not earned a JPEG byte-size
advantage. Its potential receive/decode overlap is a separate schedule/latency
experiment, not established by the Python wall timings.

## Temporal candidate

The motion corpus uses30 consecutive native decoded frames per window,
starting at1 s and4 s from each of two precompressed Mass Effect clips. Unique
image counts are19/30 and30/30 in the primary windows,21/30 and30/30 held out.
Native rates are25/29.88 fps; there is no interpolation or manufactured native
30 fps capture. Adjacent windows are limited held-out evidence.

Each normal temporal profile includes one key and29 P frames. The predictor
uses the exact ACKed reconstruction, with bounded even global vectors and
explicit replicated borders/chroma rules. Host and receiver agree after every
successful complete-frame decode. Timeout invalidates the host reference and
forces a new key, including lost ACK after receiver commit. Stale/previous-
epoch ACKs, replay, missing refs, malformed vectors, corruption and reset
conditions are tested. No wire feedback, physical drain or device protocol
is implemented.

| Exact30-frame window | MT02 temporal scale8 Mb/s / PSNR | Receiver JPEG q80 Mb/s / PSNR |
| --- | --- | --- |
| Combat primary | 1.697 /35.87 dB | 8.345 /36.19 dB |
| Second clip primary | 2.219 /36.23 dB | 5.419 /36.42 dB |
| Combat held-out | 2.745 /35.89 dB | 7.095 /36.30 dB |
| Second clip held-out | 2.635 /36.11 dB | 5.458 /36.29 dB |

Rates project actual packet sizes to hypothetical30 fps and include the same
40-byte application/28-byte IPv4-UDP envelope per1,024-byte chunk. RF/link
framing, retry, ACK, audio/input and capture/queue time are excluded. PSNR
pools active-content RGB565-output MSE. Temporal images differ from JPEG and
independent transforms; this is not an identical-pixel or perceptual-quality
comparison. Savings of roughly52–80% versus q80 at0.18–0.41 dB lower PSNR
justify further research, not automatic RTL selection.

Most real-clip vectors are zero; at scale16 only one held-out combat frame
uses nonzero global motion. The gameplay gain is mainly temporal residual
coding. A separate deterministic720×480 pan diagnostic selects(-4,0) on all
nine dependent frames and reduces mean dependent packets from9,743 to4,616
bytes compared with zero vectors. That isolates a working motion method but
is synthetic, not evidence from a fast camera pan in a game.

All sampled MT02 packets fit48 KiB. General coefficient fallback is larger,
and the offline packet benchmark does not enforce device cap admission.
Fault campaigns lose data at7, lose ACK after commit at17, and corrupt23;
keys at8/18/24 recover, with28/30 commits and final ID29. Fault PSNR covers
only committed frames and is not compared to full-corpus JPEG.

## Unclosed timing and memory gates

MT02 has one outstanding transaction and immediate ACK in its codec benchmark.
It does not demonstrate30 fps. A separate serial capacity schedule on fixed
JPEG lengths gives combat25.18 IDs/s with zero extra ACK delay,20.12 with10 ms
and16.74 with20 ms. This is decode completion, with no vblank stage. It is
not MT02 FPS: P packets are smaller and skipped inputs change the next residual
size, so the actual codec must be exercised inside a timing/feedback model.

At720×480, logical YUV reference reads/writes plus RGB565 writes and a60 Hz
scan total92.7936 MB/s at30 fps with one key in30, before compressed traffic,
color rereads, copies, overfetch, refresh and arbitration. Python reference
arrays alone are1,036,800 bytes each because they use int16. The full-frame
MT02 code is not integrated with SS01's stripe layout; their buffer claims
must not be combined. Physical memory service/allocations are unqualified.

## Next work

1. Couple native capture slots, actual MT02 re-encoding, feedback delay/loss,
   cap/age admission and independent refresh. Preserve bounded refs and
   epoch-bound commit ACKs; measure phase/jitter/strict-window counts and age.
2. Extend to longer, more varied scenes and fresh native30 fps captures,
   including cuts, real pans, HUD text and particles. Compare actual temporal
   artifacts and agreed visual quality, not only PSNR on compressed inputs.
3. Prototype bounded in-flight reference lifetimes if stop-and-wait limits
   cadence. Explicitly charge reference memory and test delayed/lost/duplicate
   ACK, session replacement, timeout/drain and stale data.
4. Combine the selected coefficient/temporal format with byte-driven stripe
   reconstruction and a real memory-service schedule. Measure whether extra
   headers buy useful decode overlap. Only then consider bounded block motion,
   regional quantization or other host/FPGA-specific refinements.
5. Select one candidate before RTL/firmware changes. Require rate/quality,
   finite storage, feedback/recovery, target fit and actual service evidence.
   Preserve current JPEG as the hardware control while this research proceeds.

All scripts, result manifests and logs are on the study branches. The
[final source/result snapshot](prototype-v3-provenance.json) records this
iteration; it does not replace component-specific start/end checks or imply
hardware qualification.

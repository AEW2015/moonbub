# Iteration26: exact bit counting, sparse-band entropy and fractional prediction

V26 advances three parts of an application-specific Gamebub codec while
preserving720×480 coded /720×405 active video and all21,120 exact RGB565 HUD
words. The results are separate experiments: their percentage gains must not
be multiplied or presented as one merged codec.

## Results on the retained gameplay windows

Complete-body rates project actual encoded bytes to30IDs/s. These are offline
compression results, not a measured physical frame rate. The same96 original
source images from v25 are reused; the footage is precompressed29.88fps.

| Window | V25 CP25 | EC26 block-major, identical pixels | Fractional causal chooser |
| --- | ---: | ---: | ---: |
|2600 |3.160445Mb/s |2.859025Mb/s |2.904850Mb/s |
|7200 |6.864830Mb/s |6.328330Mb/s |6.445595Mb/s |

The exact entropy change saves **9.54% /7.82%** complete bytes and **18.94% /
14.37%** base bytes, with identical quantized coefficients, reconstructed
references, displayed RGB565 hashes and MSE14.38366 /26.89721. All its192 actual
CP26 transactions fit49,152bytes and preserve4,055,040 requested HUD words.

The fractional experiment uses a different prediction history and wire format.
It saves **8.09% /6.11%** complete bytes while improving measured mean image
error to approximately14.0409 /26.4217. All96 accepted CP2F transactions fit
the complete cap. The decoder consumes only transmitted vectors/residuals and
actual reconstructed reference banks. This is not a lossless comparison against
v25: its decoded base pixels intentionally differ.

At the same improved HUD cost and sampled MSE thresholds, frozen low-delay
HEVC/AV1 software controls still need about1.751/1.669Mb/s on2600 and
3.838/3.812Mb/s on7200. EC26's body therefore remains approximately **1.6–1.7×**
larger. Native controls have lower MSE than these custom points, not matched
quality. No HEVC/AV1 decoder, compatibility or coding-efficiency parity is claimed.

## Exact host optimization: remove packet construction from RDO probes

V25's lossy SKIP controller constructed a complete CP02 packet for each eligible
block merely to measure its byte length. The new counter analytically computes
the exact same length, including chosen Rice parameters, escape paths, DC/AC
padding, headers, raw-mode tie and CRC size. Vectorized isolated-block counting
does not construct packets or bitstrings.

| Paired Python work, mean per source | Frozen path | Counted path |
| --- | ---: | ---: |
| Encode-prepared, all attempts paid |359.50ms |39.67ms |
| Shared analysis plus all attempts |374.51ms |54.69ms |
| RDO stage |334.22ms |14.34ms |

The encode-prepared speedup is9.06× in this interleaved paired trial. All96
source decisions and97 fine/coarse attempts retain byte-identical GM25 packets,
coefficients and reconstructed planes.186,289 logical probe packets /6,341,290
bytes are counted without constructing them.4,096 actual gameplay coefficient
blocks and24 whole-plane packets separately verify exact length parity;
the isolated counter batch is56.69× faster than constructing those packets.

These are host Python measurements under ordinary concurrent work. They are
not C++/ESP32/FPGA clock measurements or a whole-stream speedup.54.69ms already
exceeds33.33ms before adding HUD, transport and presentation. Native integration
still needs measurement. The existing GM25 wire need not change for this tool.

## EC26: a coefficient code tailored to sparse residuals

The new syntax codes row-reset DC differences and three sparse AC bands. Runs
cross block boundaries; nonzero counts terminate each band without CP02's
per-block end markers. Bounded Rice codes carry zero runs and signed levels,
with actual header/padding/CRC/raw-fallback costs. The encoder constructs real
candidate packets and retains a frozen plane when the new code is not smaller.

GE26 keeps the old prediction, quantization, maps and output tags, adding a
distinct coefficient-plane dispatch. CP26/JA26 bind that new frame with the
unchanged actual HU25 packet. This is a real new laboratory wire grammar and
decoder, rather than subtracting hypothetical bytes from a size estimate.
Existing CP25/AR03/native peers do not implement it.

Block-major bands permit a bounded four-cursor decoder: one DC reader, three
AC readers with bounded lookahead and one128-byte coefficient block before the
existing Q14 inverse transform. A separate Python iterator now reproduces every
block against the full-plane decoder and retained coefficients. It retains the
compressed packet and validates completion before publication. This is an
algorithmic memory/control proof, not FPGA RAM use, port arbitration or timing.

Allowing frequency-major bands reduces the body only another0.004065 /
0.002995Mb/s in these clips. That ordering needs full-plane coefficient staging
or extra indexing/read scheduling to produce raster blocks. Prefer block-major
for the next FPGA prototype until that small saving justifies the memory cost.
The fixed8×8 transform preserves the existing DSP-oriented arithmetic oracle;
entropy readers add control work rather than replacing the inverse transform.

## Fractional prediction: compact metadata makes the tool useful

GM26 version2 predicts half-luma-pixel positions with explicit integer bilinear
rounding and edge clamping. Chroma uses the corresponding quarter-chroma grid.
Search refines a bounded coarse result; the receiver performs no pixel motion
estimation. The Python parser does re-encode motion-map alternatives to require
the smallest canonical representation. That work is included in measured
receiver time; a hardware profile must either budget it or separate bounded
syntax validity from the encoder's rate-optimal representation policy.
Scalar oracles check negative coordinates, partial blocks and chroma rounding.

The early16-pixel trial lost bytes because dense motion maps cost2,701bytes/P.
The compact grammar adds12-bit packed vectors and row/median-predicted signed
delta Rice codes, selecting actual smallest representations. Predictor state
uses bounded previous/current vector rows; decoder state and all metadata are
part of the profile. Every losing encoder representation/search is paid.

Unconditional half32 improves rate but slightly worsens mean error on the
12-frame closed-loop probes. The full48-frame controller therefore constructs
zero and half32 candidates on the **same currently accepted reference**, then
selects half only if its actual complete packet is smaller and its current
expanded-RGB565 active-area SSE is no worse than that zero candidate. The guard
uses only the current source, not future frames. Subsequent references come
from the selected actual decoded/ACKed image.

The full experiment uses a distinct CP2F/JA2F binding with actual HU25 bytes.
Fine-key overflow retries background32 without raising the cap, pays both
attempts and regenerates following P frames from the accepted coarse key.
Half32 wins43/48 decisions in each window; keys and rejected candidates use zero.
No rule guarantees the same outcome or MSE on unseen footage.

Fractional search and repeated candidate construction remain expensive Python
work: the full paid build means are about652/676ms per frame, including losing
candidates. Bilinear P prediction executes2,073,600 modeled reference-sample fetches
per frame, compared with a one-tap predictor's518,400 samples. Real memory burst
reuse, SRAM banking, DSP scheduling and shared scanout arbitration are unproved.
The source-side SSE guard and exhaustive search are not receiver hardware work.

## What to carry into the application-specific codec

1. Port the exact counter first: it changes host work while preserving current
   wire bytes. Keep the paired coefficient/packet goldens as acceptance tests.
2. Implement EC26 block-major readers feeding the existing integer inverse/DSP
   path. Retain fixed capacity, source/reference identity and output-tag checks;
   do not release a framebuffer until full parsing and writes finish.
3. Combine compact fractional vectors and EC26 in **one negotiated profile**,
   with one coherent parser/reset/credit/publication contract. Re-encode and
   decode the combined stream; these independent wins cannot be added for free.
   Keep range/escape/padding checks, and qualify removing receiver-side
   representation re-encoding before claiming a lightweight map decoder.
4. Replace expensive host searches with bounded GPU/native work only after
   bit-exact tests. Measure actual sustained-rate control, packet credits,
   feedback dependency, memory service, input/audio and recovery together.
5. Qualify at least1,800 fresh distinct30fps captures and a later10-minute board
   test. Keep JPEG and the v20 hardware handoff available until native/RTL,
   compiled resources/timing and physical presentation meet the gates.

## Reproduce

All35 current unit tests pass:6 counter,10 prediction/controller,9 entropy and
10 independent-audit tests. Retained replay checks96 counter sources/97 attempts,
192 compact plus144 early prediction probes,96 accepted fractional frames with
189 paid attempts, and192 exact entropy frames. These reuse96 source images.
The audit independently checks actual packet/ACK bounds, byte and MSE sums,
candidate eligibility, reference identities and same-HUD standards costs;
decoder pixel and block-stream checks run in the separate replay helpers.

```sh
python experiments/verify_prototype_v26.py
```

The inventory freezes prior v25 code/results, new sources, retained packet
objects, test logs and experiment snapshots. Offline helpers recheck counter
parity, early/compact prediction, the full causal chooser, EC26 block streaming,
exact source pixels/tags and independent byte/rate/threshold accounting. Source
videos need not be downloaded again. Python and the inherited NumPy/Pillow
environment are required. No native Sunshine, ESP32 firmware or FPGA bitstream
is installed by these experiments.

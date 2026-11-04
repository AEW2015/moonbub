# Causal motion screening at the full 720×480 canvas

This Python experiment keeps the 720×480 coded canvas, 720×405 native-sample
active game image and primary 30 fps requirement. It adds a cheap source-only
screen before optionally preparing the frozen v12 RM01 GM01/BM01 candidates.
It does not change the decoder, syntax, quantizer or immutable ACKed key.

The screen samples four luma corners of each 16×16 block and evaluates the same
25 even-integer vectors within ±4 pixels. At this canvas it compares 135,000
sample pairs per P frame instead of full BM search's 8,640,000: 64 times fewer
SAD samples. Current luma is calculated from current RGB using the frozen integer
coefficients. The reference is the current ACKed reconstructed key, not a prior
unacknowledged source image or an independently updated shadow encoder.

Fixed thresholds, chosen before the benchmark, require mean sampled error gain
of at least 3, relative gain of at least 35%, at least 25% of blocks showing that
gain with nonzero motion, and best sampled error at most 24. Keys skip the screen.
No threshold is chosen from candidate lengths, quality measurements or future
source images. A positive screen enables both fully coded GM and BM candidates;
the smaller complete packet wins. Otherwise only GM is coded. Every sample,
search, transform, entropy call, envelope and losing candidate remains paid.
The extra sampled source conversion is not secretly shared with full conversion.

## Retained results

Seven tests pass. The 53.43-second benchmark records 154 source IDs across two
60-frame native windows, two 8-ID held-out windows, and 18 labeled synthetic
frames. Four profiles produce 616 decisions, 775 actual candidate packets,
604 admissions and 12 paid noise rejections. Candidate packet hashes match the
corresponding independent GM-only or BM-only controls under the same canonical
ACKed key. Independent decoding checks every admitted selected output hash.

| Native sample, 60 IDs each | GM-only bytes / prep | Blind dual bytes / prep | Screened bytes / prep | Mean screen |
| --- | ---: | ---: | ---: | ---: |
| Combat | 8,832 / 22.63 ms | 8,832 / 71.86 ms | 8,832 / 21.61 ms | 1.39 ms |
| Second sample | 12,056 / 19.75 ms | 11,741 / 63.88 ms | 12,056 / 21.06 ms | 1.43 ms |

The screen declines BM on all 136 real temporal/held-out IDs, including keys.
Consequently every real screened packet and displayed image matches GM-only
exactly. The second clip gives up the dual selector's 2.61% byte saving and its
different distortion (active PSNR 35.203 dB for GM versus 35.132 dB for dual).
Held-out second-clip savings missed by the screen are only 0.066%.

Screening avoids blind expensive search but does **not** improve real-source
compression in this campaign. A no-search GM policy is still the sensible real
sample default. The gate's cost is explicit overhead; fixed profile order and
uncontrolled host load mean combat's screened preparation being below plain GM
is not evidence that adding a screen accelerates GM. Do not add these host means
to independent finite-service scenarios or claim target CPU/FPGA timing.

On artificial opposite-moving block textures the screen enables BM on 5/8 frames
and retains the dual selector's mean 6,547 bytes versus GM's 19,809, a 66.95%
saving. These are contrived repeated block patterns, not a real-game win. The
screen deliberately misses static128's BM whole-P-zero-residual syntax saving:
no motion is detected, so its mean remains GM's 3,547 bytes versus dual's 1,329.
The noisy cut fixture rejects 3/6 decisions in every profile after actual work;
rejected packets do not consume pending credit or replace the key.

## Implications for an application-specific codec

This is a useful negative control: more motion hardware or more search is not
automatically better for this corpus. Retain optional motion gating as a research
tool, not a default real-game coding improvement. Next compare using bounded
sampled vectors directly, or a very small shortlisted block set, against full
SAD vectors. Actual residual coding, vector side bytes, quality floors and
complete admission costs must still be measured. Static skip detection belongs
in a separate exact residual/transform path rather than being inferred from a
motion screen. A sampled residual of zero does not prove all coefficients zero.

No GF02/GA01 finite-link integration, installed Sunshine mode, ESP32 firmware,
FPGA decoder or physical memory/scanout result is supplied. Two real clips are
related already-compressed native 25/29.88 fps footage; scheduling their IDs at
30/s does not create 30 distinct native captures/s. Candidate state, full frame
arrays and oracle verification consume host memory beyond the logical two-credit
model. Samples and operation counts are not DSP/BRAM fit or hardware cycle proof.

Run with the study virtual environment from this directory:

```sh
python -m unittest -v test_motion_gate.py
python verify.py
python benchmark.py > benchmark.log 2>&1
```

The verifier is read-only and checks source pins, actual complete packet/cap
accounting, paid gate work, deterministic thresholds, control hashes and summaries.
[results.json](results.json) pins 14 executed sources and both external media;
source acquisition/resize, quality/oracle checks and display/transport execution
are excluded from stage timings. The 30 fps byte-rate fields are arithmetic,
not paced transmission or displayed-frame measurements.

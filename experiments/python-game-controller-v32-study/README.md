# V32 causal residual qualification

This retains full 720×480 coded / 720×405 active geometry, exact 21,120 RGB565
HUD words and the 49,152-byte CP27 cap. GM27/CP27/JA27 syntax is unchanged.

Each policy has its own accepted decoded reference history, keys at 0/24 and
rotated execution order. `band_control` exactly repeats v30 strict packet/ACK/
pixel decisions. `shrink_strict` and `shrink_budget` add small-AC deletion and
one-step magnitude-shrink candidates. All protect DC, the lowest six zigzag
coefficients, ROI and chroma halo. Block-level YUV distortion and exact whole-plane
legacy/EC26 bytes qualify the producer's alternatives.

At each tier, zero/half32 and their v30 band alternatives first reproduce the
v30 strict controller winner as a same-history shadow. Two new shrink packets
then compete against it: they must fit, save actual complete bytes and have
current active RGB565 SSE ≤ shadow SSE (strict) or ≤101% (budget). A fitting
shadow is required. Ties retain the shadow. The 282-trial/48-frame shrink cohorts
pay all six P-frame and three key-frame encodes, including losing incumbents.
The control pays 188 trials/48 frames. Both scenes total 1,504 actual attempts
and 288 accepted packets. All source/quality/binding work is charged; fixture
acquisition/conversion, preencoded HUD creation, offline debug decode, archive
I/O, network waits and presentation are excluded from base-policy clocks.

| Window | Policy | Complete bytes | Active MSE | Host policy ms/frame |
| --- | --- | ---: | ---: | ---: |
| 2600 | Band control | 552,619 | 14.386886 | 306.10 |
| 2600 | Shrink strict | 552,584 | 14.385352 | 499.50 |
| 2600 | Shrink budget | 552,040 | 14.395848 | 500.08 |
| 7200 | Band control | 1,229,773 | 26.303889 | 409.80 |
| 7200 | Shrink strict | 1,230,134 | 26.309251 | 647.78 |
| 7200 | Shrink budget | 1,225,574 | 26.501988 | 652.01 |

The strict primary gain is negligible; complex strict is slightly worse despite
the local guard. Causal reference changes can negate same-frame improvements.
Both budgeted points are dominated in bytes and mean MSE by retained v30 budget
points. These are negative qualification controls, not recommended defaults.

The full verifier re-decodes all candidate and accepted chains, compares source
RGB/HUD words, checks magnitude/sign/DC/ROI and per-block YUV guards, independently
derives quiet masks, and reconciles nested shadow selection, caps and all paid work.
The replay covers 7,614,000 block checks across 2,820 band/shrink planes.

```sh
python -m unittest discover -s experiments/python-game-controller-v32-study -v
python experiments/python-game-controller-v32-study/verify.py
```

Four tests verify the nested v30 shadow, exact integer budget boundaries,
capacity, zero-error behavior, tie stability and malformed candidate groups.
No firmware, bitstream or standards decoder is installed by this experiment.

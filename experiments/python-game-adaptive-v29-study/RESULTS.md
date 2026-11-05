# V29 matched-reference probe results

The first12 frames from each of two retained Mass Effect sequences were compared
against the *same actual accepted v27 reconstructed references*. This produces
24 frames per policy,22 P frames and72 actual GM27/CP27 candidate packets. Policy
order alternates by source frame. Candidate output never becomes a later
reference here; the parent causal campaign measures that separate effect.

| Policy | Complete bytes,24frames | Active MSE | Mean P analysis,ms | Mean whole base encode,ms |
| --- | ---: | ---: | ---: | ---: |
| v28 mixed stride4/2 |510150 |20.396342 |189.3483 |219.7930 |
| adaptive zero2 |506257 |20.506982 |76.6360 |116.1413 |
| adaptive zero4 |515837 |20.606337 |51.9889 |94.4134 |

Zero2 reduces P-analysis work2.47× and complete bytes0.76%, with0.54% higher
active MSE. Zero4 reduces P-analysis3.64× but increases bytes1.11% and MSE1.03%.
These are short-window speed/quality trade-offs, not broad perceptual claims.

Zero2 classifies5614 of7590 P-frame blocks quiet. Scored sample differences
fall129,016,800→34,769,760; logical reference gathers fall342,856,800→91,217,760.
Zero4 classifies6821 blocks quiet, scoring14,074,944 differences and36,222,144
reference gathers. All quiet screening samples are included in these counts.
Array copies, vector-index arithmetic, prediction, coefficient transforms,
validation, hashing and output writes remain additional. These counts do not
represent total FPGA external-memory traffic.

All72 candidate envelopes fit49152bytes and preserve all exact HUD words. Four
unit tests pass. The retained verifier replays every candidate and accepted
reference, checks all pixels/metrics/tags and recomputes quiet masks and sample
counts from current source plus accepted decoded references. Python timing is
host timing, without RF/QSPI, display, native firmware or FPGA qualification.

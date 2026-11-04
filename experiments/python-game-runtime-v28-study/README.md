# GM27 runtime policies: exact lazy encoding and bounded sampled search

This study keeps the frozen GM27/CP27/JA27 wire,720×480 coded /720×405 active
geometry and all21,120 exact HUD words. The lazy encoder counts every legacy
plane size exactly, including original/pruned fallback decisions, then serializes
only a winning legacy fallback. EC26 remains an actual encoded candidate. A
proven55-byte lower bound avoids constructing EC26 when it cannot beat the
incumbent. Zero-plane and dense/SP01 tie rules match v27 exactly.

Tap-aware receive uses the independently qualified exact prediction adapter.
The sampled searches remain encoder policies; they never change interpolation,
quantization, decoded geometry or bit syntax. The exhaustive optimized policy
must reproduce all v27 accepted packets/ACKs/pixels exactly. The two sampled
policies run new causal histories, so their rates and image errors can change.

`parity.json` uses the same actual prepared source/reference and alternating
old/lazy order for96 selected source decisions. Encoding times exclude the
shared search/forward analysis. `results.json` then records six full48-frame
cohorts: exhaustive, sample4_refine2 and sample2 on each retained source window.
Every zero/half32 attempt is paid; quality eligibility compares current active
RGB565 SSE to the same-reference zero candidate. Actual complete packets must
fit49,152bytes; coarse background32 is tried only if no fine candidate fits.

Base-policy service includes analysis, all encode attempts, source quality
calculation and binding. It excludes fixture acquisition/color conversion,
preencoded HU25 generation, debug decoder replays, artifact storage, network
wait and presentation. Tap counts are logical prediction gathers; validation,
hashing, map reads and output writes are additional. These are host Python
measurements, not native MCU/FPGA clocks, fitted RAM or physical30fps.

```sh
python -m unittest -v test_model.py > tests.log 2>&1
python benchmark.py > run.log
python verify.py > verify.log
```

The fixed precompressed29.88fps footage supplies96 unique retained source
images. Cohorts reuse them. Retained packet/reference replay is offline and
does not require the original video downloads or connected hardware.

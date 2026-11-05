# V30 causal block/band residual selection

This is a Python host-encoder experiment with unchanged GM27/CP27/JA27 wire,
720×480 coded / 720×405 active geometry, exact 21,120-word RGB565 HUD and a
49,152-byte complete CP27 cap. It installs no firmware or FPGA image.

Three policies have separate accepted reconstructed reference histories:

- `adaptive_control`: frozen v29 quiet-block motion search and v28 lazy entropy.
- `band_strict`: also builds finer AC-tail residual choices; each edited 8×8
  block must have clipped source YUV SSE no greater than the incumbent.
- `band_budget`: allows each edited block an extra `min(incumbent_SSE//100,64)`
  YUV squared-error units. This is at most 1% of that block's original error,
  capped at 1 MSE unit per 64-pixel block, not a global perceptual guarantee.

Both band policies preserve DC, the lowest six zigzag coefficients, q=8 ROI
coefficients and the inherited chroma halo. Full-plane exact legacy/EC26 cost
selects among incumbent, gated tail≥21, gated tail≥6 and their mixed choice.
The incumbent wins all byte ties. Selected source pixels still cover the full
geometry; no extra decoder approximation or residual skip mode is introduced.

At each quantizer tier, the host actually encodes zero and searched incumbents,
and the corresponding two band alternatives. It selects the frozen incumbent
controller's cap-fitting winner as a same-history shadow. Band admission then
requires actual active RGB565 SSE ≤ that winner's SSE (strict), or ≤101% of it
(budget), and strictly fewer complete bytes. This is stronger than comparing
against the looser zero-motion candidate alone. A fitting shadow is required;
possible rescue-only band packets are intentionally declined at that tier.

Every attempted analysis/encode, RGB source metric and binding check is paid.
Band encoding currently repeats incumbent quantization/reconstruction, then
executes multiple full-plane inverse transforms and rate counters. These are
expensive correctness prototypes, not optimized native throughput results.
Capture/conversion, preencoded HUD generation, offline debug decodes, archives,
network waits and presentation are excluded from base-policy service clocks.

The campaign rotates policy order each source frame, maintaining three separate
causal histories. It reuses two retained 48-frame source windows at 29.88 fps.
Projected Mb/s is actual accepted CP27 bytes ×30 IDs/s, excluding ACK/transport
framing. The control must reproduce all 96 accepted v29 packets/ACKs/metrics.

```sh
python -m unittest discover -s experiments/python-game-controller-v30-study -v
python experiments/python-game-controller-v30-study/benchmark.py
python experiments/python-game-controller-v30-study/verify.py
```

`results.json` stores six scene/policy cases, all 940 attempted packets and their
work, 288 accepted packets/ACKs and source/reference identities. Each row also
records the same-history shadow's size/SSE and admitted quality allowance.
The offline verifier decodes every attempt and actual accepted reference chain,
recomputes source RGB metrics/HUD words, checks full-plane byte costs and each
edited block's YUV SSE, protects DC/low frequencies/ROI/halo, and checks all
selection and timing accounting. Its deterministic `replay.json` is bound to
results and verifier hashes for the independent audit.

The Python arrays, logical counters and laboratory bank model do not prove
ESP32 memory/RF/QSPI service, FPGA RAM/DSP resources or memory timing, native
encoder throughput, physical presentation or hardware 30 fps.

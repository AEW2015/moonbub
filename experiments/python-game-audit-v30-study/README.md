# V30 independent Python codec audit

This audit checks the retained 288 accepted v30 frames and all 940 candidate
attempts from the two 48-frame scenes. It independently parses complete CP27
packets, GM27/HU25 lengths and hashes, CRCs, exact 21,120-word HUD coverage,
ACK binding, the 49,152-byte cap, own-policy accepted-reference chains, and
the causal tier/minimum-byte selection rule. It recomputes strict and 1%
budget RGB SSE admission against each frame's same-history shadow winner,
checks every losing candidate's packet and paid timing, recomputes aggregate
SSE/MSE/PSNR/rate summaries, and verifies byte-for-byte adaptive parity with
the retained v29 adaptive policy.

The independent full decoder replay in the controller study owns actual source
pixel reconstruction and the per-attempt DC, ROI/halo, protected coefficient,
per-block YUV SSE, and actual RGB shadow checks. This audit verifies the replay
hashes against `results.json` and `verify.py`, then binds every replayed accepted
decoded/reference tag and RGB565 hash to the audited rows. Its report pins the
v30 sources, results, replay, verifier, prior baseline, audit code, tests, and
retained logs with repository-relative SHA-256 values. `audit.json` is omitted
from its own inventory to avoid a self-hash cycle.

Run from the repository root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v30-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v30-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v30-study/audit.py --check
```

These are Python host measurements and nominal bytes-per-second projections.
They do not establish native ESP32, FPGA, RF, display, or physical 30-fps
performance.

# V29 causal application-specific controller

This experiment keeps GM27/CP27/JA27 syntax, 720×480 coded geometry, 720×405
active video, exactly 21,120 RGB565 HUD words per frame, and the 49,152-byte
complete CP27 envelope cap. It installs no firmware or FPGA image.

Four encoder policies have separate reconstructed reference histories:

- `mixed_lazy`: v28 stride-4 coarse / stride-2 refinement and lazy entropy.
- `adaptive_lazy`: screen each block using stride-4 weighted current-source
  versus accepted-reference MAE; blocks at MAE ≤ 2 keep zero motion. Active
  blocks execute the same bounded mixed search. Every pixel still participates
  in full-resolution prediction and transform. This is not residual SKIP.
- `mixed_ec`: v28 search plus exact EC26-aware incumbent/original/pruned plane
  selection, guarded on each plane's clipped source YUV SSE.
- `adaptive_ec`: combines the two prototypes.

The quiet threshold was fixed before corpus evaluation. No future frames,
cross-policy outputs, or original source planes become decoder references.
Each key frame resets its reference identity; every accepted P frame becomes
the next actual decoded reference for that policy. Policy order rotates each
source frame. The `mixed_lazy` control must reproduce every corresponding
accepted v28 CP27/JA27 packet and source metric byte-for-byte.

At each quantizer tier, actual zero-motion and searched packets are constructed,
decoded, and scored against the current RGB565 source. The smallest complete
cap-fitting candidate whose active SSE is no greater than the current zero
candidate wins. Ties retain earlier candidates. The background tier changes
from 16 to 32 only if no eligible packet fits. The exact HUD is unchanged.

Base-policy service time pays all analyses, winning and losing encodes, source
quality scoring, and binding checks. It excludes source acquisition/color
conversion, preencoded HUD generation, offline debug decodes, archive I/O,
network waits and actual presentation. Receiver and ACK times are separate.
Counters describe logical scored samples/gathers, not fitted RAM or external
memory transactions. Python full-frame arrays and masks are not FPGA line
buffers or ESP32 memory allocations.

The corpus reuses 96 retained source images from two 29.88 fps clips, with 48
source IDs per window and four policy replays. Reported Mb/s values project
actual accepted CP27 bytes to 30 IDs/s. They exclude ACKs and transport framing;
they do not establish native throughput, physical frame presentation, or RF/
QSPI feasibility. See the main v29 report for the measured operating points.

```sh
python -m unittest discover -s experiments/python-game-controller-v29-study -v
python experiments/python-game-controller-v29-study/benchmark.py
python experiments/python-game-controller-v29-study/verify.py
```

The retained offline verifier needs Python, NumPy and Pillow through the inherited
prototype environment. It decodes all accepted and rejected candidate packets,
recomputes every source metric, exact HUD word and reconstructed reference chain,
checks admission/selection and paid work, and independently recomputes adaptive
quiet masks and actual scored sample counts. It writes deterministic `replay.json`.

`results.json` stores `cases[scene, policy]`; each case has `rows` and `summary`.
Rows retain source/reference identities, separate `analyses`, every `attempt`,
selected complete/base/HUD/ACK objects, timing scopes, and integer source SSE.
Packet descriptors contain relative paths, bounded raw sizes, compressed-object
SHA-256 and raw SHA-256. Zlib is archive storage only, never a video codec here.

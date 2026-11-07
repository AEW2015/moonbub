# V98: common-input codec controls

V98 now has a reproducible software comparison: 52 profile runs and 1,560
encode/decode round trips on four short 720×480 sequences. The supplied Mass
Effect Legendary Edition video contributes a new 30-frame combat sample at
30-Hz selected cadence. [Measured results](results.md) and the
[machine-readable frontier](../../experiments/python-gamebub-v98/frontier.csv)
separate rate, pixel quality, packet tails and native host costs.

This is a **partial V98 checkpoint**. Original raw gameplay, a fresh-RGB encoder
for the current CU66 syntax/policy, actual HUD readability, long-run calibrated
tails, and both physical milestones remain open. The executable custom control
is historical GM01; it cannot establish the newest CU66 rate/quality gap. No
firmware, FPGA bitstream or Sunshine service is changed by this study.

## Reproduce

Use Python with NumPy, Pillow, PyAV and imageio-ffmpeg. The retained versions are
Python 3.14.4, NumPy 2.5.4, Pillow 13.0.0 and PyAV 19.0.2; the exact receipt and
per-codec version records are authoritative. This machine uses
`/home/lori/gamebub-streaming-prototype/.venv/bin/python`.

```sh
python experiments/python-gamebub-v98/source_prepare.py --user-source /path/to/combat.mp4
python scripts/cu66-v98/validate.py
python scripts/cu66-v98/compare.py
python scripts/cu66-v98/audit.py
python scripts/cu66-v98/summarize.py
python scripts/cu66-v98/bundle_manifest.py
```

The two earlier source MP4s are referenced by hash and are not duplicated here.
The four extracted NPZ inputs are retained, so comparison can use those without
re-extracting the original videos. A fresh independent audit also requires the
original video paths to verify source-file provenance; it fails if an original
is absent or changed. Source preparation takes the first 30 native
frames at one second from the two existing clips. The user sample starts at
20 seconds and selects every second 60-fps frame, without interpolation or
duplication. See [source notes](../../experiments/python-gamebub-v98/source-notes.md).

`compare.py` creates immutable attempt directories, snapshots its Python
dependency closure, pins the input manifest/arrays, and preserves exact streams,
syntax traces, per-frame hashes, quality and timing records. Failed attempts
remain distinguishable from the selected successful index. Run one full
comparison at a time. The resource gate requires at least 8 GiB available RAM
and memory PSI full avg10 below 1; swap occupancy alone is not the gate.

`audit.py` independently recounts the ledgers without importing the benchmark,
codec wrappers or metrics. `summarize.py` requires both measured and audited
success and checks measured-source freshness. `validate.py` retains the exact
unit-test command/output and source pins. The packaging manifest includes the
specific V98 source, evidence and updated plan files, excluding build caches
and unrelated local experiments.

## Evidence boundary

All methods use identical selected RGB frames, identical frozen full-range
8-bit YUV420 conversion/sample planes and inverse, and RGB565 output
quantization. Rates count elementary stream bytes plus extradata, including
the custom packet headers/CRCs. Network, mux, ACK, FEC and RF costs are excluded.
Reference structures and coding tools differ and are documented, rather than
assumed equivalent. The standards are offline software anchors, not supported
Game Bub decoder profiles.

Pixel quality includes active-area/ROI error, worst frame, and temporal changes
in reconstruction error. Game ROIs are geometric probes with no verified HUD
semantics. Synthetic ROIs are interior panel/reticle probes; the last drawn
border pixel is outside two of the masks. These diagnostics do not measure
readability, flicker perception or subjective gameplay quality.

The next decision is to connect the current CU66 **fresh-input encoder**, then
repeat these controls with original held-out captures before freezing a codec
for the V100–V110 7-series implementation phase. Earlier complete-path
integration gates are retained; software decoder timings do not close them.

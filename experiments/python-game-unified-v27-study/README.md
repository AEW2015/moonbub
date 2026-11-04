# Unified Game Bub Python study v27

`model.py` directly emits **GM27/version1**, combining the frozen GM26/version2
fractional motion predictor and compact motion sender, exact v26 RDO size
counter, and block-major EC26 residual coding. `protocol.py` composes this base
with unchanged HU25/HD25 exact HUD packets as CP27 and JA27. This is a host
Python experiment, with no installed Sunshine, ESP32 or FPGA endpoint.

The direct path has two entropy phases. It first executes the frozen legacy
plane encoder on the RDO proposal and, when changed, the original plane. Its
actual original/pruned byte comparison fixes the coefficients exactly as in
GM26. It then constructs one EC26 layout0 candidate for each chosen plane and
selects EC26 only when its complete dispatch-plus-packet bytes are smaller.
Only that final choice is reconstructed and tagged after the RDO baseline.
There is no serialized GM26 intermediary or hidden repack step. EC26 does not
change the vector, quantization, RDO decision, reconstructed reference or output
tag for a shared prepared analysis and map.

`analyze_planes` delegates directly to the frozen predictor without mutating
its globals. `Prepared` is the actual frozen class and owner token; its source,
prediction, forward coefficients and work fields retain the same API. Each
`encode_prepared(p, qmap, rdo_lambda=1)` pays its own quantization, exact RDO
counter work, all legacy entropy trials, EC26 trials and final reconstruction.
Search and three forward transforms remain explicitly paid in `p.work`, once
per prepared analysis. `encode_planes` combines both accounting stages.

Receive uses the v27 syntax-only bounded motion decoder. The sender still
constructs the frozen byte-minimal map, but receive does not run a motion
encoder to prove minimum length. The same valid vectors can therefore have
multiple accepted map spellings in GM27. `unpack_vectors_strict` exposes the
frozen GM26 canonicality decoder for qualification of canonical sender output;
this is an explicit GM27 grammar choice and does not change GM26.

`parse_metadata` validates only the immutable base envelope: outer CRC, profile,
geometry, IDs, tags, declared map/plane bounds and exact total length. It does
not decode the quant map, motion map or entropy. Pair binding and ACK inspection
use that stage. `parse` completes those syntax checks, and `decode` also verifies
the exact source reference and reconstructed output tags. `Receiver.receive`
finishes full base/HUD decoding and ACK construction before its single modeled
publication; invalid entropy can pass metadata inspection but cannot publish.

Statistics preserve the familiar plane/work fields and add explicit accounting.
`legacy_trials` contains every original/proposed plane call. Its
`representations` counts the zero shortcut, or the direct CP02 plane plus both
SP01 wrappers; `legacy_cp02_encode_calls` additionally counts CP02 full-block
subset constructions inside SP01. `actual_entropy_candidates` sums these plane
representations plus one EC26 construction per final chosen plane. All of their
actual elapsed time is included in `entropy_ms`; EC26 time is also itemized.
Four logical reference fetches are charged per predicted YUV sample, including
zero-weight interpolation taps. These are executable-model operation counts,
not native allocation, hardware area or timing estimates.

Run the local checks from the repository root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover \
  -s experiments/python-game-unified-v27-study -p test_model.py -v
```

The 12 checks cover scalar fractional prediction, compact motion syntax and
sender minimum parity, direct key/P reconstruction, exact frozen-selected
coefficient/RDO parity, EC26 array and streaming coefficient equality, malformed
profiles/entropy/CRC/tags, reference identity, metadata versus semantic checks,
atomic publication gates, wrong source-bank/ACK binding and the complete cap.
`tests.log` records the run. Campaign results and causal replay are maintained
in this directory's separately owned benchmark and verification artifacts.

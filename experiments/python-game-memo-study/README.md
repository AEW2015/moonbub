# Exact last-source P-payload reuse

The PC encoder keeps one immutable RGB source, quantization map and compressed
P payload. Reuse requires exact source/map equality, the same mode, epoch,
geometry and the identical ACKed reconstructed key object and ID. A hit rebuilds
the current GM01 frame header and CRC, consumes normal pending credit and sends
the complete packet. It does not create a skip message or update the reference
from an unacknowledged source image. Keys and changed anchors invalidate the
cache. A two-image alternating sequence deliberately misses this one-entry cache.

Five tests pass, covering byte equality, no forward transform on a hit, key/map/
mode/source mutation, credit and generation rules, expiry, session ACKs and random
repeated sequences. The benchmark alternates baseline/cache execution order and
compares full packet bytes and independently decoded output under immediate ACKs.

| Source, all at 720×480 | Exact hits / IDs | Mean preparation, baseline → reuse |
| --- | ---: | ---: |
| Combat | 26 / 60 | 24.73 → 13.95 ms |
| Second sample | 0 / 60 | 24.89 → 25.25 ms |
| Synthetic flat repeat | 8 / 12 | 19.91 → 7.59 ms |
| Synthetic alternating images | 0 / 12 | 21.95 → 21.99 ms |
| Synthetic repeated noise/cuts | 6 / 12 | 61.69 → 31.11 ms |

These are 156 paired source IDs, 312 encoded packets and 156 decoded packets,
with 40 exact hits. All paired full packets are byte-identical. Eight noisy
packets exceed the 49,152-byte admission cap; this arithmetic comparison decodes
them but counts them explicitly. They are **not** admitted stream frames.

Preparation timers include equality checks, miss copies, normal key reconstruction
and hit header/CRC work. Source acquisition/resize, map construction and correctness
hashes are excluded. The two native samples are related precompressed 25/29.88 fps
footage, with repeated content. The first sample's gain is not a prediction for
30 distinct gameplay images per second. Host load is uncontrolled; the second
sample shows the miss overhead rather than a universal speedup.

The cache is on the PC: one RGB copy (1,036,800 bytes at this canvas), one map,
one P payload/header and a pointer to the existing ACKed YUV key. Existing
pending packets and transform workspaces are extra. No FPGA or ESP32 storage is
added by this Python experiment. All packets still traverse the link and undergo
full decoding, so there is no bandwidth or receiver speedup from reuse itself.

This standalone `prepare()` path is **not integrated into the finite rate
controller**, whose candidate API bypasses this override. Do not infer a finite
link FPS improvement from these preparation times. Integrating a bounded preview/
commit cache without admitting over-cap packets is the next software step.

Run from this directory using the study virtual environment:

```sh
python -m unittest -v test_memo_encoder.py
python verify.py                       # read-only retained evidence check
python benchmark.py                    # regenerates paired timings; external media required
```

[results.json](results.json) pins executed sources and external media. This is a
wire-compatible encoder optimization, not a new compression format or hardware
30 fps proof.

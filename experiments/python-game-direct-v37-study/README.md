# V37: direct byte-identical CN36 skip sender

The direct sender removes v36's discarded full packet construction, coefficient
syntax reparse, full-image inverse reconstruction and redundant output work.
It emits the **exact same CN36 skip bytes**, not merely similar pictures, on all
96 retained main frames and the six-frame fractional-motion probe.

| Scene, 48 frames | Equivalent v36 one-output proof sender | Direct sender | Ratio | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| Primary | 88.401518 ms | 61.847014 ms | 1.429× | 30.0385% |
| Complex | 119.159953 ms | 73.675718 ms | 1.617× | 38.1707% |

These are means of per-frame paired medians. Every frame has three paired
repetitions, with order alternating by frame/repetition. Both clocks include
source analysis/forward transform, quantization, RDO, required unmasked size
planning, entropy construction, reconstruction, reference normalization and
one CN36 wrapper. They do not include fixture/HUD reads or generation, archive
I/O, metrics/equality checks, receiver, transport, queueing or display. Source
arrays and fixed HUD bytes are loaded before each paired group.

The fair proof baseline generates only one skip output: full encode, skip
reparse/re-entropy/rebuild, one normalization, one wrapper. It excludes the
unused full canonical normalization/wrapper paid by the old two-output v36
experiment. This avoids inflating the speedup by timing a different output task.
The compiled geometry plan is initialized once outside both per-frame clocks;
the direct path applies it, while the frozen proof path replans its mask.

## Preserve decisions before removing hidden work

`model.encode_prepared(prepared, scale_map, hud, rdo_lambda=1)` returns the actual
CN36 wire packet, owned normalized planes and work counters. It deliberately
retains original quantization, RDO and **unmasked plane-global legacy reversion
size decisions**. Suppressing hidden coefficients before those decisions could
alter visible coefficients through a changed global plane-length comparison.

After those exact decisions it zeros hidden coefficients, constructs three skip
entropy components directly, reconstructs one output, applies the frozen v36
compiled support plan, and wraps that output using frozen CN36 framing. No
full-packet encoder or coefficient parser is called. Frozen metadata validation
inside the wrapper remains paid. Production code does not monkeypatch old
modules; a scoped behavioral test forbids accidental full encode/syntax decode.

The 102 accepted packets preserve all source/geometry/qmap/key/reference semantics
of v36. Main complete budgets remain441,520 /1,060,332 bytes, maxima22,569 /41,224,
and active MSE14.38366067 /26.54469598. The motion probe keeps forced(-3,+1)
half-pel block32 vectors and exact causal normalized reference/display output.
There are no additional compression savings in this study: it is an exact sender
implementation optimization. The separate root implicit-grammar experiment is
not combined with these timing figures.

## Verification and limits

Three producer tests pass, including exact key-frame bytes, behavioral no-full-
encoder/no-coefficient-parse validation, invalid input rejection without source
mutation, and original reversion parity. An independent verifier imports no new
sender and replays frozen v36 decoding against all actual archived packets. It
checks exact bytes, complete cap/accounting, reference tags, source/display
hashes, visible coefficients and the paired timing summaries. Its focused tests
and replay logs are retained separately.

The retained campaign takes no original global-RDO reversion branches. The
producer test therefore also forces a visible-coefficient RDO change and a
three-plane legacy-size reversion using scoped mocks, checks all three actual
reversion flags and exact frozen-proof parity, then restores the original
functions. That test-only strengthening happened after timing; its source hash
was refreshed and all focused tests/replay rerun without changing the timed
model, helpers, benchmark or numerical evidence.

The windows are reused short Mass Effect clips, not held-out gameplay. The main
fixed zero-motion policy is intentionally unchanged; this is not yet a complete
searched-motion/RDO controller or a source/HUD acquisition pipeline. The direct
sender is still above the33.33 ms frame budget on this Python host, and receiver,
network and display service are additional. No native ESP32/FPGA implementation,
hardware30fps, combined component speedup or HEVC/AV1 superiority follows.

```sh
cd experiments/python-game-direct-v37-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```

`results.json` binds producer source and inherited dependencies. Verifier/test
files are independently maintained and bound by the outer v37 portable manifest.

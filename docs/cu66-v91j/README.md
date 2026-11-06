# V91j: actual BR88 frames to signed inverse-transform residuals

V91j passes the bounded transform-integration milestone. The actual CS88/BR88
coefficient pipeline now feeds the unchanged RTL dequantizer and two-pass Q14
IDCT. The measured endpoint is the last accepted signed residual, with real
transform cycles and output stalls included. Next is V91k reconstruction.

## Results and scope

Two strict Verilator seeds each exercise 11 retained frame inputs under FAST
and SLOW memory service: 22 rows, **4,058,368 exact dequantized values and
4,058,368 exact residual samples per seed**, plus exact assembly/coefficient
comparisons. The 31,706 Python golden tiles include four related native frames,
a varied-qscale case and valid earlier planes of a late-CRC rejection. Repeated
service profiles and seeds do not add distinct gameplay content.

Each seed also passes 48 standalone arithmetic boundaries (42 valid, six
invalid), 13 integrated interface/recovery checks and 15 standalone directed
checks. Boundaries cover zero, positive/negative DC and AC, coefficient limits,
signed rounding, all three scales and both quantizer-table classes. Invalid
qscale/coefficient inputs return local error 3 without a transform result.

The independent auditor recomputes every golden using Python integer math,
checks actual assembly/DQ/residual trace hashes and ownership metadata, verifies
retained and live source hashes, and audits both final seeds. C++ compares every
value before emitting hashes. See [summary](../../experiments/python-gamebub-v91j/summary.json),
[audit](../../experiments/python-gamebub-v91j/audit.json) and the
[arithmetic contract](math-contract.md).

## Bounded architecture and recovery

The [RTL notes](../../fpga/experiments/cu66-v91j/README.md) describe two packed
64×16-bit coefficient banks: **256 logical payload bytes**, plus control and
existing DQ/IDCT workspace. The existing two 49,152-byte packet banks remain
98,304 bytes total. These are logical budgets, not inferred BRAM or device-fit
measurements. One math job runs while the other bank assembles; both service
profiles observe accepted coefficients while math is active. A bank remains
owned until its 64th residual is accepted, including arbitrary legal stalls.

Metadata includes frame epoch, child epoch, plane, native tile, quantizer cell,
scale and an opaque token. Token identity is `(frame_epoch, token)`; synchronous
math cancellation flushes producers before reuse. There is no global lifetime
counter limit introduced by this adapter.

Abort/reset tests cover partial assembly, active dequantization and nonzero-AC
IDCT, held residual output, both banks occupied, retry and physical scratch-ACK
drain. New starts cannot overwrite an accepted outstanding external request.
Late third-plane CRC error 147 is preserved and never completes a frame.
Transform faults use the separate `0xc0 | local_error` namespace. Previously
emitted residuals are provisional; no frame is published. A partial residual
prefix is permitted on a later failure, but the retained CRC corpus lets earlier
planes drain fully and does not itself prove an observed partial-tile CRC prefix.

## Timing interpretation

The summary retains start-to-residual-done, last-outer-byte-to-residual-done,
coefficient completion and quantizer-preload fences for each native case and
seed. QM6 preload costs 1,350 cycles separately; key-frame rows do not preload
that cache. These residual fences include actual transform work and have a
later endpoint than V91i coefficient-only fences. Comparing them as a refill
speedup would be invalid. No routed operating frequency is assumed.

## Reproduce

From the repository root, using the existing `gamebub-cu66-v69-build` container:

```sh
python3 experiments/python-gamebub-v91j/model.py
python3 scripts/cu66-v91j/run_pipeline.py --seed 911401
python3 scripts/cu66-v91j/run_pipeline.py --seed 911402
python3 experiments/python-gamebub-v91j/verify_results.py
python3 scripts/cu66-v91j/summarize.py
```

The runner uses Verilator `--assert -Wall` and GCC `-Wall -Wextra -Werror`,
retains immutable input/source snapshots, commands and logs, and records failed
attempts separately. Compressed canonical vectors reconstruct the temporary
plain transform TSV by its pinned SHA-256. Earlier failed/pre-final attempts
remain evidence; only current-source final seeds qualify the summary.

## Next milestone: V91k

Connect accepted-reference prediction, COPY/constant handling, residual addition
and clamping, hidden-pixel normalization and output conversion. Preserve exact
canonical/reference and intended RGB565 pixels, and charge real bounded memory
service. Then V91l integrates HUD/content validation and atomic publication;
V91m tests complete frame service with finite transport/display consumers.

Mixed AB38 decoding remains unsupported on this BR88 subset. V91j is not a
complete pixel decoder, a hardware 30-fps demonstration or validated complete
decoding under 10 ms. Physical 7-series mapping, placement/routing, achieved
clock and external-memory qualification remain V100–V110 work.

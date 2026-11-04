# Admission cache plus exact decoder bypass in finite execution

This combines the v13 candidate/commit-aware host cache with v12's exact zero/DC
receiver bypass. All performance cases retain the 720×480 coded canvas and a
30-ID/s schedule. Native files are resized to 720×405 active content inside it.
The model carries actual GM01/HG01, GF02 and GA01 bytes, bounded pools, reader
ownership, key drain, cap admission and delayed state publication.

`model.py` is a byte-identical copy of v12 refresh/model.py, including its requested-
expiry ACK guard. `adapter.py` selects the frozen normal rate controller or the
new cache controller, and the frozen or exact fast receiver. Both host controls
use the same normal/fallback maps. The cheap size gate is not introduced in one
arm. UI selection still executes fully; the later standalone UI cache is absent.

There is **no fixed service tape** and no assumed decode time in this benchmark.
Every preparation, rejection, receive, BOX and transport call pays its observed
host wall duration on its own serialized virtual server. Verifiers assert those
equalities. These independent servers do not measure concurrent execution on a
shared target CPU. Inner generic model descriptions cover optional modes; the
retained `service_tape: null`, config and per-call equalities identify this run's
measured-host mode. Native acquisition remains unmeasured.

## Retained results

Sixteen cases execute 1,104 capture-policy events in 75.19 seconds of host wall
time. There are two 60-frame native windows with a full cache/receiver factorial
for exact UI, GM-only control pairs, a held-out 180-frame second-source UI pair
from four seconds, and a 12-frame noise/recovery pair. These are repeated policy
runs, not 1,104 distinct captured images. The short clips contain 32 and 60
distinct RGB images; the held-out window contains 180 distinct images from a
native approximately 29.88 fps precompressed file. It is scheduled hypothetically
at 30 IDs/s, rather than proving a live 30 Hz capture source.

| Source / profile | Baseline strict / eventual / diagnostic | Cache + bypass strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat, exact UI, 60 IDs | 49 / 51 / 25 | 52 / 53 / 26 |
| Second, exact UI, 60 IDs | 40 / 42 / 21 | 41 / 44 / 21 |
| Combat, GM only, 60 IDs | 54 / 55 / 28 | 55 / 56 / 28 |
| Second, GM only, 60 IDs | 54 / 56 / 27 | 55 / 57 / 28 |
| Held-out second, exact UI, 180 IDs | 119 / 121 / 19.6 | 121 / 123 / 20.0 |

Strict counts presentations before the capture window ends; eventual includes
the separate one-second drain. Diagnostic rates cover the middle window, excluding
the first and last 500 ms. The long diagnostic window is five seconds. None of
these cases delivers every ID within the strict window. A 150 ms decode-age gate
allows the subsequent vblank, so it is not a 150 ms optical-age guarantee.

In the combat UI factorial, cache alone gives 52/53/26 and receiver bypass alone
50/52/25. In the second, cache alone gives 40/43/21 and bypass alone 41/44/21.
The complete combination includes 24 cache-hit attempts on combat UI and no hits
on the distinct second-source/held-out windows. Means in the paired combat UI
cases are 26.03→17.29 ms preparation and 23.71→21.05 ms receive; second UI means
are 28.35→28.56 and 27.20→25.03 ms. Histories and call counts differ, so these are
context, not isolated same-packet causal timing comparisons.

The optimized second-source UI case still waits 559.05 ms on P credits over the
two-second window. The held-out case waits 1,661.01 ms over six seconds, alongside
1,366.65 ms encoder-busy waiting. Waiting categories are exclusive state intervals,
not additive attribution of lost frames. The later credit-window study separately
tests whether more host transactions help; no extra credit exists in this run.

Case order reverses between short clips, but host load is uncontrolled. Re-measured
service changes capture skips, keys, references and later bytes. Pair summaries
therefore retain common source IDs, same-anchor IDs and identical-packet IDs.
Do not add standalone cache and bypass percentage gains to predict end-to-end FPS.

Both synthetic runs have three paid cap rejections and three eventual displays.
Fault coverage is in small actual-packet unit tests, not injected into these clean
native timing runs. Four tests cover all four paths with identical packet/timing
traces under a declared unit-test clock, key/ACK loss and corruption recovery,
cap rejection before send/commit, and the frozen scheduler copy. The unit clock
is never used in the performance benchmark.

## Memory and timing limits

There are two sender transactions, two ingress payloads, two P credits and three
metadata framebuffer roles, plus bounded feedback descriptors and latest capture
queues. PC cached sources/payloads, original/source/oracle/output images, transform
workspaces and packet copies are additional allocations. These are logical
ownership checks, not measured peak memory or physical SDRAM/BRAM fit.

Forward/reverse 8 Mb/s, QSPI 160 Mb/s, 10 ms feedback propagation and 60 Hz vblank
are declared assumptions. No real sockets, ESP32, RF, QSPI framing, native codec,
DMA/CDC, scanout or physical display is tested. Sustained hardware 30 fps remains
open. The unchanged stream syntax makes native execution work possible without
requiring a full HEVC/AV1 decoder.

```sh
python -m unittest -v test_execution.py
python verify.py                         # read-only retained evidence checks
python benchmark.py                      # regenerates timing; external media required
```

Use the study virtual environment. `results.json` pins executed sources and native
media; the parent manifest pins documentation, tests and retained evidence.

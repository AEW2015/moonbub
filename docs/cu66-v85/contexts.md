# V85 per-context entropy observations and parallel-lane prototype

V85 attributes each native AB38 primitive to the DC context, one of three AC
contexts, or shared work. The observation fork retains the four-context
interleaved decode, DC predictor, next-event lookahead and exact original
coefficient semantics. **457 native sources / 1,371 planes** match the frozen
coefficient decoder and original packet/canonical/HUD/display digests. Every
shared-plus-four-context counter equals its V84 aggregate on all 3,701,700
canonical tiles.

The native observer is not a clock trace. Its counters inform conditional
Python scheduling; they do not establish FPGA timing, DSP mapping or Fmax.
Native payloads are compressed AB38. The implemented raw fallback is absent
from this corpus and is not qualified by it.

## Counter attribution and imbalance

| Owner | Arithmetic decisions | Renormalizations | Compressed byte-cache fills |
|---|---:|---:|---:|
| DC / context 0 | 8,287,033 | 5,917,901 | 743,426 |
| AC / context 1 | 18,221,516 | 15,895,970 | 1,990,697 |
| AC / context 2 | 14,860,950 | 12,328,273 | 1,544,784 |
| AC / context 3 | 2,067,070 | 1,701,996 | 216,688 |

CRC scanning, parameter/padding fetches and tile emission are shared. Each
context owns its preload/termination bits, byte cache, Rice decisions, AC
events and 88 probability initializations per plane. Shared counts therefore
retain all 4,591,565 CRC-scan bytes, 38,388 extra header fetches and 3,701,700
emits. Summing the contexts and shared work preserves every V84 counter,
including initialization and event lookahead, not just coefficient equality.

Under V84 LOW weights, context-only compute is distributed DC **17.81%**, AC1
**43.41%**, AC2 **34.12%**, AC3 **4.65%**. The streams are strongly unbalanced.
Four arithmetic lanes cannot be modeled by dividing total work by four;
shared fetch and the longest sequential context remain necessary costs.

## Standalone scheduling experiment

The sample is the first six sources from each independently reset history,
plus native aggregate-work corner cohort 3 / source 50: **25 sources**. It
runs LOW/HIGH weights, 1/2/4 arithmetic lanes and 8/64-tile windows, for **300
conditional schedules**. All 457 sources contribute to the counter/balance
statistics; only these 25 contribute to latency results.

The model has one shared nonpreemptive fetch/control server, separate
arithmetic lanes and one emitter. Each context keeps its own order; tile
emission waits for all four context frontiers and the previous tile's
emission. Admission of tile i waits for emission of tile i−window. Byte-fetch
work is batched before arithmetic for that context/tile. Shared setup/header
prefetch may overlap prior arithmetic within the admitted window. The external
consumer accepts emitted tiles immediately; inverse, reconstruction, memory
stores, LCD, ESP32 and end-to-end frame completion are outside this model.

Even the one-lane case decouples fetch from arithmetic. It is a prospective
architecture, **not the V84 single-resource architecture or a measurement of
the existing RTL**. Compare lane counts within this experiment; do not present
its one-lane result versus V84 as a measured speedup.

At an assumed 100 MHz, the eight-tile-window results are:

| Cost assumptions | Arithmetic lanes | Selected-source median ms | Selected-source maximum ms |
|---|---:|---:|---:|
| LOW | 1 | 3.51731 | 13.14572 |
| LOW | 2 | 2.22879 | 7.39914 |
| LOW | 4 | 2.10841 | 6.76155 |
| HIGH | 1 | 6.73302 | 25.17113 |
| HIGH | 2 | 4.25804 | 14.17027 |
| HIGH | 4 | 4.02163 | 12.91737 |

For a 64-tile window, LOW median/max becomes 3.51503/13.14569 ms with one
lane, 2.22044/7.31579 ms with two, and 2.05974/6.50886 ms with four. HIGH
becomes 6.73074/25.17107, 4.24561/14.02544 and 3.92823/12.44712 ms. Larger
windows improve some overlap but also need more coefficient assembly storage:
128 logical bytes per admitted coefficient tile, before ports or RAM rounding.

The sample favors testing two arithmetic lanes first, with four as a
comparator. This is a prototype choice, not a resource/clock/fit conclusion.
The HIGH four-lane corner still exceeds 10 ms before the full decoder path.
LOW front-end-only times below 10 ms do not close the validated-decoding goal.

## Evidence and implementation gaps

`contexts/model-attempts/20261106T125933013875Z/results.json` retains the
selected-source model and 18 synthetic cases, including exact hand-calculated
balanced/single-stream one-tile-window checks. Every selected schedule passes
dependency, resource and window-lifetime auditing. Two full LOW/window-8
corner witnesses, with one and four lanes, are retained. The separate
`audit_model.py` reconstructs their complete DAGs from native per-tile counts
and reaudits timelines using the frozen generic auditor. It also recomputes
all 300 row work counts and summaries independently. Other timelines retain
in-process audits and summaries rather than full retained timing traces.

Real implementation must account for context switching/state-bank access,
coefficient assembly write ports, event/predictor rendezvous, response FIFOs,
byte-cache contention, copy/control logic, actual DSP feedback pipelining and
all downstream backpressure. A Python full future-task graph is not bounded
streaming hardware control. There is no full-corpus parallel latency,
sustained-30-fps, full-under-10-ms, target-fit or ESP32 proof here.

## Reproduction

Native collection refuses to overwrite its retained index:

```sh
python3 scripts/cu66-v85/collect_contexts.py
```

Verify retained observations and the selected model without recompilation:

```sh
python3 experiments/python-gamebub-v85/contexts/verify.py --verify
python3 experiments/python-gamebub-v85/contexts/audit_model.py --attempt experiments/python-gamebub-v85/contexts/model-attempts/20261106T125933013875Z --verify
```

The loader `contexts/data.py` yields `shared_work[8100]` and
`context_work[8100][4]`, each with V84's eleven counter names. Source snapshots,
native binary/compiler/commands/logs and per-record digests are retained.

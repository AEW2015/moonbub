# Cheap conservative CP02 lower-bound guard

This second experiment leaves the [exact preflight](README.md) sources and
results unchanged. It asks only whether a candidate is **provably too large**,
without scanning Rice parameters or constructing strings. It does not predict
an exact length for packets it allows through.

## One-sided bound and bounded admission

For N validated coefficient blocks, count nonzero AC coefficients and blocks
whose final zigzag position63 is nonzero. Every DC has at least one Rice bit;
every nonzero AC needs its5-bit prefix/run plus at least one Rice bit; incomplete
blocks need a2-bit EOB. Ignore positive ZRL and extra Rice costs. Thus coded
DCbytes≥1+ceil(N/8), ACbytes≥3+ceil((6×nonzeroAC+2×(N−last63))/8). Include the
26-byte CP02 envelope and take the minimum with128×N raw bytes. This gives a
lower bound regardless of raw/coded selection. Whole GM01 includes its50-byte
header/CRC and actual map bytes.

`cheap_gate.py` counts nonzeros directly on the coefficient arrays; no zigzag
reordering, Rice-cost sweep or entropy token/bit-string creation is needed.
Its quantized plan is reused for actual emission. If the lower bound exceeds
the cap, that attempt is rejected. Otherwise the normal complete packet is
serialized and **its actual length is still checked** before commit. A weak
bound can allow an oversized candidate to be serialized; it never authorizes
sending that packet. Normal/fallback maps, fixed ROI8 floor, immutable anchor
and GM01 credit/generation rules remain unchanged. No old globals are patched.

## Actual paired results

`gate_benchmark.py` repeats the exact same32 inputs/caps as the previous study:
eight seeded dense-noise keys, twelve predeclared real normal keys and twelve
real pressure keys. Alternating same-run variant order checks identical selected
bytes/RGB, admission decisions and fallback labels. Every lower bound is checked
against the actual baseline attempt length. Rejected lower-bound candidates
never serialize their entropy payload. Verification is outside preparation time.

| Same-run branch | Full serialization mean | Cheap guard mean | Observation |
| --- | ---: | ---: | --- |
|8 dense-noise rejects|113.68 ms|25.04 ms|78.0% less service; zero payload serializations|
|12 normal real keys|33.52 ms|32.93 ms|1.8% lower; small uncontrolled variation|
|12 real pressure keys|37.07 ms|37.75 ms|1.8% regression|

All eight noise calls still drop both candidates. The guard improves wasted
host work, not those frames' delivered quality or admission. Their observed
maximum preparation is28.68 ms, but this sample maximum **is not a worst-case
33.33 ms guarantee**. Normal-path p95 is40.67 ms and pressure p95 is50.69 ms.

All six pressure oversize first attempts pass the weak lower bound and therefore
still serialize, for18 actual serializations across12 calls. The guard is
particularly effective for dense coefficients, but it ignores magnitude/Rice
parameter costs and can miss other expensive oversize content. No broad
same-service or throughput win is claimed from these independent-key samples.

Preparation includes map construction, one RGB/prediction/raw-DCT analysis,
all quantization/bounds, emitted candidates, selection and admitted-key
reconstruction. Acquisition, oracles/receiver checks, network and display are
excluded. Host load, frequency, affinity and warmup are uncontrolled. The videos
are the same short related precompressed25/29.88fps sources; source IDs are
reused across caps and noise is separately synthetic. There is no finite link/
feedback run or physical platform test in this experiment.

## Tests and reproduction

The directory now has five tests: the three frozen exact-preflight tests plus
two lower-bound tests covering80 families/all64 positions, bound≤exact,
provable rejection without serialization/state mutation, exact candidate bytes
and stale/cloned plan rejection. Existing72 frozen GM01 packet SHA and216 exact
plane-size checks remain in `prior-check.json`.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python gate_benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python gate_analysis.py
```

`gate-results.json` preserves the actual run and code/input bindings;
`gate-summary.json` derives separate pressure branches. These files complement,
rather than replace, the exact preflight's admitted-path regressions. A mixed
transport timeline, actual capture/scale, reference-memory traffic, native
implementation and varied long capture remain required before rate or hardware
claims. The guard is a promising host-side rejection option, not a new codec or
FPGA/ESP32 mode.

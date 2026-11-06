# V86 context replay on the actually re-encoded residual streams

V85's parallel-context model used the original input streams. V86 observes the
**actual residual-only AB38 bytes** retained by V85 at chunk caps 256 and 65536
(whole residual plane), then models their frontend schedules. It does not infer
new-stream work by scaling old counters or removing COPY-attributed work.

## Native observations and independent checks

There are **914 variant records: 457 native sources × two chunk profiles**.
The collector feeds each of **7,432 actual chunks** through a native bridge.
Its interleaved four-context observer must produce exactly the same coefficient
array as the frozen independent AB38 decoder. Python scatters those decoded
coefficients back into all 8,100 canonical positions, inserting zero
coefficients for COPY/hidden CONST positions, and requires the complete
coefficient SHA-256 to equal V85's native result for each variant record.

Each canonical tile retains eleven primitive counters for a shared part and
four arithmetic contexts. CRC/header fetches are shared. Context byte caches,
Rice/decision/renormalization work, preload/termination and probability
initialization remain attributed to their actual streams. Every new chunk
pays its own initialization and integrity work. COPY and CONST carry no
residual entropy; the frontend model assigns one local emission operation per
canonical tile. The operation-map parser itself is outside this model.

The independent retained-data verifier checks every input/chunk identity and
compressed/raw/count hash. It parses nested AB38 CRCs, geometry, stream bit
lengths and event counts. Its observed per-context decisions and renormalization
counts must equal the actual selected V85 encoder's counters. Initializations,
fetches, consumed bits and Rice/event relationships are independently checked.
This native corpus contains compressed chunks only; raw fallback is not
qualified by these observations.

| Residual chunk cap | Chunks | AB38 bytes scanned for CRC | Arithmetic decisions |
|---|---:|---:|---:|
| 256 | 6,061 | 4,707,730 | 36,579,240 |
| Whole plane | 1,371 | 4,265,737 | 37,656,819 |

Under LOW weights, the whole-plane arithmetic work distribution is about
DC 14.45%, AC1 44.06%, AC2 36.46%, AC3 5.02%. Cap 256 is similarly uneven.
Decision count alone does not predict bytes or latency: cap 256 has fewer
decisions but more packet/reset/fetch work and more encoded bytes.

The packed retained work payload is 1.63 GB before compression and
**34,082,887 gzip bytes**. It is host evidence storage, not an FPGA or ESP32
allocation. `contexts/data.py` yields `shared_work` and `context_work` arrays in
canonical tile order together with cap/source identities and per-part totals.

## Conditional model contract

The frontend uses one shared fetch/control server, one ordered emitter, and
one, two or four arithmetic lanes. Each context keeps its own stream order;
each tile waits for all four context frontiers before ordered emission. An
eight-tile ring bounds admission and releases a slot when the immediate
external consumer takes its emitted coefficient tile.

The same V84 LOW/HIGH weights and assumed 100 MHz are retained as controlled
inputs. Each context/tile's fetch batch precedes its arithmetic batch. Header
prefetch can overlap prior arithmetic within the admitted window, and contexts
reset separately at real chunk boundaries. This is a prospective architecture
with batched operations, **not an instruction-level or RTL clock trace**.
Even its one-lane case decouples fetch and arithmetic, so it is not a direct
timing comparison against the original single-engine RTL.
The all-visible matched wire control is not scheduled here, so these results
also do not establish a matched-control decoder speedup.

The full campaign covers all 457 native sources, both actual chunk profiles,
LOW/HIGH weights and lanes 1/2/4: **5,484 schedules**. Four cohort processes
preserve independent histories and source identities. Eighteen synthetic
checks exercise balanced work, one-stream dominance and shared-fetch limits.
The final audit independently checks all row work/counts and statistics and
reconstructs four retained full witness DAGs using a separate frozen
constructor. Other schedules retain in-process audits and timeline hashes,
rather than complete timelines.

All four cohort processes completed with exit code 0. The independent model
audit created and then rechecked `model-verification.json`, both with exit
code 0; repeat output is captured in `model-audit.log`. The audited results
cover all 457 sources for every row below:

| Residual chunk cap | Arithmetic lanes | LOW median / max ms | HIGH median / max ms | LOW / HIGH front-only cases below 10 ms |
|---|---:|---:|---:|---:|
| 256 | 1 | 3.89676 / 13.10073 | 7.42483 / 25.01289 | 399 / 302 of 457 |
| 256 | 2 | 2.37868 / 7.35281 | 4.52181 / 14.03072 | 457 / 376 of 457 |
| 256 | 4 | 2.22303 / 6.68774 | 4.22345 / 12.75125 | 457 / 410 of 457 |
| Whole plane | 1 | 3.84096 / 13.01751 | 7.37003 / 24.92039 | 405 / 302 of 457 |
| Whole plane | 2 | 2.34734 / 7.23107 | 4.47110 / 13.83299 | 457 / 378 of 457 |
| Whole plane | 4 | 2.19716 / 6.56867 | 4.17342 / 12.53027 | 457 / 418 of 457 |

Two lanes are the useful first comparator. Four lanes give a smaller further
reduction because work is uneven and the fetch/control server remains shared.
The HIGH case still exceeds 10 ms for some sources even with four arithmetic
lanes; LOW/HIGH are assumptions, not calibrated timing bounds.

A frontend-only conditional time below 10 ms is not full validated FPGA
decoding below 10 ms. Operation-map/outer-envelope parsing and CRC, HUD,
dequantization/reconstruction, pixel memory, display, physical RAM ports,
descriptor/control storage and ESP32 execution are excluded.

## Reproduction

Collection refuses to overwrite its retained index:

```sh
python3 scripts/cu66-v86/collect_contexts.py
```

Verify retained native observations:

```sh
python3 experiments/python-gamebub-v86/contexts/verify.py
```

The full model runner writes a new four-cohort session rather than overwriting
an earlier one:

```sh
python3 experiments/python-gamebub-v86/contexts/run_model.py
```

Recheck the selected retained model without rerunning the scheduler:

```sh
python3 experiments/python-gamebub-v86/contexts/audit_model.py --session experiments/python-gamebub-v86/contexts/model-sessions/20261106T134837375141Z-e85a111c --verify
```

No FPGA fit/Fmax/DSP count, physical throughput, sustained 30-fps operation,
full validated under-10-ms decoder or ESP32 transport result follows from this
study.

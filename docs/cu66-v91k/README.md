# V91k: reference reconstruction and base RGB565 output

V91k connects the actual supported CS88/BR88 frame path through dequantization,
IDCT and canonical pixel reconstruction. A second RTL simulation reads the
**actual candidate memory written by that path** and converts it to base RGB565.
The frame geometry remains 720×480 YUV420. HUD/content validation and atomic
publication are later gates; these images and outputs remain provisional.

## Functional coverage

The retained matrix has 11 original inputs under FAST and SLOW service. Six
successful inputs per profile produce a complete 518,400-byte canonical frame:
four related native gameplay frames, one synthetic varied-quantizer case and
one synthetic all-visible-COPY case. The native current/reference bytes are
checked against the digest-verified V82 pixel archive and accepted V88/V90
receiver histories. Synthetic cases have explicit separate provenance.

Mode 0 reads the same-position accepted reference tile, mode 1 writes hidden
CONST128 without reading a reference, and mode 2 adds the signed RTL residual
to key prediction 128 or the accepted reference, then clamps to [0,255]. The
actual retained admission mode/scale RAM is read through its registered port;
the bench does not provide a substitute mode stream. The unchanged V69
reconstruction arithmetic consumes actual V91j residual handshakes.

Each full candidate contains 8,100 canonical tiles. Per seed, 12 successful
case/profile combinations check **6,220,800 complete-frame canonical bytes**
and **4,147,200 base RGB565 words**. Additional canonical bytes emitted before
the late third-plane CRC failure are checked as provisional prefixes. Repeated
profiles and seeds are not additional distinct source content.

The canonical directed suite has 21 checks, including held residual/canonical
output, abort/reset with accepted scratch and reference requests, response-tag
and bus errors, blocked replacement, snapshot ownership and clean retries.
The converter adds eight directed checks for byte-read drain, held output,
wrong response epoch, bus faults and invalid start identity. Four constant-color
smoke frames additionally exercise signed chroma, clipping and neutral gray.

See [the exact arithmetic/vector contract](reconstruction-contract.md),
[RTL ownership notes](../../fpga/experiments/cu66-v91k/README.md),
[conversion notes](../../fpga/experiments/cu66-v91k/rgb/README.md),
[summary](../../experiments/python-gamebub-v91k/summary.json) and
[independent audit](../../experiments/python-gamebub-v91k/audit.json).

## Memory and timing interpretation

The canonical consumer's `ready` means that byte's candidate-memory write has
committed. FAST accepts one byte per cycle; SLOW adds finite seeded stalls.
A reference tile is a 64-byte logical burst, charged eight edges after request
acceptance in FAST or 12–24 in SLOW, plus request stalls. One reference owner
survives local reset/abort until its matching response drains. The model does
not stand in for a physical SDRAM controller or infer achieved bandwidth.

Reconstruction adds 320 logical payload bytes (signed residual tile, reference
tile and frozen output tile) beyond the existing 256-byte coefficient banks,
math workspace and 98,304-byte packet staging. The candidate canonical bank is
518,400 bytes, and a delta frame leases a separate immutable reference bank of
the same size. A retained RGB565 bank would add 691,200 bytes; the converter
interface can instead feed a suitably owned output consumer. No mapped fit is
claimed from these logical capacities.

RGB565 replay makes nine acknowledged byte reads per pixel: **3,110,400 reads
per frame**. It uses native horizontal-then-vertical chroma interpolation, exact
signed floor shifts and clipping. This uncached schedule deliberately exposes
the real integration cost. It is a correctness baseline, not the final
low-latency memory schedule. FAST returns a byte after two edges; SLOW uses two
through six plus finite request/output stalls. All accepted RGB words must
match independent goldens derived without DUT output.

Canonical and conversion cycles are separate measured RTL fences. Their sum
is a **sequential candidate-memory replay service count**, not a monolithic
shared-controller, transport, display or validated-publication latency. A
routed clock and physical service measurements are still required. Earlier
V91j residual-only cycle counts are a different endpoint.

## Measured failures retained

The first strict compile identified an unconnected named `ref_ready` port. The
new path now observes and asserts that handshake. The first gameplay RGB run
found an unsigned expression context affecting negative arithmetic shifts at
pixel 22,320; an explicitly signed luma integer fixes the expression, and signed
chroma/clipping fixtures plus the complete actual-frame suite recheck it. Failed
attempt snapshots/logs remain separate and cannot qualify the final summary.
No warnings or assertions were waived.

## Next optimization and integration

The [cache implementation and promotion plan](chroma-cache-plan.md) defines
the exact read budget, row ownership, synchronous banking and regression gates.

A two-row chroma cache needs **1,440 logical bytes** (two rows × 360 columns ×
two planes). Retaining row pairs and loading each chroma row once would reduce
external reads to 345,600 luma + 172,800 chroma = **518,400 reads per frame**,
six times fewer than this baseline. This is an architectural count, not a
measured RTL speedup. Preserve both interpolation rounding points and edge
replication. Four 180×16-bit parity/row banks could expose Cb/Cr neighbors
through synchronous ports; exact 7-series RAM mapping remains to be measured.
Invalidate row tags on cancellation while retaining any accepted fill request
until its matching response drains. Compare cached and uncached controls with
identical source bytes and declared finite memory service.

Proceed to V91l HUD/content validation, canonical hashes/seals and atomic
publication. Join those consumers and finite transport/display service at
V91m; qualify memory scheduling before claiming the 30-Hz workload. Physical
30 fps and complete validated decoding strictly below 10 ms remain open.

## Reproduce

Use the existing `gamebub-cu66-v69-build` container from the repository root:

```sh
python3 experiments/python-gamebub-v91k/model.py
python3 scripts/cu66-v91k/run_rgb_smoke.py
python3 scripts/cu66-v91k/run_pipeline.py --seed 911501
python3 scripts/cu66-v91k/run_pipeline.py --seed 911502
python3 experiments/python-gamebub-v91k/verify_results.py
python3 scripts/cu66-v91k/summarize.py
```

The runner pins source/vector/command hashes, strict Verilator/GCC flags and
compressed canonical output/event artifacts. Temporary uncompressed vector
aliases are reconstructed by hash and removed. The independent auditor checks
both current-source seeds, exact pixel/word goldens, retained/live hashes and
ownership/service receipts. No board or ESP32 firmware is exercised here.

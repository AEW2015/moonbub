# V91k chroma cache: measured RGB565 memory reuse

This follow-up replaces repeated external chroma reads with two registered local
rows. The unchanged V91k converter is the control. Both RTL paths read the same
actual canonical candidate memories captured by V91k and compare every accepted
RGB565 word with independent goldens. Wire bytes, quantization, geometry, image
quality, ESP32 forwarding and the canonical decoder are unchanged.

## Architecture

Four 180×16-bit row/parity arrays hold paired Cb/Cr bytes: **1,440 logical payload
bytes**, plus registered read data, row tags, control and arithmetic registers.
Each array has one registered lookup port and byte-enabled fill writes. No
cache payload is bulk-reset. This structure is intended for synchronous FPGA
RAM; physical 7-series mapping, fit and timing have not been qualified.

Fill Cb row 0, Cr row 0, Cb row 1, Cr row 1 before the first pixel. A row becomes
valid only after its last Cr byte ACK, with all 720 Cb/Cr bytes acknowledged.
Two luma rows reuse each row pair. On advance, retain the old bottom as top and
fill only the new bottom. Row 239 aliases the final bottom; there is no read
past the plane. Column-parity banking permits neighbor lookup with one read
per bank. Horizontal rounding precedes vertical rounding, with exact signed
color conversion and edge replication.

See the [independent contract](cache-contract.md) and
[RTL details](../../fpga/experiments/cu66-v91k-cache/README.md).

## Results

| Per complete 720×480 frame | Uncached control | Registered cache |
|---|---:|---:|
| External luma byte reads | 345,600 | 345,600 |
| External chroma byte reads | 2,764,800 | 172,800 |
| Total external reads/ACKs | 3,110,400 | 518,400 |
| FAST full conversion cycles | 10,022,400 | 2,938,320 |
| FAST first accepted read → first accepted RGB word | 28 | 4,328 cycles |

The cache makes **six times fewer external reads** and uses **70.68247% fewer
FAST conversion cycles**. Full conversion includes all prefill, synchronous
lookup, arithmetic, output and drain work. Startup increases because the first
row pair loads before any pixel can be emitted. The first-read fence is not
the frame-start or source-capture fence.

The independent FAST count is `518400*3 + 345600*4 + 720 = 2938320`: three
request/ACK edges per external byte, four local lookup/convert/output edges per
pixel, and 480 luma-row checks plus 240 completed-fill checks. The control count
is `3110400*3 + 345600*2 = 10022400`.

SLOW applies the same seeded rules to both benches: finite request/output
stalls and byte ACK two through six edges after acceptance. Changed schedules
consume random draws differently, so absolute stall traces differ. The
[summary](../../experiments/python-gamebub-v91k-cache/summary.json) records
per-case SLOW measurements and cycle reductions (75.48199–75.49652% fewer
cycles in the retained main matrix). These are observations under
those rules, not an identical-stall-trace proof or measured board bandwidth.

## Qualification coverage

Two final seeds each run six existing case identities under FAST and SLOW
service, including four related native frames and two previously labeled
synthetic cases. The input bytes come from simulated candidate-memory writes emitted by the
V91k RTL. Each path checks 4,147,200 RGB words per seed for this matrix.

A separate deterministic synthetic edge frame runs under both profiles. Its
last two chroma rows and columns differ, closing a coverage gap in the retained
frames, whose last two chroma rows are identical. Both paths check another
691,200 RGB words per seed. Across both final seeds, each path checks
**9,676,800 RGB565 words**, with cached/control output identical.

The unchanged control has eight recovery checks. The cache has 29, covering
partial Cb/Cr fill, luma reads, registered lookup request/response, held RGB
output, wrong epochs, matching bus errors, last-fill ACK coincident with
abort/reset, and later row eviction after pixels have already been emitted.
New starts cannot bypass pending physical read drain. Local row validity clears
on cancellation; accepted physical work retains its owner until a matching
response drains. Mutated external start descriptors cannot change a leased
frame. Exact request/data schedules, row-fill receipts and lookup latency are
checked independently. No backdoor RAM corruption is used to claim fault bins.

The [audit](../../experiments/python-gamebub-v91k-cache/audit.json) and bundle
manifest pin live and retained sources, actual input provenance, gzip/raw
hashes, strict commands, outputs and selected attempts. Earlier passing runs
before the diagnostic/late-eviction additions remain retained as superseded
coverage evidence; only current-source final runs qualify the summary.

## Reproduce

Use the existing `gamebub-cu66-v69-build` container from the repository root:

```sh
python3 experiments/python-gamebub-v91k-cache/model.py
python3 scripts/cu66-v91k-cache/run_comparison.py --seed 911601
python3 scripts/cu66-v91k-cache/run_comparison.py --seed 911602
python3 experiments/python-gamebub-v91k-cache/verify_results.py
python3 scripts/cu66-v91k-cache/summarize.py
```

Both builds use Verilator `--assert -Wall`, GCC `-Wall -Wextra -Werror` and two
compiler jobs. The runner snapshots sources and keeps compressed input/event
artifacts; temporary plain TSVs are reconstructed by pinned hashes and removed.
The frozen canonical pipeline need not be rerun for this converter-only change;
its input and accepted-reference provenance remain pinned to V91k. The old
report records build-base revision `914fe698`; its exact source snapshots are
published in qualified V91k bundle commit `a0a60502`, which is this study's
frozen baseline. A recorded build-base Git revision alone is not the snapshot
source manifest.

## Next gates

V91l still needs HUD/content validation, canonical hashes/seals and atomic
publication. V91m must join the complete finite transport, memory and display
path. This conversion remains a separate RTL replay of candidate memory and
cannot establish monolithic validated latency or presentation rate.

Next compare bounded aligned multi-byte reads with this byte-service cache,
including every accepted beat, gather/edge byte, bus stall and pending-owner
lifetime. Local lookup can also overlap acknowledged luma fetches if pixel
owners and output credits remain bounded. Measure those changes individually;
do not divide transaction counts by a bus width and call that RTL performance.

No routed clock, physical RAM fit, ESP32 throughput, board presentation,
sustained hardware 30 fps or complete validated decoding below 10 ms is proven
by these simulations.

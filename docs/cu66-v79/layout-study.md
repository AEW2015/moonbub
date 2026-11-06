# V79 grouped-tile physical layout study

This Python prototype tests whether changing the physical arrangement of
canonical tiles reduces the conflict between portrait display reads and
raster-order decoder traffic. **The best shape depends on the schedule.**
The 4×4 hypothesis is useful for a next experiment; it is not an assumed or
measured hardware winner. No existing memory layout, source, result, or HDL
is changed.

```sh
python3 scripts/cu66-v79/layout_study.py
python3 scripts/cu66-v79/layout_study.py --check
```

The standard-library script produces `results.json`, `mappings.json` and
`measurements.csv` under `fpga/experiments/cu66-v79/layout-study/`. The check
command recomputes all artifacts and compares exact bytes. Input hashes pin
the script, frozen traces, source memory geometry and actual YUV fixture.
There are six mappings and 96 service-work scenarios; no RTL build is used.

## Address contract and verification

A physical SDRAM row holds 512 x16 words, enough for sixteen 32-word / 64-byte
canonical tiles. Compare groups **16×1, 8×2, 4×4, 2×8, 1×16** tiles. Each group
occupies one physical row, in local raster order. Groups themselves are in
raster order. Each plane is padded to complete groups and starts on a row
boundary. Logical grids remain Y=90×60 tiles and U/V=45×30 tiles; resolution,
logical tile order, packed-u8 contents and byte order are unchanged.

For group width G, height H=16/G, logical tile `(x,y)` and plane width W:

```text
groups_per_row = ceil(W / G)
group_index = floor(y/H) * groups_per_row + floor(x/G)
physical_tile = group_index*16 + (y%H)*G + x%G
x16_address = bank_base + new_plane_offset + physical_tile*32 + block*8
```

Bank bases stay `0x080000`, `0x480000`, `0x880000`; corresponding HUD bases
stay `0x100000`, `0x500000`, `0x900000`. New plane spans and offsets are:

| Layout | Y/U/V offsets, x16 words | Y/U/V spans, x16 words | Extra allocation bytes |
| --- | --- | --- | ---: |
| Current unpadded | 0 / 172800 / 216000 | 172800 / 43200 / 43200 | 0 |
| 16×1 | 0 / 184320 / 230400 | 184320 / 46080 / 46080 | 34,560 |
| 8×2 | 0 / 184320 / 230400 | 184320 / 46080 / 46080 | 34,560 |
| 4×4 | 0 / 176640 / 225792 | 176640 / 49152 / 49152 | **31,488** |
| 2×8 | 0 / 184320 / 231424 | 184320 / 47104 / 47104 | 38,656 |
| 1×16 | 0 / 184320 / 230400 | 184320 / 46080 / 46080 | 34,560 |

The largest span is 557,056 bytes per canonical bank, below the 1,048,576-byte
space before its HUD base. Every active tile is checked in all three banks:
no alias, cross-bank address, HUD overlap or partial BL8 occurs. Plane spans
are disjoint and all grouped-plane offsets/spans are row aligned. The padded
16×1 layout is a separate candidate from the current unpadded raster tile
layout; it changes plane offsets and the stride at logical row boundaries.

The actual 518,400-byte golden YUV fixture named by column four of the first
row of `experiments/cu66-native-v69/index.tsv` is scattered through each
candidate layout. Its exact file is
`experiments/cu66-native-v69/fixtures/927e4b27b815228919275cdbd3cbdfcc8b7cbd0eae60749a3919e1754e5d6257.yuv`;
its SHA-256 must equal that filename/index digest. It is retained canonical
fixture data, rather than an address-dependent synthetic pattern. An independent inverse mapping scans physical
tile positions, reconstructs raster pixels from little-endian x16 word pairs
and requires exact whole-fixture equality and SHA-256. All 8,100 active tile
locations are injective; their 32-word intervals do not overlap, proving
injectivity of all active words and byte lanes. Padding tiles retain a sentinel
and are never transferred. This checks contents and address bijection, not an
RTL decoder or display pipeline.

## Traffic and declared synthetic scheduler

The script transforms the exact retained **V76 display BL8 request order**
through logical plane/tile/block identities into each new address map.
It retains all 32,400 YUV reads and 2,640 HUD reads. The exact static SAFE-map
reference list provides 7,806 tiles / 31,224 BL8 reads in immutable bank 0,
shared with display. Full canonical writes traverse all 8,100 logical tiles /
32,400 BL8 in candidate bank 1. HUD writes and functional verification use
2,640 BL8 each in bank 1. Thus every combined scenario transfers exactly
**103,944 BL8 / 1,663,104 bytes**, for every layout. Allocation padding increases
capacity, with **zero added transfer bytes** in this experiment.

That combined workload is one cold synthetic display trace plus one delta
workload. It is not one actual V78 decode-window display count and does not
repeat panel fetches as elapsed work increases. The physical-address bijection
preserves the retained trace's logical blocks; cache misses are replayed,
without implementing a new hardware cache.

Each standalone stream starts with all four physical banks closed. Combined
scenarios use five queues, all released at clock zero. Deterministic round
robin issues **4, 8 or 16 whole BL8 grants** from each nonempty queue, in this
order: display, reference, canonical write, HUD write, HUD verification.
Drained queues are skipped. This is an explicitly synthetic interleaving;
the actual V74 LCD grant policy, codec/qmap release times, candidate-write
dependencies, HUD preparation and response backpressure are absent. In
particular, HUD verification can precede completion of all synthetic HUD
writes: the model counts address/service work and is not an execution-correct
functional frame scheduler. Standalone streams and combined scenarios are
separate measurements, never added together as wall time.

The source-derived open-row approximation charges read/write row hits 15/13
clocks, activation four clocks, conflicting precharge four, and three bridge
gap clocks per request. Sensitivities use refresh disabled or every 750
clocks; refresh is approximated at an eligible boundary as 15 clocks, closes
all bank rows and restarts its interval at the modeled REF command. `ACT`
counts row openings, `PRE_conflict` excludes refresh precharges, and `REF`
counts refresh reset events. These are model counters, not observed command
pins. There is no fit to measured controller service or V79 wall latency.

## Results and implication

Standalone ACT counts with refresh disabled show the locality tradeoff:

| Layout | Display ACT | Reference ACT | Canonical-write ACT |
| --- | ---: | ---: | ---: |
| Current | 9,346 | 500 | 507 |
| 16×1 | 9,346 | 535 | 540 |
| 8×2 | 5,296 | 1,056 | 1,080 |
| 4×4 | 3,316 | 2,037 | 2,100 |
| 2×8 | 2,326 | 3,941 | 4,080 |
| 1×16 | **1,786** | 7,806 | 8,100 |

Tall groups help the portrait display's vertical coded-tile walk, while
increasing row changes for raster-order reference reads and writes. With
refresh disabled, the combined synthetic service-work results are:

| Layout | Quantum 4: work clocks | Quantum 8: work clocks | Quantum 16: work clocks |
| --- | ---: | ---: | ---: |
| Current | **1,954,864** | 1,917,472 | 1,898,864 |
| 16×1 | 1,955,112 | 1,917,784 | 1,900,712 |
| 8×2 | 1,955,208 | **1,890,104** | 1,874,864 |
| 4×4 | 1,960,888 | 1,897,312 | **1,874,312** |
| 2×8 | 1,974,496 | 1,913,792 | 1,896,232 |
| 1×16 | 2,003,504 | 1,970,600 | 1,955,120 |

With the modeled 750-clock refresh interval, 8×2 has the lowest combined
service work at quantums 4 and 8; 4×4 is lowest at quantum 16. All actual
numbers are retained in CSV/JSON. A shape's apparent advantage can reverse
with interleaving. None of these differences is a calibrated hardware gain,
decode-time estimate, source-fps estimate or under-10-ms claim. LCD deadlines
are not modeled or qualified here.

No default layout is recommended from these synthetic interleavings. First
capture actual controller command chronology, per-client acceptance/completion,
candidate-ready events and native LCD deadlines. Then run a controlled,
versioned A/B layout simulation with matching arrivals and phases; **8×2 and
4×4** are candidates to compare, rather than predetermined winners.
It must update every canonical reader/writer,
reference prefetch walker, renderer address calculation, software painter and
independent oracle. The frozen memory map's 259,200-word canonical allocation
guard must become the appropriate padded span; leaving that guard unchanged
would reject legal padded-tail accesses. Every address must remain guarded,
with the unchanged HUD boundaries. Descriptors or reset/versioning must
prevent interpreting an old bank with a new layout. Logical canonical hashes,
plane dimensions, byte order, ownership, abort/drain semantics and exact native
pixels must remain checked. No such integration is implemented by this study.

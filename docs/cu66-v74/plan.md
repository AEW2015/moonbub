# CU66 V74 tile-major implementation and direct-YUV study

## Scope

This iteration combines the V74 tile-major canonical memory and wide-read
painter implementation with a separate Python-only direct-YUV/cache traffic
study. V74 RTL simulation covers tile writes, painter conversion/HUD output,
SDRAM command traffic, history, LCD presentation, and integrated system behavior.
The direct-YUV study itself does not add RTL or prove exact output, physical
service, or frame cadence. V73 and earlier bundles remain frozen and are
checked by `scripts/cu66-v74/verify_baseline.py`.

Completed V74 RTL scope includes contiguous 8×8 physical tiles (32 x16 words
per tile), four full BL8 canonical writes per tile, eight-word P1 reads with
held response snapshots, a tile-aware painter, and two/four-frame system
history. See [V74 results and integration handoff](hardware-handoff.md) for
measured simulation results and remaining system-level gates.

## Baseline verification

The pinned V73 commit is `78d35ddc45fb22732804967748f31042860dbdce`; it is required
to be an ancestor of `HEAD`, not equal to it. The read-only verifier checked
bundle counts: V69 4,879; V70 460; V71 122; V72 131; V73 161. It ran the V73
baseline verifier, which recursively runs the earlier authorities. These checks
establish file integrity and ancestry only, not functional behavior or cadence.

## Study question

Compare physical-raster-order point sampling through a bounded BL8 cache with an
8-row physical-strip prefetch plan. The prototype address function uses physical
tile-major 8×8 byte-sample tiles, packed as 32 x16 words per tile. Y, Cb, Cr base
words are `0x80000`, `0x80000+172800`, and `0x80000+216000`. Cache tags use
`physical_word_address >> 3`; one BL8 read has eight x16 beats and 16 wire bytes.

Physical active coordinates map to coded coordinates as `u=physical_y-40`,
`v=physical_x`; the active image is 480×720 within the 480×800 panel. Each 8-row
physical strip therefore scans 8 coded-u columns by 480 coded-v rows. There are
90 such strips. Y touches 240 BL8 lines per strip. Depending on chroma tile
alignment, each chroma plane touches 120 or 240 lines, including the required
bilinear halo. The strip-prefetch model retains one rolling LRU cache between
strips; 8/64/128/256/512/720/1024-line capacities were evaluated. A
720-line (11,520-byte) cache retains chroma halo tiles across strips and reaches
the 518,400-byte packed-plane traffic bound.

## Frozen constants and assumptions

- Panel timing: Htotal 541, Vtotal 834, 34.058 ns pixel period; 65.0755 Hz.
- The 8-physical-row scheduling deadline is 147.403024 µs.
- Raw memory bandwidth is treated as 200 MB/s.
- 20–32 controller clocks per BL8 is an explicit conservative transaction-cost
  assumption, not a measured service time for this path. The report uses the
  current model's 100 MHz controller clock and separately shows raw-bandwidth time.
- The controller ACT/PRE estimate uses issue order (Y then Cb then Cr, ascending
  line address per plane) and the requested address fields: bank `addr[23:22]`,
  row `addr[21:9]`. It does not model refresh, turnaround, arbitration, or
  controller-specific row policy. HUD addresses are not included in ACT/PRE.
- Four native HUD rectangles total 21,120 x16 words per panel. Opaque HUD areas
  still fetch YUV conservatively; HUD reads are additive. Maximum HUD reads in
  one strip are 1,536 bytes.
- Candidate uploads write one 720×480 YUV420 frame (518,400 bytes) at 30 fps.
  Direct scanout reads are charged at panel refresh. Other foreground work and
  reference-client sharing are unmodeled. Front-generation/lease cache
  invalidation on buffer switch remains an RTL integration gate.

## Current V74 iteration and next milestones

The V74 tile-major memory, painter, controller, LCD and integrated-system
evidence is complete for this simulation iteration and retained in separate
result artifacts. The direct-YUV script here is a separate memory-traffic
estimate; it does not claim exact conversion/HUD output or establish a
direct-YUV RTL path.

Next gates for direct YUV are: implement front generation/lease-aware cache
invalidation; compare every active pixel against the native YUV/HUD oracle;
integrate the direct reader with the existing controller and LCD timing;
exercise upload plus P-reference plus HUD plus scanout in one fixed-arrival
30-fps campaign; and measure the target controller service and underruns. The
current estimate shows that a 720-line rolling cache can reach the packed-plane
traffic bound. A 20-clock-per-burst service estimate fits the largest strip
before unrelated traffic; 32 clocks per burst misses the 8-row deadline. Exact
pixels, memory arbitration, and target service are required before making a
cadence claim.

## Reproduction

```sh
python3 scripts/cu66-v74/verify_baseline.py
python3 scripts/cu66-v74/direct_yuv.py > fpga/experiments/cu66-v74/direct-yuv-results.json
```

The JSON retains source hashes, every strip's burst/HUD/ACT/PRE counts, cache
sizes, and all assumptions. See [direct-YUV results](direct-yuv.md).

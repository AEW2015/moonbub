# V76 direct-YUV physical-memory service experiment

The frozen controller can serve the synthetic direct-YUV/HUD read trace within
its eight-row deadline without background traffic. With paced shared-front
reference reads and uploads, the current P1 route fails; the dedicated LCD route
misses one strip by 3.08 µs. A separate one-strip-early release experiment lets
the dedicated route meet all original deadlines. This is a measured scheduling
hypothesis for the next display design, not an implemented direct-YUV renderer
or a 30-fps proof.

## What is implemented and checked

`generate_service_trace.py` independently maps 720×480 YUV420 into the physical
portrait image: coded `(u,v) = (physical_y-40, physical_x)`. Each of 90 strips
covers eight coded-u columns by 480 coded-v rows. Samples use contiguous 8×8
packed-u8 tiles (32 x16 words per tile), Y/Cb/Cr word offsets
0/172800/216000 and bank-0 base `0x080000`. Chroma accesses use the exact 1/2/4
neighbor parity and edge clamps. The software trace retains a 720-line YUV LRU
cache, with a 16-byte physical BL8 line.

The four opaque HUD patches retain native geometry and packed patch-word order.
Patch x=22 is not aligned with the eight-column strip grid; the generator uses
actual packed word addresses, not simply logical HUD bytes divided by 16.
A separate 192-line (3,072-byte) HUD LRU retains overlapping blocks. Baseline
software cache capacity is therefore 11,520 + 3,072 = **14,592 bytes**, not a
combined 11,520-byte cache. These are request-trace cache capacities, not a proven live
consumer/prefetch buffer allocation. All caches start cold and roll within one panel
trace. Requests are ordered Y, Cb, Cr, HUD, ascending physical blocks per group.

The resulting trace has **32,400 YUV + 2,640 HUD BL8 reads**, 35,040 total
commands / 280,320 x16 words / **560,640 wire bytes**. Its largest strip has
576 reads / 9,216 bytes. These are cache-miss schedules; there is no RTL cache,
pixel consumer, YUV converter or generation-tagged front descriptor in this
experiment.

The self-checking HDL harness instantiates the unchanged `cu74_memory_system`,
`cu74_tile_memory`, `cu74_word_bridge`, `cu72_sdram_controller` and checked
`cu72_sdram_model`. It initializes bank-0 canonical data and HUD plus bank-2
reference data through **67,440 actual full-write commands / 539,520 physical
word beats**. No model backdoor initializes memory. Setup is excluded from the
measurement. Every foreground returned word is compared with an independent
address-derived 16-bit pattern; all background reference words are also checked.
Each functional run compares 280,320 foreground words and drains all accepted
operations. This is data/address/service verification, not video-pixel equality.

Both foreground interfaces are legal: P1 uses the actual wide auxiliary port;
the existing dedicated LCD port streams eight checked words with `last`
framing. Its frozen range guard accepts aligned canonical/HUD physical
addresses, so no mapping or guard bypass is used.

## Clock, admission and deadline contract

The model assumes a 100-MHz memory clock, 279-degree read sample phase, 4-ns
clock flight and tAC corners 2/7 ns. The panel timing is Htotal=541,
Vtotal=834, pixel period=34.058 ns, giving an eight-row period of
**147.403024 µs**. For the baseline schedule, strip i is released at
`start + floor(i*147403024/10000)` memory clocks and retains deadline
`start + floor((i+1)*147403024/10000)`. A late strip does not slide the next
release or deadline. Both service time and accumulated lateness are recorded.
The implied consumer timeline has strip i start consumption at its original
`(i+1)P` deadline, after an initial one-period preroll. Thus even the baseline
may retain the previous consuming strip while filling the next strip. Request-
trace LRU capacity alone does not prove that the consuming strip remains resident.
The separate structured-cache study budgets 19,968 bytes for two live strip
windows; no such live cache/consumer RTL is implemented here.

Rounding deadline timestamps to memory clocks is conservative by less than one
clock.

The default producer adds no idle clock between successive transfers: next
request acceptance can occur one clock after the prior response drains. Gap
statistics reset at strip boundaries to exclude scheduled inter-strip idle.
For P1, this is auxiliary-wrapper acceptance; internal bridge arbitration can
still delay that accepted request. LCD acceptance happens at the bridge and
therefore includes arbitration directly. The comparison includes two explicit
one-extra-idle-clock controls. All strip service times include request issue,
port acceptance, controller/bridge wait, real refresh and final response drain.

## Background traffic

Three modes are measured:

- Display only.
- Independent paced uploads at **8,100 tiles × 30/s** and references at
  **7,806 tiles × 30/s**, using absolute rational release clocks. Jobs queue
  without release-time sliding or dropping. Uploads use bank 1. References read
  immutable bank 0, the same physical bank used by foreground scanout.
- Continuous alternating upload/reference saturation, explicitly **not** a
  30-fps workload.

The reference order comes from the frozen profile's 7,806 nonhidden SAFE-map
plane/tile identities. It is a static service trace, not execution of a live
packet's entropy decoder or qmap. The upload order traverses all 8,100 tiles.
The request-generation and tile-adapter work are real HDL; codec computation,
CPU work and transport are absent.

Released and completed counts at foreground completion are recorded separately.
Pending jobs then drain, and every released job must complete. For example,
the baseline paced LCD case releases 3,202 uploads / 3,086 references; 3,194 /
3,079 complete before the last foreground response, and all 3,202 / 3,086
complete after tail drain. The approximately 13-ms foreground window is shorter
than a 33.333-ms source period. Zero background frame-window deadline misses in
this short sample is not proof that a whole frame's 8,100/7,806 jobs finish at
30 fps. Post-measurement tail work is included in final model command counters
but not the foreground elapsed interval.

## Baseline results: no early release

All **14 functional runs** pass with exact data. The twelve continuous-issue
cases cover two interfaces × three traffic modes × two tAC corners; two tAC=2
controls insert one idle producer clock. Corresponding tAC=2/7 cases have
identical summary and strip counters.

| Interface | Background | Worst strip service | Deadline misses / 90 |
|---|---|---:|---:|
| P1 auxiliary | None | 124.60 µs | 0 |
| Dedicated LCD | None | 118.94 µs | 0 |
| P1 auxiliary | Paced shared-front | 224.67 µs | 90 |
| Dedicated LCD | Paced shared-front | 150.48 µs | 1 |
| P1 auxiliary | Saturation | 259.44 µs | 90 |
| Dedicated LCD | Saturation | 149.99 µs | 1 |

The paced dedicated-port miss is **3.08 µs**; saturation's is 2.59 µs. The
smaller saturation maximum is a phase/locality effect, not proof that
saturation is an easier general workload. P1 is round-robin with the tile
client, while the LCD port has bounded priority. The interfaces are therefore
not interchangeable for this proposed display reader.

One extra producer idle clock raises display-only P1/LCD maxima to
**129.82 / 124.60 µs**. Continuous display-only runs have drain-to-next-port-
acceptance gap exactly one clock; controls have exactly two. With background,
the dedicated port's observed acceptance gap reaches 35 clocks paced and 36
clocks saturated. P1's wrapper still accepts after one clock while its bridge
wait remains inside measured service time.

An independent Icarus tAC=2 paced dedicated-port replay matches Verilator's
**entire summary counter record exactly**, including the 150.48-µs bound and
one missed deadline. `crosscheck-results.json` retains both command logs,
source hashes and the exact reference-log hash.

## Separate one-strip-lookahead hypothesis

A copied testbench changes **only release times**, to
`start + floor(max(0,i-1)*147403024/10000)`. Original strip deadlines remain
unchanged. Data, physical address order, background workload and frozen
controller/bridge are the same. It does not merge these runs into the baseline
14 or erase the no-lookahead failure.

| Interface | tAC | Worst individual service | Original deadlines missed |
|---|---:|---:|---:|
| Dedicated LCD, paced shared-front | 2 ns | 153.97 µs | **0 / 90** |
| Dedicated LCD, paced shared-front | 7 ns | 153.97 µs | **0 / 90** |
| P1 auxiliary, paced shared-front | 2 ns | 224.67 µs | **90 / 90** |

The dedicated-port run's minimum observed deadline slack is **24.70 µs**.
An individual service can exceed 147.403024 µs because it was released one
strip earlier; no deadline was extended. This release/deadline contract can retain **three** strip generations: strip
(i-2) consuming, strip (i-1) already ready, and strip i being filled. It requires
three Y columns, three chroma columns per plane and up to four packed-HUD block
columns per rectangle under the root's structured model: **29,184 bytes**.
The two-live-window 19,968-byte model does not justify this earlier-release pass.
The benchmark does not implement or prove that cache/lease architecture. The separate
[direct-YUV architecture study](direct-yuv-architecture.md) supplies a bounded
storage hypothesis; it must still become actual RTL, exact video output,
generation invalidation and vblank/read-drain lease switching before use.

The lookahead foreground fill completes after 13.03324 ms; it releases 3,167 /
3,052 paced upload/reference jobs, of which 3,159 / 3,044 complete before the
last foreground response, with all remaining jobs subsequently drained.
This is one cold panel fetch trace, not steady-state source-switch operation.

## Evidence, provenance and reproduction

Main results and logs are under `fpga/experiments/cu66-v76/service/`:
`trace.json`, `results.json`, `crosscheck-results.json` and the separate
`lookahead-results.json`. Every producer pins its source files and retained
command logs. Functional PASS and deadline PASS/FAIL remain separate fields.
The trace is synthetic; the controller service is actual HDL/model execution.

The first strict build's width/unused diagnostics are retained in
`build-attempt1-width-unused.log`. Fixes were limited to this new testbench.
The initial one-idle-cycle qualification is preserved in the hashed
`initial-gap-display/` ZIP. A subsequent cross-simulator check found a
blocking testbench cycle counter racing with release/timestamp processes:
physical and deadline counters matched, but four instrumentation metrics
varied. The counter now uses a nonblocking update; all 14 runs were requalified
and Icarus now agrees exactly. The superseded qualification is retained in the
hashed `before-deterministic-cycle/` ZIP and the initial metric-difference JSON.
Archives are checked internally against their own member manifests, not current
sources. No frozen production RTL was changed. The lookahead build's initial
width diagnostic is separately retained. The valid base/lookahead qualifications
before separating quick/full log filenames and clarifying the consumer timeline
are archived in `before-log-path-separation/`; quick runs now have their own
log paths so subsequent full runs cannot stale their log bindings.

```sh
python3 scripts/cu66-v76/generate_service_trace.py
python3 scripts/cu66-v76/run_service.py --quick
python3 scripts/cu66-v76/run_service.py
python3 fpga/experiments/cu66-v76/service/run_crosscheck.py
python3 fpga/experiments/cu66-v76/service/run_lookahead.py
```

Each build uses one job in the existing container. These results do not prove
an RTL cache, converter/HUD output, descriptor/lease safety, actual decoded
source arrivals, target fit/Fmax/CDC/electrical timing, live ESP32 or CPU service,
physical 30 fps, or strict maximum validated decode under 10 ms. The next useful
implementation is a bounded dedicated-port prefetch reader and cache/consumer
ownership model, followed by actual renderer pixels and full-source integration.

# CU66 V75 — BRAM-friendly painter and guarded HUD bursts

V75 implements two improvements to the V74 tile-major pipeline: synchronous
full-word input-cache reads, and guarded full-BL8 processor HUD upload/readback.
The input caches now map to BRAM in an unplaced XC7 family flow, removing
2,304 RAM64M cells while increasing RAMB18E1 allocation from 8 to 32. Four
chronological sources remain bit-exact with zero detected LCD underruns.

The measured performance tradeoff is mixed. The matched P transaction improves
**92.38045 → 75.86986 ms**, while the key transaction regresses
**45.43165 → 47.16430 ms**. The four-source maximum is **87.28132 ms**.
These are command-model measurements, not physical hardware results. The
30-fps and strict maximum validated-decode-under-10-ms milestones remain open.

## Implementation and interface

The new painter registers complete 16-bit Y/Cb/Cr bank words before byte
selection. An extra right-word-fetch state preserves the exact bilinear
rounding, chroma clamps, opaque HUD rectangles, portrait transpose and borders.
Each of the 24 input banks now has one synchronous read port and one write
port. Logical data storage stays **23,056 bytes**. The no-stall painter pays
**345,600 additional cycles**, one per active pixel, at the same assumed clock.
See [painter](display.md) and [frontend/mapping evidence](elaboration.md).

The new top-level HUD port adds `hud_aux_req_burst`,
`hud_aux_req_read_burst`, `hud_aux_req_burst_data[127:0]`,
`hud_aux_req_byte_enable[15:0]` and `hud_aux_rsp_burst_data[127:0]`.
Scalar callers tie both flags and the byte-enable mask to zero. Full writes
require write=1, write-burst=1, read-burst=0, mask=`ffff`; full reads require
write=0, write-burst=0, read-burst=1, mask=0. The lowest-address x16 word occupies
bits 15:0. Scalar compatibility data remains available.

Wide transfers must start at an eight-word-aligned physical address and keep
all eight words inside the selected 21,120-word HUD allocation. Writes must
start at the next uncompleted word; generation/frame, ownership, bounds and
request shape are checked before a physical command. The arbiter captures all
qualifiers and payload at acceptance. Completed-word coverage advances by eight
only after the actual drained write acknowledgment. Invalid requests return
local errors, and accepted commands retain their owner through response drain.
No enqueue-time success, early HUD-drain claim or partial mask bypass is added.
See [HUD contract and control tests](hud.md).

V74 canonical layout, frozen memory adapters and controller/model, CU66 packet
syntax, canonical hash order, source/reference/front leases and processor commit
reconciliation remain unchanged. This is an internal memory/interface change;
it does not add a new encoded-video format or modify Sunshine/ESP32 packet
forwarding. An actual processor/MMIO interface and software driver for the new
128-bit capability still need hardware integration. Old board wrappers must tie
the new scalar-compatible qualifiers to known zeros rather than leave them open.

## Integrated ablation

Three runs compare the same packets and clocks:

| Source | V74 scalar HUD | V75 scalar HUD | V75 burst HUD |
|---|---:|---:|---:|
| Key frame 0, transaction | 45.43165 ms | 48.88119 ms | 47.16430 ms |
| P frame 1, transaction | 92.38045 ms | 84.93487 ms | 75.86986 ms |
| Key validated interval | 15.80350 ms | 15.80350 ms | 14.08760 ms |
| P validated interval | 36.84403 ms | 27.05641 ms | 16.98661 ms |

Scalar/burst V75 runs use identical RTL, testbench, fixture and producer hashes;
only the runtime HUD mode changes. The scalar configuration identifies the
resource/scheduling tradeoff separately from enabling full transfers. Relative
to V75 scalar, bursts reduce the key/P transactions by **3.51% / 10.67%** in
this specific replay. Relative to V74, the combined key is **3.81% slower** and
the matched P is **17.87% faster**.

These decoder-paced runs change when the new front first reaches vblank, and
therefore the phase of background LCD reads and refresh relative to the next
source. In particular, the first P partially executes before initial scanout
starts in V75. Do not interpret its 16.98661-ms validated interval as a steady
worst-case decode bound, or attribute every whole-system timing difference to
one cache operation. A fixed-arrival, phase-controlled campaign is still needed.

Four-source burst history transactions are **47.16430, 75.86986, 87.28132,
85.49906 ms**. Its validated intervals span **14.08760–29.40852 ms**; composition
spans **33.07667–58.88256 ms**. Each complete transaction exceeds the 33.333-ms
new-source budget. Removing composition alone has not been implemented, and the
short modeled validated tail excludes real CPU/transport service. It cannot
establish 30 fps or a target decoding bound.

The history verifies four distinct sources and 17 complete repeated rasters
(5/5/6/1), with **14,016 clean lines, zero mismatching black lines, zero LCD
underruns and 6,727,851 observed pixels**. Refreshing an unchanged front is not
counted as a new streamed frame. Lost processor COMMIT acknowledgment still
retries without a second global commit.

The native oracle reconstructs all logical planes from actual tile-major SDRAM
contents and checks the canonical hash, every portrait RGB565 word and live LCD
pixel/order/generation behavior. Predicted reference pixels come from previous
RTL-produced SDRAM, never from golden backdoor data. Wide HUD readback is
flattened into native patch order and its actual readback hash is checked before
the transfer fence. The bench's first-correct-pixel timestamp can include black
borders; it is not first-game-image or input-to-photon latency.

## Memory and resource results

| Per complete frame | V75 scalar | V75 burst |
|---|---:|---:|
| Active x16 updates | 664,320 | 664,320 |
| Total write commands | 101,520 | 83,040 |
| Total physical write beats | 812,160 | 664,320 |
| HUD upload requests | 21,120 | 2,640 |
| HUD functional readback requests | 21,120 | 2,640 |
| Painter input commands / words | 35,040 / 280,320 | 35,040 / 280,320 |
| Painter output commands / words | 48,000 / 384,000 | 48,000 / 384,000 |

Burst mode removes **18,480 write commands and 147,840 physical write beats**
per frame. The active data and codec packet bytes stay unchanged. All positive
full-frame writes now use their physical BL8 beats; abort/error/control cases
remain separately tested and are not included in that statement.

| Painter, unplaced XC7 mapping | V74 | V75 |
|---|---:|---:|
| RAM64M | 2,304 | 0 |
| RAMB18E1 | 8 | 32 |
| RAM32M | 3 | 3 |
| DSP48E1 | 11 | 11 |
| FDRE | 1,059 | 1,018 |
| Total mapped cells | 7,050 | 3,896 |

These are painter primitive counts, not whole-decoder utilization. Small control
and HUD memories still use distributed resources; RAM64M elimination is not a
claim of zero LUT RAM everywhere. More BRAM allocation is the explicit tradeoff.
There is no exact-device fit, mapped-netlist timing, physical Fmax or CDC result.
The declared `xc7a100tcsg324-1` preflight again returns
**UNAVAILABLE_EXACT_PART**, before RTL synthesis or implementation. No new
hardware bitstream is produced.

## Verification and reproduction

Native and pinned-sv2v-converted painter campaigns each pass **39 exact rasters,
14,976,000 compared RGB565 words, 20 fault probes and 30 invalid starts**. The
new fault probes interrupt both sides of the clocked-read pipeline before
composition; native/converted case counts and cycles agree exactly. Generic
inspection checks the synchronous bank ports, and bounded family mapping checks
its actual primitives. An eight-member hashed archive preserves the earlier
16-fault qualification; its sources are superseded and are checked internally,
not compared with current source hashes.

The dedicated real-controller control campaign separately exercises malformed
requests, ownership/identity, held response snapshots, producer mutation after
acceptance, complete HUD upload/readback and partial-burst abort/drain behavior.
Its exact scope, final counts and retained development diagnostics are documented
in [hud.md](hud.md); it is not a successful full-frame display test.

Run from this research checkout with the same mounted tool containers. Each
build uses one job. Preserve every V69–V74 artifact; only new V75 paths are
producer outputs.

```sh
python3 scripts/cu66-v75/verify_baseline.py
python3 scripts/cu66-v75/run_painter.py
python3 scripts/cu66-v75/run_elaboration.py
python3 fpga/experiments/cu66-v75/system/run_control.py
python3 scripts/cu66-v75/run_system.py --hud-mode scalar
python3 scripts/cu66-v75/run_system.py --hud-mode burst
python3 scripts/cu66-v75/run_system.py --frames 4 --hud-mode burst
python3 scripts/cu66-v75/compare_system.py
python3 scripts/cu66-v75/run_ooc_preflight.py
python3 scripts/cu66-v75/verify_evidence.py
python3 scripts/cu66-v75/bundle_manifest.py
```

The OOC runner records an unavailable declared part as exit 2, not a synthesis
PASS. The source manifest selects 20 hardware sources; hardware top is
`cu75_system`, with `USE_STRIP=1`, `P0_CACHE_LINES=8`, no `SIMULATION`, and
simulation wrapper/model excluded. Source, log, derived frontend/mapping and
archive hashes are retained. Baseline verification establishes frozen-file
integrity and ancestry, not target performance.

## Next milestones

1. Run phase-controlled source admissions after scanout is already active,
   including multiple arrival phases, to separate bootstrap effects from a
   steady decode/compose bound. Keep exact pixels, distinct source identities,
   missed deadlines and all black/mismatching lines as explicit verdicts.
2. Prototype actual-controller direct-YUV strip service before replacing RGB
   composition. Measure row/refresh/turnaround interference with upload and
   reference traffic; the V74 Python cache study is not a service guarantee.
   Overlap cache fill with conversion only with measured strip deadlines.
3. Give direct scanout a generation/frame/bank descriptor, cache invalidation,
   old-front read-drain fence and qualified-vblank ownership switch. Preserve
   exact bilinear/HUD output and stale-response/abort/pending-descriptor tests.
4. Evaluate queueing/pending-write fences and independent cache-hit replies,
   then safe phase overlap. Further pack underfilled BRAM banks only with
   explicit port schedules, exact-output regressions and measured resource and
   cycle cost. Do not assume BRAM mapping alone improves target frequency.
5. Extend the changed full-system path to all retained 457-frame histories and
   the predefined 1,800-distinct-source fixed-arrival campaign. Close exact-part
   fit/route/CDC and live ESP32 Wi-Fi/QSPI plus CPU HUD service before a ten-minute
   physical distinct-source 30-fps verdict. Retain that gate while pursuing the
   strict observed maximum validated target decode below 10 ms, including stalls
   and recovery. Average or kernel-only times satisfy neither milestone.

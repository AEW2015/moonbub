# V72 hardware-development handoff

V72 implements masked SDRAM BL8 writes, canonical half-row bursts and full
portrait painter bursts. The matched P-frame command-model transaction improves
from **260.18963 ms to 148.51433 ms (42.92% less time)** while preserving exact
output and zero LCD underruns. The four-frame history also passes. **Verified
30 fps, validated target decoding under 10 ms and FPGA implementation remain
open.** This is an experimental source handoff; no hardware was programmed.

Baseline: v71 commit `207b16d8f0e04a928810a294787609c6e664db71`. All 4,879 v69,
460 v70 and 122 v71 bundle files remain unchanged. CU66 syntax, resolution
(720×480), decoded quality, Sunshine and ESP32 wire protocols are unchanged.

## Implemented path

- `cu72_sdram_controller` uses read/write BL8, CAS3, mode `0x033`. It latches the
  whole payload and mask, drives per-byte DQM, drains every accepted write and
  waits for recovery after the last physical beat. Ready/idle are gated by reset.
- `cu72_tile_memory` writes a 64-byte tile in eight aligned half-row bursts
  rather than 32 scalar requests. Chroma rows correctly alternate burst halves.
- `cu72_word_bridge` retains v71's elastic LCD reader, bounded four-grant
  priority, finite request-gap grace and cache ordering. It adds checked wide
  writes and maps legacy scalar writes to masked BL8 requests.
- `cu72_painter_burst` gathers each strip's eight contiguous portrait words into
  one write. It emits 48,000 requests for 384,000 words, including both borders,
  and waits for visible completion. Start metadata and allocation overlaps are
  checked before memory work.
- `cu72_system` retains the frozen packet/qmap/base owner, actual stored prior
  reference, real native HUD semantic endpoint, guarded transfer/readback and
  commit/presentation lifecycle. Only the write service and producer interfaces
  change; model readback never feeds golden reference pixels into the DUT.

See [the reviewed API](api-review.md), [controller](controller.md),
[memory adapter](memory.md), [plan](plan.md) and [milestone checklist](milestone-checklist.md).

## Qualification results

| Scope | Result |
| --- | --- |
| Controller | 8/8 runs: Verilator/Icarus × two seeds × tAC 2/7 ns; 2,478 checks/run, 195 writes, 212 reads, eight masks, nine reset prefixes and one reset-edge case |
| Memory adapters | 28/28 runs: 24 concurrency runs plus four reset runs; 9,078 checks, 237 tiles, 6,751 auxiliary operations, 43 existing aborts and eight wide-write abort boundaries per normal run |
| Cache aliases | Four direct runs, 19 checks each; both clients' partial writes invalidate both read caches and preserve neighbors |
| LCD service under modeled contention | Worst tested line **15.90 µs**, within **18.425378 µs** available; request bubbles and same-bank backslot conflicts included |
| Standalone painter | **39 raster executions / 14,976,000 exact RGB565 words**, ten fault/abort probes and 30 rejected-start probes |
| Integrated guard/control | Two headers parsed, two HUD words completed/read back, seven denied writes, two abort drains, premature HUD completion rejected, zero incomplete frames accepted |
| Key/P command model | Exact canonical/HUD/portrait memory and two distinct complete presentations; **zero underruns**; lost COMMIT ACK retry |
| Four-frame command history | IDs 0–3, exact canonical/HUD/RGB output for every frame, actual prior RTL-written references, four distinct complete presentations; **zero underruns** |
| Evidence audit | Frozen baseline, current source/command/log hashes, terminal counts, comparison and superseded archive pass |
| Generic implementation preflight | `UNAVAILABLE_FRONTEND`: native Yosys 0.33 rejects `int'(...)` casts before elaboration; no resource counts produced |
| Exact-device OOC preflight | `UNAVAILABLE_EXACT_PART`: Vivado 2025.2 lacks `xc7a100tcsg324-1`; synthesis/implementation did not start |

All timing values below use declared model clocks: 100 MHz memory, 279-degree
read sampling, 34.058 ns pixel period and approximately 65.0755 Hz panel refresh.
These are not achieved hardware clocks or electrical timing results.

| Matched key/P phase | V71 key | V72 key | V71 P | V72 P |
| --- | ---: | ---: | ---: | ---: |
| Full transaction through COMMIT ACK | 109.58523 ms | **59.72594 ms** | 260.18963 ms | **148.51433 ms** |
| Packet-complete to modeled validated-ready | 35.02723 ms | **22.94679 ms** | 90.66040 ms | **77.76904 ms** |
| Validated-ready to RGB-ready | 74.55797 ms | **36.77912 ms** | 169.52854 ms | **70.74460 ms** |

This comparison uses the same chronological packets and clocks. Changed
transaction lengths change concurrent LCD/refresh work, so raw background read
counts are not normalized per-second bandwidth comparisons. The key transaction
is 45.50% shorter; the P transaction is 42.92% shorter.

The four-frame run records transaction times **59.72594, 148.51433, 148.63374,
149.87094 ms**. Its modeled packet-to-ready interval spans **22.94679–78.15837 ms**.
It checks 24,988 complete clean lines and 11,994,314 observed pixels. There are
31 complete raster refreshes but only **four new source presentations**; repeated
panel refreshes are not new game frames. Trailing partial rasters are not counted
as complete. The separate key/P run is repeated coverage, not two additional
unique source captures.

The native HUD code executes real preparation and readback/tag checks, but its
processor execution does not advance simulation time. Typed sidebands and
immutable packet staging substitute for live transport. Thus the model phase is
not the fixed, fully charged **target** validated-decoding interval. Neither the
30-fps nor under-10-ms gate is met by these results.

## Commands saved, bus work retained

| Writes per codec frame | V71 requests/commands | V72 commands | Active x16 words | V72 physical beats |
| --- | ---: | ---: | ---: | ---: |
| Canonical | 259,200 | 64,800 | 259,200 | 518,400 |
| RGB portrait | 384,000 | 48,000 | 384,000 | 384,000 |
| HUD scalar fallback | 21,120 | 21,120 | 21,120 | 168,960 |
| Total | **664,320** | **133,920** | **664,320** | **1,071,360** |

Commands fall **79.84%**, but masked bursts increase physical write beats from
664,320 to 1,071,360. Only about 62.01% of the new write beats update words. The
speed gain comes from amortizing command/handshake/row overhead, not from a
claimed reduction in bytes on the SDRAM bus. Accepted aborted work is also
charged in fault-test counters.

## Reproduce

Use the existing `gamebub-cu66-v69-build` container with the checkout mounted at
the same absolute path. Builds use one job each and separate V72 build outputs
under the shared 4-CPU/4-GiB limit.

```sh
python3 scripts/cu66-v72/verify_baseline.py
python3 scripts/cu66-v72/run_controller.py
python3 scripts/cu66-v72/run_memory.py
python3 scripts/cu66-v72/run_painter.py
python3 fpga/experiments/cu66-v72/system/run_control.py
python3 scripts/cu66-v72/run_system.py --frames 2 --strip
python3 scripts/cu66-v72/run_history.py --frames 4 --strip
python3 scripts/cu66-v72/compare_system.py
python3 scripts/cu66-v72/verify_evidence.py
python3 scripts/cu66-v72/bundle_manifest.py
```

Producer reruns replace current V72 logs; regenerate comparison, evidence audit
and the bundle manifest afterward. Do not run old-version producers into frozen
v69/v70/v71 paths.

The generic preflight runner `run_elaboration.py` deliberately returns 2 for its
recorded unavailable frontend. Its three parser failures are not functional
simulation failures or successful elaboration. The staged exact-target flow is
`build/ooc_system.tcl`; its `status.json` pins the source list, includes, Tcl,
tool identity and logs. It exits 2 on the unavailable exact part without using a
substitute device.

Use `system/sources.json`, hardware top `cu72_system`, `USE_STRIP=1`, no
`SIMULATION`, and exclude the simulation wrapper/model for hardware integration.
Review board clocks, I/O, CDC, reset, real packet staging and processor service.
A write's ready handshake is not completion. Preserve candidate/front/reference
leases and the actual drained-boundary presentation ACK.

`system/before-reset-gate/` retains 97 exact source/log files in a hashed ZIP.
It preserves the successful first normal-load results and the controller reset
interface subsequently fixed and requalified. Controller/adapter development
lint and overstrict-recovery probe logs remain labeled as unqualified history.

## Next work

1. Inspect and make strip memory banking explicit if needed. Eight source read
   expressions now gather one burst; actual inferred ports, replication and
   BRAM cost remain unknown. Evaluate eight 720×16 lane banks or a 720×128
   lane-writable store and retain exact-output/drain tests.
2. Profile reference-read wait and service separately. Canonical reads still use
   scalar assembly and a one-line p0 cache. Evaluate a burst tile reader, a
   larger row-working-set cache and cache-hit replies independent of bus service,
   with explicit write ordering and ownership proofs.
3. Evaluate tile-major canonical storage: a 64-byte 8×8 tile could use four full
   BL8 writes instead of eight masked half-row writes. Account for painter and
   scanout access changes before choosing it; a local decoder gain can worsen
   raster reads. Preserve canonical hashing and exact logical pixel order.
4. Batch guarded HUD writes only with a new count/identity/mask contract. Assess
   direct transposed-YUV scanout and safe phase overlap to reduce RGB copy work.
   Keep the existing exact HUD and reference lifecycle. Add DSP lanes after
   profiling their benefit on the measured critical path.
5. Qualify all 457 retained histories through the changed command path, then
   the predefined 1,800-distinct-source fixed-arrival campaign, exact-device fit/
   timing/CDC and ten-minute physical 30 fps. After retaining throughput, close
   the strict observed maximum under-10-ms validated decoding gate with real
   processor and transport timing. The current command-history bench is bounded
   for short runs; larger campaigns need an explicitly sized watchdog/window.

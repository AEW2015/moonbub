# CU66 V77 — direct-YUV cache and pixel pipeline in RTL

V77 turns the V76 structured-cache hypothesis into working RTL. The bounded
cache/converter drives exact native portrait pixels through the actual SDRAM
controller model and existing LCD line buffers. Across both timing corners and
with/without paced upload/reference traffic, **eight source-condition panels
pass with zero pixel mismatches, memory errors or LCD underruns**.

This is a renderer/cache milestone. **The compressed-frame FPGA decoder is not
connected to this new path yet. Sustained 30 distinct source-fps and strict
maximum validated FPGA decode below 10 ms remain unproven.** The V76 warm
validated decode measurement remains 28.17–30.37 ms for the old integrated path.
No new bitstream, exact-target fit, routed clock or physical display result is
produced here.

## Implemented components

Use `cache/cu77_direct_cache_bounded.sv` with `render/cu77_yuv_rgb.sv` for further
integration. The original `cu77_direct_cache.sv` remains a qualified comparison.
The [interface contract](interface-contract.md) defines accepted work, ordering,
response ownership, counters, finish and local abort behavior.

The cache holds three Y columns, three Cb/Cr columns per plane and four packed
HUD block columns per rectangle: **29,184 data bytes**, excluding tags, pipeline
staging, controller caches and output buffers. Ten word memories use complete
16-bit synchronous reads and a streamed write port. Chroma is banked by row and
packed-word parity so the interpolation neighborhood can be read without
inventing extra RAM ports.

A frame's 90 ordered prefetches produce **35,040 BL8 requests / 280,320 x16 words**
through the dedicated display-read port. Each received word is written on its
accepted cycle; there is no extra eight-clock snapshot-unpack stage. Column tags
become valid only after the full required column drains. Ordered consumption
and a maximum three-live-strip window protect current data while prefetching.
Missing/out-of-range samples return explicit error responses.

Descriptor acceptance binds bank, generation and source ID and invalidates tags.
Replacement while active is backpressured. Finish requires all strips consumed
and cache work drained. A local abort suppresses new requests and drains every
accepted eight-word memory burst before clearing the epoch. Held pixel responses
that are canceled are explicitly counted in the testbench accounting.

The converter is a three-stage elastic pipeline, accepting one neighborhood per
clock when unblocked. It implements the exact CU66 parity-dependent bilinear
rounding, signed Q8 color conversion, clamp, RGB565 packing and opaque HUD
replacement. Coordinates and errors travel with the pixel. The minimal render
wrapper retains ownership until cache and converter outputs drain.

See [cache tests](cache.md) and [converter/native render tests](render.md).

## Real-controller and native display integration

`system-bounded/cu77_display_bounded_sim.sv` connects the bounded cache and
converter to the frozen V74 memory adapters, V72 controller/checked SDRAM model,
and V71/V70 native descriptor/line-buffer path. A burst adapter converts the
existing portrait line requests into coded cache coordinates and returns eight
RGB565 words. Pixel and memory clocks retain the existing unrelated-clock test
schedule: assumed 100-MHz memory, 279-degree read capture and 34.058-ns pixels.

The input YUV planes and native HUD are decoded **by the C++ fixture oracle** and
seeded through **35,040 actual physical write commands / 280,320 word updates**
per source, outside display measurement. No model-memory backdoor or direct
sample bypass fills the cache. That seed operation qualifies the renderer and
memory path, not the FPGA decoder or its validation latency.

| Condition per variant | Sources/panels | Expected portrait pixels | Mismatches / underruns |
|---|---:|---:|---:|
| tAC 2 ns, display only | 2 | 768,000 | 0 / 0 |
| tAC 2 ns, paced upload/reference | 2 | 768,000 | 0 / 0 |
| tAC 7 ns, display only | 2 | 768,000 | 0 / 0 |
| tAC 7 ns, paced upload/reference | 2 | 768,000 | 0 / 0 |

Both original and bounded variants pass that complete matrix, with **every
recorded counter and cycle identical**. Each panel contains 345,600 active
cache/converter pixels plus generated black borders. Every native pixel is
compared against the full independent fixture render, with coordinate and epoch
checks. Epochs use canonical banks 0 and 2; component regressions also exercise
all three canonical banks.

Each paced panel window releases and completes **3,688 upload tiles and 3,555
reference tiles**, using absolute 30-fps-equivalent workload release rates.
References share the immutable front bank; uploads target separate bank 1. Every
released job is retained, and the small measurement-end backlog drains before
changing source data. Physical model counts reconcile with cache foreground
reads and background tile work. No portrait RGB framebuffer is written by this
new display path; converted pixels feed the existing line buffers directly.

The measured portrait window is about **15.1809 ms**. It ends at the final active
portrait pixel, not the end of a sustained sequence of complete panel periods.
It is not an input-to-photon, FPGA decode or distinct-source-fps measurement.
There is a blank/reset boundary between the two source epochs. This experiment
does not prove seamless pending-source handoff, repeated-front operation,
mid-line global recovery or a real 30-fps input stream.

## Resource optimization with exact behavior preserved

The initial cache used wide signed integer modulo-three expressions. Their
unplaced mapping generated excessive address-control logic. A separate bounded
variant replaces them with a small unsigned base-four digit fold and narrows
the column operand. The actual RTL helper is exhaustively checked for all
128 possible seven-bit inputs. The original sources/evidence remain unchanged.

| Cache + converter + minimal render guard | Original | Bounded |
|---|---:|---:|
| Total mapped cells | 29,462 | **2,970** |
| CARRY4 | 4,137 | **271** |
| DSP48E1 | 8 | **7** |
| FDRE | 664 | **664** |
| RAMB18E1 / RAMB36E1 | 11 / 3 | **11 / 3** |
| BRAM allocation, 18K equivalents | 17 | **17** |

The cell reduction is **89.92% in the unplaced XC7 family flow**. Every cache
seed counter/cycle, native/converted render case and actual-controller/native
panel case matches the original. The bounded form is the preferred source for
next integration.

Those counts cover the cache, converter and minimal query-ownership guard.
They exclude the SDRAM controller/model, legacy LCD buffers, the system
address adapter and compressed-frame decoder. No device utilization percentage,
route, target Fmax or timing/CDC conclusion follows from them. The existing
exact-part availability limitation remains. [Frontend and mapping evidence](elaboration.md)
records tool identities, generated-only exceptions, derived hashes and the
separate before/after comparison.

## Finite verification results

- Standalone converter: **103,631 accepted = 103,590 emitted + 41 abort-flushed**
  samples, 21 abort probes and 9,997 checked continuously accepting cycles.
- Cache, each variant: three schedules × two epochs, **six synthetic active
  frames / 2,073,600 exact neighborhoods**, **78 fault probes and 48 invalid
  requests**. Accepted queries equal delivered plus one explicitly canceled
  held response per schedule. All per-strip physical requests match V76's
  independent trace.
- Cache-backed rendering, each variant and frontend: **39 active frames /
  13,478,400 exact RGB565 words**, plus four abort/memory-error integration probes.
  Cases include eight real key/P fixtures from four cohorts, four synthetic
  patterns and recovery per schedule. Native and pinned-sv2v-converted case
  counters/cycles agree exactly.
- Actual controller/native LCD, each variant: **eight exact portrait panels /
  3,072,000 checked native pixels**, zero mismatch, memory error and underrun.
  Bounded/base records agree exactly across both tAC corners and background modes.

The ideal-memory renderer's no-stall active-frame loop takes 350,870 cycles,
about **3.50870 ms at the assumed 100 MHz**. This is cache/render work on already
decoded planes, **not under-10-ms FPGA decoding** or real-SDRAM timing. The
controller-backed native panel test is the separate memory/display measurement.
Neither replaces the [30-fps and validated-latency contract](../cu66-v76/milestones.md).

Initial arithmetic/strict-lint and test-harness diagnostics remain retained.
Hashed archives preserve earlier cache fault and native controller proofs rather
than leaving stale passing records mixed with current sources. Audits check
archives internally and current source/log/derived hashes separately.

## Reproduce and select sources

```sh
python3 scripts/cu66-v77/verify_baseline.py
python3 scripts/cu66-v77/run_cache.py
python3 scripts/cu66-v77/run_cache_bounded.py
python3 scripts/cu66-v77/run_render.py
python3 scripts/cu66-v77/run_render_bounded.py
python3 scripts/cu66-v77/run_elaboration.py
python3 scripts/cu66-v77/run_elaboration_bounded.py
python3 scripts/cu66-v77/run_display.py
python3 scripts/cu66-v77/run_display_bounded.py
python3 scripts/cu66-v77/verify_evidence.py
python3 scripts/cu66-v77/bundle_manifest.py
```

The source lists and tool/container commands are explicit in those producers.
Each build uses one job. Keep all predecessor paths frozen. The real-controller
`*_display*_sim.sv` wrappers contain a behavioral SDRAM model and are **test
integration wrappers**, not board synthesis tops. The minimal render wrappers
are the mapped cache/converter guard scope. Hardware integration must select the
bounded cache and real controller I/O path with the simulation define removed,
then supply actual clocks, pins and a production source/lease owner.

## Next steps toward the goals

1. Integrate the new direct path after the **actual FPGA validated-ready event**,
   replacing the old RGB-copy composition stage. Keep source IDs, processor
   commit reconciliation and failure accounting intact; do not substitute a
   renderer time for decoder latency.
2. Implement continuous panel scheduling and seamless source changes. A global
   owner must retain canonical front/reference/candidate leases, drain accepted
   old-front work, invalidate generation tags and switch at qualified vblank.
   A cache finish is only its local display-work boundary; it does not release
   a reference still used by the decoder. Keep real preroll and output-buffer
   storage/timing in the budget.
3. Implement and test global recovery through the native line/descriptor path.
   The current system harness uses a drained stop and paired display reset
   between epochs. Its exposed local component abort is not a qualified
   standalone mid-line display-recovery procedure.
4. Repeat many panel periods with actual source arrivals, bursts, errors and
   cache invalidation; measure warm fixed-phase admission and queue tails.
   Close the 457-frame functional and 1,800-source/60-second modeled campaigns.
5. Profile and optimize the FPGA decode path toward a strict maximum below 10 ms.
   V76's warm decoded-frame result remains open; memory command scheduling,
   validated-output drains, hashing/entropy/inverse work and ownership-safe
   overlap need measurement. Do not add/subtract overlapping counters as a
   complete critical-path decomposition.
6. Close exact-device fit/route/CDC and live ESP32/processor service, then require
   **18,000 distinct sources / 600 seconds at 30 fps**, retaining that throughput
   while pursuing the under-10-ms validated decode gate. No milestone is closed
   by panel refreshes of an unchanged source or an assumed clock.

# CU66 v69: native reference and connected RTL handoff

The immediate deliverable is a qualified fixed-profile decoder architecture,
not a replacement bitstream or ESP32 firmware image. General RTL development
and simulation need no DAP/JTAG connection. The exact target's device files
are required for target synthesis/place-and-route; a board connection is
required later for SDRAM, transport and panel measurements.

## What can be used now

| Deliverable | Location | Intended use |
|---|---|---|
| Portable C++17 CU66 decoder | `experiments/cu66-native-v69/` | Independent native reference, fixtures, malformed-input cases, firmware/RTL comparison |
| Packet preflight and qmap RTL | `fpga/experiments/cu66-v69/packet/` | Outer/inner CRC/profile/reference/geometry checks and synchronous local quantizer-map access |
| Connected base-layer RTL | `fpga/experiments/cu66-v69/integration/` | AB38→full tile grid→dequant→Q14 inverse→reference join→canonical bytes→SHA |
| Software HUD prepare/transfer/commit gate | `fpga/experiments/cu66-v69/hud-partition/` | Qualified Linux native semantic endpoint and explicit generation-bound rollback/transfer contract |
| Candidate/reference/front ownership | `fpga/experiments/cu66-v69/banks/` | Three-bank control contract with explicit safe swap and abort drain |
| Portrait layout proof | `fpga/experiments/cu66-v69/layout/` | Exact existing-panel orientation and storage-layout tradeoffs |
| OOC implementation script | `fpga/experiments/cu66-v69/scripts/ooc_base_pipeline.tcl` | Exact-part in-memory synthesis/route once Artix-7 support is installed |
| Evidence and reproduction index | [component matrix](component-matrix.md), [reproduction](reproduction.md) | Review scope, commands and retained logs before reuse |

The native reference accepts only the frozen epoch-25 CU66/GU66 720×480
YUV420 profile, dispatch 5/6 and canonical zero motion. Other capabilities are
rejected explicitly. This preserves the existing wire format; it does not
silently turn legacy JPEG or broader CU66 profiles into compatible ingress.

## Measured software improvement

The matched three-pair campaign covers all 457 retained frames and includes
wire/integrity/entropy/inverse/normalization/SHA/HUD/RGB565 composition and
publication on both paths. Mean per-frame medians are **97.33174 ms Python**
and **7.60878 ms native C++**, a **12.79×** host-call reduction. Native worst
per-frame median is 10.21305 ms; largest individual sample is 11.84083 ms.
These are shared Ryzen host measurements, not ESP32 or FPGA measurements.

There is no new compression result in this iteration: the packets and decoded
pixels are unchanged. Earlier native HEVC/AV1 decode-only timings have a
different scope and cannot be used as a complete-presentation comparison.
The existing study's HEVC/AV1 byte advantage at matched sampled quality gates
is not overturned by accelerating the custom decoder implementation.

## Connected RTL result

Two complete 457-frame schedules pass, each checking 3,701,700 full-grid tiles
and 236,908,800 canonical sample bytes, plus full SHA-256. Each schedule has 20
keys and 437 predicted frames. The shared schedule additionally passes all
three accepted read/write abort drains; both schedules check five distinct
fault classes and a clean recovery. The [independent audit](integration-audit.md)
checks command flags, full counts, logs and all 475 recorded source/fixture pins.

| Schedule | Minimum clocks/frame | Mean clocks/frame | Maximum clocks/frame |
|---|---:|---:|---:|
| Ideal memory-port control | 540,387 | 1,093,623.75 | 2,360,627 |
| Shared x16 slots, display/refresh reservations and seeded stalls | 1,185,675 | 1,627,146.52 | 2,708,663 |

These are behavioral cycle counts for the declared schedule. They are not
measured device latency, routed clock rate or actual presentation cadence.
The shared results are retained separately from the ideal control.

## Integration boundaries that must stay explicit

The connected top is actual RTL through SHA, but the bench supplies metadata
from a qualified native parser. The packet preflight RTL is separately tested;
it is not yet wired to that top's shared memory arbiter. HUD semantic decode
is a software partition, not FPGA HUD decode. Bank control is separately
verified and must remain the single owner of accepted history.

Before committing a candidate, require all of the following for the same
lease generation and frame ID:

1. Packet framing/profile/CRC/reference/capability checks passed.
2. Every nested AB38 plane completed, including its own integrity and geometry
   checks; full/compact scattering and hidden-coefficient validation passed.
3. Canonical base samples produced the expected CU66 output tag.
4. Original HUD bytes decoded semantically against the accepted immutable HUD
   cache; HUD output tag and exact rectangles/word count passed.
5. Canonical and HUD writes completed visibly; compressed, qmap, reference,
   transfer and memory adapters are drained as required.
6. The bank controller can commit and subsequently present at a safe boundary.

Packet metadata-valid, HUD decode-ready, a memory queue's ready signal, and
base tag-valid are each insufficient alone. An error preserves the accepted
reference/HUD and front buffer. A stale completion cannot authorize a newer
lease. A local reset requires external response queues to be flushed.

The base top now distinguishes write acceptance from `write_done`/`write_error`.
It drains accepted writes on abort and fences successful tags until those
writes finish. Its independent memory/hash fork holds each branch until
acknowledged, preventing a consumer's readiness from withdrawing another
consumer's valid transaction.

The software HUD gate independently passes all 457 HUD histories and release/
ASAN/UBSAN qualification, plus 32 native directed HUD cases. Its candidate
owns its decoded words and exposes a generation/frame-bound transfer contract;
failed base-layer candidates do not advance accepted HUD state. Each cache has
42,240 logical word bytes; observed previous-plus-candidate vector capacity
peaks at 94,720 bytes, excluding decode temporaries and other memory. This is
not an ESP32 SRAM-fit result. Replacing the compressed HUD with raw words would
push 279 of the 457 retained full packets over the existing 49,152-byte cap,
so the semantic partition preserves the current compressed wire payloads.

## Memory and display integration

Canonical YUV420 is 518,400 bytes/frame. A full reference read plus candidate
write is 1,036,800 logical bytes before other clients. Hidden normalization
avoids 294 of 8,100 reference tile reads in this fixed profile. These counts
exclude refresh, command efficiency, scanout, HUD transfers, compressed staging
and protocol overhead.

Existing scanout maps coded `(u,v)` to physical `(x=v,y=u+40)` on the 480×800
portrait raster. Hashing stays canonical Y/Cb/Cr row order regardless of
physical storage. The Python layout proof shows that naive canonical-plane
storage produces strided panel reads; a tile/transpose/cache adapter is still
needed. It has not been implemented by the canonical row/hash serializer.

The Rev4.1 source schematic records two 32 MiB SDRAM devices and 512 KiB SRAM.
The checked-in controller currently selects one 32 MiB SDRAM device. Neither
the full schematic capacity nor the locality model proves an implemented
address map, storage fit or sustained bandwidth on the fitted board.

The connected bench's shared-bus experiment rotates three modeled x16 clients,
reserves alternate clocks for scanout and 16/7,800 clocks for refresh, and adds
seeded service stalls. Qmap is a separate synchronous local port. This is useful
for contention sensitivity; it is not command-accurate SDRAM/ESP32 simulation.

## Next implementation gates

1. Connect packet metadata/qmap and the entropy byte port through an actual
   immutable compressed-bank arbiter. Bind all clients to the same lease.
2. Connect canonical reference/candidate tile adapters to the real memory
   controller and bank owner, including write acknowledgments and all drain
   paths. Exercise actual SDRAM commands, refresh and concurrent scanout.
3. Integrate the HUD semantic endpoint and its transfer/commit protocol. Port
   and measure it on the intended processor before making an ESP32 SRAM or
   cycle-budget claim; the current qualified endpoint is Linux C++.
4. Implement color/HUD/filter/portrait scanout against the recorded physical
   layout, preserving normative integer rounding and canonical hash order.
5. Run exact-target OOC and full-board synthesis/route. Review actual DSP,
   LUT, FF, BRAM, clock, I/O, CDC and unconstrained-path reports. The current
   Vivado install lacks `xc7a100tcsg324-1`; no fitted-resource or Fmax result
   is available. A generic Yosys mapping attempt was stopped near the dedicated
   4 GiB container cap before completion; it supplies no resource/timing result.
6. Measure real ESP32 transport and memory budgets, then unique complete
   presentations, drops, decode-to-display latency and recovery on hardware.
   Preserve JPEG as the deployed compatibility path until this qualification.

Thirty fps is a **33.333 ms complete-frame cadence**, not a claim obtained by
dividing isolated block cycles by an assumed FPGA clock. Full-system handoff
must include achieved clock, tail-cycle costs, input arrival, bank availability,
all memory clients, HUD and scanout deadlines. No physical 30 fps or end-to-end
latency is established by this handoff.

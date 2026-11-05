# AR03 memory and presentation implementation plan

Goal: 720x480 at 30 unique panel presentations per second, then audio and
controller coexistence. The current private KEY result and AKD1 bars do not
constitute decoded video presentation. This plan follows the frozen MoonBub kit
`27a4dde6a7e2ea4fab09d892551ef542f05c8965` and Sunshine native contract
`c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`.

The reviewed reuse baseline is build50's `fpga/candidates/v21-audio/rtl`, manifest
`ab274599ef9372addb19bd2a9c15a1e74458d0e66fe55c818695ebb54b099270`.
Do not substitute the older single-write adapter under `fpga/rtl`.
The source-bound architecture review is retained locally under
`evidence/coordinated-ar03-20261104/memory-presentation-review/`.

## 1. Finish the isolated hardware diagnostic

The guarded-ROM successor has completed routed setup/hold/pulse and scoped RAM
warning review. Its source export and exact test sequence are recorded in
[the current checkpoint](30FPS-UPDATE-CHECKPOINT-20261104.md) and
[the prepared hardware window](AKD1-LAB-WINDOW-20261104.md). Keep its conservative
16 MHz QSPI limit: max-delay routing bounds are not external hold or
maximum-bandwidth qualification. Keep the normal SD build50 recovery.

Test the uninstalled v26 app against unchanged build50 first. Then measure a
fresh volatile AKD1 configuration with no external reset during its owned job.
Retain exact identities, private tag/count/cycle results, own-worker stack and
heap measurements. Neither its independent LCD bars nor repeated fixed-fixture
jobs establish 30 unique displayed frames/s.

## 2. Prove compact YUV storage and actual drain

Implement in isolated `fpga/experiments/ar03-yuv-store-20261104` before modifying
the board image. Tee the existing canonical raster/SHA handshake into a bounded
byte packer: one accepted byte advances both private storage and hashing exactly
once. Pack two adjacent uint8 samples per 16-bit word. Do not store int16 merely
because the canonical tag hashes each sample followed by a zero byte.

Use the real retained BL8 packer/controller and a bounded SDRAM model. A full
720x480 YUV420 image is 518,400 bytes. Expand model capacity explicitly, check
all addresses and nonalias regions, and keep the original model unchanged.
Its current 2 MiB capacity cannot silently represent new regions beyond the two
existing RGB apertures. Confirm the actual board part capacity before choosing
a physical bank map; a 24-bit word interface does not prove installed capacity.

Pass gates:

- Compare every stored byte with the pinned full-frame oracle under backpressure.
- Exercise competing reads, held writes, partial masked groups and final flush.
- Prove accepted physical bursts complete before ownership can be reused.
- Abort at local packing, queued request, accepted burst and final-drain phases;
  suppress publication and retain ownership until actual drain is observed.
- Reject tag/input failures without mutating a published region. Preserve any
  counterexample if the existing writer's idle signal proves insufficient.

This step produces stored private samples, not an RTL renderer or a displayed
frame. A testbench scoreboard read is not a substitute for a real read client.

Current [owned baseline result](measurements/ar03-yuv-store-20261104/README.md):
all bytes/tag/drain checks pass, but the modeled path takes 48.65759 ms under
uniform competing reads. The separate elastic-FIFO successor measures 512- and
1,024-byte capacities against the same stimulus at 31.23946 ms. The selected
512-byte variant also blocks simultaneous START/abort/fault admission. This
does not replace scanout deadline testing or agree production reset/rekey
semantics.

## 3. Render one validated KEY through real scanout

Add an owned arbitrary YUV read client and arbitration at the burst-controller
seam. The existing LCD request is a fixed 480-word line, not a general read API.
Use bounded chroma/tile caches and response ownership, including stale-response
and abort tests under scanout priority.

Match the pinned native renderer exactly: bilinear co-sited chroma with edge
replication, integer full-range color conversion and signed rounding, then
RGB565 truncation. A generic JPEG converter or nearest chroma is insufficient.
Apply validated HP01/HR01 HUD patches after the base conversion, preserving
mandatory rectangles; patches never enter predictor samples or the tag.

Transpose/coalesce RGB into the established portrait memory order
`base + x*480 + y` in word units. A direct landscape raster feed would repeatedly
flush the existing single-group BL8 packer. Reuse bounded tile coalescing.

Join real SDRAM write drain, held back-frame ownership and an LCD frame-boundary
swap. Only the swap increments the unique presented-frame counter. Verify every
pixel against the independent native oracle, old-frame preservation on failure,
line-request epochs, no tearing and starvation/underflow under moving frames.
Reintroducing SDRAM also requires live read-clock, I/O and CDC constraints;
AKD1's inactive-memory assertions are not memory qualification.

The elastic storage experiment now measures 31.23946 ms on this fixture. A
strictly sequential RGB565 write alone needs at least 345,600 memory data cycles,
or 3.456 ms at 100 MHz, making at least 34.69546 ms before read, HUD and drain
overhead. Thus a first sequential renderer is a functional milestone, not a
30 fps implementation. Sustainable throughput needs measured stage/frame overlap
or further service improvement. Rendering provisional late stripes or an older
private frame is possible only with separate held regions, explicit response
ownership and final integrity/drain gates before publication.

## 4. Add temporal references and the real ESP32 backend

Keep display front/back storage separate from logical predictor banks. General
KEY/P support needs unpublished physical backing and atomic logical-bank remap:
two published YUV banks plus a provisional destination generally need three
physical regions. A failed final tag or patch must leave published state and
samples unchanged. An initially empty KEY region proves only the first KEY seam.

Preserve independent events: ingress acceptance, packet completion/read drain,
FINISHED, RELEASE, stored-reference AF03 and physical presentation. No-store P
(`destination=255`) creates no reference. Reference publication requires all
validation and real storage drain, while visible presentation additionally
requires RGB/HUD drain and frame-boundary swap.

Implement the bounded ESP32 FIFO/credit backend only against those actual
submission, drain and owner-completion observations. Do not allocate full-frame
buffers on the no-PSRAM ESP32. Agree the unresolved production peer/port,
identity lifetime, reset/rekey, nonce and lost-result semantics with Windows
before enabling any custom capability. Existing MSV1/AV ports remain unchanged.

## Service budget and acceptance

At the current preset0, the 29.361979 MHz pixel clock and 541x834 totals imply
about 65.07617 panel refreshes/s. Frame-boundary presentation intervals are
quantized to that refresh; measure 30 unique IDs/s and the interval distribution
rather than assuming a 60 Hz panel or exactly 33.33 ms for every swap.

| Useful memory operation | Lower bound, decimal MB/s |
| --- | ---: |
| Current repeated RGB565 scanout | 44.981 |
| RGB565 writes at 30 frames/s | 20.736 |
| Compact YUV writes at 30 frames/s | 15.552 |
| Ideal one-read YUV rendering at 30 frames/s | 15.552 |
| KEY storage, rendering and scanout total | 96.821 |
| Above plus one P predictor read | 112.373 |

These are arithmetic lower bounds, not measured service. Refresh, row changes,
turnaround, masks, patch traffic and chroma reuse matter. The raw 200 MB/s bus
ceiling is not usable headroom. Current AKD1 uses 106/135 RAMB36 tiles; full YUV
regions belong in external memory, with bounded on-chip caches.

Measure FPGA-only initiation interval and memory arbitration first, then the
concurrent Wi-Fi/QSPI/decoder path. Qualify recovery and 60-second runs at
5/10/15/20/30 fps, followed by five and 30 minutes at 30 fps. Reconcile unique
decoded/reference/presented IDs, queue peaks/drops, faults, deadlines and frame
intervals. Add audio and controller load only after video-only acceptance.

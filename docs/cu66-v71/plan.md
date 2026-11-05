# V71 — bounded memory service for the CU66 streaming receiver

Continue the [v70 system plan](../cu66-v70/plan.md) toward verified 30 fps, followed
by validated decoding below 10 ms. Keep the 720×480 coded image, exact CU66 output,
processor HUD semantics and reference/publication rules. This iteration changes
memory service rather than compression syntax or output quality.

## Implementation

1. Give scanout an independent aligned BL8 read port. Each portrait LCD line
   contains 480 x16 words and requires 60 read bursts, instead of 480 scalar
   request/response round trips through the HUD/painter arbiter.
2. Retain eight words of elastic response capacity, but forward each word as
   soon as it becomes available. Backpressure must hold the visible beat stable;
   the controller's unstallable burst must still fit in the buffer. Keep its
   allocation until all eight words have been delivered.
3. Keep one read-cache line for canonical tiles and four associative lines for
   auxiliary readers. Writes invalidate every aliasing scalar line. Preserve
   ordered, visible write completion rather than acknowledging enqueueing.
4. Bound LCD priority to four consecutive burst grants when scalar clients are
   waiting, then grant a scalar request. Allow one finite grace clock after an
   LCD completion to catch a one-clock adapter gap; never renew it without
   another LCD completion or postpone the scalar grant due after four bursts.
   Measure actual line service under row conflicts and refresh: this grant bound alone does not prove a cycle deadline.
5. Preserve the committed RGB front lease through actual drained frame-boundary
   presentation. Do not release the previous RGB slot merely on raw vblank.
6. Instrument immutable-packet completion, admission, validated-ready, RGB-ready,
   commit acknowledgment, descriptor presentation and complete correct rasters.
   Check raster x/y order and unique source IDs. Retain all queue time.

## Qualification sequence

- Run the frozen-input integrity check first.
- Check memory data, alias invalidation, alignment/range rejection, response
  stability, bounded grants, refresh, accepted-operation abort/drain and reset.
  Use Verilator and Icarus with two seeds and two SDRAM tAC corners.
- Check the asynchronous LCD path with full exact rasters, delayed replies,
  malformed LAST, read errors, explicit starvation and coordinated reset.
- Re-run integrated partial-transaction/HUD guard tests through the new memory
  wrapper. Rejected or incomplete work must not become an accepted reference.
- Replay the same chronological key/P pair through the actual packet parser,
  qmap/base decoder, prior RTL-written reference, processor HUD transfer,
  controller command model, portrait painter and LCD. Compare all canonical and
  RGB words with an independent native decoder. Retry one lost COMMIT ACK.
- Report clean rasters and underruns separately from descriptor switches. Compare
  fixed inputs and clocks with frozen v70; transaction lengths change background
  LCD workload, so unequal-duration runs are not normalized underrun-rate tests.
- Run generic leaf elaboration/checks. Exact-device implementation, target timing,
  CDC and physical validation remain separate gates.

The initial fully buffered burst implementation remains archived with its source
and logs in `fpga/experiments/cu66-v71/system/initial-buffered/`. It reconstructed
exactly but worsened the full P transaction to about 428 ms and retained underruns.
Its component tests were insufficient to predict system behavior. Preserve this
counterexample when assessing the elastic version. The intermediate elastic
version without grace is also archived under `system/elastic-before-grace/`: it
passed the full key/P run without underruns, but failed the adversarial request-
gap and same-bank conflict line deadlines. The final scheduler must pass those
scenarios as well as the original full-system workload.

## Next implementation work after this iteration

The controller still uses single x16 writes. Qualify an actual BL8 write service
before claiming 30 fps: byte masks, half-burst canonical rows, accepted beat
ownership, partial aborts, final write recovery and cache invalidation all need
explicit contracts and tests. The strip painter naturally produces eight
contiguous portrait words, whereas a canonical eight-pixel row produces four
x16 words. Do not coalesce indefinitely across requests whose producers wait for
completion; that can deadlock.

Measure decode/HUD/reference service and painting separately. Evaluate safe
phase overlap and a direct transposed-YUV scanout alternative if RGB write/read
traffic remains the limiting cost. Keep exact HUD overlays and the reference
bank lifecycle. Add DSP lanes only after profiling shows arithmetic is limiting.
The [milestone checklist](milestone-checklist.md) retains the fixed 30 fps and
under-10-ms acceptance definitions and their physical evidence requirements.

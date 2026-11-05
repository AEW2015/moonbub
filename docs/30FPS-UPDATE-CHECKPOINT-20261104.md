# ESP32 / FPGA update checkpoint

Continue toward 720x480 at 30 unique physical presentations/s. This checkpoint
updates the execution order in the coordinated plan; it does not change the
published MSV1 or AV v1 wire formats. Hardware remains unchanged in this offline
increment. The last observed installation was the v22 app and build50 FPGA;
current device address, readiness and counters have not been probed.

## Completed and measured

| Work | Result | Scope |
| --- | --- | --- |
| Private KEY compute | 3,000,322 simulated cycles, exact 518,400 samples/tag | One ROM-fed fixture, not decoded LCD output |
| Compact YUV store with selected admission guard and 512-byte elastic FIFO | 31.23946 ms nominal at 100 MHz; all 259,200 stored words and canonical tag match | One KEY plus synthetic competing reads; no moving-frame publication |
| Native RGB565 arithmetic | 1,471,588 oracle pixels match; separate 160-bit ownership-tag regression passes | Arithmetic/component simulation |
| Direct YUV scanout, original write-load stress | 718 missed lines under uniform writes; 444 under batch writes | Preserved counterexamples; throughput alone did not protect deadlines |
| Bounded read-reservation successor | Zero missed lines, underruns or pixel mismatches in matched static, uniform and batch tests | Two refreshes of one immutable image per profile; not 30 fps video |
| Bank-separated memory service | Mixed useful writes/reads each improve from about 34.308 to 51.349 MB/s | Completed synthetic mixed comparison; KEY/P results pending |

The reservation successor checks 691,200 native canvas pixels and 76,800 margin
pixels per profile, with 1,440 good line latches. Both write-load profiles verify
all 238,981 offered words after actual drain. Uniform producer backlog increases
from 3 to 70 words; the batch profile still needs a 5,760-word peak. This is a
latency/buffering tradeoff, not free bandwidth. Minimum observed final-RGB-word
to latch intervals are 1.930366 us and 1.950765 us; these are simulation intervals,
not routed electrical timing slack.

## Next implementation order

1. **Finish memory-service comparison.** Complete bank-separated KEY/P windows,
   actual accepted-work drains and upper-address/masked-write checks. Compare
   offered, admitted, physical and delivered work at identical phases. Keep the
   bank map experimental until the actual board capacity and active SDRAM path
   are qualified. Do not tune clocks to hide an arbitration or row-conflict issue.
2. **Integrate the real producer with direct YUV scanout.** Add bounded transpose
   storage between canonical raster reconstruction/hash and the column-major
   SDRAM layout. Reuse the tested owned-read service, bounded reservation and
   exact RGB kernel. Drive writes from actual codec traces rather than synthetic
   counters. Measure FIFO occupancy, backpressure and line deadlines together.
3. **Implement immutable frame publication.** Hold the displayed region while a
   separate candidate is written; require tag success and physical drain before
   a frame-boundary swap. Test changing images, failed/truncated frames, stale
   responses and cancellation without tearing or mutating the current front.
   Count unique frame IDs only at physical presentation.
4. **Add P/reference and HUD behavior.** Keep predictor, provisional and display
   ownership separate; preserve published banks on failure. Match native chroma,
   signed rounding and HP01/HR01 semantics. Add predictor and patch traffic to
   the measured memory budget before claiming sustained 30 fps capacity.
5. **Join the bounded ESP32 transport.** Use actual FIFO permits, completion and
   drain events, with bounded internal-SRAM queues and explicit session recovery.
   Agree unresolved production endpoint/reset/nonce semantics with Sunshine;
   do not announce a custom UDP port or capability before implementation.
6. **Qualify board implementation and rate ladder.** Close live SDRAM/CDC/I/O,
   resource and routed timing gates, then test video-only at 5/10/15/20/30 fps.
   Reconcile unique decoded/presented IDs, deadlines and queues before adding
   audio/controller load. Finish with five- and thirty-minute 30 fps runs.

A strictly serial RGB back-buffer write adds at least 3.456 ms to the current
31.23946 ms stored-KEY result, before reads, HUD or drain. That path cannot meet
one frame per 33.33 ms without overlap or further improvement. Direct YUV is a
measured development candidate, not an accepted production architecture yet.

## Separate controlled hardware window

The v26 ESP32 diagnostic app and guarded-ROM AKD1 BIT are prepared for a short
private-compute experiment. Follow [the exact hardware procedure](AKD1-LAB-WINDOW-20261104.md):
app-only regression against build50 first, then a fresh volatile AKD1 load,
audio off and QSPI at most 16 MHz, followed by recovery to build50.

This BIT does **not** contain the new YUV store, read service, reservation or RGB
scanout experiments. Its visible bars are independent of decoded samples.
The experiment measures private compute correctness/cycles, USB/SPI behavior,
stack and heap; it cannot qualify network video or 30 fps presentation.

## Reproducible inputs and evidence

- Frozen codec kit: `27a4dde6a7e2ea4fab09d892551ef542f05c8965`.
- Coordinated Sunshine pin: `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`.
- Selected elastic-store manifest: `40815ab116f82708eaa064a24b8091eeee70a850fd31e843f91faa1bbd38a051`.
- Reservation successor manifest: `4a1b5465c629affe7b6489a480603bdd8fcbc98931af53104b985bf893b10c87`
  (199 artifact hashes independently checked).
- Portable AKD1 FPGA source package: `fpga/exports/akd1-compute-source-20261104`,
  manifest `380c9860655e0d67a72b2d69d7426621da139221c41650dddcdfb24fa07b545a`.
  Its original supplied BIT is distinct from the separately executed clean
  source synthesis/route; no byte-identical rebuild claim is made.

Full experiment sources and raw evidence remain in the local
`fpga/experiments/` directories. Simulation, clean implementation reports and
future physical observations remain separate evidence categories.

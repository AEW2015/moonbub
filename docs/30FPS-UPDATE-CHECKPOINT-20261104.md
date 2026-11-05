# ESP32 / FPGA update checkpoint

Latest: [November 5 development and hardware gates](30FPS-STATUS-20261105.md).
The newer record covers installed v27, the 100-frame hardware result, double-bank
storage and restricted HUD decoding; it supersedes older pending-work status here.

Continue toward 720x480 at 30 unique physical presentations/s. This checkpoint
updates the execution order in the coordinated plan; it does not change the
published MSV1 or AV v1 wire formats. A subsequent controlled hardware window
installed v26, measured the private AKD1 fixture and restored normal operation;
see [the physical results](V26-AKD1-HARDWARE-RESULT-20261104.md). The complete
fixture target is now explicitly [CP23/HC22/HD22](CP23-FIRST-HARDWARE-FIXTURE-20261104.md),
with no complete-profile image or loader implemented yet. A current network
address/readiness is not inferred from earlier sessions.

## Completed and measured

| Work | Result | Scope |
| --- | --- | --- |
| Private KEY compute | 3,000,322 simulated cycles, exact 518,400 samples/tag | One ROM-fed fixture, not decoded LCD output |
| Compact YUV store with selected admission guard and 512-byte elastic FIFO | 31.23946 ms nominal at 100 MHz; all 259,200 stored words and canonical tag match | One KEY plus synthetic competing reads; no moving-frame publication |
| Native RGB565 arithmetic | 1,471,588 oracle pixels match; separate 160-bit ownership-tag regression passes | Arithmetic/component simulation |
| Direct YUV scanout, original write-load stress | 718 missed lines under uniform writes; 444 under batch writes | Preserved counterexamples; throughput alone did not protect deadlines |
| Bounded read-reservation successor | Zero missed lines, underruns or pixel mismatches in matched static, uniform and batch tests | Two refreshes of one immutable image per profile; not 30 fps video |
| Bank-separated memory service | Mixed useful writes/reads each improve from about 34.308 to 51.349 MB/s; KEY backlog is periodic, P backlog grows | Sealed finite service simulation, not frame-deadline or hardware acceptance |

The reservation successor checks 691,200 native canvas pixels and 76,800 margin
pixels per profile, with 1,440 good line latches. Both write-load profiles verify
all 238,981 offered words after actual drain. Uniform producer backlog increases
from 3 to 70 words; the batch profile still needs a 5,760-word peak. This is a
latency/buffering tradeoff, not free bandwidth. Minimum observed final-RGB-word
to latch intervals are 1.930366 us and 1.950765 us; these are simulation intervals,
not routed electrical timing slack.

## Next implementation order

1. **Seal memory-service comparison and address P service.** Bank-separated
   KEY/P windows and accepted-work drains have completed. KEY write backlog at
   matched panel boundaries is 6, 12, 10 and 9 words with zero read backlog.
   P write backlog grows from 75,766 to 288,233 words, with per-flow pending
   reads also growing. All checked data and LCD deadlines pass; this is a
   capacity failure for the offered P profile, not permission to drop work.
   Upper-address/masked-write checks also pass, including one accepted final-word
   BL8 burst, all eight physical beats and preserved sentinels. Compare
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

The v26 ESP32 diagnostic app and guarded-ROM AKD1 BIT passed the limited physical
private-compute experiment documented above. The repeat procedure is
[the exact hardware sequence](AKD1-LAB-WINDOW-20261104.md):
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
- Bank-locality manifest: `83ebcc2c1355736954917bcf97fee1b217486c7a595dc3f095c1060445aba312`
  (112 artifact hashes and all 111 unchanged baseline artifacts verified).
- Portable AKD1 FPGA source package: `fpga/exports/akd1-compute-source-20261104`,
  manifest `380c9860655e0d67a72b2d69d7426621da139221c41650dddcdfb24fa07b545a`.
  Its original supplied BIT is distinct from the separately executed clean
  source synthesis/route; no byte-identical rebuild claim is made.
- Portable v26 ESP32 source package: `firmware/exports/v26-key-diag-source-20261104`,
  manifest `8b40f9a06d5f9634a3686d503455a7cb736c61b2e99951722cd9fdf213beba6b`.
  All 575 selected source/harness inputs are unchanged; 656 included artifacts
  are hash-bound. It includes assets and locks, with explicit esp193/IDF5.4.3
  tool/cache requirements. An existing GameBub checkout is not required.
  Release UF2/BIN/ELF are identified but omitted, and packaging did not rebuild
  the target or establish byte-identical image reproduction.
  Follow [the fresh-copy verification instructions](V26-SOURCE-EXPORT-USAGE-20261104.md)
  so regenerated test logs do not replace the package's sealed evidence.

Full experiment sources and raw evidence remain in the local
`fpga/experiments/` directories. Simulation, clean implementation reports and
future physical observations remain separate evidence categories.

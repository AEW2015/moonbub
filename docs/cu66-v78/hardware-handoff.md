# V78 decoder/direct-display handoff

## What changed

The new production candidate is `cu78_system`. It uses actual compressed-packet
parser, inverse/reconstruction, SHA validation, canonical writes and stored
reference reads, plus the guarded native semantic HUD endpoint. It commits a
canonical bank directly to `cu78_direct_scanout`; there is no painter, RGB slot
allocation, RGB framebuffer copy or fabricated paint-complete acknowledgment.

The frozen V77 cache/converter produces RGB565 at native line-buffer ingress.
The coded image remains **720×480**, mapped into the **480×800** portrait raster
with black margins. This iteration does not lower resolution, replace the
compressed format, or change Sunshine/ESP32 packet semantics.

The receiver, scanout and evidence audit were developed in parallel, with a Luna
agent handling the evidence audit. Root integration and retained failures are
reviewable in the same package. Earlier revisions remain frozen.

## Ownership and validation

Three physical canonical/HUD banks retain separate front, reference, pending
and candidate leases. A new candidate can use the third bank while a previous
descriptor is pending, but it cannot overwrite any leased front/reference.
Global commit is irreversible; processor COMMIT acknowledgment can be retried
idempotently. Visible source generation changes only at a matching qualified
vblank and old-reader drain. Completing a local cache epoch does not release a
canonical reference lease.

`validated_ready` is reached after canonical hash, HUD result and physical write
fences, independently of RGB composition. The complete timestamp contract
remains [V76 milestones](../cu66-v76/milestones.md): immutable ingress-complete
→ validated-ready is the primary latency, retaining queue time. Processor ACK,
front switch and first complete correct raster are separate events.

Scanout repeats the immutable front at native refresh and accepts one pending
source. A late pending descriptor can wait behind an already prepared repeat,
adding a native refresh of presentation latency. Repeat rasters retain the old
source identity and never count as newly streamed frames.

## Retained evidence

The detailed machine-readable results live below
`fpga/experiments/cu66-v78/`. `system/analysis.json` reports latency and finite
source cadence, derived from the result timestamps rather than renderer clocks.

| Layer | Exercised boundary | Result scope |
|---|---|---|
| Receiver | Actual packet/base/hash RTL, controlled RAM and presentation endpoints | 32 frame cases, including bad CRC, failed drains/write errors, stale responses, three-bank concurrency and lost COMMIT ACK |
| Scanout | Actual cache/converter/LCD, delayed immutable fixture memory | Two seeds, each three source epochs and seven exact native rasters; 5,376,000 pixels total, zero underruns/errors |
| Integrated positive | Actual decoder, SDRAM controller/command model, guarded HUD transfers/readback and native scanout | Independent full canonical planes/tags and complete rasters for every requested source; no canonical seeding or per-source reset |
| Integrated faults | CRC rejection, physical partial canonical write abort and valid retry | Accepted reference/HUD/front retained; old front still produces an exact full raster after each rejection; no reset |

Each successful source writes **280,320 x16 words** in **35,040 BL8 commands**:
259,200 canonical words plus 21,120 HUD words. Its HUD endpoint also reads back
21,120 words in 2,640 requests and hashes the physical result before reporting
the transfer fence. **RGB framebuffer writes are zero.** The oracle reads
actual SDRAM storage; its expected planes/references never supply decoder input.

The two-frame paced run passes at both modeled SDRAM tAC corners, 2 and 7 ns.
Validated latency is **14.08760 ms key / 28.82138 ms P** at an assumed 100 MHz.
The four-source fixed-30-arrival run validates in **14.08760–28.76078 ms**, with
all four processor ACK intervals below 33.333… ms. Its arrival-to-first-full-
raster end is **30.54665–58.68038 ms**. Source raster-start gaps include an
initial **61.46706 ms**, followed by **30.73353 ms** gaps. Thus passing a serial
service budget does not establish a display latency bound or sustained 30 fps.

The extended **30-source fixed-arrival campaign passes all 30 canonical and
full-raster checks**, including keyframes 0 and 24, without per-source resets.
It observes **25,353,488 native pixels**, including repeated rasters and a
partial final raster: zero black/mismatching lines and zero underruns. All
30 processor COMMIT-ACK intervals fit the serial 33.333…-ms budget. The maximum
recorded ingress-to-admission queue interval is one model clock (10 ns).

| Thirty-source run, modeled 100 MHz | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Ingress → validated-ready | 14.08760 ms | 26.96566 ms | 29.10779 ms |
| Ingress → processor COMMIT ACK | 14.08764 ms | 26.96570 ms | 29.10783 ms |
| Ingress → first complete correct raster end | 30.54665 ms | 51.71677 ms | 58.68038 ms |

Its finite first-to-last source cadence is **29.48734 fps**, using 29 source
intervals between first complete-raster starts. This excludes initial loading
and final drain and includes native refresh quantization and the initial
late-pending delay. It is a short diagnostic, not the 1,800-source/60-second
qualification. **0/30** validated intervals meet the strict under-10-ms goal.

For context, the frozen V76 warm RGB-copy path took **86.60411–89.20155 ms** per
complete transaction. V78 removes that composition stage, while validated decode
remains in a similar tens-of-ms range. These are different finite schedules,
not a matched-phase speedup benchmark. See the retained V76 phase results.

## Reproduction

Use the existing `gamebub-cu66-v69-build` container, repository mounted at the
same absolute path, Verilator 5.020 and one build job. The runners retain exact
commands, input/source hashes, logs and finite watchdogs.

```sh
python3 scripts/cu66-v78/verify_baseline.py
python3 scripts/cu66-v78/run_receiver.py
python3 scripts/cu66-v78/run_scanout.py
python3 scripts/cu66-v78/run_system.py --frames 2 --mode paced --tac 2
python3 scripts/cu66-v78/run_system.py --frames 2 --mode paced --tac 7
python3 scripts/cu66-v78/run_system.py --frames 4 --mode fixed30 --tac 2
python3 scripts/cu66-v78/run_system.py --frames 30 --mode fixed30 --tac 2
python3 scripts/cu66-v78/run_system_fault.py
python3 scripts/cu66-v78/analyze_system.py
python3 scripts/cu66-v78/verify_evidence.py
python3 scripts/cu66-v78/bundle_manifest.py
```

Do not run concurrent builds sharing the same `/build/v78-system-tacN` directory.
Corner directories and fault builds are separate. A failed initial build missing
the renderer wrapper and the fault bench's original non-quiescing HUD producer
are retained; the latter received the guard's expected error. No RTL fix was
needed for that bench correction. The earlier generic partial-write PASS is also
archived before strengthening the abort condition to require canonical writes.

## What the results do not establish

Native HUD decoding, readback hashing and CPU control execute in zero simulated
time. Wall-time measurements are diagnostic, not substituted for target CPU
cycles. Packets are immutable local fixtures rather than live ESP32 Wi-Fi/QSPI.
Fixed arrivals are modeled releases; the queue estimate is not a qualified ESP32
buffer capacity. The current producer samples that estimate before waiting for
`start_ready`; use admission-minus-release timings for actual recorded queue
latency and improve queue occupancy accounting before a slower-load campaign.

The model assumes 100-MHz memory service and a 34.058-ns pixel period. It is not
routed timing, CDC/IO/electrical signoff or physical throughput. The declared
Artix-7 exact part remains unavailable in the installed Vivado setup; no device
fit or new bitstream is claimed. V77's component-only unplaced mapping counts
cannot be reused as V78 whole-system utilization.

Bad-candidate recovery is narrower than display fault recovery. A fatal cache
or memory error stops publication until reset; `lcd_error`/`lcd_memory_errors`
are exposed separately rather than automatically aborting the receiver. The
positive bench checks errors during transactions and native output continuously,
but a future regression should explicitly retain sticky error observations
through readiness/release waits and final drain, with per-source raster-progress
deadlines. Those windows must not hide a late diagnostic-only error.

The **457-frame changed-path coverage**, **1,800 distinct sources / 60 modeled
seconds**, target implementation, and **18,000 distinct sources / 600 physical
seconds** remain separate open gates. Neither a short fixed-arrival campaign
nor repeated display refreshes closes them. Strict under-10-ms validated decode
also remains open: a finite minimum or average is insufficient.

## Next implementation work

1. Harden campaign instrumentation: sticky display-error capture in every wait,
   explicit full-raster progress bounds, ingress/admission queue accounting and
   declared presentation-jitter limits. Preserve all failed/late/rejected IDs.
2. Run all retained histories before the 1,800-source campaign; vary arrival
   phase, reference/front sharing, SDRAM timing, CPU/HUD service and response
   stalls. Include the repeat-epoch delay in output cadence and latency.
3. Profile and reduce reference-memory critical-path stalls toward 10 ms. P
   frames still require 31,224 reference BL8 reads with the current ordered
   SAFE tile set. Prototype bounded outstanding reads, next-tile prefetch and
   row-aware command grouping without violating display deadlines or bank
   leases. Check critical-path timestamps; wait/service counters can overlap
   and must not be subtracted as a complete latency decomposition.
4. Implement and test a coordinated fatal-display recovery policy: stop new
   candidate admission, retain errors, drain accepted work and reinitialize only
   under an explicit generation/reset contract. Never acknowledge a failed
   raster as successful.
5. Qualify exact-device fit/route/CDC, real HUD firmware cost and live ESP32
   transport, then instrument physical source IDs and synchronized timestamps
   for the sustained 30-fps and strict max-under-10-ms milestones.

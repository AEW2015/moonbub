# Python memory/service tradeoff prototype

This is a deterministic **architecture what-if model**, not a memory-controller
RTL test, memory-data test, fitted SRAM timing model or physical throughput
measurement. It advances the software part of memory plan M3/M4; it does not
complete the hardware gates. See the [memory audit](../../docs/external-memory-audit-plan.md).

## Reproduce

Python 3.10 or newer, standard library only:

```sh
cd experiments/python-memory-study
python3 -m unittest -v test_model.py
python3 model.py
```

`results.json` contains all configuration values, service/queue counters and
SHA-256 hashes of the model and its tests. The default run compares 29 short
scenarios, with 15 source frames each. The 30 fps capture window is 500 ms;
the 60 fps window is 250 ms. Scanout continues throughout a separately declared
eight-frame-period drain allowance. This is a short capacity experiment, not
a sustained FPS qualification. The repeated default compressed size is 26,991
bytes, taken from an existing synthetic JPEG fixture; it is not gameplay.
Reconstruction and hypothetical-vblank eligibility observations use the
explicit half-open window **`[0, N/fps)`**: a timestamp exactly at its endpoint
is excluded. Line deadlines instead cover lines whose scheduled deadline is
at or before the endpoint; completion exactly at a line deadline is timely.
`lines_completed_by_deadline_window` counts eventually completed lines in
that scheduled-deadline set, not line completions observed before the endpoint.

Supply actual encoded frame sizes to connect the codec benchmark:

```sh
python3 model.py --frame-sizes sizes.json --frames 30 --output measured-sizes-service.json
```

The input is a JSON list of positive integer byte counts or
`{"frame_sizes": [26991, 49152, 262144]}`. A short list repeats explicitly;
use the corresponding number of frames to avoid accidental cycling. The input
file hash is recorded. No actual encoded pixels are decoded by this model.

## Model boundaries and assumptions

* One 100 MHz request scheduler and one shared SDRAM DQ bus; it is not two
  independent channels. All modeled addresses use one chip and one bank.
  Sequential byte addresses determine the current 512-word SDRAM row;
  switching clients can close locality. References at byte address 2 MiB
  extend past the old functional model's 2 MiB array: these are analytical
  address/service calculations, not validation that existing RTL accesses it.
* BL8 transfers carry 16 payload bytes. Row-hit writes/read take 13/15
  serialized **request-service cycles**, and row changes add eight cycles,
  matching the prior isolated controller scenarios. These are not data beats
  at one word per controller cycle, nor a fitted-part guarantee. Refresh here
  is an explicit assumption: 12 cycles every 780 cycles. Refresh debt cannot
  disappear, and refresh invalidates the open-row state. No read/write
  turnaround penalty beyond these assumptions is modeled.
* A grant can hold up to eight serialized BL8 requests. A line arrival or
  refresh cannot preempt a grant; refresh is serviced afterwards. The model
  accounts for those bounded blocking intervals. It does not implement an
  SDRAM command/timing engine or infer actual inter-chip timing.
* Display is a uniform 480-word × 720-line scan of the **720×480 coded
  canvas**, at 60 or 65.076 Hz. Every line must finish by its next uniform
  release. This excludes physical-panel blanking, the prototype's larger
  480×800 canvas, actual LCD prefetch/FIFO/CDC, scanline phase and raster
  timing. It is neither the former 1,843-cycle line test nor a qualified panel
  mode. At 60 Hz its modeled deadline is about 2,315 cycles. Set geometry and
  deadlines from the fitted display before interpreting hardware margin.
* `strict_display` always services pending display work first, then background
  clients round-robin. It can starve all background clients. `deadline_rr`
  additionally rotates through display/background clients when display is not
  urgent, using a conservative remaining-request-cost threshold. It is a
  candidate scheduling policy, not a proven real-time arbiter.
* A source frame is ready in its entirety at capture time. Network delivery,
  host encode, ESP32 forwarding, QSPI, CDC, input/audio and decoder arithmetic
  take **zero time**. This is intentionally optimistic memory-only analysis.
  The SDRAM path completes compressed writes, then compressed reads, then
  reconstruction. Pixel writes and optional complete-reference reads contend
  with scanout. A reference read is charged once per RGB565 pixel; no extra
  reference-copy cost is added. No motion overfetch/cache/reuse is modeled.
* Pixel/reference jobs are independent **unbounded queues**, not a bounded
  framebuffer ownership architecture. The reference traffic is demand only;
  this model does not maintain reconstructed reference pixels or commit IDs.
  Jobs may refer to the same hypothetical reconstruction address while older
  work exists. No tearing-free framebuffer ownership, decode/write streaming,
  physical memory-drain ACK, CRC calculation or atomic presentation is proved.
* BRAM compressed storage is ideal zero-time, two hypothetical 48 KiB slots.
  SRAM uses a separate single port, with write + read at an assumed three
  cycles per 16-bit word and no turnaround penalty. That assumption is
  configurable and **not derived from the fitted part**. Independent SRAM
  service may overlap SDRAM; its requests still serialize with each other.
* SDRAM and SRAM compressed cases model two 256 KiB slots. For SRAM that uses
  all 512 KiB, with metadata/scratch outside SRAM; it is not a selected viable
  production allocation. Two 224 KiB slots plus 64 KiB metadata/reserve are a
  separate allocation example. BRAM 96 KiB of compressed storage is also a
  hypothetical candidate, not evidence of full-design packing or timing.

`SlotPool` is a separate bounded ownership oracle. Tokens include a generation,
and accesses must fit the **acquired frame length**, not merely the slot cap.
Commit requires a supplied integrity-success flag and no outstanding accesses;
release before drain fails. Tests exercise stale token/range/cap/commit/reuse
failures. The model's success flag is not a computed CRC, and this oracle is
not production RTL/firmware. Padding traffic is charged in BL8 service counts;
the oracle checks logical payload ranges rather than physical byte masks.

## How to interpret the result

The default short scenarios show the intended architectural distinction:

| Workload | Shared SDRAM compressed | Separate SRAM compressed | Interpretation |
| --- | ---: | ---: | --- |
| 30 fps intra / 60 Hz coded-canvas scanout | about 10.64 ms max memory age | about 10.62 ms | Compressed staging is a small cost at this size |
| 30 fps + full reference read / 60 Hz | about 22.96 ms | about 22.94 ms | Reference traffic dominates the difference |
| 60 fps + full reference read / 60 Hz | about 111.50 ms | about 99.39 ms | Growing frame queues despite no scanline misses |
| 60 fps + full reference read / 65.076 Hz | about 132.59 ms | about 119.69 ms | Faster scanout leaves less reconstruction service |

These rounded numbers are **model output**, not physical latency. At 60 fps
with full reference reads and 60 Hz scanout, all 15 source frames eventually
finish during drain in these cases, but only 10 shared-SDRAM frames or 10 SRAM
frames become eligible for a hypothetical vblank before the 250 ms endpoint.
Zero display-line misses therefore cannot be used as a streaming success
criterion. Fairer scheduling in this particular address pattern does not
resolve the capacity deficit and may add row-switching costs.

`hypothetical_vblank_eligible_by_window` only rounds each reconstruction's
completion to the next vblank. It **does not count distinct displayed frames**:
multiple frames may share one eligibility timestamp, publication ownership is
absent, and no actual scanout buffer swap is performed. Strict-window and drain
counts are reported separately rather than moving the deadline after the run.
For example the 60 fps intra / 60 Hz cases reconstruct all 15 frames, but only
14 become vblank-eligible strictly before the 250 ms endpoint. This boundary
effect is separate from the growing queues in the full-reference workloads.

In the size-tail scenario (26,991 / 49,152 / 262,144 bytes), the BRAM48 cap
rejects five of 15 frames; SDRAM/SRAM admit them under the hypothetical larger
cap. No frame-size policy can make 256 KiB transmit quickly over a constrained
network. The allocation check separately rejects the original 128 KiB
assembly region as insufficient for the negotiated 256 KiB frame cap.

## Verification and next experiments

### Connection to actual offline JPEG sizes

Run `python3 codec_sizes.py` after completing the adjacent codec benchmark.
`codec-size-results.json` binds its input JSON, model and driver by SHA-256.
It feeds all 60 sizes from each video sample, separately for fixed q80 and
the bounded 8 Mb/s JPEG policy, through all three storage scenarios at 30 fps
and 60 Hz. These are 12 additional two-second memory-only scenarios. The
reference-read option is **off**; this does not evaluate temporal tile copies.

| JPEG workload | BRAM max memory age | Shared SDRAM | Separate SRAM |
| --- | ---: | ---: | ---: |
| Combat, fixed q80 | 9.813 ms | 10.809 ms | 10.785 ms |
| Combat, wire-budget policy | 9.813 ms | 10.626 ms | 10.603 ms |
| Second clip, either selected policy | 9.813 ms | 10.462 ms | 10.441 ms |

All 60 reconstruct and become hypothetically vblank-eligible within each
two-second window, with no modeled scanline deadline misses. That observation
belongs only to this zero-network/zero-decoder-compute workload. The separate
network projection includes ideal serialization and an assumed 8 ms decoder
and has different counts. Do not combine these numbers by addition/subtraction
or treat them as measurements of one pipeline. Finite framebuffer ownership,
real decoder timing and simultaneous arrival/service traces remain missing.

The small modeled SRAM advantage is roughly 0.02–0.024 ms here, under an
unqualified assumed three-cycle SRAM port. It supports measuring whether SRAM
is useful; it does not establish a physical advantage or select a controller.

### Remaining validation

The tests include an intentionally impossible short line deadline, a saturated
display stream that starves background requests, a deliberately slow SRAM
scenario whose strict-window count differs from drain completion, cap
rejection and ownership errors. Those are expected negative **conditions**
checked by passing unit tests; they are not hidden successful FPS runs.

Next use the codec study's encoded sizes with the same frame IDs and add an
actual byte/arrival trace. Qualify the fitted memory and panel, then replace
service constants with measured/controller-RTL distributions. Add finite
pixel/reference queues, source/back/front ownership, real decoder computation,
response backpressure and line FIFO timing before using this model to select
an architecture. The current result favors preserving 30 fps intra JPEG as
the control and avoiding a full-reference read merely to consume spare RAM.
It does not justify an SRAM controller solely from average byte capacity.

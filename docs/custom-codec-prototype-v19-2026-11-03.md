# Iteration 19: frame-slot ownership and exact sparse decoder design

Target remains **720×480 coded / 720×405 active / 30 scheduled source IDs/s**.
The paired `handoff/gamebub-app-codec-v19-20261103` branches carry two separate
Python studies: actual-byte frame admission and packet-derived decoder arithmetic/
service planning. They are not one calibrated ESP32/FPGA simulation. No installed
firmware, native Sunshine codec, FPGA bitstream or physical 30 fps is supplied.
Frozen v18 branches retain their original source and results.

## Frame grants: reserve whole-frame capacity before committing

The [frame-grant study](../experiments/python-game-frame-grant-study/README.md)
adds CRC-bound FG19 REQUEST/GRANT, CANCEL/CANCELED, FINISH/FINISHED and RELEASE.
Every control message has 32 field bytes plus four CRC bytes and pays 28 bytes
IPv4/UDP overhead. Control traffic uses the actual shared forward wire/mailbox
worker and reverse wire. Five data tokens reserve the sixth mailbox position
for one FG19 or QC18 control; this partition has its own no-grant control run.

Receiver frame ownership is bound to epoch, frame, nonce, exact slot, body CRC
and declared total. The sender commits only after a received grant. FINISH is
sent after all packet consumption permits return. FINISHED acknowledges receipt
of that drain barrier and frees the request-control token; it does not free the
frame slot. RELEASE follows actual receiver ingress/decode/read drain. The sender
requests only a host-known-free slot, so a lost RELEASE cannot cause silent reuse.
AF03 remains the separate decoded-reference publication acknowledgment.

Cancellation is allowed only before data enters the engine, including committed
frames that expire before packetization. Wrong-kind/slot/nonce replies, delayed
old data and duplicate fragments cannot release a different owner. Unknown lost
grant/release/packet-credit outcomes intentionally stop with bounded retained
ownership; no timeout invents capacity. Reset/rekey across sessions is not modeled.

The first serialized design held the request token until frame RELEASE and lost
substantial cadence. Its retained fixed-cost control is compared with the new
FINISHED pipeline. These are protocol/service experiments, not compression gains.

## Controlled gameplay and fault results

There are 12 cases and 790 scheduled capture events:
seven 90-frame native profiles across two existing 1280×720 regression clips,
and five 32-frame synthetic fault controls. The native profiles reuse
180 distinct acquired source hashes. Sources run at 29.88 fps and are
hypothetically scheduled at 30 IDs/s; offline acquisition is excluded, BOX resize
is paid. Neither source is a fresh held-out long gameplay recording.

| Profile | Strict / eventual out of 90 | Diagnostic IDs/s in [500,2500) ms | Busy feed rejections | Maximum presentation gap ms |
| --- | ---: | ---: | ---: | ---: |
| mass-effect-2600/fixed_base6 | 87 / 89 | 29.5 | 0 | 66.7 |
| mass-effect-2600/fixed_partition5 | 87 / 89 | 29.5 | 0 | 66.7 |
| mass-effect-2600/fixed_serialized_grants5 | 55 / 58 | 18.5 | 0 | 83.3 |
| mass-effect-2600/fixed_grants5 | 79 / 82 | 27.5 | 0 | 83.3 |
| mass-effect-2600/measured_grants5 | 79 / 82 | 27.0 | 0 | 66.7 |
| mass-effect-7200/fixed_base6 | 60 / 63 | 20.5 | 0 | 116.7 |
| mass-effect-7200/fixed_grants5 | 54 / 57 | 18.0 | 0 | 116.7 |

Fixed profiles use identical historical Python stage-service constants: resize
3.25972 ms, candidate build 29.4824 ms, decode begin 23.87022 ms, commit 0.09932 ms,
packetize 0.03485 ms, decode complete 0.01377 ms and ACK apply 0.00672 ms; other
Python stages cost 0.005 ms. Real functions still execute to validate actual bytes,
references and pixels. These constants are not ESP32/host native calibration.
The measured profile separately pays remeasured Python work and is not a controlled
speedup comparison. Independent virtual servers do not prove a shared CPU schedule.

The constant-median native baselines may have zero busy failures; that is not a
native throughput benefit from grants. A deterministic slow-decoder regression
reproduces busy failures without grants and removes them with grants. The five-token
partition control separates mailbox partitioning from frame reservation. The second
scene adds bitrate/admission pressure, rather than assuming every scene behaves
like the first. All decoded native selected RGB565 HUD words match the source.
The more complex 7200 scene does not always fit all four requested HUD patches
under the 49,152-byte cap. Exactness applies to the actual selected subset, not
all requested HUD pixels. For example, its first key can fit three selected
patches but adding the fourth would exceed the complete cap. Coverage is:

| Profile | Decoded frames carrying all requested HUD patches | Selected exact pixels per decoded frame |
| --- | ---: | --- |
| mass-effect-2600/fixed_base6 | 89 / 89 | 21120 |
| mass-effect-2600/fixed_partition5 | 89 / 89 | 21120 |
| mass-effect-2600/fixed_serialized_grants5 | 58 / 58 | 21120 |
| mass-effect-2600/fixed_grants5 | 82 / 82 | 21120 |
| mass-effect-2600/measured_grants5 | 82 / 82 | 21120 |
| mass-effect-7200/fixed_base6 | 39 / 63 | 15360, 21120 |
| mass-effect-7200/fixed_grants5 | 37 / 57 | 15360, 21120 |

Omitted regions still appear through the lossy base image. Full requested HUD
coverage is an unmet gate for that scene. The next encoder policy should reserve
mandatory HUD bytes first and adapt background quality within the remaining budget,
while retaining the 720×480 geometry and reporting source-quality loss.

Rejected builds still cost service and can incur FG19 request/cancel traffic;
they send no AR03 data and publish no reference. Three blackhole/control-loss
cases deliberately retain unknown owners at safe stop; remaining cases drain.

## Exact decoder arithmetic and compact reference storage

The [causal-stripe study](../experiments/python-game-causal-stripe-study/README.md)
replays 16 real AR03 decisions: 12 native decisions reuse six acquisitions across
GM/exact cohorts, and four small controls exercise SR paths. Its sparse separable
Q14 inverse preserves both rounding boundaries. **97,308 blocks, 6,227,712 residual
samples, 6,224,472 reconstructed YUV samples and 253,440 selected UI words** match
frozen vectors. Tests also cover negative rounding, legal coefficient extremes,
DC values, bounds and cases where sparse scans cost more than dense arithmetic.

Across the 12 native decisions, general-block MAC demand falls from 27,777,024 to
4,267,808: **84.64% fewer products beyond the existing zero/DC bypass**. That is
an operation-count result, not an FPGA speedup. Index discovery, dequantization,
two dependent passes, output stores, color/packing, tag and memory work are paid
separately in the conditional schedule. Dense-all-blocks is only a diagnostic.

Compact YUV8 storage round-trips all 16 reconstructed vectors and produces the
same canonical int16 reference tag. Physical YUV reads/writes become one byte per
sample; tag hashing still consumes the canonical two-byte stream, with expansion
work charged. UI patches remain display-only and never enter prediction banks.
Neither optimization changes experimental AR03 payload syntax.

| Conditional decoder profile | Mean service over 12 native decisions | Change |
| --- | ---: | ---: |
| Existing zero/DC bypass, four wide lanes | 88.5134 ms | Baseline |
| Sparse general inverse, same memory/lanes | 84.7320 ms | 4.27% reduction |
| Sparse plus compact YUV8 | 67.6294 ms | Further 20.18% reduction |

All native decisions in all ten profiles miss the declared 33.33-ms single-frame
budget, including the compact 240-MB/s sensitivity. This conservative serial
planning model is not a physical upper bound; it identifies costs that average
MAC/bitrate arguments omit. More DSP lanes alone barely help this schedule.

The full-resolution local planning footprint is **100,112 bytes**: a 49,152-byte
compressed cache, bounded coefficient/reconstruction stripes, inverse scratch,
basis/quantizer storage, color lines, palette and reservoirs. Parser/control state,
whole Python coefficient/output/oracle arrays and external banks are excluded.
This is not a complete decoder heap or BRAM fit proof. The cache trades area for
entropy/SDRAM decoupling; fill and token reads are paid. A smaller refill cache
requires an explicit shared-memory arbiter.

Service assumptions include 100 MHz, hypothetical wide multiply/accumulate slots,
140 MB/s effective SDRAM before the average 800×480×60 RGB565 scanout reserve,
20 MB/s QSPI and four full-packet preflight planning passes. The two-18×18-per-wide-lane
mapping is an assumption, not mapped utilization. Legal operand/biased accumulator
bounds are checked, but routing, Fmax and physical 480×800 line deadlines are not.

## Next application-specific implementation gates

1. Reserve mandatory HUD bytes before selecting background quantization; record
   source-quality loss and full requested coverage separately from selected-patch
   exactness. The second scene currently omits a patch on some admitted frames.
2. Keep the FINISHED pipeline and whole-frame ownership tests. Explore pre-granted
   reusable capacity leases or grant overlap with candidate construction to avoid
   another request round trip per frame. Preserve exact identity binding, bounded
   controls, explicit cancel/drain and epoch reset before production negotiation.
3. Feed canonical tags during ordered reconstruction instead of rereading the full
   bank. Extend the frozen v16 StripeTagger ordering proof to these AR03 vectors;
   overlap hash service only after proving ordering, storage and backpressure.
4. Fuse compact reconstruction, chroma/color and RGB565 output where causally possible;
   otherwise charge intermediate reads. Compare a small bounded compressed refill
   cache plus real arbitration against the 49-KiB full-cache planning variant.
5. Port the exact sparse inverse and compact-bank kernels to bounded native/RTL
   implementations, using the exported vectors as correctness gates. Preserve old
   zero/DC shortcuts and switch to dense work when scans are more expensive.
6. Calibrate native host construction and ESP32 CRC/copy/DMA/heap, RF and QSPI service;
   then integrate this actual frame/reference trace with mapped memory, full-panel
   scanout, resource and timing checks. Test fresh long gameplay before choosing a
   default. Keep the working JPEG hardware path while custom AR03 remains experimental.

Run `python experiments/verify_prototype_v19.py` for retained source/result hashes,
exact-vector replay, deterministic service reconciliation and fresh independent
audit. It does not rerun timed benchmarks. Study READMEs give reproduction commands.

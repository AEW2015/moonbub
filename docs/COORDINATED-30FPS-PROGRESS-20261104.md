# Coordinated 30 fps implementation progress

Date: 2026-11-04, America/Denver. Hardware updates remain deferred.

Goal: 720×480 at 30 unique physical presentations/s, then audio and controller
coexistence. Current complete custom-pipeline throughput and maximum physical
presentation rate remain **unknown**. No installed firmware, FPGA image, SD
configuration, serial session or running stream was changed for this work.

For the earliest useful physical test, see
[the hardware-window plan](HARDWARE-TEST-GATES-20261104.md). The prepared v22
app-only JPEG/AV regression can run at a coordinated window with unchanged
build50. Custom AR03 streaming still needs an integrated, routed image and live
backend; no calendar readiness estimate is established by component results.

## Shared versions

- Coordinated Sunshine plan: `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`;
  its separately identified encoder baseline is
  `19cdd7080e7ee181b9bd7a73f4ba5ac5400a36fc`.
- Frozen MoonBub codec/transport kit:
  `27a4dde6a7e2ea4fab09d892551ef542f05c8965`.
- Published contract/state review:
  `7fc6eb244ecb50aa5c52d385d8757a674b86a3d1`,
  [AR03-LAB-CONTRACT-REVIEW-20261104.md](AR03-LAB-CONTRACT-REVIEW-20261104.md).
- New firmware experiment: `v23-ar03-gateway-20261104`, built and unflashed.
  Source inventory SHA-256:
  `d904373e006126480d3de5c9d2711e459a614b0ed04de1dcc2b83b602243f36d`.

## ESP32: executable source export

[The portable receiver-core export](../host/ar03-receiver-core-20261104/README.md)
contains the exact four dormant production Rust modules, two host harnesses and
seven fixture files from sealed v23. `source-snapshot.json` binds all 13 copied
files to their original paths and hashes. It does not distribute the SDK or the
complete firmware application.

The standard-library runner executes 22 gateway-core and 10 shared-state tests,
then verifies four expected compiler rejections for copying or cloning mutable
frame/packet ownership managers. It needs Python and Rust stable; compiled files
live only in a temporary directory. This export was independently rerun before
publication.

Implemented laboratory behavior includes bounded parsers, two frame owners, five
DATA leases, a reserved control position, completion-bound PC18 replies, and
retained ownership on ambiguous backend outcomes. The real FIFO/DMA backend is
absent. The shared state oracle covers ten scenarios/51 supplied model steps;
its drain inputs do not prove physical completion. The retained 1,725 FG19 history
messages are wire fixtures, not 1,725 complete state-machine scenario proofs.

Live profile advertisement and activation remain disabled. GF03 lacks the FG19
grant nonce: an unseen delayed datagram can rebind if frame/body/length identity
is reused within a generation. The tests preserve that counterexample. Agree
identity lifetime, epoch generation, reset/rekey, peer binding, custom port and
lost-reply recovery with Windows before implementing a live endpoint. No new
wire field or unilateral transport version is introduced here.

Full v23 packaging passed 389 host-test executions, target build and validation
of 12,309 app-only UF2 blocks. These include repeated harness executions; they
are not 389 unique portable-core tests. Static SRAM is 121,772 bytes and BIN size
3,150,944 bytes. The dormant module may be removed by the linker, so these sizes
do not establish memory or scheduling cost for a future active receiver.

[The owned-storage adapter](../host/experiments/ar03-owned-backend-20261104/README.md)
now copies five bounded datagrams and implements the dormant core's backend
trait against a private hardware-adapter interface. Twenty host tests and three
expected compiler rejections pass, including stale/ambiguous completions,
reservation/retirement failures, buffer reuse and bounded polling. Ownership is
retained on exhaustion or ambiguity. The FIFO trait has no real implementation:
this is software storage scaffolding, not SPI/DMA, a live receiver or target SRAM
qualification. The finite poll-call budget does not establish worker wall-clock
service. Existing production negotiation/recovery and GF03 nonce limitations
remain open.

## FPGA: complete the decoder before measuring frame throughput

[The source-review export](../fpga/ar03-components-20261104/README.md) binds the
five experimental RTL components and two small control-path testbenches to their
sealed local inputs. Its portable runner checks admission/cancellation and
storage-cap controls only. It does not reproduce the full coefficient/KEY corpus
or distribute a complete integrated design, bitstream or live backend.

The isolated CP02 entropy component passed RAW/Rice coefficient validation,
real-section replay and a KEY seam into the verified inverse/reconstruction
component. Its frozen baseline corpus covers 259 cases, including 58 rejected
cases with no coefficient output, and 9,879,424 coefficient comparisons including
recovery. The joined seam checks 519,471 visible/recovery samples across six
planes. This is functional simulation evidence, not a full decoder benchmark.

The clocked-memory variant passed the same 259-case corpus and six-plane KEY
seam, plus 521 RAW reset/abort offsets and 33,344 recovery coefficients. Its 38
functional artifact hashes and all 102 baseline artifact hashes were rechecked.
An independent source review found no concrete functional sequencing defect;
that review did not rerun simulation.

Default capacity remains 65,536 packet bytes and 8,192 blocks; the outer complete
AR03 cap remains 49,152 bytes. Exact-default OOC synthesis on xc7a100tcsg324-1
mapped the clocked variant to 2,409 LUTs, 1,883 FFs, 20 RAMB36 and no DSP/LUT RAM.
This establishes isolated mapping, not combined fit or timing closure. Clock-only
100 MHz setup slack is **−2.641 ns**, with +0.260 ns hold slack. A separate ideal
zero-IO-delay diagnostic exposes a **−56.694 ns** path through descriptor variable
modulo; it is not a physical board constraint/result. No timing exception or
parameter reduction is used to conceal either failure.

The isolated **variant002** fixes those setup paths with registered arithmetic
and a 14-step restoring remainder after descriptor bounds checks. It passed the
259-case/9,879,424-coefficient corpus, 58 rejection cases, six-plane KEY seam,
521 RAW cancellation offsets, and admission checks including 8,192 blocks,
width256, held first byte, 16 reset/abort offsets and exact block-ID overflow
boundaries. Synthesis uses 1,909 LUTs, 2,012 FFs and the same 20 RAMB36. Clock-only
100 MHz setup/hold slack is **+1.606/+0.260 ns**, with no internal setup/hold
failures. The ideal zero-delay interface diagnostic now has +1.606 ns setup but
**−0.489 ns hold** across 451 endpoints. Routed/board/interface closure remains
open. A bounded native XSim synthesized-netlist replay passed all22 valid/eight
rejected admissions and16 cancellation offsets, including width256, high-bit
rejection and exact block-ID overflow. This checks the exercised divisor behavior
despite the source-order warning; it is not a full entropy netlist replay.

A passive-observer rerun of each six-plane KEY stimulus measured actual posedges.
For one complete 720×480 fixture, variant001's serialized window including plane
setup is 2,970,202 cycles; variant002's is **3,042,828 cycles**, or 30.42828 ms only
at the nominal simulated 10 ns period. Seeded stall sampling differs after
arithmetic staging, so this is not a controlled stall-for-stall speed comparison.
This tight component budget excludes parsers, real prediction memory, tags,
patches, memory arbitration/write drain, scanout and network service. It does not
establish physical 30 fps capacity or complex-scene bounds.
The [actual-clock measurement record](measurements/ar03-key-seam-v002-20261104/result.json)
retains all six plane events, stalls, source hashes and the explicitly excluded
stages; [the CSV](measurements/ar03-key-seam-v002-20261104/metrics.csv) supplies
the accepted-event cycle records.

The independent outer AR03 envelope component passes 56 cases, including all20
real mandatory-HUD packets:25 certificates,31 rejections,818,528 exact replay
bytes and12 reset/abort cases. It checks complete outer bounds/CRC, reference
profile, minimal inner identity and patch length framing before descriptors or
replay become valid. Normal retirement waits for pending/held reads to drain.
An explicit bad-inner-CRC/recomputed-outer-CRC case passes only this envelope
scope and is rejected by the full oracle. Actual GM01/map/plane and inner CRC
validation remain downstream work, as do patch semantics, temporal banks,
canonical tags, write drain and atomic presentation. Its64-bit opaque owner must
be preserved by an explicit wrapper around the entropy seam's32-bit identity;
silent truncation is not an integration strategy.

The separate GM01 section/map validator passes62 cases:28 certificates and34
rejections, including20 retained real GM01 packets,178,469 queried block
descriptors and12 cancellation phases. It checks inner CRC, exact header/map/
section bounds, zero motion vectors required by AR03, map domain/padding and
owner-bound scale queries. SR01 is explicitly unsupported. CP02 entropy/CRC is
still downstream: a deliberate bad-CP02/repaired-inner-CRC case demonstrates
that boundary. Independent read-only review verified22 artifact hashes and the
pinned Python/native source bytes; it did not rerun RTL simulation.

Integration work now joins envelope, GM01/map, CP02 and exact KEY reconstruction
with generated quantizer tables and a checked64-to32-bit owner sidecar. Its
private YUV output will precede HUD application and will not assert AF03 or
presentation. A canonical SHA256 tagger is being developed separately; raster
reordering, bank/patch work and actual memory/scanout remain required.

## Next gates

1. Retain the explicit interface hold/route limits and preserve all exact
   baselines and failed-gate evidence when integrating the next stages.
2. Validate the outer envelope and inner section/map parsing, then integrate
   reference banks, tag/patch work and real memory/scanout service. Only the
   complete pipeline can establish FPGA-only sustainable initiation interval.
3. Agree production transport/recovery semantics and implement the bounded ESP32
   backend against actual FIFO/read-drain evidence. Measure concurrent Wi-Fi,
   QSPI and decoder service before setting a supported live profile.
4. Exchange exact source/artifact versions and starting counters with Windows,
   then schedule a hardware window. Retain MSV1/AV as the known recovery/control
   path. Do not flash or start a stream on the strength of this document alone.
5. Qualify custom video-only fixtures and recovery, then 60 seconds each at
   5/10/15/20/30 fps. Follow with five minutes and 30 minutes at 30 fps before
   audio/controller coexistence qualification. Reconcile unique presentations,
   backlog, drops, faults and frame intervals; ingress ACKs are not presentations.

Cap-sized bodies alone require 11.79648 Mbps at 30 fps, before transport/control,
audio and radio overhead. Measure useful capacity and headroom. Neither host
encoding speed, entropy simulation cycles nor isolated OOC slack establishes
30 fps playback.

# Coordinated 30 fps implementation progress

Date: 2026-11-04, America/Denver. The v22 demo window has ended; development
has returned offline. See the dated results below.

Goal: 720×480 at 30 unique physical presentations/s, then audio and controller
coexistence. Current complete custom-pipeline throughput and maximum physical
presentation rate remain **unknown**. The v22 application was installed during
the requested demo; the FPGA image was retained. The receiver is now disconnected
and its serial recorder stopped.

For the earliest useful physical test, see
[the hardware-window plan](HARDWARE-TEST-GATES-20261104.md). The prepared v22
app-only JPEG/AV path was exercised with unchanged build50, with an unexplained
reboot still open. Custom AR03 streaming still needs an integrated, routed image and live
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
- Dormant gateway experiment: `v23-ar03-gateway-20261104`, built and unflashed.
  Source inventory SHA-256:
  `d904373e006126480d3de5c9d2711e459a614b0ed04de1dcc2b83b602243f36d`.
- Current diagnostic app candidate: `v26-key-diag-access-20261104`, built and
  unflashed; exact package/build records appear below. Installed app remains v22.

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

The [GM01 section/map source export](../fpga/ar03-gm01-20261104/README.md)
reproduces62 cases:28 certificates and34
rejections, including20 retained real GM01 packets,178,469 queried block
descriptors and12 cancellation phases. It checks inner CRC, exact header/map/
section bounds, zero motion vectors required by AR03, map domain/padding and
owner-bound scale queries. SR01 is explicitly unsupported. CP02 entropy/CRC is
still downstream: a deliberate bad-CP02/repaired-inner-CRC case demonstrates
that boundary. Independent read-only review verified22 artifact hashes and the
pinned Python/native source bytes; it did not rerun RTL simulation.

## Completed private KEY integration and controlled optimization

The local joined KEY pipeline now validates envelope, GM01/map and CP02, then
performs exact reconstruction with generated quantizers and a checked 64-to-32-bit
owner sidecar. Its corpus passed 35 cases (14 positive, 21 rejected), including
late failures that invalidate previously emitted private samples.

The canonical SHA-256 tagger and double-stripe raster adapter are also joined.
The final baseline checked 1,038,501 sample transfers across seven main cases,
plus metadata, cancellation and downstream-error tests. Completion requires
the entire private pre-HUD candidate and all 16 stored tag bytes to match.
It does not authorize HUD acceptance, reference publication or AF03.

A controlled inverse-only A/B used the same near-cap 48,203-byte 720x480 KEY
packet, source gaps and observer behavior. Actual simulated clocks from start
to private tagged result fell from **3,788,358 to 2,950,451**, saving 837,907
clocks (22.1%). At a nominal 100 MHz that is 29.50 ms, before HUD, temporal
banks, external-memory service and scanout. It is not physical 30 fps evidence.
The [retained measurement](measurements/ar03-private-key-20261104/README.md)
includes exact cycle records and source-bound result manifests.
The faster inverse preserves the exact samples and tag. Its isolated internal
setup/hold estimates are positive, but the ideal-IO hold diagnostic still fails;
combined board routing and interface timing remain open.

Board resource review adds a separate integration gate: the retained build50
utilization report records **120.5/135 BRAM tiles (89.26%)**, while the isolated
CP02 implementation alone uses 20 RAMB36. Adding both decoders, packet storage,
stripes and a fixture ROM cannot be assumed to fit. The next diagnostic must
measure combined resources and choose either a separate synthesis variant or
an explicitly verified shared-storage design before routing. Existing JPEG/AV
remains the recovery image.

The first isolated fixture-diagnostic OOC synthesis has now mapped the full
default private KEY/raster/tag path plus its fixture ROM: 15,428 LUTs,
13,503 FFs, 53 RAMB36 and 33 DSPs. These are synthesized estimates, not a routed
board design. At a 10 ns clock its internal setup slack is **-2.961 ns**;
hold is +0.186 ns. The critical path crosses GM01 geometry/header validation.
The raster adapter also uses 2,202 LUTs as memory and zero BRAM in this run.
This baseline led to the registered-validation and raster-memory variants below;
the baseline and failed timing report remain retained. At that stage the diagnostic
CSR controller was not yet connected to a board image or live receiver.
Its sealed full fixture replay checked 518,400 samples, the stored tag and
48,203 ingress bytes in 2,997,214 actual simulated clocks, with busy-command
rejection and abort/recovery. The ROM feeder differs from the earlier controlled
A/B, so these cycle counts are different experiments. Baseline diagnostic
manifest: `4b1edb00c306ae8e71a003a2d6b67bff6e250c255465f5fb5f0ee400d7147a4b`.

The installed v22 ESP USB command set cannot start/read this CSR window.
The later v26 candidate below adds a restricted command with core-identity
checks, idle-session guards and bounded polling. The v24 runtime
query does not provide arbitrary register access.

### Internal closure and board-wrapper milestone

The final private compute source now passes synthesized internal100MHz timing:
setup+0.456ns, hold+0.180ns, zero failing endpoints. Clock constraints are loaded
before synthesis; the same RTL's earlier post-synthesis-clock failure is retained
as a flow A/B. The source-bound qualifying report is selected explicitly by
manifest`93b61cc6fb05f157554aefa7fa5770a34934e38ab28469d476a5214a858947f6`.
Final fixture replay remains exact, at3000322 actual simulated clocks. See
[timing closure and its scope](FPGA-TIMING-CLOSURE-20261104.md).
The [compute source replay export](../fpga/ar03-compute-replay-20261104/README.md)
distributes the exact RTL and a Python/Icarus runner. It requires explicitly
supplied, hash-checked fixture data and does not assume either GameBub or
Sunshine repositories already exist on the receiving computer.
An independent full replay from the publication checkout passed all 518,400
samples and 20 controller checks without reusing simulator output;
[its executed record](measurements/ar03-compute-publication-replay-20261104/run.json)
binds the validated inputs, source hashes, commands and temporary-directory cleanup.

The decoder-exclusive AKD1 shell also passed its real-compute actual-top tests:
153 QSPI checks,16 reset cases/96 checks,two complete natural LCD frames and the
golden private job. Its native bars/overlay are an independent LCD background;
they are not the decoded private frame. Source/test manifest:
`a6e521238b6e6843940d0100bc85397aa21f91cd3da76856a04da1a3bff4f15d`.
The separate board candidate has now completed routing. Strict structural gates
pass after removing only obsolete LCD synchronization attributes, but setup
fails at -2.184 ns across 13,629 endpoints. Hold is +0.007 ns and pulse width
+2.000 ns, with zero DRC errors. The critical path runs from the QSPI queue BRAM
through command/cancel logic to decoder register enables. The next change targets
that control boundary; no bitstream or physical result is established yet. Its
unused SDRAM interface is explicitly inactive, not memory-qualified. The normal
SD image remains preserved.

The [registered-CANCEL successor](measurements/akd1-cancel-route-20261104/README.md)
then reduced routed setup failure to -0.025 ns/three endpoints, preserving all
golden behavior. Hold is +0.051 ns and pulse width +2.000 ns. It still fails setup,
and checkpoint inspection confirms a separate fixture-ROM enable-high-during-reset
startup blocker. A guarded-ROM successor is in functional verification; neither
failed image was generated as a bitstream or loaded on the handheld.

The [AKD1 local contract](AKD1-COMPUTE-DIAGNOSTIC-20261104.md) reserves distinct
AKD1 magic and MBK1 build identity with zero JPEG admission. This is a local CSR
interface; there is still no networked custom endpoint or port.

Local evidence anchors (not portable source exports):

| Record | SHA-256 |
| --- | --- |
| `fpga/experiments/ar03-key-tagged-20261104/manifest.json` | `d4f879da5b19eee0cc75acf983219fc0ac44254bd5b95d15c73e7906f3fdbe61` |
| `fpga/experiments/ar03-key-tagged-20261104/ab-manifest.json` | `cd9e308871449b1b24c92de50fd81832e027609d7b7bc383e4ae40f6a5881940` |
| `fpga/experiments/ar03-inverse-pipeline-20261104/manifest.json` | `d503495d5f5a5567a9bb8e4d5670b556393c3c74a1143b208114abff941d618d` |

## Physical v22 demo and next application change

The app-only v22 UF2 was written and verified during the authorized hardware
window. Its startup marker identified `v22-stream-service-20261104`; the core
reported build50/V4 (`0x4D424F50`). The retained build50 BIT hash identifies the
selected artifact, not a cryptographic readback of the running configuration.

One spontaneous reboot occurred; its cause was not captured. The subsequent
Legacy/default-four-slot interval and later restoration of 32 slots/overlap
make the totals unsuitable for a clean 15 fps acceptance result. At the final
20:00:18 UTC sample, the application reported 3,245 received, 3,240 decoded,
3,240 presented and 1,518 dropped; queue packet drops were zero and high-water
was 25/32. Core fault count was zero. These independently sampled counters do
not establish atomic correspondence between pipeline stages.

The demo is stopped, remote controls released, and v22 remains installed.
The isolated v24 application adds a read-only reset/uptime/image-identity
query and bounded diagnostic pages to replace truncated large debug lines.
It preserves the streaming contracts and current task/queue settings. Its
371 host-test executions, target check/build and production parser verification
of 12,301 UF2 blocks passed. Static SRAM is 121,780 bytes; all 553 source inputs
and 180 artifact hashes were rechecked. Compiled SDK configuration matches v22
byte-for-byte. Its candidate UF2 SHA-256 is
`c13c4f4183092fdf9c897fdf083e492e66ea6112c84c8412f5930ae250488c20`;
build manifest SHA-256 is
`8c5d2792da22742ba087fc404ae5580cae2625b9a926a5334190b776778125d8`.
The [seven-file diagnostic source export](../host/runtime-diagnostics-20261104/README.md)
reproduces the 14 SDK-free formatting/telemetry tests, separately from the full
application build. All exported bytes match the sealed candidate.

The image is **unflashed and physically unqualified**. The 161-byte maximum
tested page payload is not a measured logger-line or runtime-stack bound.
Selected ELF frame sizes changed, including new nested formatting calls; no
overflow cause or stack-safety proof follows from those figures. Follow
[the diagnostic regression checklist](V24-DIAGNOSTIC-REGRESSION-20261104.md)
at a future coordinated window. This candidate does not claim to fix the reboot.

The later v26 restricted-access SDK candidate now passes host adapter tests and
its target typecheck/build/application-only packaging. It guards actual FPGA
programming, receiver/AV and maintenance admissions and provides the local AKD1
commands. It preserves the existing connected/TestReady AV lifecycle; it does
not decouple standalone network/AV sessions. Final worker-specific resource
telemetry, ELF analysis and artifact sealing are complete. Independent verification
checked 575 frozen inputs, 3,844 artifact bindings and the sealed v25/v24 parents.
The selected UF2 is
`80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63`;
its build manifest is
`00b3d4a4bd6190646d72b817dc22d3802e6f70b87cfec35d9d5b2547cf8c4a66`.
It passes 39 model tests, 66 SDK host tests, 24 expected compiler rejections,
target build and production parsing of 12,419 UF2 blocks. Static SRAM is
122,124 bytes. The new 4,096-byte KeyDiag worker allocation remains provisional:
stack, logger framing, heap, SPI duration and teardown require physical evidence.
The [published build records](measurements/v26-key-diag-access-20261104/README.md)
identify this exact local candidate; they do not distribute its full SDK or images.
See [the v26/AKD1 regression sequence](V26-AKD1-REGRESSION-20261104.md).
It is uninstalled;
the installed v22 and its unexplained reboot remain the physical comparand.
Evidence is retained under
`evidence/15fps-controller-demo-20261104T193749Z/`.

## Next gates

The concrete next memory/presentation steps are expanded in
[the implementation plan](AR03-MEMORY-PRESENTATION-PLAN-20261104.md). A first
owned compact-YUV storage simulation now matches all 518,400 bytes and the exact
tag through the retained SDRAM writer, but takes 4,865,759 clocks (48.65759 ms at
nominal 100 MHz) under synthetic uniform competing reads. This misses the 30 fps
budget before RGB/HUD rendering. It is not a matched A/B against the ROM-only
diagnostic and does not qualify real LCD scheduling or hardware bandwidth. A
bounded elastic-storage experiment will measure the line-stall buffering hypothesis
against the same owned baseline and read schedule. Its production reset/rekey
behavior remains unqualified; the simulation reset is power-on only.

1. Retain the explicit interface hold/route limits and preserve all exact
   baselines and failed-gate evidence when integrating the next stages.
2. Preserve the completed private KEY/tag path and prepare an isolated FPGA-only
   fixture diagnostic using the actual board wrapper and constraints. Integrate
   reference banks, HUD patches and real memory/scanout service. Only the
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

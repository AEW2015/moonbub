# Coordinated 30 fps implementation progress

Date: 2026-11-04, America/Denver. Hardware updates remain deferred.

Goal: 720×480 at 30 unique physical presentations/s, then audio and controller
coexistence. Current complete custom-pipeline throughput and maximum physical
presentation rate remain **unknown**. No installed firmware, FPGA image, SD
configuration, serial session or running stream was changed for this work.

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

## FPGA: complete the decoder before measuring frame throughput

The isolated CP02 entropy component passed RAW/Rice coefficient validation,
real-section replay and a KEY seam into the verified inverse/reconstruction
component. Its frozen baseline corpus covers 259 cases, including 58 rejected
cases with no coefficient output, and 9,879,424 coefficient comparisons including
recovery. The joined seam checks 519,471 visible/recovery samples across six
planes. This is functional simulation evidence, not a full decoder benchmark.

Default capacity is 65,536 packet bytes and 8,192 blocks; the outer complete
AR03 cap remains 49,152 bytes. RAM inference and resource/timing fit require
synthesis evidence. A clocked-memory variant is being checked with the same
public interface, capacities and coefficient oracle; changing parameters is not
a substitute for demonstrating fit.

An independent outer AR03 envelope component is the next bounded integration
step: validate complete bounds/CRC before exposing section descriptors or replay
bytes, then connect actual GM01/map parsing and CP02. It must retain exact owner
identity through stalls and cancellation. Inner patch semantics, temporal bank
access, canonical tagging, HUD application, write drain and atomic presentation
remain separate required work.

## Next gates

1. Finish synchronous-memory entropy corpus and inspect actual RAM utilization
   and OOC timing. Preserve the existing exact baseline; report synthesis stalls
   or failures explicitly.
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

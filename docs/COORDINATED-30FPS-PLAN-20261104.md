# Coordinated MoonBub / Sunshine 30 fps plan

Date: 2026-11-04, America/Denver.
Latest execution order and measured bottlenecks:
[ESP32 / FPGA update checkpoint](30FPS-UPDATE-CHECKPOINT-20261104.md).
Older pending-work descriptions below are historical where that checkpoint
records a completed gate; the acceptance objective remains unchanged.
The first complete-fixture target is now explicitly
[CP23/HC22/HD22](CP23-FIRST-HARDWARE-FIXTURE-20261104.md). Neither complete-profile
decoder image nor local payload loader exists yet. Earlier private AR03/GM01/CP02
component work below remains separate from that target.

Windows plan/prompt pin: Sunshine `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`,
branch `gamebub/windows-jpeg-retry-20261103`.

This document supersedes the development order and acceptance sequence in
`ESP32-FPGA-30FPS-PLAN-20261104.md`. Its detailed engineering tasks remain useful
where consistent. The primary path is the coordinated custom-codec endpoint;
MSV1/JPEG remains the working control and independent diagnostic path. Long JPEG
runs do not substitute for custom transport/decoder qualification.

## Comparison with the previous MoonBub plan

| Topic | Previous MoonBub plan | Coordinated decision |
| --- | --- | --- |
| Primary order | First MJPEG capacity attempt; custom path in parallel | Freeze custom contract/ownership and measure complete receiver path before custom hardware streaming |
| Host baseline | Earlier paired handoff3d49c6f | Use Windows plan c9c0bf4; it identifies encoder baseline19cdd708 and newer native progress |
| Throughput | Separate stages and backlog, with JPEG first | Full custom decode/tag/patch/memory/presentation locally, then concurrent receiver service; both need complete implementation |
| Coexistence | Early combined regression and combined acceptance | Keep short existing-AV regressions separate; qualify custom video-only before adding audio/controllers |
| Rate ladder | 15/20/25/30, following low-rate regressions | Fixture, key/P/promotion/recovery, then60 s each at5/10/15/20/30 |
| Final soak | Five minutes then20 minutes | Five minutes then30 minutes at30 fps; repeat with audio/controllers |
| Numeric gate | 30 target; tolerance to agree | Keep30 target; Windows proposes >=29.9 unique presentations/s plus gap/quality/fault gates; confirm jointly before acceptance |
| Capacity example | 11.376 Mbps projected mean forward reference scene | Also budget cap-sized bodies:49,152×8×30 =11.79648 Mbps before transport/control/audio/radio overhead |

The plans agree on exact arithmetic, bounded buffers, no fabricated credits,
separate ingress/decode/presentation evidence, measured useful capacity, unchanged
resolution and source-bound artifacts. Pipeline initiation interval matters:
one complete frame per33.33 ms is required in steady state; overlapped end-to-end
latency can exceed one frame interval.

## Actual receiver capabilities and versions

Updated after the requested v22 demo: the app was installed, build50 was retained,
and the demo is now stopped. One unexpected reboot is unexplained. See
[the current progress record](COORDINATED-30FPS-PROGRESS-20261104.md) for physical
results and the newer private KEY/tag simulation. Coordinate the next hardware
window after its candidate gates finish.

| Item | Exact version/evidence | Status |
| --- | --- | --- |
| Recovery ESP app | AV parent UF2d43b3137fde1d95358181b23c80d71d3ef908b074510c3d5ae0271d4b46e37d3 | Retained recovery artifact; not currently installed |
| Last confirmed selected FPGA | Build50/V4 BITa1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9 | JPEG overlap, APC1 audio and controls; not AR03 |
| Installed ESP app | v22-stream-service-20261104 UF2329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542 | Written and startup marker observed; one unexplained reboot, qualification incomplete |
| New ESP source binding | a6ad0a5f72201a1192733c3157ba54f0ce301dc27631852c1816806141f9dc04 | 550 inputs rechecked; no source mismatch |
| Custom codec kit | MoonBub27a4dde6a7e2ea4fab09d892551ef542f05c8965 | Wire/golden/arithmetic references, not installed decoder |
| Native receiver helpers | host/experiments/ar03-gateway-contract-20261104 | C parser/serializer and lab frame ledger tested; no firmware endpoint/packet-credit FIFO |
| FPGA reconstruction | fpga/experiments/v22-av-service-20261104; manifest SHA f3f2a0d292c9ea8bfe810e5ae30a049d5c4af24fedd2861747887820483ae90f | Exact inverse/predict/clip/crop component, RTL and bounded netlist tests; not a complete decoder/bitstream |

The new ESP app and FPGA component have hash-bound local sources/artifacts but
no published source commit in the handoff branches. Publish a reproducible source
snapshot/manifest before asking Windows to depend on a replacement version.
Existing documentation-only publication is not a firmware source release.

Current offline implementation order:

1. Finish isolated v24 ESP diagnostics: reset/uptime/image identity and bounded
   frame/queue pages, preserving existing wire formats and streaming behavior.
2. Simulate an FPGA-only sealed KEY/hash diagnostic, then measure combined
   resource use. Build50 already occupies 120.5/135 BRAM tiles, so adding a second
   complete decoder is not an assumed fit. Choose an explicit synthesis variant
   or verified storage sharing before a board build.
3. Close actual board constraints/routing and produce a source-bound diagnostic
   image before requesting programming. Add a separate restricted ESP diagnostic
   control only after its CSR contract is frozen: verify diagnostic magic/schema
   and exact core build, require video disconnected and AV inactive, then start
   and poll boundedly with short Device-lock holds. Existing USB commands cannot
   access the new CSR window, and v24's `?` query does not add that access.
   This first test measures computation; it does not implement networked custom playback.
4. Complete HUD/reference-bank/memory/scanout integration and the agreed live
   backend/transport gates below, then start the custom physical rate ladder.

Firmware experiment `v24-runtime-diagnostics-20261104` is distinct from the
remote host-codec research branch `study/gamebub-codec-v24-comparison-20261104`.
That host study does not change the pinned receiver wire contract or imply an
implemented HEVC/AV1 FPGA decoder.

Windows reports native GM01/CP02, HP01/HR01 and AR03 candidate/HUD/AF03 conformance,
with20 byte-matching cases and42 native tests. These are Windows-reported results,
not a locally rerun sustained benchmark. SR01 encoding and live custom transport
are absent in the cited Windows plan.

## G0 — Joint contract and recovery freeze

Start from the27a4dde kit and publish one versioned contract bundle accepted by
both agents, with byte-identical copies and hashes. Identify each field/behavior
as implemented, laboratory-only or proposed. Include:

- Supported custom profile: AR03/GM01/CP02 and HP01/HR01,720×480 canvas, centered
  720×405 active image with pinned integer placement,49,152-byte complete cap,
  mandatory HUD regions and allowed quantization maps. Advertise only implemented
  inner formats; SR01 encoding is not assumed.
- GF03/FG19/PC18/QC18/AF03 offsets/endian order, exact CRC coverage, datagram sizes,
  timestamp units/meaning, identities, counter rollover and source/port binding.
- Capability negotiation, custom endpoint ports, generation/epoch reset/rekey,
  reconnect, cancellation, disconnect, lost replies and ambiguous hardware outcomes.
  Current UDP5533 MSV1 and UDP5534 AV v1 do not imply a custom endpoint exists.
- Packet permit, request completion, frame-slot release and decoded-reference
  publication as separate transitions. FINISHED never frees frame storage;
  RELEASE follows real ingress/read/decode drain; validated AF03 alone confirms
  the reference. There is no implicit ACK-of-FINISHED packet.
- Pinned1,725-message control histories plus expected ownership state and negative
  vectors for loss, duplication, reordering, delay, wrong kind/slot/epoch/tag,
  CRC/truncation, exhausted capacity, reset and sequence boundaries.

The current C helper tests parse/replay those history messages but do not prove
each complete protocol history's expected state: physical-drain events are absent
from those histories. Export the missing explicit model events or add a separate
full-state transcript format with agreed expected states. Never invent hardware
drain evidence while replaying a message log.

Exit: both sides pass the same exact bytes/state/fault cases, retain unknown
ownership boundedly and establish recovery without stale publication, double
release, reader/DMA reuse or fabricated credit. No format divergence is adopted
unilaterally. Fix/report the kit's strict floating-point report portability issue
separately from byte/ownership conformance.

## G1 — Complete FPGA-only custom pipeline and measure it

Implement parser/entropy/dequantization, prediction access, compact banks,
canonical tagging, required patches, write-drain/publication and actual scanout
around the verified reconstruction component. Define the mapped memory and FIFO
interfaces before integrating the ESP gateway. Include all work in measurement.

Use real easy and complex locally available continuous custom sequences with
valid reference evolution. Isolated P-frame fixtures require their specified
pre-banks and cannot be concatenated arbitrarily. Test key/P/promotion and recovery.

For each stage collect frame-correlated initiation/completion/presentation times,
occupancy/backpressure, SDRAM service/refresh, tag/patch work, faults and backlog.
Retain the physical480×800 scan order and line-deadline checks. Report simulation,
OOC timing, routed timing and physical playback separately.

Current full-path FPGA-only custom throughput: **UNKNOWN**. It cannot be measured
from the inverse or cropped-tile component alone. No complete custom decoder
bitstream exists in the current artifacts. Existing JPEG-only measurements are
control evidence and must retain their codec label.

Exit: exact full-path tests, resource/CDC/reset and routed implementation gates
pass; measured service supports the selected operating point without growing
backlog. Do not infer30 fps from one-frame latency or standalone timing slack.

## G2 — Implement gateway and measure concurrent receiver service

Integrate the agreed native ownership/packet-permit state machines into ESP32
firmware with actual FIFO availability, bounded storage and coherent receipts.
Use v22's short locks and service/input diagnostics as the scheduling foundation.
Keep the known JPEG/AV control and recovery artifacts preserved.

With Wi-Fi active, continuously retain bounded records for socket/queue events,
pool exhaustion, packet drops, queue peak, QSPI wait/transfer and minimum credit,
decoder admission/owning frame, AF03 and actual presentation. Record first failure
reason/offset/bytes/timestamps for timeout, supersession, Busy and sequence gaps.
Keep invalid/contended snapshots separate from confirmed FPGA or SPI faults.

Current full-path concurrent custom throughput: **UNKNOWN**; there is no live
custom receiver endpoint. The v22 application-only build and357 host executions
do not establish that endpoint or physical throughput.

Run useful concurrent capacity tests against explicit agreed modes. Budget the
49,152-byte body limit at11.79648 Mbps for30 fps before headers, reverse credits,
frame controls, reference ACKs, audio and Wi-Fi airtime/retries. The earlier
11.376 Mbps figure is a particular scene's mean forward projection, a different
quantity; neither is measured capacity. Select a jointly agreed size/quality/rate
with measured headroom while preserving720×480 resolution.

Exit: bounded native endpoint passes peer-emulator fault soak, memory/stack/DMA
review, concurrent stage tests and agreed recovery. The performance bottleneck
remains unknown until these complete-path measurements exist.

## G3 — Coordinate hardware windows with Windows

Before any flash, core reload or stream, exchange an explicit readiness record:

1. Exact host commit and executable hash; firmware/FPGA source/artifact hashes.
2. Implemented endpoint/profile/recovery version, receiver address and accepted
   sender's actual IP/port, source/viewport geometry and negotiated capacities.
3. Workload identity, map/HUD/quality, cap/pacing, frame-ID range and duration.
4. Starting video/audio/input/core/queue counters; independent frame baseline or
   explicit reset/rekey proof; continuous capture paths on both machines.
5. Which agent starts the sender, receiver-ready acknowledgement, run completion,
   drain/STOP collection and fault/abort responsibilities. One live serial owner.

Do not start or reconfigure a working session without that window. The user has
deferred hardware updates; this plan does not silently revoke that constraint.
Local v22 regression tests may be coordinated separately, clearly labeled JPEG/AV.

## G4 — Video-only custom qualification, then coexistence

1. One deterministic frame: reconcile acceptance, exact decode/reference, display
   geometry and owner release.
2. Short key/P/promotion sequence and one controlled recovery in an isolated test
   session.
3. Video-only moving content:60 seconds each at5/10/15/20/30 fps, fixed source and
   profile. Change one variable; stop escalation at a reproducible bottleneck and
   preserve its first failing frame.
4. Five minutes at30 fps, then30 minutes across detailed moving scenes.
5. Repeat qualification with audio and controllers; retain audio sequence/drain /
   underrun results and input release-on-disconnect/latency separately.

Goal remains30 unique displayed frames/s. Windows proposes >=29.9 over the actual
steady-state window, with all outcomes reconciled, no progressive backlog/freeze/
corruption/overflow/core or scanout fault, frame-interval p50/p95/p99/max and
investigation of every gap over100 ms. Record quality/map/HUD coverage and latency
method. These numeric thresholds are proposed joint acceptance criteria, not
achieved performance or a silently reduced target.

Use actual run duration and counters, not scheduled IDs. Save final snapshots
before another START clears session counters. Correlate frame identities and
local intervals; use synchronization or an optical method for source-to-display
latency. Host encoding speed, localhost throughput, RTL simulation and physical
presentation must have separate result labels.

## Immediate work and reporting

1. Publish actual source-bound receiver capability inventory and draft contract /
   full ownership transcripts for Windows review. Keep proposed fields unadvertised.
2. In parallel: complete FPGA parser/bank/tag/patch integration; port the bounded
   gateway to firmware against an executable peer; Windows profiles sustained
   native encoding and implements its ownership emulator.
3. Establish FPGA-only, then concurrent full-path service. Optimize the measured
   limiting stage with exact arithmetic and ownership unchanged.
4. Schedule the first fixture only after both sides implement the same contract.
   Keep JPEG as the recovery/control path throughout.

Each status report must include exact versions/capability matrix; contract and
transcript hashes; stage timings and backlog; maximum verified sustained unique
presentation rate; content/geometry/quality/map/bitrate/duration; drops/queue/faults;
latency method; limiting stage; unknowns; and next safe coordinated test.

Current custom maximum physical rate and limiting performance stage are
**unavailable**, because the complete path and live endpoint are missing. Component
tests are exact functional evidence; they cannot fill those measurement fields.

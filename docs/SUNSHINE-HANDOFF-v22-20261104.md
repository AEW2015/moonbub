# MoonBub v22 handoff for Sunshine development

Date: 2026-11-04, America/Denver.

Later status: the requested v22 hardware demo has now ended. v22 was installed
with build50 retained; one unexplained reboot remains open. Streaming is stopped.
See [current progress](COORDINATED-30FPS-PROGRESS-20261104.md) for results and
the resumed offline plan. The following sections preserve the original handoff.

ESP32 and FPGA development has progressed offline. **Hardware testing is deferred.**
The new ESP32 application is built but unflashed. The FPGA work is a verified
reconstruction component; it is not an integrated replacement bitstream.
Do not change the host's runtime protocol based on these component results.

## Shared source baseline

- MoonBub codec handoff: `handoff/gamebub-app-codec-v20-20261103`, commit
  `27a4dde6a7e2ea4fab09d892551ef542f05c8965`.
- Paired Sunshine handoff: same branch name, commit
  `3d49c6fe87753eb5b35d693991fdff0365e4bbbf`.
- Shared wire/development JSON files match byte-for-byte. Four paired Sunshine
  artifact hashes also match the MoonBub provenance manifest.
- The new v22 implementation artifacts below are local and are **not claimed to
  be published on those branches**.

## Current working wire contract remains unchanged

| Function | Contract |
| --- | --- |
| Video | Individual baseline JPEG frames in MSV1 UDP packets; receiver port5533 |
| Audio and session control | AV v1 handshake/control and independent stereo IMA ADPCM blocks; receiver port5534 |
| Controller | Independently sequenced MSI1 button packets; same mapping and payload layout |
| FPGA audio | Existing APC1/schema1; PCM rate176171875/3648 =48,292.728893 Hz |

Retain product-based IMA rounding and the existing golden PCM oracle. No new
sample rate, codec, header, feedback field, port or controller mapping is introduced.
MSI1's build field remains the FPGA identity, not the ESP32 firmware version.
MSV1 status0 confirms ingress; decode and presentation still require receiver
counters. Local MSI1 send success does not establish host reception.

Last restored test configuration was receiver `192.168.0.157`, accepting sender
`192.168.0.47`, with build50, overlap,32 video queue slots, margin13 and timing0.
**This is historical configuration, not a fresh readiness announcement.** A restart
can reset volatile queue/overlap/display settings. Confirm readiness and baseline
counters with the receiver before transmitting a comparison run.

## ESP32 v22 changes

Local candidate: `firmware/experiments/v22-stream-service-20261104`.

- Slint CPU rendering runs outside the shared Device lock. Overlay SPI publication
  locks one line at a time and checks the software FPGA-program epoch. A changed
  epoch suppresses stale writes/bounds and requests a full redraw.
- USB diagnostic CSR reads release Device before formatting and logging.
- Audio feeder passes stop on the first Device lock miss or unchanged phase.
  Attempts and actual progress are counted separately.
- RX is limited to four attempts /1 ms decision budget; feeder work to20 attempts
  /2 ms. Fresh cancellation, lease and input checks occur between work units.
  These checks do not preempt a synchronous SPI/snapshot/cleanup operation.
- MSI1 retains its20 ms scheduling target and independent sequence. New local
  diagnostics record send errors, short sends, encoding failures, gaps between
  successful submissions, lateness and maximum submission gap.
- Eight bounded diagnostic pages retain audio FIRST/LAST failures and new
  service/input metrics. They are sampled pages, not an atomic global snapshot.
- A pre-QSPI Device-lock timeout is now labeled explicitly instead of being
  called FPGA Busy. No ambiguous SPI write is retried.

The four-block compressed audio queue,32 ms receiver-relative age limit, single
2,020-byte PCM DMA owner, SDK/BLE configuration and task priorities are unchanged
from the queue diagnostic parent. The installed legacy AV app remains preserved.

Validation:357 host test executions, target build and all12,309 production UF2
parser blocks passed. Static shared SRAM121,772 bytes; BIN3,150,944 bytes;
application-partition headroom2,091,936 bytes. Selected ELF frames were reviewed,
but full stack bounds and runtime watermarks are unmeasured.

UF2 SHA-256:
`329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542`.

The candidate manifest remains INCOMPLETE pending physical scheduling, sound,
input/video behavior, heap/stack and sustained-rate tests. No measured improvement
in FPS, packet loss, audio underruns or controller latency is claimed yet.

## FPGA custom-codec progress

Local component: `fpga/experiments/v22-av-service-20261104`.

The exact inverse is now wrapped with prediction addition, signed widened
arithmetic, clipping before uint8 narrowing, cropped output and stable
owner/block/epoch/bank/plane/tile identity. A cropped `out_last` does not release
the block owner: hidden padding must drain and `start_ready` must return.

- RTL:618 blocks /36,312 cropped samples,24,455 stalled cycles,7 negative cases,
  428 reset/abort cases and60 cropped-drain checks passed.
- Actual synthesized netlist:50 selected blocks /2,694 samples, plus recovery,
  stall, negative and reset/abort cases passed in native XSim.
- OOC synthesis:3,205 LUTs /6,129 FF /16 DSP /0 BRAM;100 MHz internal estimate
  +2.178 ns setup /+0.186 ns hold. This is unplaced and external ports lack board
  timing; it is not integrated or routed qualification.

Real tile tests use AR03 coefficients, scale-map dequantization and declared
predictor banks, checked against IT20 fixtures. IT20 remains an offline fixture,
not a runtime codec. Existing audio/QSPI/control regressions pass on unchanged
baseline modules; this does not prove a combined AR03/audio memory arbiter.

Remaining FPGA work includes entropy/parser/dequantization integration, compact
reference/display banks, canonical tags, publication rules, actual memory/FIFO
arbitration and physical scanout deadlines. The ESP32 does not advertise or accept
a production AR03 capability yet.

## Sunshine work that can proceed now

1. Continue the native mandatory-HUD encoder against v20's isolated fixtures.
   Prepare all requested RGB565 patches, reserve their full framed bytes, pay
   losing candidate work, and reject the whole frame if no declared profile fits
   the49,152-byte complete-frame cap. Keep predictor-bank preconditions explicit.
2. Keep FG19 frame grants, PC18 packet capacity, FINISHED control completion,
   RELEASE after actual drain and AF03 decoded-reference confirmation separate.
   None establishes physical presentation. There is no ACK-of-FINISHED packet;
   do not introduce one implicitly.
3. Agree capability negotiation, generations/reset/rekey, reconnect and ambiguous
   ownership recovery before enabling an AR03 runtime sender. Current laboratory
   epoch1 and bounded safe-stop models are not production recovery.
4. Preserve exact packet-deadline/pacing logs and capture/encode/queue timings.
   Record actual local UDP endpoint, frame ID and capture timestamp, complete vs
   partial/zero-byte sends, first unsent offset and feedback identities.
5. For audio, retain first/last sequences, encoded/sent counts, queue/stale drops
   and send-gap distributions. Keep local send counts separate from accepted,
   rejected/unconfirmed, played and underrun counters.

The complex mandatory-HUD case projects11.376 Mbps forward traffic at30 fps,
before reverse controls, audio and radio overhead. The existing2 Mbps cap cannot
support that case. This is a bandwidth projection, not measured receiver capacity;
do not increase load without a coordinated capacity test.

## Next coordinated hardware test, when resumed

Keep build50, source clip, geometry, quality, cap, gain, mapping and observer query
cadence fixed while comparing the new app. Restore/read back overlap,32 slots,
margin13 and timing0 after boot. Begin input-only/tone, then short5 fps and12 fps
combined runs before long or higher-rate runs. Snapshot final audio after STOP
and before a new START resets session counters. Preserve video IDs, reasons,
queue drops/high-water, input gaps, audio dispositions/underruns and runtime
watermarks. Retain the known-good app for rollback.

Supporting local documents:

- `docs/v22-av-stream-service-20261104.md`
- `docs/ar03-v20-implementation-plan-20261104.md`
- `docs/ar03-session-ownership-draft-20261104.md`
- `evidence/v22-stream-service-20261104/firmware-review.md`
- `evidence/v22-stream-service-20261104/fpga-review.md`

Conformance caveat: all34 component unit tests and C/packet/reconstruction replays
passed freshly. The pinned aggregate verifier still fails exact equality on15
tiny floating-point aggregate-report fields in the available environment. A
separate narrowly allowlisted numeric comparison passes, with other fields exact;
it does not turn the original aggregate/audit failures into passes. Details and
dependency-version deviation are in `evidence/ar03-v20-20261104/p0/p0-status.json`.

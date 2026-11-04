# Receiver AV handoff —2026-11-03

The verified application and FPGA build50/V4 are now installed. Core/APC1
identity, audio FIFO online state, margin13/timing0 and overlap/32-slot queue
are confirmed. Physical A/D-pad input and neutral releases reached the Windows
observer in954independently sequenced MSI1 packets with no sequence gaps.
Clean STOP and Wi-Fi power-save restoration are confirmed by receiver logs.
See [input results](av-hardware-input-first-20261103.md). The first audio-only
tone admitted944blocks and consumed475721PCMframes; microphone capture confirms
tone output, with13underruns. See [audio results](av-audio-first-20261103.md).
Clean sustained playback, stereo routing and Windows gamepad injection remain pending.

## Windows interface

The frozen byte layout and all seven golden packet classes are in
[`av-wire-v1.md`](av-wire-v1.md) and
[`host/av-v1/fixtures/av-v1`](../host/av-v1/fixtures/av-v1).
Reference implementation lives on branch`feature/av-v1-20261103`.

- AV destination UDP5534, additional to unchanged MSV1 video UDP5533.
- Receiver source-IP filter remains192.168.0.47. Last observed receiver address
  was192.168.0.157; it must be checked after updating/reconnecting.
- Bind a separate AV socket and retain its source port for handshake, audio,
  keepalive and STOP. Replies return to that socket. Do not reuse a video
  socket that another thread already owns.
- Audio is512-byte independent stereo IMA ADPCM WAV blocks,505 stereo sample
  frames at nominal48293Hz; source is decoded to signed16 little-endian L/R.
  No Opus/PCM/mono or alternate sample-rate transport is supported by v1.
- HELLO/OFFER/START pins a fresh random64-bit device cookie, host nonce and exact
  endpoint. Keepalive100ms; control lease500ms. Whole-datagram CRC includes the
 48-byte header with CRC field zeroed. Validate against bytes, not just names.
- MSI1 is independent of video frame IDs, every20ms scheduled, with its own
 32-bit serial sequence and complete12-bit button state. Reject stale/duplicate
  input without refreshing its500ms lease. MSF1 input must stay diagnostic.
- Only digital A/B/X/Y, D-pad, LB/RB, Start/Back are present. Analog sticks,
  stick clicks and analog triggers are not encoded. Xbox output needs the
  separately qualified Windows virtual-controller driver; observation-only
  mode works without it.

MSI audio-accepted count means verified FPGA admission. Field2 means rejected
**or unconfirmed** block outcomes, not proof of physical rejection after an
ambiguous I/O fault. AUDIO_ENABLED is the negotiated mode, not playing/health.
Queued/played/underrun fields need FPGA_SNAPSHOT_VALID. Digital consumption is
not acoustic output. No measured A/V synchronization or drift servo is claimed.

## Receiver implementation and gates

Receiver artifact paths below refer to the receiver computer's workspace;
this published branch contains the host reference and wire/receiver handoff.

New application: `firmware/experiments/v21-audio-controls`.
UF2 SHA256:
`d43b3137fde1d95358181b23c80d71d3ef908b074510c3d5ae0271d4b46e37d3`.
232test executions and all12247production-parser UF2blocks pass;539source
bindings and release hashes independently verified. Static SRAM121036bytes,
noPSRAM, effective SDK byte-identical to the previous application. Runtime heap,
stack, latency, sound and physical input observations remain pending.

New app starts UDP5534 only inside a selected network Test MJPEG session. A
validated AV START disables Wi-Fi modem power saving temporarily and restores
the captured previous setting on exit; listener/video-only/local-loop/boot do
not change it. Existing DAC volume, routing, flash partitions and SD files are
preserved. An8KiB worker and one2020-byte DMA block feed the FPGA without an ESP
PCM queue. Input reads an existing atomic cache, never an extra QSPI button poll.

Audio FPGA: candidate`fpga/candidates/v21-audio`, identity0x4d424f50, APC1 FIFO
8×512stereo frames/16KiB. Two complete blocks prefill; whole-block CRC/length
commit prevents partial publication; starvation emits silence. Sample rate is
176171875/3648Hz, unchanged LCD-derived MCLK, DSP16offset0/fallingBCLK capture.
Margin/timing controls remain compatible. Build49 supports new input-only
sessions but rejects audio-enabled offers.

Digital gates pass: serialized sample/edge/CRC/slot tests, actualTOP/QSPI80checks,
32independent stop/reset/publication race cases, and16actualTOP stopped-clock/
PLL-loss cases. The first routed V3 met timing but introduced two reset-domain
CDC criticals; its image was archived as **not hardware-ready**. V4 registers a
common reset from separately synchronized PLL locks in the reference domain.
V4 final checks pass: setup+0.029ns,hold+0.014ns,DRC0,criticalCDC0,20749/20749
nets routed. All170manifest artifact hashes and51inventory inputs were
independently verified, alongside539application bindings. DAC8ns requirements
match TI SLAS666B section4.9; PCBskew/pad rise-fall/acoustic behavior remain
unmeasured. SelectedBIT SHA256:
`a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.
The failed V3 image with the same buildID must not be substituted.

## First live run

Wait for a fresh receiver-ready record with installed application/FPGA hashes,
actual address, margin13/timing0, overlap/32queue slots and starting counters.
Queue selection is RAM-only: after an app restart the preserved default is4,
so the receiver operator explicitly selects32 before comparison tests.

1. Observe input packets20seconds, no injection/audio; validate buttons/releases.
2. Once the Windows driver is available, test the Xbox device in controller
   properties, including timeout neutralization.
3. Send a10second quiet left440Hz/right660Hz tone. Record source blocks,
   accepted/unconfirmed counts, played/underruns and audible observations.
4. Then30seconds captured game sound with720×480video5fps,quality25,2Mbpscap,
   host shift0. Hold panel timing/margin fixed. Audio adds roughly392kbit/s
   compressed payload plus headers/input traffic to the video cap.
5. Check graceful STOP, silence, released controls and empty FIFO before a
   longer A/V run. Keep12fps and30fps acceptance separate.

Windows supplied a separate successful5second speaker-capture/478-block result,
230tests/fiveskips and absent virtual-controller driver. Those are host-reported
results, not independently rerun receiver tests. Golden-vector compatibility is
being validated by that agent; it has not yet been confirmed here.

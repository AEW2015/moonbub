# MoonBub experimental audio and ordered input v1

Contract frozen for the new build50 prototype on 2026-11-03. Implementation,
simulation and physical acceptance remain separate gates. The installed build49
does not implement this contract. MSV1/MSF1 video UDP5533 remains unchanged.
This is a standalone test companion, not Sunshine's negotiated Moonlight audio.
Trusted LAN only; CRC and random session cookies are not authentication.

## Shared header and endpoint

Host sends to the configured receiver IPv4 UDP **5534**, from a single bound
socket. Receiver filters the configured video host IP and binds an active AV
session to the exact source IP and port. Replies return to that socket. No
discovery or broadcast. All integer fields are unsigned and **network byte order**.

| Offset | Bytes | Field |
|---:|---:|---|
|0|4|Magic: MSC1 control, MSA1 audio, MSR1 offer, MSI1 input/status|
|4|1|Version, exactly1|
|5|1|Type, defined below per magic|
|6|2|Header bytes, exactly48|
|8|8|Session cookie; HELLO carries host nonce instead|
|16|4|Independent sequence number for this packet class|
|20|4|Nominal sample rate, exactly48293|
|24|2|Sample frames,505 for audio and0 otherwise|
|26|2|Payload bytes, exact datagram length minus48|
|28|4|Flags: HELLO/OFFER/START bit0 enables audio; otherwise0|
|32|8|Sender monotonic timestamp in microseconds; diagnostic, not ordering|
|40|4|IEEE CRC32 of complete header with bytes40..43 zeroed, followed by payload|
|44|4|Reserved, exactly0|

Maximum datagram560bytes. Reject wrong version, fields, length, CRC, rate,
unknown flags, magic or type before changing liveness, session or FPGA state.
No fragmentation/reassembly, variable format negotiation or codec autodetection.

## Session and liveness

1. Host generates a fresh nonzero random64-bit nonce and sends **MSC1 type1
   HELLO**, sequence0, no payload, flags chosen audio-enabled or input-only.
2. Receiver generates a fresh nonzero random64-bit cookie and replies **MSR1
   type1 OFFER**, sequence0, flags echoed, payload8bytes containing the host
   nonce. Pending offer expires after2000ms. A repeated matching HELLO may
   retransmit the same offer; it must not flush or change an active session.
3. Host validates source/nonce/flags and sends **MSC1 type2 START**, cookie,
   sequence1, payload8bytes host nonce. Receiver activates only the matching
   unexpired offer/source. Immediate MSI1 confirms ACTIVE. Repeated START for
   that active cookie/nonce retransmits MSI1 without resetting audio or sequences.
4. **MSC1 type3 KEEPALIVE** has no payload/flags, sequence2 and upward. Send
   every100ms. Subsequent control sequences wrap modulo2^32; the parser cannot
   reject0/1 statelessly, but the active-session ordering check rejects them
   immediately after START1. **MSC1 type4 STOP** uses the next control sequence and no payload.
   Newer means `0 < ((candidate-previous)&0xffffffff) < 0x80000000`.
   Duplicates/stale packets never refresh the lease. START duplicate is only a
   receipt retry, not a lease refresh. Only valid newer KEEPALIVE refreshes the
   active500ms lease. On STOP/expiry/disconnect, silence/flush audio and cease
   MSI1; the host releases all controls. A new session needs a fresh handshake.
5. Ignore HELLO with a different nonce/source while active. A host that crashes
   can reconnect after the old500ms lease expires; no live-session takeover.

Cookie/nonce correlation rejects delayed prior-session data. Session counters
must not be reused after firmware restart. Random generation is ESP-IDF entropy,
not a timestamp or fixed seed. Control/audio/input use **separate sequence spaces**.

## Audio

**MSA1 type1** contains one independent **512-byte Microsoft IMA ADPCM WAV
stereo block**, decoding to **505 stereo sample frames**,8-bit block indices,
signed16-bit little-endian initial predictors, zero reserved byte per channel,
standard WAV four-byte channel interleave, low nibble first. Invalid index or
reserved fields reject the whole block. Codec identifier is implicit in v1;
PCM, Opus, other sample rates, mono and multichannel are unsupported.

Audio sequence starts at0 and increments per captured/encoded block, including
blocks later discarded by a bounded sender queue. Receiver accepts only newer
audio sequences for the active audio-enabled cookie/source, records gaps, and
discards stale/duplicate blocks without replay. Blocks are independently
decodable, so gaps do not poison predictor state. Do not retransmit stale audio.

ESP32 decodes one block to2020bytes PCM: little-endian signed16 **left then
right**, one32-bit FPGA word per stereo sample frame, LEFT[15:0]/RIGHT[31:16].
One DMA scratch block, no unbounded ESP queue; reject/backpressure is reported.
FPGA uses **8 slots of512 stereo frames (16KiB)**, whole-block CRC/count commit,
and starts/rebuffers after at least2 committed blocks. No partial block is
audible. Underflow outputs digital silence, not the last sample.200ms without a
new accepted audio block stops/flushes audio independently of the input lease;
later audio may prefill/restart within the same live session without replay.

DAC framing is existing Rev4 DSP signed16 left/right, offset0, falling-BCLK
capture; MCLK derives from the unchanged LCD clock, BCLK=MCLK/8,
608MCLK/sample frame. Exact nominal rate **176171875/3648 Hz =
48292.72889254386 Hz**. Host resamples to rounded48293Hz. This is not an exact
48kHz sink. Clock drift and Wi-Fi jitter must be measured; initial prototype
uses bounded queues, drops stale backlog, and reports underruns/occupancy.
It does not yet promise long-run adaptive resampling or audio/video sync.
Keep the saved DAC volume/routing and panel timing unchanged.

## Independently sequenced input and playback status

Receiver emits **MSI1 type1** every20ms while active, including when buttons do
not change or video is idle. Sequence starts0 per new cookie and increments
for every emission attempt; it is independent of video IDs and audio/control
sequences. Payload32bytes contains eight network-order u32 fields:

| Index | Meaning |
|---:|---|
|0|Complete12-bit GameBub button mask|
|1|Accepted/committed audio blocks in this AV session|
|2|Rejected or unconfirmed audio blocks in this AV session|
|3|FPGA queued PCM frames, latest valid snapshot|
|4|FPGA played PCM frames, lifetime modulo2^32|
|5|FPGA underruns, lifetime modulo2^32|
|6|State bits: ACTIVE=1, AUDIO_ENABLED=2, FPGA_SNAPSHOT_VALID=4|
|7|FPGA build ID, e.g.0x4d424f50, or0 if unavailable|

Field2 includes a received block whose admission could not be confirmed after
an I/O fault, timeout or cancellation, counted once. It does not count a control
failure without an audio block and does not prove that an ambiguous COMMIT was
physically rejected. This clarification changes no bytes or packet layout.
Audio counters describe block admission, not acoustic output; played is actual
digital consumption, not guaranteed sound at the speakers. Snapshot reads may
be at100ms cadence; MSI1 input uses a cached atomic button mask and never waits
on a QSPI transaction. When snapshot-valid is clear, occupancy/played/underruns
must be ignored. No input analog axes or triggers are present in v1.

Bits: A11,B10,X9,Y8,Up7,Down6,Left5,Right4,L3,R2,Start1,Select0.
Here L/R mean shoulder buttons, **not** stick-click L3/R3 or analog triggers.
Host maps to Xbox A/B/X/Y, D-pad, LB/RB, Start/Back. Host accepts only matching
cookie/source, valid CRC/fields and a strictly newer MSI1 sequence. It must
neutralize on500ms without a newer valid MSI1, STOP, exception or shutdown.
Duplicates and stale MSI1 cannot refresh input liveness. A host may recover
after a local input timeout only on a newer valid sequence in the same still
live session. MSF1 snapshots remain diagnostic and must not drive this backend.

## First acceptance sequence

Test parser negatives, ADPCM against FFmpeg, session replay/expiry, input
reordering/timeout/releases, FPGA partial commit/overflow/stop/underflow and
existing video/calibration regressions. Build firmware and route FPGA with
source hashes and positive setup/hold before loading. Start with input-only,
then quiet channel-ID audio, then captured game audio with low-rate video.
Report simulated, digital hardware, audible and operator game-control evidence
separately. Preserve sealed build49/firmware fallback and app-only updates.

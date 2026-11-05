# APC1 PCM audio, schema1

Build identity `0x4D424F50`; additive core offsets below use the existing QSPI
core window `0xe0000000`. MRG1/TIM1/video CSRs and all video processing remain
compatible with build49. There is no compressed-audio decoder in this FPGA.
Firmware validates MSI1/MSA1 network identity and decodes bounded IMA packets to
PCM before writing this interface. See root `docs/av-wire-v1.md` for network rules.

| Offset | Register |
|---|---|
|300|RO magic `0x41504331` (APC1)|
|304|RO schema `0x00010001`|
|308|WO command, full32 enum:0 STOP+flush,1 ARM,2 BEGIN,3 COMMIT,4 ABORT unpublished staging|
|30c|RO status:0 online,1 staging,2 enable requested,3 playing mirrored,4 rebuffer mirrored,5 flush pending (=!online),6 sequence valid,7zero,15:8 last result,31:16zero|
|310|RW frame count1..512, a frame is one stereo pair|
|314|RW uint32 packet sequence|
|318|RW expected CRC32|
|31c|RW session; accepted only online, disabled, no queued or staging slot; clears sequence-valid baseline|
|320|RO free whole slots3:0 excluding staging reservation; queued slots11:8 including active until its last sample is latched; staged stereo frames25:16; other bits0|
|324|RO committed packet count, modulo32|
|328|RO last accepted sequence|
|32c|RO last accepted session|
|330|RO rejected operation count, modulo32|
|334|RO consumed stereo-frame count, safe Gray mirror, modulo32|
|338|RO underrun event count, safe Gray mirror, modulo32|
|33c|RO4096 stereo-frame physical capacity|
|340|RO rate numerator176171875|
|344|RO rate denominator3648|
|348|RO conservative queued stereo-frame count, excludes staging and already latched samples; `0xffffffff` invalid while offline/flush|
|380|WO fixed-address32-bit PCM FIFO word: signed LEFT15:0, signed RIGHT31:16|

PCM CRC is standard zlib CRC32 over chronological four little-endian bytes per
word. For example word `RIGHT<<16|LEFT` is transferred from a little-endian PCM
buffer using QSPI Bits32, byte_swap=true, **increment_address=false** (quad
command0x4c). This packing is tested through the actual top/endpoint/CDC. The
existing write/read barrier drains prior writes before returning a CSR read.

Metadata writes require online and no staging. BEGIN snapshots frame count,
sequence and session, reserves one free slot, and initializes packet CRC.
Sequence must advance in serial32 order: delta=(candidate-last) modulo2^32
must be nonzero and below2^31; wrap is accepted and the half-range is rejected. First sequence may be any uint32 value. Session
changes require a stopped/empty pipe. Metadata cannot be changed while staging,
so expected CRC remains stable through commit. Write exactly count words to380.
Extra words poison staging. COMMIT requires exact count and CRC before advancing
one published-slot token atomically. Failed length/CRC commit discards staging;
neither counters nor reference receipts claim acceptance. ABORT releases only
unpublished staging. Already committed packets remain immutable until consumed.

After COMMIT, check committed count advanced once and last sequence/session
match, with an ordered count-before/count-after bracket if needed. Check error
status too. Do not blindly replay an ambiguous COMMIT. A commit receipt means
PCM was admitted, not that it was played or acoustically emitted.

Last results:0 RESET,1 ARMED,2 BEGIN,3 COMMITTED,4 ABORTED,5 STOPPED,6 RANGE,
7 BUSY,8 FULL,9 LENGTH,10 CRC,11 SEQUENCE,12 SESSION. Invalid writes increment330.
No implicit retry, overwrite, partial publication, or clear-on-read is supported.

STOP disables playback, cancels staging and initiates a four-phase offline
flush. Published write ownership is held until the pixel side acknowledges
offline/reset read ownership. Producer resets its pointer, settles, then
rearms and waits for online acknowledgment. While offline, credits0 and348 is
invalid. Poll status online before changing session/prefilling. Firmware should
STOP on session loss, timeout, decoder error, app exit or core replacement.
Transport-loss pulse also initiates STOP. Repeated STOP may extend the handshake.

Prefill at least two complete packets then ARM. Playback starts at a DSP frame
boundary after two queued slots. On empty while playing, emit silence, increment
underruns once and rebuffer until two complete slots are available. One tiny
packet does not satisfy the two-slot prefill. STOP takes effect at the next DSP
frame boundary; the already latched frame completes unchanged. Clocks continue
in silence when disabled. With both clocks running, flush control completes in
microseconds and silence within one20.708us sample period plus synchronization;
no wall-time bound applies if a clock is stopped. Shared asynchronous assertion/
synchronized release resets both FIFO domains if either service/pixel PLL loses
lock. Normal STOP preserves324/330/334/338; FPGA/audio-clock reset clears them.

Eight fixed512-frame slots provide16384 PCM payload bytes. Each RAM word has a
LAST sidebit; no variable-length descriptor payload crosses clock domains.
COMMIT advances one Gray slot pointer; last-frame latch advances one read Gray
pointer. RAM is never reused before release crosses back. Unpublished slots
cannot be read.348 uses committed-epoch frames minus Gray-mirrored consumed
epoch frames; it can briefly overstate by a sample due to synchronization and
is not an admission credit. Epoch counters reset only during offline handshake.
Multiple CSR values are current observations, not a coherent global snapshot.

DSP output follows the existing GameBub AudioDspTransmitter/native speaker
format: signed16 LEFT then RIGHT, MSB first, offset0, DAC sampling falling BCLK.
MCLK is the existing LCD clock29.3619791667MHz, BCLK=MCLK/8,608 MCLK per stereo
frame. Exact sample rate is176171875/3648=48292.728893Hz. Data/WCLK change on
rising BCLK; WCLK is high for one BCLK period at the start. Remaining44 bit
positions are zero. Audio does not depend on LCD raster porches/margins.

No DAC I2C configuration, saved volume, analog routing, acoustic level or
audio/video clock synchronization is implemented by this RTL. External DAC
setup/hold budgets are provisional; audible output and sustained A/V service
require separate physical tests. Preserve sealed49 as video fallback.

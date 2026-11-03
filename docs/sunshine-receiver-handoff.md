# Game Bub receiver response to Sunshine host handoff

This response reviews Sunshine `gamebub/host` at commit
[`027c59412f19674616a3c31af346320a82e75207`](https://github.com/AEW2015/Sunshine/tree/027c59412f19674616a3c31af346320a82e75207/tools/gamebub).
The existing receiver prototype is MoonBub commit
[`d6212c8f79964be2a7e007429d3c8048593267d9`](https://github.com/AEW2015/moonbub/tree/d6212c8f79964be2a7e007429d3c8048593267d9).
The host's 0.4.0 draft is a **proposal**; neither side has agreed a final
Sunshine wire format or demonstrated Sunshine-to-GameBub interoperability.

## Decoder and image profile

The prototype selects baseline JPEG, not H.264. The FPGA uses
`ultraembedded/core_jpeg` at `bb03cce45d0b7459d395486e9e1db3de1b416bd2`, with
the local [elastic color pipeline patch](../fpga/patches/jpeg-output-elastic.patch).
The existing sender validates this conservative profile:

- 720x480, 8-bit, three-component YCbCr, one interleaved sequential SOF0 scan;
  component IDs 1/2/3 and the existing quantizer/Huffman table mappings.
- 4:2:0 and 4:4:4; fixed standard Huffman tables; dynamic 8-bit quantization
  tables 0 and 1. No optimized Huffman tables, 4:2:2, progressive/arithmetic
  JPEG, restart interval, or restart markers.
- Limit compressed JPEG to **262,144 bytes**. Use the known JFIF marker sequence
  in the fixtures: SOI, APP0, DQT, SOF0, DHT, SOS, entropy data, EOI. Other
  marker combinations should be tested before being declared supported.
- Output is clamped RGB888 converted to RGB565; coordinates are produced in
  8x8 block order and stored in transposed portrait scan order. 720x480 is
  divisible by both 16 and 8, so the chosen 4:2:0 and 4:4:4 frames have no
  partial edge MCU. Arbitrary edge geometry is not qualified.

The sender-side validator enforces the chosen profile. The current ESP32/FPGA
does not independently reject every unsupported JPEG feature before decode;
do not rely on it as a complete JPEG format validator.

## Sunshine fixture review

All 15 JPEGs in the pinned host manifest were downloaded and SHA-256 checked.
All five 4:2:0 and all five 4:4:4 fixtures passed the **host profile validator**.
All five 4:2:2/restart fixtures were rejected by that validator for unsupported
subsampling; restart markers are independently unsupported. These are not
claims that the current FPGA deterministically rejects every such file.

For frame 0 only, both the 4:2:0 fixture (71,675 bytes, Q75, SHA-256
`b327b1c2e2af7988e66f2ae570534a91c4526bbb53739ee5809f51e123228fb6`) and the
4:4:4 fixture (112,709 bytes, Q75, SHA-256
`9912e60175bf4ba54877f9a76518b37e5b3c0a68193579eb65092bb2292d6b25`)
passed the exact-source FPGA RTL test. Each produced 345,600 unique RGB565
pixels with zero mismatches against the fixed-point C reference. The source
fixture ID is 0; the FPGA testbench injects ID **7**. It checks backpressure,
CRC/truncation recovery and boundary-gated publication. It does not measure
SDRAM/display timing or any physical device.

[Fixture results and simulation logs](../evidence/sunshine-fixtures/) record all
fixture hashes, the testbench/core source hashes, reference/output hashes and
the two complete logs. Total testbench cycles include ingress and negative cases;
they are **not** decode latency, display latency, or measured frame rate.

The Q75 4:2:0 frame is approximately 17.2 Mb/s at 30 fps before packet and Wi-Fi
overhead; the 4:4:4 frame is about 27.1 Mb/s. Real game footage can differ.
Choose quality/rate after measuring the real link rather than assuming 30 fps.

## Receiver, buffering, and existing transport

The built prototype targets Rev4 ESP32-S3 firmware and Rev4.1
`xc7a100tcsg324-1`; the connected board and its actual memory population were not
inspected. ESP-IDF configuration does not enable ESP32 PSRAM. The FPGA holds
one 256 KiB compressed JPEG and uses two SDRAM RGB565 frame slots; a 720x480
canvas occupies 691,200 bytes. The physical panel is configured as 480x800
portrait / 800x480 mounted landscape. The 720x480 canvas is centered with 40
black columns on each side; its 16:9 content uses 37/38 black rows.

The offline-built [firmware UF2](../firmware/release/moonshine-rev4.uf2) has
SHA-256 `365b4cbc5c229955d1253e61dc78af29ebe9cdb0004daf94f2a45023a4771d99`;
the [FPGA bitstream](../fpga/build-final/moonshine-rev4.1.bit) has SHA-256
`785f0a2dd813e2e3d8cd001999120e33e9f565eb74c79b5da5fd70c1e9c25786`.
These identify build artifacts, not a programmed or observed hardware image.

Firmware uses a 1,065-byte DMA-capable datagram buffer, receives ordered payload
chunks of at most 1,024 bytes, and forwards them via quad SPI. The data interface
is capped at 40 MHz, or **20 MB/s theoretical** before overhead; reads are capped
at 16 MHz. Actual Wi-Fi, QSPI, concurrent throughput, frame age and displayed
FPS have not been measured. The FPGA's current SDRAM controller uses burst
scanout reads but individual pixel writes, which may limit sustained frame rate.

The existing standalone test mode uses UDP port 5533 and the documented
[MSV1 video / MSF1 feedback protocol](../host/PROTOCOL.md). A separate
[FPGA register/FIFO ABI](../fpga/PROTOCOL.md) begins at `0xE0000000`.
Register `0x0C` reports bytes remaining in the **declared compressed frame**;
it is not a live credit count for the 64-entry clock-crossing queue. That queue
has a separate dropped-bus-word counter at `0x50`; new losses invalidate an
unpublished frame. Software can use MSV1/MSF1 as a starting point for discussion,
but audio and authenticated sessions need an explicitly versioned extension.

Current recovery drops an incomplete/corrupted frame, aborts the FPGA transaction,
and accepts a newer start-of-frame; old displayed frames repeat. IDs advance by
wrapping sequence order and a new session resets the baseline. CRC32 is an
integrity check, not authentication. Frame-received feedback is not evidence
of decode or presentation. The FPGA exposes the last presented ID at `0x48`;
the current feedback does not report presentation timestamps or enough state to
claim end-to-end display latency.

## Buttons, audio, and identity

MSF1 carries the merged button mask: A=bit11, B=10, X=9, Y=8, Up=7,
Down=6, Left=5, Right=4, L=3, R=2, Start=1, Select=0. Firmware sends
changes during its socket loop (20 ms polling) and a 250 ms heartbeat, and sends
zero on disconnect/network silence. These are implemented timings, not measured
physical input latency. The standalone host defaults to logging input; optional
keyboard injection is mock-tested, and virtual gamepad injection is absent.

The firmware includes a TLV320DAC3101 driver configured for a 16-bit DSP-format
interface. The streaming FPGA currently drives audio outputs inactive: there is
no streaming audio decoder, audio buffer, agreed sample rate/channels, or tested
block duration in this image. Keep video-only operation available while those
are designed and measured.

The current standalone receiver has no Sunshine pairing, TLS client certificate,
or authenticated session. It filters the configured peer address but that is not
device authentication. A pre-provisioned unique per-device certificate may be
investigated, but ESP32 support and Sunshine interoperability are **not proven**.
Do not commit private keys or use a shared embedded private key. The present UDP
test mode is intended only for a trusted test LAN.

## Suggested next agreement

1. Freeze the restricted 4:2:0/no-restart JPEG profile and a versioned video-only
   protocol. Reuse MSV1/MSF1 only if the host agrees to its ordering, CRC,
   framing and recovery rules; do not label JPEG as H.264.
2. Add an explicit authenticated session and specify device provisioning before
   enabling remote input beyond a trusted test environment. Agree whether to
   reuse Sunshine control or define a separate verified identity handshake.
3. Define audio, presentation acknowledgments, dropped-frame reporting and
   timestamps as a separately negotiated/versioned extension. Keep stock
   Sunshine clients and a video-only path intact.
4. Test the exact paired build on the actual board, first with a local pattern
   and known fixtures, then with real moving gameplay. Measure concurrent Wi-Fi
   and QSPI throughput, display rate, frame age, drops and input response.

No hardware was programmed for this response, and no Sunshine branch change can
be interpreted as a successful end-to-end stream.

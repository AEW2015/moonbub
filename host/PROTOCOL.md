# Moonshine standalone test protocol v1

This experimental protocol is separate from GameStream/Sunshine. It carries
video only; neither audio capture nor transmission is enabled. The firmware
must explicitly select Test MJPEG mode. Default UDP destination port: 5533.
All multibyte fields use network byte order. Datagram size is at most 1064
bytes, avoiding IP fragmentation on a conventional 1500-byte LAN MTU.

## Video datagram MSV1

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | ASCII `MSV1` |
| 4 | 1 | Version, 1 |
| 5 | 1 | Codec, 1 = restricted baseline JPEG |
| 6 | 2 | Flags: bit0 SOF, bit1 EOF; other bits zero |
| 8 | 4 | Frame ID, wrapping unsigned32 |
| 12 | 2 | Width, 720 |
| 14 | 2 | Height, 480 |
| 16 | 4 | Total compressed JPEG byte count, 1..262144 |
| 20 | 4 | Chunk byte offset |
| 24 | 2 | Payload byte count, 1..1024 |
| 26 | 2 | Reserved, zero |
| 28 | 4 | IEEE CRC32 of the complete JPEG, zlib convention |
| 32 | 8 | Host capture Unix timestamp in microseconds |
| 40 | variable | Exactly the declared payload count |

SOF is required exactly at offset0. EOF is required exactly when offset plus
payload count equals total length. Frame metadata must agree on all chunks.
Chunks are sequential; no retransmission, duplicate acceptance, or reorder
queue exists in this prototype. A gap corrupts the current frame and the sink
recovers on a newer SOF. IDs are newer iff wrapping delta is in1..0x7fffffff.
A disconnect resets the session ID baseline, allowing sender restart at ID1.
Integrity is checked before the FPGA is permitted to present a completed frame.
CRC is corruption detection, not authentication; use only a trusted test LAN.

`moonshine.protocol.packets()` is the canonical host encoder. The golden
`fixtures/pattern-msv1-packets.bin` contains repeated u16 big-endian datagram
length followed by one exact UDP datagram. The length prefix is fixture
framing and is not transmitted on the network.

## Feedback MSF1

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | ASCII `MSF1` |
| 4 | 1 | Version, 1 |
| 5 | 1 | Status:0 accepted,1 dropped,2 busy,3 error |
| 6 | 2 | Merged GameBub button mask |
| 8 | 4 | Latest frame ID |
| 12 | 4 | Free ingress bytes, advisory snapshot |
| 16 | 4 | Received complete frame counter |
| 20 | 4 | Dropped frame counter |
| 24 | 8 | Echoed host capture timestamp |

Firmware replies to the sender's UDP source port on complete/drop events and
every250ms while connected. The sender only accepts feedback from its connected
peer. A received-frame ACK does not prove decode or presentation. Credits are
advisory network telemetry; firmware separately enforces actual FPGA FIFO
credits before each QSPI chunk.

Input mask: A11,B10,X9,Y8,Up7,Down6,Left5,Right4,L3,R2,Start1,Select0.
The host optionally writes mask changes to `--input-jsonl`. Keyboard injection
requires the explicit `--inject-keys` flag and uses arrows,Z/X/A/S,Q/E,Enter/Space
for D-pad,A/B/X/Y,L/R,Start/Select respectively. Default operation logs only;
virtual gamepad injection is absent. The host releases held injected keys on
a500ms feedback timeout, disconnect, socket error and sender shutdown. Firmware
sends release0 on disconnect. Cleanup paths are verified with a mocked backend;
no real Windows key event was injected during development.

## JPEG profile

The sender emits 720x480,8-bit,three-component, interleaved SOF0 JPEG with
YCbCr4:2:0, standard Huffman tables, dynamic8-bit quantization tables, one scan,
no restart interval/markers, no progressive coding, no arithmetic coding, and
no optimized Huffman tables. `validate_jpeg()` checks these constraints before
transmission. A1280x720 source becomes720x405 with37/38 black rows on the
720x480 canvas. The physical Rev4 panel source is800x480; the FPGA owns centering
the720-wide canvas without changing panel timing.

The sender holds one latest captured frame; slow encoding/transmission replaces
old captures. It decreases JPEG quality until a frame fits90% of the selected
per-frame wire budget. A frame that cannot fit at minimum quality is dropped.
Packets are paced using a high-resolution clock; expired frames are abandoned
and the next SOF replaces them. The configured Mbps includes MSV1 UDP payload
headers, but excludes UDP/IP/802.11 overhead and retransmission costs.

The capture timestamp permits host feedback RTT and same-clock software frame
age measurements. ESP32/FPGA timestamps require clock synchronization or a
separately measured clock offset before claiming one-way hardware latency.

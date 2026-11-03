# Moonshine FPGA prototype ABI v1

The native framework routes **0xE0000000** to the core. Framework registers at
0x01000000 and overlay at 0x03000000 retain their original meanings. Word
registers use the stock 32-bit big-endian QSPI command (0x54 write, 0x55 read);
FIFO writes use stock 8-bit quad, nonincrement command 0x40, max40MHz.
Reads retain eight dummy bytes and max16MHz. Programming-clock80MHz is unrelated.

| Offset | Meaning |
|---|---|
|00|RO magic 0x4D425631|
|04|RO version 0x00010000|
|08|RO caps bit0 baseline JPEG, bit1 deterministic pattern|
|0C|RO credits (bytes remaining in compressed frame; zero outside receive)|
|10|RO status bit0 READY,1 DECODING,2 FAULT,3 RECEIVING,4 PENDING|
|14|RW next frame ID|
|18|RW next compressed length (1..262144)|
|1C|RW dimensions width high16,height low16; prototype720x480|
|20|RW expected IEEE CRC32 of complete JPEG|
|24|WO command START=1, ABORT=2, COMMIT=4, PATTERN=8|
|28|RO accepted bytes in current frame|
|2C|RO complete compressed frames|
|30|RO decoded frames|
|34|RO presented frames|
|38|RO faults|
|3C|RO dropped/aborted frames|
|40|RO ingress overflow count|
|44|RO scanout underruns|
|48|RO last presented frame ID|
|4C|RO maximum compressed length|
|50|RO dropped CDC write-queue bus words (data or control words); reset by FPGA reset|
|100|WO byte FIFO, no address increment|

Write metadata, START, poll credits, send sequential bytes, COMMIT. CRC32 is
initial0xffffffff, reflected polynomial0xedb88320, final XOR0xffffffff. A
commit requires exact length and matching CRC and SOI/EOI. Decoder output is
bounded by expected dimensions and a watchdog; damaged frames are never
published. ABORT clears fault/receive/decode and preserves the displayed frame.
The decoder starts only after a complete frame is buffered; ESP32 never holds
a decoded framebuffer. Only one compressed frame and one pending display frame
are allowed, keeping memory and frame age bounded.
The CDC write queue additionally counts every dropped bus word in its200MHz
domain. Gray-coded telemetry crosses into the100MHz core and is exposed at50.
Any change faults and aborts the current receive/decode/pending transaction,
preserving the displayed frame; ABORT and a new START recover after transport
stabilizes. Register40 counts compressed-RAM/FIFO-port overrun attempts.

JPEG is SOF0 sequential8-bit YCbCr420 or444 with standard Huffman tables,
no optimized tables, restart markers, progressive coding, or422. Sender uses420
and dimensions divisible16. core_jpeg is pinned to
bb03cce45d0b7459d395486e9e1db3de1b416bd2 (Apache2.0).

The verified source panel timing is **480x800 portrait /800x480 mounted**,
not720x480. The720x480 transmitted canvas is centered with40 black columns at
each landscape side. Within that canvas,16:9 content is720x405 plus37/38 black
rows. Native HDMI/dock remains a later milestone in this standalone prototype.

# V21 proposed integration tasks

This is a prototype extension to the frozen v20 hardware-development kit. Current
MSV1 JPEG endpoints and AR03 peers do not implement HC21/HA21/CB21. No endpoint
should enable these bytes without an explicit new negotiated profile.

## Host/native team

Port HD21 integer word coding and HC21 parsing against the retained packets and
original RGB565 words. Preserve the existing full-patch compressor as a paid
fallback. Current mode selection tries both actual encoders; optimize it only
against identical outputs and complete framed byte counts.

Integrate HC21 with the existing candidate API, not by calling its standalone
prepare and treating that as whole-frame commit. A candidate must carry private
video bytes, four exact patches, pending cache identity, complete binding cost
and source lease. Reject an oversized/deadline-expired pair without burning its
issued frame ID, advancing a YUV bank or publishing cache state. Keep every
rejected encoder attempt paid.

Choose a negotiated pair envelope and versioned capabilities; CB21 is currently
only a functional fixture container. Bind the exact base and HUD identities,
bytes, epoch and geometry. Define complete-cap validation before allocation,
malformed-length reason codes, retry limits, timeout, reset/rekey and fallback.

## FPGA/decoder team

Continue the v20 exact inverse, entropy, compact YUV/tag and scanout work. HD21
COPY/XOR is an additional simple integer/display-memory stage; it does not
replace the transform DSP pipeline or prove its throughput.

Plan explicit external-memory address ranges for two 42,240-byte immutable HUD
banks plus 42,240-byte private staging, with all parser/hash/packet scratch and
descriptors accounted separately. Prove exact geometry-bound hashes and CRCs,
bounded spans, no duplicate/overflow output and the retained full-display results.

Do not use a stale, speculative or read-pinned bank as overwrite space. Unique
reader tokens must survive independent DMA/scanout readers, duplicate releases,
counter exhaustion and reset. An ACK is issued after valid output and write
completion, not after the final input word arrives.

Implement private base+HUD preparation and atomic matching-epoch presentation.
On a damaged or missing component, retain the old complete display or drop the
whole update under a defined policy. Never publish YUV/cache ACKs for invalid
private work. Reset/abort at every phase must release only owned resources.

## ESP32/gateway team

Keep the gateway an opaque bounded-fragment forwarder. Do not place full HUD
banks or unbounded complete-pair reassembly in the ESP32 by default. Record real
SRAM/DMA heap, mailbox occupancy, driver copies/CRC costs, QSPI service and reset
behavior. No PSRAM or new memory bank is assumed by these Python studies.

Negotiate and route each permission separately: PC18 packet tokens, FG19 frame
owners, AF03 decoded YUV-reference ACK and HA21 decoded display-cache ACK. A packet
permit is never an exact reference confirmation. Retry only identical outstanding
cache bytes/identity; unknown ownership stays owned or enters a defined session
reset, rather than inventing credits.

## Integration acceptance

Use `python experiments/verify_prototype_v21.py` and the frozen v20 hardware kit
for conformance. V21 retains 6 patch goldens, 132 cache update/ACK/original-word
sets and 10 composed display fixtures. V20's 101,667 inverse blocks remain the
hardware arithmetic oracle. Full native/RTL tests, resource/timing reports,
physical memory/line deadlines and calibrated 30-fps gameplay remain required.

Extend fault testing to one-sided resets and lost reset handshakes; current local
reset calls are not protocol recovery. Add fresh long captures for camera pans,
rapid HUD changes, menus, text, particles and scene cuts. Record admitted/rejected
source IDs, unique presented IDs, age, long gaps, cache refresh/fallback traffic,
all directional bytes, input/audio and errors. Preserve the strict observation
window and JPEG comparison. Never report a network-only bound as achieved FPS.

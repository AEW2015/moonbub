# HC21: acknowledged exact display-HUD cache

This Python prototype adds a **separate experimental display-only sidecar** to
v20's unchanged lossy YUV/base reconstruction. It does not modify AR03 grammar,
installed JPEG firmware, YUV banks, native Sunshine/ESP32 code or FPGA RTL.
The target remains 720×480 coded /720×405 active, with all four declared HUD
rectangles totaling 21,120 original RGB565 words per accepted update.

## What runs

Each patch pays both the existing HP01/HR01 adaptive full encoder (including its
bounded host byte cache and validation) and the new HD21 RAW/COPY/SPAN_XOR
candidate. The smaller **actual encoded patch** wins; ties retain legacy full.
HC21 then adds a real 79-byte header and four-byte CRC. Its four lengths and
patch dispatch modes are inside that header. No source-equality oracle skips a
wire cost. COPY references a specific acknowledged decoded patch and sends its
geometry/content tags; it is not free omission of an update.

Only one transaction may be unresolved. A sender uses its last fully ACKed
immutable cache bank, and a receiver publishes all four decoded patches together
only after their inner grammar, whole update digest and identity validate. The
54-byte HA21 ACK binds epoch, frame, generation, destination, full packet digest
and decoded complete HUD digest. ACKed display state is separate from AF03/YUV
publication. HC21's SHA256[:16] tags and CRC are consistency checks, not transport
authentication, encryption or an implemented session-negotiation mechanism.

Two receiver banks alternate. A maximum of eight unique display-reader leases
prevents a destination overwrite/reset while read ownership remains active.
Duplicate release cannot drain another reader; uint32 lease-token exhaustion
fails closed until a later-epoch reset. No actual scanout DMA/fence is implemented.
Python object assignment is functional atomic publication, not a physical clock
crossing or memory-order proof.

A dropped packet or ACK leaves the sender unresolved. It may retransmit exactly
the outstanding bytes; the receiver returns the same ACK idempotently without
republishing. It cannot issue the next frame until that exact ACK arrives.
Different bytes for a repeated identity, older/reordered input, wrong epochs,
wrong reference identity, corrupt patches and forged ACK identity all reject.
The model has separate local sender/receiver reset calls with increasing epochs;
coordinated reset/rekey over a wire remains native integration work. There is no
retransmission timeout, retry limit, wire schedule or automatic recovery policy.

## Measured source replay

Both native cases reuse the exact 48-frame windows at four seconds in
`mass-effect-2600.mp4` and `mass-effect-7200.mp4`: 96 acquired precompressed source
frames at 29.88 fps, resized with the same BOX canvas as v20. These are regression
windows, not fresh held-out desktop capture. PyAV acquisition is excluded from
stage timing; BOX time is retained separately. Both complete patch candidates,
hashing, validation and cache preparation are included in encode wall time;
receive/decode/publication and ACK application are separately measured.

| Scene | Legacy full patch section | HC21 forward bytes | Forward patch reduction | Unchanged-v20-base accounting total |
| --- | ---: | ---: | ---: | ---: |
| 2600,48 updates |498,746 B |442,450 B |11.2875% |988,011→931,715 B |
| 7200,48 updates |1,124,704 B |1,023,067 B |9.0368% |2,116,013→2,014,376 B |

Each native case additionally transmits 2,592 ACK bytes before lower-layer
framing; this is **not** a free acknowledgement. Complete cache update plus legacy
base byte replacement is arithmetic accounting only: the base packet history,
maps and pixel losses are fixed from v20 and no new AR03-compatible packet is
claimed. Root v21 composition/transport studies qualify complete packet semantics
and necessary wire/RTT budgets separately. None of the accounting replacements
exceeds the prior 49,152-byte cap, but a cap is not sustained bandwidth or latency.

Across native updates the chosen modes are 265 legacy full patches,117 span-XOR
patches and two COPY patches; HD21 RAW loses to the legacy alternative. All
2,027,520 native HUD words are exact. Three separate 12-update controls demonstrate
static, sparse changes and noise: forward patch bytes fall 56.7982% and47.8408%
on the first two, while noise **increases 0.1581%** because all legacy full patches
win and HC21 still pays its header. Those favorable controls do not replace the
native scene result. All132 updates /2,787,840 words match exactly.

## Storage and traffic limits

One decoded complete HUD uses 42,240 bytes. The receiver retains at most two
published banks (84,480 bytes) and stages up to one complete replacement
(42,240 bytes) before atomic publication: **126,720 pixel bytes**, before inner
decoder scratch, packet data, hashes, descriptors, metadata and Python objects.
This explicit staging is not a fitted Gamebub SRAM/BRAM claim. Real simultaneous
scanout/bank refill and SDRAM ownership remain open.

Sender confirmed + pending complete words reach 84,480 bytes. The existing
four-entry legacy encoder cache additionally retains its original words and
encoded packet bytes (recorded per row), plus pending immutable HC21 wire bytes.
The caller's RGB canvas, extraction/encode temporaries, all losing candidates,
hash copies and interpreter allocations are additional. These are bounded pixel/
encoded-object counts, not measured native heap peaks or a no-PSRAM ESP32 port.
One can place display caches in FPGA external memory; actual mapped capacity,
arbitration and deadlines must be implemented and measured first.

Rows expose selected-reference word-copy reads and complete destination writes
as functional byte counts. Whole-HUD/tag reads and decoder scratch are additional;
these counters are not measured bus transactions or free extra memory ports.
Stop-and-wait ACK pacing imposes a round trip per update. Lower payload alone
does not establish 30 fps; native encoding, actual link/QSPI/FPGA service and
RTT/feedback are still uncalibrated.

## Retained proof

`results.json` pins 53 source/dependency files,132 complete packets/ACKs and exact
original patch arrays. Content-addressed bounded zlib objects deduplicate repeated
words. `verify.py` independently replays the entire five sequences without media,
compares exact originals and ACKs, repeats each packet idempotently, and checks132
atomic outer-CRC rejections. Fifteen unit tests cover packet/ACK loss, immutable
banks, stale/reordered/reset identities, missing references, eight-reader bounds,
duplicate lease release, token exhaustion, false decoded tags and a bad fourth
patch after the first three decode. No partial update is published.

From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Regeneration additionally needs NumPy, Pillow, PyAV and both existing media files:

```sh
GAMEBUB_MEDIA_DIR=/path/to/media /home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

Keep pinned sources fixed during a campaign. These are actual Python component
results, not ESP32 ISA timing, RF calibration, native endpoint interoperability,
FPGA utilization/Fmax, routed bitstream or sustained physical30fps proof.

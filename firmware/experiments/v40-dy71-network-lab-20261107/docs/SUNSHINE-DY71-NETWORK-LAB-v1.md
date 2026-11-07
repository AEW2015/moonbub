# DY71 network bring-up: V40 / DYN1 lab v1

Status: implemented offline; not installed or hardware-tested. V023 remains the color-verified FPGA baseline, V39 the installed app. This lab transport is a proposal shared with the sender implementer, not an agreed production Sunshine protocol.

The first end-to-end network gate sends two original CU66 v1 packets (key then its dependent P), not JPEG/MSV1, AR03, CP23 or a naked GM01 body. It preserves the FPGA's native decoder/HUD/reference protocol. No video rate, audio or controller capability is negotiated or advertised.

## Endpoint and invocation

- Explicit USB `~` launches the lab worker. It acquires the existing exclusive maintenance lease, refuses JPEG/AV peers and requires a fresh DY71 identity: magic `44593731`, ABI `00010000`, capabilities `0000000f`, idle status `1`.
- No bitstream is loaded by this worker. Program the exact verified V023 through the existing safe JTAG procedure after the app update and cold boot. Do not program under V39's current retained native lease.
- UDP port **5535**, with the existing saved `host` IPv4 allowlist from `/sdcard/moonshine.cfg`. The first valid sender endpoint and nonzero 64-bit session are pinned. Credentials use the existing Wi-Fi owner and are never logged.
- Wi-Fi/native memory allocation is checked before any FPGA writes. Worker stack 16,384 bytes. Free heap must be at least 140,000 bytes and largest block 24,576 after Wi-Fi setup. A refusal is evidence of insufficient budget, not permission to lower the guard blindly.
- Complete frames are staged directly into FPGA memory using the existing completed-word count and CRC protocol; ESP32 has no full-frame video allocation. The native HUD endpoint and temporary original HU message still consume bounded SRAM.
- Two frames only, then hold the last picture, native endpoint, Wi-Fi and maintenance lease. Cold boot is required before another run or image switch. Any post-mutation failure retains/quarantines ownership.

## Wire layout

All integer fields are little-endian. Each data datagram is exactly 48-byte header + 1..1024 payload bytes + 4-byte CRC32. CRC is IEEE CRC32 over header and payload, excluding its trailing CRC. Maximum datagram 1,076 bytes.

| Offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 4 | `DYN1` for data; `DYA1` for reply |
| 4 | 1 | Version 1 |
| 5 | 1 | Data=0; reply status below |
| 6 | 2 | Header length 48 |
| 8 | 8 | Nonzero random session identity |
| 16 | 4 | Original CU66 frame ID |
| 20 | 4 | Original CU66 reference ID |
| 24 | 4 | Original CU66 total bytes, 80..49,152 |
| 28 | 4 | Data chunk offset / reply next completed offset |
| 32 | 4 | CRC32 of entire original CU66 packet, including its own inner CRC |
| 36 | 8 | Host capture timestamp in Unix microseconds; identity only |
| 44 | 2 | Data payload length; replies zero |
| 46 | 2 | Reserved zero |
| 48 | variable | Original CU66 bytes (replies have no payload) |
| end | 4 | Header+payload CRC32 |

Data offsets are multiples of 1024; chunks have exactly min(1024, total-offset) bytes. Header identity fields remain unchanged for the complete frame. Dimensions in original CU66 must be 720x480. Frame/reference fields must match the original header. HU extent must end immediately before CU66's inner CRC and HU length must not exceed 20,000 bytes. FPGA parser/native endpoint perform semantic checks; wire validation is not a decode-success guarantee.

Replies are exactly 52 bytes, echoing the complete identity. Status:

- **0 stored-prefix**: the acknowledged prefix has reached completed FPGA staging writes.
- **1 fully-staged**: all declared bytes reached staging. Not an integrity/decoder/presentation certificate. Whole-frame CRC, parser, native HUD and all completion checks must still pass.
- **2 actually-presented**: only after actual owner/accepted/presented, per-word HUD readback and reference-tag checks succeed. No speculative presentation ACK.
- **3 failed/retained**: the worker failed and retains/quarantines any mutated ownership. This is not a safe-to-reuse notification.

Sender is stop-and-wait per chunk, then waits for actual presentation before the next frame. Matching old chunks are idempotently acknowledged and never uploaded twice. Unknown peers, identities, malformed packets and unexpected offsets are ignored within bounded receive deadlines. Do not compare host/receiver monotonic epochs. No congestion or sustained-rate behavior is claimed.

## Reference command (only after receiver readiness)

```powershell
python tools/dy71_fixture_sender.py --receiver 192.168.0.157 --bind 192.168.0.47 --log dy71-key-p.jsonl packet0.cu66 packet1.cu66
```

The original fixture bytes are under `handheld/src/cu66/fixtures/`. No frame IDs or compressed body bytes are rewritten. Sender validates CU66 inner CRC before sending and expects two actual presentation replies. Existing MSV1 senders must not transmit JPEG to port 5535.

## Qualification and next work

Host tests run the real C++ HU endpoint through the software CSR model, plus actual localhost UDP packet exchange. These are not FPGA timing or hardware/network results. Preserve actual target compile/configuration, ELF/UF2 hashes, updater-parser validation and physical memory/stack logs separately.

The V023 diagnostic uses scalar CSR operations to write and verify 21,120 HUD words per frame. The prior two-frame hardware test took 53.895463 seconds including diagnostic work. The new network wrapper preserves that behavior to establish correctness; it cannot turn this into interactive streaming. After network KEY/P works, measure packet upload, decoder, native HU, HUD write/readback, commit and presentation separately. A practical moving-video implementation needs a verified bulk/batched HUD transport and a bounded continuous owner/session loop, then sender integration and sustained pacing. Do not drop the physical readback/tag gate as an optimization.

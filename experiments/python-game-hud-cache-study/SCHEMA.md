# `gamebub-hud-cache-v21`

`results.json` stores relative `source_sha256`, fixed header/ACK/pixel-bank sizes,
96 native and36 synthetic decisions, dependency versions and five named cases.
Each case contains its source manifest, sequence rows and aggregate summary.

A row records frame/generation, actual legacy full patch section bytes (all four
length prefixes), complete HC21 bytes, complete HA21 ACK bytes, actual losing and
chosen patch sizes, chosen mode names, changed words vs confirmed bank, encode/
decode/ACK application wall milliseconds, exact-word mismatch count, source
canvas SHA256, functional reference-copy and destination-write bytes, pixel bank/
staging and actual existing legacy-cache/pending-wire sizes.

Native rows bind the matching v20 source-canvas hash, its complete mandatory AR03
size and inner bytes. `accounting_only_replaced_total` is old complete bytes minus
old framed UI bytes plus new complete HC21 bytes; it does not serialize a new
AR03 format or account for lower transport, ACKs, retries or RF.

`packet`, `ack` and four `original_patches` are zlib object descriptors with safe
relative path, exact raw size/hash and stored SHA256. Original words are `<u2`
rasters in the four fixed declared-region shapes. All decisions form complete
sequences for independent receiver replay; no hidden precondition cache is needed.

HC21 fixed header `<4sBIIIBBII16s16s4I4B` is79 bytes: magic/version, epoch/frame/
generation, destination/reference slots, reference frame/generation, reference/
current whole-HUD tags, four payload lengths and four mode dispatch bytes. Modes
0=existing self-contained HP01/HR01 patch,1=HD21 component. Four payloads follow,
then outer CRC32; complete packet cap49,152 bytes. Region positions/geometries
are the fixed local profile and are hashed with all exact words. Capability
negotiation is not implemented. Delta's own geometry/content header is additional.

HA21 `<4sBIIIB16s16s` is50 bytes plusCRC4: magic/version, epoch/frame/generation,
destination, whole packet SHA256[:16] and decoded complete HUD SHA256[:16].
ACK identity and publication never imply a decoded YUV predictor bank.

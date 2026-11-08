# Three-frame CU66 qualification package

November 7, 2026. Scope: historical `mass-effect-10000` KEY0/P1/P2, not the user's requested 120-second Mass Effect source. First two packets match the physically tested V43/V027 originals byte for byte. The third packet is new to integrated-system/hardware qualification. No hardware readiness or current IP readiness is asserted here.

## Payload and reference evidence

`prepare.py` imports the frozen Python CU66 receiver, decodes all three packets in order and checks canonical tag, exact canonical YUV, HUD words and composed RGB565 hashes against the retained independent manifest. It exports `frameN.cu66`, `.yuv`, `.hud`, `.rgb565` and `.canonical.u16` with hashes in `manifest.json`.

`canonical.u16` is tile-major 8x8 within Y/U/V planes, with adjacent x pixels packed low/high byte into little-endian words. The exporter checks frames0/1 are byte-identical to the original native canonical reference dumps. Raw `.yuv` is raster-order planes and is not the physical SDRAM layout.

Four actual reference failure cases pass: P1 without KEY, P2 without P1, CRC corruption, duplicate P2. Failed calls leave published identity unchanged. This establishes software-reference behavior, not FPGA failure recovery.

## Explicit bounded3 lab transport: dy71-bounded3-v2

This is a new incompatible bounded diagnostic profile. DYN1 data and DYA1 reply layouts remain 48-byte little-endian headers plus CRC, but byte4 is **2**. Existing V43/v1 receivers must reject v2 before mutation; the V44 candidate must reject v1. Port remains5535 only when that exact candidate is deliberately armed. No negotiation, discovery, production streaming, audio or AV coexistence is defined by this profile.

Data header layout (`<4sBBHQIIIIIQHH`):

| Offset | Field |
|---:|---|
|0|DYN1 magic,4bytes|
|4|version2,u8|
|5|data type0,u8|
|6|header length48,u16|
|8|nonzero session,u64|
|16|frame ID,u32|
|20|reference ID,u32|
|24|whole CU66 length,u32,80..49152|
|28|chunk offset,u32,multiple1024|
|32|CRC32 of complete CU66 bytes,u32|
|36|capture timestamp,u64,identity only across machines|
|44|chunk length,u16,exact min(1024,total-offset)|
|46|reserved0,u16|
|48|chunk bytes then CRC32 over header+chunk,u32|

DYA1 replies are52bytes: same identity fields, byte5 status, offset28 completed prefix, length/reserved fields44..47 zero, CRC32 over first48bytes at48. Status0=stored prefix,1=all staged,2=actually presented,3=failed/retained. Stored means completed FPGA storage, not socket receipt; status1 does not prove decode/display. Status2 must match complete identity and full length.

One sender/socket/session, one frame in flight, exactly KEY0/refFFFFFFFF then P1/ref0 then P2/ref1. Chunks use stop-and-wait credit: next chunk only after exact completed prefix acknowledgment. Next dependent frame only after matching actual presentation reply. Exact duplicate retries use existing per-frame idempotence; no whole-run retry. First KEY readiness may wait1..1800seconds (default600); later chunks retain10second budget, presentation90seconds. Failure/unknown outcome stops the invocation and leaves recovery to the coordinated receiver owner; no automatic reset or forced lease release. Successful third presentation leaves receiver ownership held as designed. This is finite three-frame correctness testing, not continuous-video lifecycle or 30fps support.

`bounded3_sender.py` requires `--profile dy71-bounded3-v2`, adjacent packet manifest hashes, explicit sender bind and a new exclusive log. `dyn1_pair_core.py` is a local per-frame-only derivative of the original pinned sender (original SHA256 `a86c6e78401e3723fe72397240d087e97822088bd8c6bc878d1151e0ecea9a63`), with explicit v2 data/reply checking. Original production sender remains untouched. Do not invoke the core directly.

Prepare command only, **not START**:

```powershell
python bounded3_sender.py --profile dy71-bounded3-v2 --receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600 --log fresh-lab3.jsonl
```

The uploader is permitted only after the receiver owner confirms exact candidate ELF/FPGA/ABI, mode/version, memory reserve, clean ownership and explicitly coordinates START.

## Package verification

This publication contains the three exact CU66 packets, transport-specific manifest, uploader/core, eighteen golden vectors and five pure fake-transport tests. Full `.yuv`, `.hud`, `.rgb565` and tiled SDRAM oracles plus their preparation script remain in the local qualification evidence directory; they are deliberately not duplicated here. `manifest.json` pins the full local qualification manifest SHA and ships only packet file entries. The package tests need no PyAV, native compiler, media file or device.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python ./test_bounded3.py
```

Five tests use an in-memory fake transport: exact three frames/58 chunks with matching status2, receiver-failure stop before next dependent frame, explicit profile/count refusal, v1 ACK rejection, and all published golden CRCs/hashes/version fields. No socket is opened by tests. Do not run the sender until the receiver owner gives coordinated START for the exact bounded3-v2 candidate.

# V58 / V029 forty-frame hardware result

V58 passed the original forty-frame custom-codec sequence: **40 accepted, 40 presented, zero rejected and zero underruns**. All **844,800 HUD words were written and read back correctly**. Receiver elapsed time was **26.532393 seconds**, without added inter-frame pauses. The sender exited zero after all forty matching status-2 replies; its 40.734-second invocation includes initial Wi-Fi/readiness waiting and is not playback time. The camera showed the final decoded scene. The sender and recorders are stopped; the successful final endpoint/lease and image remain held. No automatic retry or reset followed.

## Change and verification

V58 reserves four private, validated HUD output buffers largest-first before decoding. Huffman/Rice processing streams symbols into those buffers, avoiding large transient symbol/channel vectors. The Rust receiver reuses one HC70 wire buffer across frames. Accepted reference data remains immutable until full validation succeeds. Native arena98,304, physical reserve8,192, stack16,384, transport and all FPGA logic remain unchanged.

Offline verification passed original12/new40 exact output checks, 59 mode cases (41 valid/18 rejected), malformed/late-failure rollback and recovery, constrained allocation models and independent review. The host suite and target build passed, followed by production updater/parser checks. These models do not prove physical contiguous allocation or whole-stack bounds.

The installed candidate then passed cold CPU12 (253,440 HUD words) before this network trial. Physical network native allocation peak was86,020 bytes, largest request15,360, with zero allocation failures; final heap72,576/largest36,864, minimum native free13,560 and observed task stack low2,772 bytes. Two independent read-only exports each validated43 indexed/checksummed records, checksum33d9ccb4; underlying USB transmit-loss count remains unknown.

## Exact versions

- ESP32 V58 SDK ELF: `c7d9452a123db12c9edeede96551a3bb6c1206da617ad431103656aba6f476c4`
- BIN: `2b044b6cae910338c2d2f15cff3984d922d583a382f9d82aaa643b1169fd6359`
- UF2: `abaf8af2caec8ec9deaa97f0e1c3a5e409b5232b7fd48a08a4695bfbd1c5b6e6`
- Native HUD: `be6565d96f6d2b986ac06656142b5e6484982473d496d104a76dabc72a27f656`
- FPGA unchanged V029 BIT: `59a2439488c529941661debcf3f3c75f8fd2f6e61418c3c63a45e377e971e7c3`; DONE1/USERCODE44593741. Routed setup0.000ns (user accepted for this lab), hold+0.008ns. Two inherited critical bundled-status CDC findings remain; no zero-critical-CDC claim.
- Fixture manifest: `76b37ca8245b8ed657c6caabbbd9d416de3dd4c775b1626ed466699559623034`
- Session6372797075029519005, `.33:59443 -> .157:5535`, unchanged DYN1/DYA1v3 sender, one frame in flight, KEY0 followed by39 dependent P frames.

The app-only install was fully readback verified; updater/partition table and SD files were preserved. Windows DFU needed the authorized device-specific WinUSB rebinding. The helper's post-install description-check error was retained; independent PnP and complete readback established access, rather than treating that helper exit as success.

## Scope and next development

This is the same20-second source interval sampled at2fps, not a20fps acceptance test. It uses a local rendering-breakdown clip, RGB444 and uniform codecq32, prepared as720x405 at(0,37) inside720x480. Source SHA `151749815d3b34781d4ef780632efba2efe4f7f1ed08b5cad06faab32e35bc80`. It is not Mass Effect, live Sunshine, JPEG quality32, audio or controller evidence. Full HUD readback and presentation replies do not constitute an independent canonical full-frame pixel readback. No all-core fault snapshot was collected.

The allocation failures from V56 frame8 and V57 frame17 are resolved for this unchanged forty-frame sequence. Next work is to separate staging/decode/HUD readback/presentation costs, then qualify a longer moving sequence and sustained unique display rate using the same versioned contract. This verification-heavy stop-and-wait run does not establish a production throughput ceiling or20/30fps readiness. Reconfiguration requires an explicit reviewed restart to release the held native endpoint.

Exact source, BIN/ELF/UF2, source/build bindings, mode fixtures, independent review and selected hardware receipts are preserved in [the V58 package](../../firmware/experiments/v58-hud-storage-plan-20261108/README.md). The unchanged replay/oracles are in [host/dy71-clip40-20261108](../../host/dy71-clip40-20261108/README.md). Raw flash backups and full Wi-Fi logs remain private under C:/moon.

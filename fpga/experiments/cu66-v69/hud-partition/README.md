# Qualified software HUD gate for the partial CU66 FPGA pipeline

This directory implements and tests the software side of a deliberate partition: packet/base processing can run in FPGA RTL, while the qualified native C++ HUD decoder remains a software commit gate. **It is not a complete CU66 FPGA decoder.** The tested software endpoint is the Linux build host. No ESP32 port, processor timing/SRAM qualification, live mailbox, QSPI word writer or physical DMA fence is implemented here.

`hud_gate.hpp` wraps the frozen native `decode_hud` implementation; it actually decodes original HU25/HX32/HX33 bytes, rather than loading golden HUD words. `test_hud_gate.cpp` replays all 457 retained packet HUDs through four causal histories, including 20 keys. Every candidate's full RGB565-word SHA256 matches the retained native/Python golden. Compressed input is overwritten after preparation to check that the candidate owns its words.

## Control operations

These are typed software operations with assigned logical opcodes, not an implemented network or MMIO wire ABI. A future adapter must encode messages, preserve generation/identity and implement the signal/fence rules in `interface-contract.json`.

| Opcode | Operation | Effect |
| --- | --- | --- |
| `0x01` | `PREPARE` | Decode and validate one HUD packet for a generation/frame/reference. Produces an immutable candidate; accepted HUD stays unchanged |
| `0x02` | `STATUS` | Read phase, identity, verified tag, word count and failure state |
| `0x03` | `READ_CANDIDATE` | Borrow an owned read-only candidate only for the matching generation/frame |
| `0x04` | `ACK_EXTERNAL_WRITE_DRAIN` | Accept matching count/tag from the external writer after its actual copy/drain; does not publish |
| `0x05` | `COMMIT` | Root-authorized, matching, transferred candidate becomes accepted HUD. Identical retries are idempotent |
| `0x06` | `ABORT` | Discard the matching candidate/failure; previous accepted HUD remains unchanged |
| `0x07` | `RESET` | Fresh generation plus externally established quiescence clears accepted/candidate state |

Generation is 64 bits and frame/reference IDs are 32 bits. A newly admitted prepare/reset requires a nonzero, strictly increasing generation. A busy prepare does not consume a future generation. Old IDs/generations cannot replace a current candidate. Root owns whole-frame acceptance; the accepted HUD cache is updated only by its commit event.

`candidate_ready()` is true only while a verified candidate exists. Historical `Committed` status is not a new ready token. Preparation performs all native HUD envelope/patch CRC, identity/reference, prediction, Huffman/Rice, component range, exact-consumption and reconstructed-tag checks. A failure produces no ready candidate. The prior HUD cache is immutable across preparation, failure, abort, transfer and later commits.

The test transfer sink copies the actual decoded candidate words into a separate native buffer and hashes that copy. The ACK checks generation, frame ID, 21,120 words and reconstructed HUD tag. In hardware, that ACK must come from a real writer/owner after write completion and visibility/readback assurance. Supplying matching fields to this software method alone proves no physical transfer.

## Required FPGA/root fence

The root may publish the combined YUV/HUD bank descriptor only when all of the following refer to the same active generation/frame:

- packet/entropy checks and hidden-coefficient validation passed;
- the canonical base output tag matches and all base writes drained;
- software reports a verified candidate with the expected frame/reference, HUD output tag and exactly 21,120 words;
- those exact words reached the candidate HUD bank, bank contents match the candidate and external HUD writes drained;
- no error or abort is pending.

A native HUD success cannot override a base failure. Tests prepare and transfer four HUD-valid candidates whose base fails for another reason, then abort them without advancing the previous HUD cache. Late HUD CRC/output-tag failures likewise preserve the old cache. Independent key 24 recovery is checked afterward.

Root commit must be delivered to the software cache for the matching generation/frame. Do not start a new frame until the FPGA publication and software commit acknowledgement are reconciled. Retry the same commit identity after a lost acknowledgement; never infer a new acceptance from an older ACK. Candidate readers can retain a read-only pointer across an abort, so the real writer/arbiter must still drain or discard old-generation writes before bank reuse. Reset requires all relevant readers/writers and lease generations to be quiescent.

No RTL join or physical writer is supplied in this directory. The root still must implement the generation-qualified software-ready/failure, external write-drain, commit and software-commit-ACK bridge. The packet parser's successful metadata handshake is not this semantic gate.

The candidate word order is four row-major patches in the fixed profile order. Their word offsets are 0, 3,840, 7,680 and 15,360; the total is 21,120 little-endian RGB565 words / 42,240 bytes. The adapter must copy the decoded candidate, not obtain pixels from an expected-output fixture.

## Audited scope and state sizes

The actual corpus contains 1,828 patches: 1,466 HS33, 58 HS32, 297 HD25 and seven HR01. Envelopes are 443 HX33 and 14 HU25. HS33 channels use 4,307 zero-gap schemes and 91 repeat-run schemes. The observed Huffman maximum is 86 symbols / depth 13, and HS33 Rice maximum is `k=12`; legal bounds remain 253 symbols / depth 16 and `k=14`. These observations cannot silently narrow a future decoder's advertised capability.

Full compatible HUD RTL would need canonical Huffman table construction/decoding, bounded Rice run expansion, temporal/intra/row-delta component reconstruction, global/tiled HUD reference reads, HD25 byte/span residuals, HR01 palette/row runs, exact CRC and geometry-bound patch/envelope SHA checks. It also needs distinct previous/candidate HUD banks and generation-qualified failure/commit handling. The software partition retains these semantics while that implementation remains absent.

A raw-HUD shortcut is not free: exact format-size accounting for an all-raw HU25 envelope gives 42,462 bytes per HUD and would put **279 of 457 complete frames above the 49,152-byte cap**; maximum complete size would be 70,031 bytes. This is a size counterfactual, not a new encoded/transport-tested format.

| State measurement | Bytes |
| --- | ---: |
| Logical word data per accepted or candidate cache | 42,240 |
| Logical word data for accepted plus candidate | 84,480 |
| Largest observed one-cache `std::vector` word capacity | 47,616 |
| Largest observed previous-plus-candidate word capacity | 94,720 |
| `sizeof(HudGate)` on this GCC/libstdc++ build | 120 |
| `sizeof(HudCache)` / `sizeof(Patch)` | 56 / 32 |

These are not total SRAM/heap bounds. Decoder temporaries, Huffman maps, channel arrays, allocator/control blocks, status strings, retained external readers, compressed input, test sink and FPGA HUD banks are additional. A fixed-array embedded port could use different storage, but the existing Wi-Fi/UI/firmware allocation and real processor time must be measured. The Linux test is not evidence that this C++ gate fits or meets deadlines on ESP32.

The validation run observes roughly 0.8 ms per native prepare on the shared host; sanitizer observations are slower and recorded separately. These are single-pass qualification clocks, excluding physical word transfer and root protocol work. They are not a matched speedup or hardware frame-rate result.

## Reproduction and verdict

```sh
# In the documented native build container:
bash run_contract_tests.sh
# On the host, with the pinned NumPy environment:
/home/lori/gamebub-streaming-prototype/.venv/bin/python audit_native_hud.py
python3 audit_results.py
```

The release and AddressSanitizer/UndefinedBehaviorSanitizer gate runs pass all 457 frames, stale/busy/early-commit/bad-ACK tests, rollback after provisional transfer, reset fences and recovery. The script also freshly builds and invokes the frozen native 32-case HUD directed suite. Source, input and log hashes are retained in `results.json` and checked by `audit_results.py`.

Current Gamebub JPEG firmware/backend is unchanged. Processor placement, mailbox/command transport, exact word DMA, physical write/coherency fences, RTL join and joint bank publication remain explicit integration work. This partition is a tested software semantic endpoint and a commit contract, not a claim of autonomous FPGA CU66/HUD playback.

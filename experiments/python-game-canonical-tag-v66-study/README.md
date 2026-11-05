# Canonical-only cached-tag profiles (v66)

Two isolated, explicitly configured profile candidates remove redundant full-frame fingerprint work while preserving every canonical pixel, coefficient, quantizer, motion vector, HUD word and display from the retained CS38 histories. They use fixed epoch 25 and 720×480 geometry; a live capability-negotiation handshake is not implemented. **Neither profile is implemented in the current JPEG firmware/backend or in a new FPGA decoder.** CS38 remains the unchanged compatibility reference.

| Profile | Inner layout | Canonical fingerprint domain | Full-frame video hash calls/key or P | Wire change |
| --- | --- | --- | ---: | --- |
| Old CS38/GS38 | 76 B inner header | `<HH geometry>` + planar little-endian int16 | 2 key /3 P | reference |
| CS66/GS66 | 60 B inner header | same old domain/tags |1 | remove only 16 B inner pre-normalization output tag |
| CU66/GU66 | 60 B inner header | `<HH geometry>` + validated planar uint8 |1 | same 16 B removal; new reference/output tag domain |

Both retain 128-bit truncated SHA256 canonical/reference fingerprints, all CRCs, IDs, geometry, maps, coefficient data and exact HUD. These are unkeyed matching fingerprints, not authentication or a new SHA-128 algorithm. The pre-normalized values that canonical normalization hides are not part of the new output-fingerprint contract. No dummy tag or fake old packet is inserted into either receiver.

## Actual retained-wire proof

All 577 retained CS38 presentations across eight causal histories were explicitly converted: 24 v38, 96 v39 and 457 v40. They contain 553 distinct original packets; these are not 577 new captures. Each new profile packet is exactly 16 bytes smaller, with identical map/vector/coefficient/HUD body bytes. The removed original `base_tag` is retained only as audit evidence.

Each profile totals 9,664,886 bytes versus 9,674,118 old bytes: 9232 bytes removed, approximately 0.0954%. Canonical i16 references, every decoded array, exact HUD words, displayed RGB565 hashes and future-reference histories match the old receiver. CS66 retains original reference/output tag bytes; CU66 recomputes both base tags in its new declared uint8 domain. Its integer/range/geometry checks run **before** casting, rejecting negative/over 255/float/wrong-geometry samples including large uint64 values. It changes no color depth or coefficient syntax.

The configured receiver accepts exactly one explicit profile. CS38 and cross-profile packets are rejected. The offline conversion helper is an explicit compatibility tool after old43 preflight; there is no automatic fallback or on-device negotiation implementation. A future host/ESP32/FPGA deployment must agree on the new profile and reference-bank contract.

## Verified cache and atomic publication

For a P frame, incoming reference ID/tag is compared with the cached **previously verified** canonical tag beside its published bank. The decoder does not hash the whole input bank again. It parses/validates the frame, reconstructs and normalizes, computes one canonical fingerprint, compares the outer output tag, then validates/copies the HUD. Only after all checks succeed does it publish the new read-only reference, ID, HUD, last ID and immutable cached tag together.

Each new profile has 577 actual observed canonical-hash calls, one per key/P frame. The old total of 1705 full-frame video-tag calls is **calculated** from 26 keys × two calls plus 551 P frames × three calls; directed tests validate that legacy schedule, rather than a legacy call spy running over the full campaign. Per-packet new-profile hash-call spies run on matching-state forks outside timing clocks. The canonical hash call is distinct from unchanged smaller HUD hashes/CRCs; this study does not claim one cryptographic operation for the entire codec.

Wrong/missing references, IDs, output tags, CRCs, late reconstructed-HUD tag failures and replay leave published state/cache unchanged. Returned metadata and mutable copies cannot change the immutable cached-tag bytes. Published array ownership/read-only flags are checked, and key 24 recovery is tested after a deliberately corrupted visible bank changes the canonical output and is rejected.

**Caching is not ECC.** The cache assumes the verified bank stays unchanged under its owner. The independent test also demonstrates a privileged hidden-bank fault that does not change canonical output and can therefore pass the new profile. The old input-bank rehash offered a different runtime fault check. Read-only software flags and matching fingerprints supply no general DDR-integrity or authentication guarantee. Real bank ownership, write drains and hardware memory-fault policy remain integration requirements.

## Explicit SHA round-demand assumptions

A canonical frame contains 518400 valid 8-bit samples. The old/int16 preimage has 1,036,804 bytes including geometry and 16201 padded 64-byte SHA blocks. The packed domain has 518,404 bytes and 8101 padded blocks. With 64 rounds/block and an **assumed** iterative one-round/cycle core at 100 MHz:

| Path | Assumed round cycles | Serial round-demand ms |
| --- | ---: | ---: |
| CS38_key | 2,073,728 | 20.73728 |
| CS38_P | 3,110,592 | 31.10592 |
| CS66_key_or_P | 1,036,864 | 10.36864 |
| CU66_key_or_P | 518,464 | 5.18464 |

Thus a P-frame round demand changes from three old tags to one same-domain tag, or approximately 6× fewer assumed round cycles for one packed-domain tag. Padding blocks are included. Block-load/control, memory ordering, input feed, buffer/port costs, overlap with decode, HUD hashes/CRCs and all other stages are not proved free. This is not an RTL implementation, fit, timing-closure, clock or physical-FPS result. Preimage serialization sizes are not measured DDR traffic; hardware could generate old high zero bytes without reading them twice.

## Whole-receive host timing

Three balanced whole-call rounds per frame rotate CS38/CS66/CU66 so that every path occupies each order position once. Incoming-state forks, old preflight, explicit conversions, hash-call probes, comparisons and archive I/O are outside those clocks. The host was **not isolated**; another research filter workload overlapped part of the campaign and CPU pressure was not measured. Samples remain unchanged, so the small ratios below are descriptive host-workload observations rather than a robust hardware or isolated-CPU speedup.

| Path | Mean per-frame three-sample median ms | Ratio to CS38 |
| --- | ---: | ---: |
| CS38 | 77.03874 | 1.00000 |
| CS66 | 76.13525 | 0.98827 |
| CU66 | 75.93861 | 0.98572 |

The primary result is the exact wire/content/hash-call contract and round-demand model, not an extrapolated FPS. Full Python coefficient/reference/prediction arrays remain. No new encoder implementation, firmware, RF test, hardware decoder or end-to-end streaming deployment is claimed.

## Verification and reproduction

Seven producer tests and eight independent directed tests cover profile boundaries, actual key/P hash calls, strict packed range validation, atomic failures, immutable cache ownership, visible/hidden bank faults and key recovery. Independent full replay verifies 577 old presentations/1154 new-profile receives, 1303 source pins, all original content/future references and tag domains, exact packet repacking, zero entropy re-encoding and the complete timing math. All actual packets, old omitted-tag evidence and paired observations remain archived.

```sh
cd experiments/python-game-canonical-tag-v66-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

All earlier source files and results remain frozen. Negotiation/backend and hardware integration remain future work.

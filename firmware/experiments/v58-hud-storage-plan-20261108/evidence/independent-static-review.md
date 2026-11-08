# V58 native HUD storage review

## Review result

**Static review: PASS, no source blocker found** for the frozen V58 source reviewed below. This is a source review plus inspection of existing offline evidence; I did not run tests, builds, device operations, or hardware.

Frozen `native/hud.hpp` SHA-256 is `be6565d96f6d2b986ac06656142b5e6484982473d496d104a76dabc72a27f656`. The native freeze receipt says only `hud.hpp` changed among native sources and that `HudGate`, allocator cap/reserve, endpoint, and FFI are unchanged. The app-side `handheld/src/cu66/network_driver.rs` SHA-256 is `bd42ce2e050abc5953fce29db4c6ffcb1cedc259d680110f41f69b3d19219f33`.

## Source findings

- `decode_hud` validates the envelope, identity, fixed component rectangles and lengths, allocates four private `Patch` outputs in decode order `{2,3,0,1}`, and reserves exact word capacities for all four before decoding any component. It transfers those same buffers into `_into` decoders; `clear`, `resize`, `assign`, and fills remain within reserved capacity for the reviewed paths. Decoder return wrappers remain available, but production `decode_hud` calls the `_into` versions.
- Production HS33 uses `channel33_emit`; production HS32 uses `huffman_emit`. They share a fixed canonical Huffman table/cursor and borrowed bitstream. The production paths emit symbols directly into the private word plane and do not create event-count or expanded channel-sized vectors. The old return-vector wrappers remain but have no production callers in the reviewed native code.
- Input `View`s only point into the packet for the synchronous `v34_hud_transact` call. The returned candidate owns decoded word vectors; neither `HudCache` nor `HudGate` retains packet views. Accepted patches are read through `const` references. Motion prediction writes to the private `out` plane, and the special HD25 grammar-2 Rice path aliases prediction and destination only within that private plane.
- HD25 grammar-2 equivalence checks out: V57 reconstructed Rice absolute components against the predicted plane, XORed once inside grammar 2, then XORed again in the shared mode-4/5 tail. The two XORs cancel. V58 starts with the predicted private plane and writes those same absolute per-channel results in place; each channel reads its old bits before replacing only that channel. The differential corpus and full-image evidence report exact-word agreement.
- Zeroing/initialization remains defined: independent HS modes assign a zeroed plane; motion modes populate every predicted output word before channel updates; copy mode copies the accepted plane; sparse HD25 residual modes preserve prediction and XOR only validated residuals; raw/RLE/byte-plane and Rice modes initialize or populate every output position before the final size/tag check.
- Remaining decoder scratch is bounded rather than absent: the Huffman cursor is fixed-size stack state; motion fields and per-span words can use small vectors; full-patch decoding retains palette and used-index storage. Existing allocation model evidence reports all four output reservations before component scratch, no late fixed output allocation, maximum observed post-plan allocation 720 bytes, and a 7,168-byte adversarial allocation limit pass.
- `HudGate::prepare` still constructs the decoded words locally and assigns `candidate_` only after decoding and tag verification complete. Failures leave `accepted_` unchanged. Commit remains gated on external write/drain acknowledgement. The driver’s one HU wire vector is cleared and reused across frames; `transact` is synchronous, and the wire capacity remains charged while the candidate is read back and committed. The existing allocation model reports retained wire capacity 14,920 bytes, baseline free 116,072 bytes, reserve 8,192 bytes, and a passing 5,636-byte reserve-headroom check.

## Existing evidence inspected

- `native-freeze.json` binds this `hud.hpp` hash and records output requests `[15360, 11520, 7680, 7680]`, the 8,192-byte reserve, and unchanged allocator/Gate/FFI files.
- `final01/RESULT.json` reports exact native outputs for 12- and 40-frame sequences, 59 mode cases (35 positive, 24 stream cases including 18 rejects), 104 fault checks, 52 recovery checks, and no hardware. The 40-frame model peak is 87,324 bytes under the 98,304-byte cap.
- `allocation01` reports phase-conditioned/adversarial 7,168-byte model checks; `allocation02-retainedwire14920-baseline116072` reports the retained-wire reserve model pass.

These are offline host/model results, not physical ESP32 execution or a general heap-fragmentation guarantee. They do not establish runtime stack margin, performance improvement, or release readiness. Continue with the separately required target-bound qualification and hardware gates; keep V029 quarantined until those gates pass.

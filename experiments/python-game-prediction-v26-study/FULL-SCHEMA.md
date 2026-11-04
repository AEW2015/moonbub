# CP2F / JA2F full-window model

`full_pair_model.py` is an isolated copy of the frozen CP25 laboratory state
machine with its base codec import bound to the GM26 version2 fast adapter,
outer magic changed to `CP2F`, and acknowledgement magic to `JA2F`. The frozen
original files and imported module globals are never modified. HU25 and HD25
remain unchanged. Epoch25 is explicitly used for reuse of the retained actual
HU25 bytes; base and outer epochs are the same25.

The pair header is `<4sBBIIBBII16s16s>`: CP2F, version1, key/publish flags,
uint32 epoch/frame, uint8 source/destination slots, uint32 base/HUD lengths,
16-byte SHA256 prefixes of complete inner base/HUD packets. Append the actual
GM26 and HU25 bytes and uint32 CRC32 of everything before the CRC. Fixed pair
cost is60bytes. The complete packet must be at most49152bytes. GM26, HU25 and
pair identity, geometry, key/reference and output tags are validated together.
A rejected overcap candidate's bytes are retained but never sent to `Receiver`.

JA2F uses `<4sBII16s16s16s>` plus CRC32: magic/version, epoch/frame, digest of
complete pair, reconstructed base tag and reconstructed HUD tag, exactly65B.
The sender validates all fields against the exact selected pair before changing
its reference. Keys0/24 reset base and HUD references independently. Keys publish
to slot0; every nonkey publishes to the other bank. The receiver checks actual
source-bank ID/tag and reconstructed outputs before one modeled publication.
Write-drain/vblank gates are explicit synchronous booleans, not hardware evidence.

`fast_prediction_model.py` copies the frozen model's encode functions and binds
only its own `_rdo_skip` to the v26 exact CP02 bit counter. Packet/output parity
against the frozen slow model is tested; the adapter changes host work, not the
GM26 grammar or RDO decision. Residual entropy stays frozen CP02/SP01.

The full campaign pays a zero and half32 analysis for each nonkey source, using
the same accepted reconstructed reference and current source. Each receives
ROI8/bg16, lambda1; both complete packets and active RGB565 exact-HUD SSEs are
actually constructed. Half32 wins only if it is smaller and its source SSE is
at most the zero candidate's. A key pays only zero. If neither quality-eligible
candidate fits the actual complete cap, both policies retry ROI8/bg32 using the
same prepared analyses. Keys do not run RDO. Every attempt, including failures
and rejected quality candidates, retains base/pair bytes, work, metrics and
verification timing. All representations in each motion-map pack are paid.

Accepted pairs are received, exact HUD words checked against original retained
source, ACK bytes validated, and only then become the next encoder reference.
This source-only comparison is causal. It is not an exhaustive rate-distortion
optimizer and does not guarantee improvement over a separate reference history.
The full summary separately compares aggregate quality/bytes with the frozen
v25 stream. Fixture loading, offline attempt verification, quality scoring,
binding/validation, accepted receive and ACK checks have separate measurements.
Retained original HUD encoding clocks are reused evidence, not remeasured costs.

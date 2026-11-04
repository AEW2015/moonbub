# V23 independent audit checklist

Scope: independently audit the real HD22 joint-dispatch and shared-analysis
implementation against the v22 contracts. This is a Python study audit, not an
endpoint implementation or hardware qualification.

## Integration and state safety

- [x] Joint packets carry actual HD22 bytes under the explicit new versioned
  profile; retained HD21/HC21 and legacy controls still decode. Capability
  negotiation remains open.
- [x] CP23 application framing and the 49,152-byte cap include dispatch/profile
  bytes, bindings and CRCs; transport framing is included in rate arithmetic,
  and the complete JA23 ACK is counted. JA23 jointly
  binds the exact accepted base/HUD pair and cannot confirm either half alone.
- [x] Candidate source ownership lasts through commit/discard; changed inputs
  and source/configuration identities reject reuse. Hash guards do not lock out
  concurrent writers during one synchronous encode.
- [x] The analysis cache is one-entry and leased to guarded source/config
  identity, released on every success/error/reject/discard path, with explicit
  final cleanup. No global monkeypatching or hidden global state.
- [x] Every quantization, entropy, and failed map attempt remains paid and
  visible in stage accounting. Shared prediction/DCT work reflects actual
  forward calls and produces byte-identical plain/shared variants.
- [x] Preparation/rejection/abort/deadline/build exception leaves issued IDs,
  references, cache banks, pending publications and visible state unchanged.
- [x] Private receiver decode and display publication remain atomic; modeled
  private base/HUD/display writes require explicit write-drain and vblank before
  publication. ACK follows publication only.
- [x] Retained prediction/transform arrays are accounted per context and
  differentiated from temporary/staged storage.

## Independent results and claims

- [x] Independently rederive row-byte parity and actual selected mode from
  complete serialized bytes; distinguish actual wire bytes from projections.
- [x] Report complete joint pair size and cap/headroom for every replayed row;
  never treat a passing HUD projection as an actual replay.
- [x] Independently reproduce rate arithmetic and quality/rate tradeoffs using
  actual selected packet bytes and decoded output; compare same source IDs and
  preserve changed-reference-history caveats.
- [x] Retain frozen source pins, packet/ACK identity, output hashes, actual
  forward-call accounting and runnable verifier output.
- [x] Old profiles reject unsupported HD22/HC22/HA22/JA23 dispatches before
  mutating any state; malformed inputs and wrong/mixed ACKs fail closed.

## Evidence boundary

- [x] State that this does not establish Renode, ESP32 native, RF, DMA, RTL,
  physical-memory, panel-vblank, or sustained distinct-source 30-fps behavior.
- [x] Run final frozen `python audit.py --check`, at least six meaningful tests,
  `tests.log`, `audit.json`, and verifier logs only after root requests final
  freeze; retain the resulting evidence in this study directory.

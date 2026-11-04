# V22 independent audit checklist

Scope: independently review the joint base/HUD transaction and gap-span study against the frozen v21 contracts. This Python study is not an endpoint implementation.

## Transaction and ownership

- [ ] Candidate preparation is private: base decode, HUD reconstruction, metadata, and integrity checks cannot mutate visible state or confirmed references.
- [ ] Admission checks the *complete* serialized pair, including bindings, ACK/control bytes, fragmentation, and cap; rejected/oversized/deadline-expired candidates burn no issued frame ID and advance no base or HUD reference.
- [ ] Publish is one atomic base+HUD action for the same epoch/frame/generation, after both validate and all modeled writes complete. No intermediate base-only or HUD-only visible state.
- [ ] ACK is emitted only after successful whole-pair publication. A failed/rejected candidate cannot produce either the base-reference confirmation or HUD-cache confirmation.
- [ ] Retry accepts only byte-identical outstanding packet/identity; stale, conflicting, duplicate, or wrong-generation ACKs cannot commit new state.
- [ ] Reader/scanout leases pin immutable source banks through their full hold interval. A bank cannot be reused while any unique lease remains; duplicate release cannot release another reader; exhaustion/reset fail closed.

## Gates, byte accounting, and results

- [ ] Every claimed deadline is computed from actual stored packet sizes and configured forward/reverse service rates, feedback delay, control/fragment overhead, and decode/write service. Identify excluded costs; do not turn a network-only pass into an FPS claim.
- [ ] Compare the whole accounted pair against the 49,152-byte cap, including every binding/header/CRC/control byte charged by the selected profile. Report rejected candidates and headroom.
- [ ] Independently recompute both study results from source pins and actual serialized packet decodes. Check output identity and exact reconstruction, not encoder intent alone.
- [ ] Base-quality comparison reports bytes *and* decoded quality/error against both current references and frozen v21. Any higher-quality or changed-prediction base output is a quality tradeoff, not a free gap-packing gain.
- [ ] Label the fixed v20 profile run as a stored chosen-map-trace control: it replays map choices and omits v20 controller search, so it is a bytes/image control rather than a fair timing or deployable causal policy baseline.
- [ ] Gap-span savings use complete serialized bytes and complete comparable base+HUD pairs; count metadata, padding, outer framing, bindings, and any base-quality change. Report net savings (or regression) per window and aggregate.
- [ ] Preserve source IDs/pins, packet bytes or reproducible hashes, decoder results, and derivation scripts so each table can be independently reproduced.

## Prototype limits

- [ ] State explicitly: no DMA completion implementation, no ESP32/SRAM/QSPI/RF behavior, no RTL or FPGA resource/timing proof, and no measured end-to-end 30-fps result.
- [ ] Fresh live gameplay, native endpoint port, reset negotiation/recovery, and physical deadline measurements remain open gates where applicable.

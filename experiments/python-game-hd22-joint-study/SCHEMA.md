# HC22/HA22/CP23/JA23 laboratory contract

The experiment implements real version1 profile bytes, not negotiated endpoint
support. Fields are little-endian unless the inherited nested codec explicitly
specifies otherwise. Never reinterpret a packed native C structure as these bytes.

| Envelope | Fixed struct | Complete fixed bytes |
| --- | --- | ---: |
| HC22 | `<4sBIIIBBII16s16s4I4B` +CRC32 |83 |
| HA22 | `<4sBIIIB16s16s` +CRC32 |54 |
| CP23 | `<4sBIIII16s16s` +components+CRC32 |57 |
| JA23 | `<4sBII16sHH` +AF03+HA22+CRC32 |134 total |

HC22 requires all four declared regions; each patch dispatch is LEGACY0 or
HD22 DELTA1. HD22 RAW/COPY/SPAN_XOR are internal mode0/1/2 and preserve exact
uint16 RGB565 words. RAW/COPY/span geometry/content/CRC bounds are enforced by
the frozen HD22 decoder. A DELTA1 body with HD21 magic rejects.

`parse` validates framing/identity, `Receiver.receive` validates exact references
and all decoded pixels before whole-HUD publication. CP23 binds component digests
and exact epoch/frame; the joint receiver additionally requires720×480 base
geometry before reconstruction. JA23 binds the complete pair digest, AF03 content
identity and HA22 exact outstanding cache identity. No single component ACK can
advance only one live sender state.

Candidates are local exact-object handles, not serialized protocol messages.
`Candidate.info` records actual HUD preparation, map/build/discard attempts,
complete sizes, selected map, state snapshots and paid Python service. Optional
`source_analysis` reflects the injected encoder's completed source-context metrics.
They do not imply target CPU cycles or hardware service. Receive-candidate
`display`/`planes` are private diagnostic arrays until explicit write/vblank gates
permit logical joint publication.

Epoch reset is currently a local drained-state operation. Profile negotiation,
transport authentication, reset/rekey messages, packet/frame gateway ownership
and native peers require separate implementation and validation. Root campaign
results and source/object manifests define their own retained evidence schema.

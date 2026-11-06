# Metadata payload capture family

Frozen production candidate: `cu71_receiver_metapayload_v002.sv`, SHA
`2769de13b89f25e7c0937891966fb01a05ea419ee7615585dedaf770defc5b5b`.
This extends the separately sealed HUD-only variant, with only the reset+META
payloads: HUD tag128, canonical tag128, HUD offset16 and length16 (288bits).
Their original data and synchronous reset values remain. The exact proven
meta_fire&&!fatal_non_hud enable removes their current HUD-tag-to-CE dependency.

Actual owner temporal induction proves the reachable metadata invariant and all
288bits against an original-global-guard shadow every edge after actual reset.
Initial owner state is arbitrary;88 child outputs and64 original inputs remain
unconstrained. No state/zero-data initialization assumption substitutes for reset.
Global fatal/error priority, event producer, event ring and full diagnostic suffix
are byte-identical to actual selected7991bfc5... parent. Native selected validpipe
KEY/P/P, actual HUD/canonical/pixel checks and control failure/abort/firstfault
traces (including144word DIAG and expected tag snapshots) are byte-identical to
the frozen parent, with zero underruns. No event-ring implementation was changed.

Generic optimized CE inspection reports zero current HUD-tag bits in enables of
all four moved fields. **fid/rid/key/parsed_at remain unchanged** because they also
have accepted-start writes: each still has128 HUD-tag bits in its old generic CE
cone. This variant does not claim every metadata false dependency or the true
fatal-to-event path is removed. Any further split must preserve those priorities.
No device timing, physical CDC, SDK/SPI, network, BIT or hardware claim is made.

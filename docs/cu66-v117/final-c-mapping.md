# Final C native mapping review

**Both completed C component runs miss setup timing:125MHz WNS−1.679ns;100MHz WNS−0.317ns.** Hold and pulse checks pass and both designs route completely with zero routing errors. These are completed component measurements, not clock closure or hardware qualification.

The first finite review preserved stage observations through13:47:44UTC. This one-shot terminal update reads the retained reports after both jobs complete; it starts no tool jobs and changes no source, constraints or physical method. Machine evidence is [final-c-mapping-observations.json](../../experiments/python-gamebub-v117/audit/final-c-mapping-observations.json), containing unchanged stage hashes and final receipt/report pins.

## Completed runs

| Clock | Actual receipt | Setup WNS | Setup failing paths | Hold WNS | Pulse WNS | Routing errors |
|---|---|---:|---:|---:|---:|---:|
| 125MHz | [20261109T132139123840Z](../../experiments/python-gamebub-v117/repair-study/native/20261109T132139123840Z/receipt.json) | -1.679ns | 17,428 | +0.039ns | +2.750ns | 0 |
| 100MHz | [20261109T132645224285Z](../../experiments/python-gamebub-v117/repair-study/native/20261109T132645224285Z/receipt.json) | -0.317ns | 324 | +0.085ns | +3.750ns | 0 |

Both receipts are `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Their selected source contracts use ingressG2 SHA27800275… and reconstructionwordbank SHA6bef0bea…, with separately loaded8ns/10ns clocks under the fixed part/method. Every retained artifact hash was rechecked for this review. Functional main/peer/LIVE success remains separate from native timing.

## Actual stage results

| Clock | Stage | WNS ns | Worst path |
|---|---|---:|---|
| 125MHz | synth | -1.729 | `coefficients/child/packet_decoder/synchronous.ingress/raw_position_reg[5]/C` → `coefficients/child/scratch/assembly_bytes_reg[1]/CE` |
| 125MHz | place | -1.694 | `coefficients/selected_offset_reg[1]/C` → `coefficients/fault_o_reg/D` |
| 125MHz | route | -1.679 | `coefficients/child/scratch/read_band_reg[1]_rep__0/C` → `coefficients/child/scratch/state_reg[2]_rep__1/D` |
| 100MHz | synth | +0.271 | `coefficients/child/packet_decoder/synchronous.ingress/raw_position_reg[5]/C` → `coefficients/child/scratch/assembly_bytes_reg[1]/CE` |
| 100MHz | place | -0.102 | `base_kill_authorized_reg/C` → `coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/available_reg[4]/CE` |
| 100MHz | route | -0.317 | `transform/result_head_reg_rep__5/C` → `reconstruction/residual_reg[456]/CE` |

The positive100MHz synthesis estimate did not survive placement/routing. No stage is substituted for the final routed result.

## Mapped bank enables and residual writes

All six synthesis/place/route fanin reports show each canonical payload bank's CE starts only at its corresponding `storage_copy_bank0_reg/C` or `storage_copy_bank1_reg/C`; payload reset is constant0. The routed high-fanout report identifies each512-load CE driver as FDRE. B125 instead used LUT5-driven state/tail decoding. This intended mapping change is verified, but it does not ensure a short routed wire.

| Routed composition | Bank0 CE slack / net delay | Bank1 CE slack / net delay | Driver |
|---|---|---|---|
| B125 | −0.742ns /5.589ns | −0.235ns /4.852ns | LUT5 |
| C125 | −0.976ns /8.231ns | +0.636ns /6.619ns | FDRE |
| C100 | +1.564ns /7.691ns | +1.503ns /7.788ns | FDRE |

C125 bank0 still fails because of routing, despite its local registered enable. It would be incorrect to claim both banks improved. These are whole-composition placements, not isolated causal measurements of the CE edit.

The old B residual CARRY4 net with fanout2152 is absent from all C top50 high-fanout reports; no reconstruction CARRY4 high-fanout row remains in those lists. That supports the constant-word insertion hypothesis while remaining bounded-report evidence, not an exhaustive netlist/cone proof. Reset/reference bulk clears were deliberately retained. Their remaining routed negatives at125MHz include reconstruction reference-pixel CE−1.001ns and reset control−0.542ns.

## Actual remaining critical paths

C125's worst routed path is scratch read_band→scratch replicated state through cursor/head selection, tile-event validity, bank_ready and busy_owned/state control:13levels,4CARRY4,9.555ns data, comprising2.464ns logic and7.091ns routing (74.2%). The source net has fanout66, the next cursor-select net171, and one carry-result wire contributes1.507ns. The following selected_offset→coefficient fault-status path is−1.509ns. Routed top50 destinations are27admission,13other/status,6ingress and4scratch; the old descriptor ceil→metadata CE family is no longer the reported dominant family. Overall WNS is0.523ns better than B125's−2.202ns but still negative.

C100's worst routed path is inverse result_head→reconstruction residual-word CE:9levels,3CARRY4,10.028ns data, comprising2.750ns logic and7.278ns routing (72.6%). The result-head source fanout153 costs1.947ns routing, followed by a selected residual-owner metadata/validation/fault cone, a fanout64 control and final24-bit word CE. All50 worst routed C100 paths terminate in reconstruction. Constant word addressing removed the old wide-insert fanout structure, but the accepted tuple's validation/kill logic still feeds payload CE.

The C125 path and C100 path are different problems. No further V117 source composition or reroute is proposed. B100 is a separate Root-managed existing-composition control and is outside this C review.

## Limits and next architecture work

See [next-timing-steps.md](next-timing-steps.md) for bounded future hypotheses tied to these actual paths. Neither current clock closes. A cycle count converted at125MHz remains conditional when125MHz setup fails;100MHz timing is also not qualified here. Full-parent routing, physical SDRAM/ESP32 behavior, sustained hardware30fps and validated under-10-ms decoding remain open. The observations do not justify dropping ownership, first-fault priority, accepted reference debt, canonical byte goldens or reset/cancel coverage.

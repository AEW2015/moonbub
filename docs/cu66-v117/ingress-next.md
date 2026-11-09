# V117 ingress extents: mapping hypothesis and remaining gates

This is a read-only explanation of the prepared ingress source, not a simulation result, mapped-netlist observation or achieved-clock prediction. It changes no frozen focus input. The production candidate is [br88_packet_ingress_sync_v91h.sv](../../fpga/experiments/cu66-v117-ingress/br88_packet_ingress_sync_v91h.sv), SHA256 `abfcef202b0c6792c89a45723bf0916c33c3ed7259ad756a59c120d03b7f6882`. The [qualification contract](ingress.md) remains the pinned preparation document.

## Actual A125 cause

The [A125 routed report](../../experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/reports/route-setup-paths.rpt) measures ingress `size_bytes[1]` → `offsets[0][0]/CE`: WNS −1.925 ns, 16 logic levels with eight CARRY4, 9.636 ns data delay, 60.148% routing. The mapped path passes through cursor/descriptor qualification before the shared descriptor commit enable. That is different from the earlier V116 scratch selected-AC path and the separate admission q-index family.

The source's DESCRIPTOR state depends on size in three places: `cursor>size_bytes-4`, `active_length>size_bytes-4-cursor`, and `descriptor_bits>8*(size_bytes-46)`. A shared synthesized gate can make one of these length/ownership conditions reach offset, size or state enables. An instance's mapped cursor name alone does not identify an independent cursor arithmetic operation; use the actual source expressions and whole path.

## Intended register boundaries

| Existing interval | New private result | Work remaining at original DESCRIPTOR edge |
| --- | --- | --- |
| Prior packet-owner clocks | `packet_payload_end=size_bytes-4` | No size-minus-four subtraction in descriptor bound logic |
| Prior packet-owner clocks | `packet_bit_limit=8*(size_bytes-46)` | Compare original descriptor bits with held full32 limit |
| SELECT_BAND | `active_remaining=packet_payload_end-cursor` and `active_cursor_bad=(cursor>packet_payload_end)` | Original short-length test, held bad flag and unsigned comparison `active_length>active_remaining` |
| SELECT_BAND | `active_length_minus6=lengths[band]-6` | Compare original ceil-byte count with held full32 expected bytes |

The first two registers are continuously updated from retained internal size_bytes, with no reset or global enable. They are not a combinational shortcut from an unconstrained external packet_bytes port. SELECT_BAND still has its original controller eligibility and takes one existing clock; the original active descriptor fields and new extents become coherent together. Ready DESCRIPTOR is reached only after the same physical read sequence as before.

Nominal added payload is 129 bits: two 32-bit packet results, two 32-bit selected descriptor results and one flag. The low three packet-bit-limit bits are mathematically zero, so the physical register inventory may shrink. Neither this count nor source-level absence of reset predicts mapped FF types or control sets. Verification-only ownership certificates are removed under synthesis and must not be counted as hardware pipeline capacity.

The intended timing change is decomposition: size-to-packet-extent arithmetic, packet-extent/cursor-to-selected-extent arithmetic, and selected-extent comparison/commit qualification are distinct registered paths. The current source does not remove the descriptor-ready, k/count/padding, failure or cancellation gates. It does not delay offsets, busy/status or errors. It also leaves descriptor byte-ceil arithmetic on the original cached descriptor bits. That retained expression, a selected-extent D path or another global control cone can become the next worst path.

## What a native result must establish

A source diagram does not establish a technology-mapped pipeline. After the exact combined source's focused/full/peer/LIVE proofs pass, inspect a newly eligible native run for:

- The actual packet_payload_end, packet_bit_limit, active_remaining, active_length_minus6 and active_cursor_bad registers and their D/CE/R connections. Confirm that their owner clocks and enables match the source; do not infer “all reset pins tied off” from unreset RTL.
- Whether the old direct size arithmetic still reaches descriptor commit enables or moved elsewhere. size_bytes still legitimately feeds RECEIVE, HEADER and staging bounds; not every size-based path is removed.
- Whether a full32 subtractor now ends at a payload D input instead of a late shared commit CE, and whether selected-extent comparisons, descriptor byte-ceil or other branches dominate. Measure actual logic levels and routing fraction rather than assuming a fixed number of carry primitives.
- Actual A/B/C setup/hold/pulse/internal-clock coverage, route completion and resource use under the same part, clock and implementation recipe. Any observed change belongs to the whole mapped composition, not an isolated-cell attribution.

Read-only report observation patterns for these new register names may be added to a separately frozen C reporting recipe before dispatch. They must not add KEEP, DONT_TOUCH, fanout, retiming, placement or timing-exception directives. If the bounded report omits a name, that does not prove the register was optimized away; check the scope and control-set inventory first.

## Functional conditions that cannot be traded for slack

The packet tuple must mature for the current retained size/epoch before SELECT_BAND; the selected remaining/length tuple must name the current band and cursor before each actual DESCRIPTOR consume. The new certificates compare literal old expressions there, retaining all uint32 wrap semantics. The original full34-bit HEADER length sum, high-byte forwarding, CRC-first rejection, physical response ownership and context prevalidation assertions remain unchanged.

The direct synthetic boundary tests mature the new data through real predecessor clocks, then independently check initial fetch eligibility, request/last address, completed descriptor errors, all four offset/size/k arrays and wrapped cursor commits. They do not force new private registers or claim arbitrary corrupt states are valid packets. Actual packet and caller suites retain complete physical retries, all public counter/debug/invalid-output comparisons and the old assertions. Any setup fix that delays ownership retirement, disables a comparison or changes which malformed branch wins fails this contract.

No cycle saving or 125 MHz improvement is credited here. The source preserves the parser's schedule. The separately measured inverse/reconstruction latency work and full-parent physical memory/CDC/display/ESP32 milestones remain independent, even if this descriptor timing hypothesis succeeds.

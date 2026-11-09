# Dormant V118 replay-owner hypothesis

This source is prepared, not tested or integrated. The integrated candidate continues using frozen V110 coefficient control. No native dispatch may consume this dormant source until separately qualified.

V117 C125 retained `selected_offset` to `fault_o`, nine carry primitives, 9.454ns data path and −1.509ns slack. Actual native top fixes REFILL_OVERLAP=1, but exposed FSM logic still retains the mode0 REFILL_WAIT arithmetic comparison. Removing that branch outright would discard an existing mode and private state contract.

The proposal captures the actual accepted physical replay request's full32-bit address and frame epoch, then compares REFILL_WAIT responses to these immutable tags. It retains all old assertions and adds a mode0 certificate that the accepted address/epoch equal the original stable offset+cursor/epoch owner. Admission bounds, queue address span/wrap checks, response fault priority and mode selection remain literal. The capture adds64 payload bits and no intended public edge or extra response lease.

Before integration: strict both-mode whole-caller comparison, unsolicited/wrong-address/wrong-epoch/matching responses, accepted-request hold, cancel/reset and retry, queue push+issue on the same edge, exact last-byte ownership, original complete component/peer/LIVE qualification. Explicitly deposited REFILL_WAIT contexts must declare the accepted request owner rather than initialize a response from a later cursor. No per-eval testbench refresh is permitted. Preserve raw failures and count these tests as RTL only after actual simulator execution.

A fresh fixed-method route must establish any timing improvement. The accepted lease cannot be called faster merely because the source no longer spells the old sum in its response comparison.

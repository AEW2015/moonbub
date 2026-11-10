# V128: complete tuple validation and owned header padding

V128 carries forward the open V127 timing exit before the dependent streaming
qualification. The source baseline is commit
`c196ad83e4c077bb50f9706058fb6416425d4fc5`. V127 passes functional qualification
but fails 125 MHz at −1.193 ns WNS, −1,762.554 ns TNS and 6,980 setup endpoints.
This plan selects two measured control-cone changes before the first V128 RTL
freeze. A version number does not close the clock or hardware gates.

## Measured targets and source changes

The routed worst path starts at ingress RAW mode and reaches scratch state:
9.140 ns data, including 6.611 ns routing, with 11 logic levels. A bounded
read-only leaf trace confirms that the last carry output has exactly 97 timing
startpoints: 32 RAW epoch bits, 32 context epoch bits, 32 scratch epoch bits and
the RAW selector. The preceding epoch-mux LUT has INIT `8'hB8` and three timing
startpoints. This supports a concrete selection-before-validation dependency.

The second global path starts at admission header byte124 bit0 and reaches a
tile register's synchronous R pin at −1.165 ns. Reserved header bytes116–127
feed a 96-bit padding reduction in the ordered acceptance/error chain.

1. **Complete validation before selection.** Export direct RAW and context
   `{epoch32, block16, index6, signed_value16, band2}` tuples through synchronous
   ingress and its wrapper/child. Scratch evaluates both complete validation
   lanes across all eight phase encodings, then selects a Boolean. The ingress
   selector remains distinct from scratch's stored format mode. Original selected
   payload/debug views, full-width casts, arbitrary rank-mask behavior, epoch
   error2 before format error3 and all old assertions remain.
2. **Incremental padding on existing byte edges.** One unreset Boolean payload
   starts with current byte116 and accumulates zero tests through current byte127.
   HEADER_CHECK consumes it after the complete owned sequence. Verification-only
   ownership tracks epoch, packet size and byte sequence; these monitors must
   disappear in synthesis. The last byte is forwarded from the writer input,
   rather than reading the previous value of header127. No old reset is removed,
   no public cycle is added and the entire ordered rejection chain remains.

The final [selected composition](../../fpga/experiments/cu66-v128-raw/selected-composition.json)
merges five changed aliases into the same eighteen-origin core, leaving thirteen
origins byte-identical. The raw-only four-origin recipe and its earlier selection
remain an immutable component record. Padding has its own one-origin recipe.
The complete parent keeps its twenty-four-entry source order. The combined
candidate adds one logical production payload bit and no synthesis attribute.
Physical replication, trimming and resource counts must be measured separately.

## Verification before implementation

The [verification design](verification-options.md) separates inherited evidence
from current source execution. The finite Python raw-tuple model is algebra
evidence only. New source-extracted and paired-controller RTL must exercise the
actual selected formulas, full tags, invalid/unready views, both selectors and
formats, signed boundaries, full8 phase domain and arbitrary/coherent rank masks.
Prepared combinational domains must not be called naturally reachable packets.

The paired real scratch test must retain original assertions, exact public and
private views, actual request/ACK ownership, same-edge faults, cancellation,
wrong-response handling and clean retry. Padding must be primed through its
actual writer, including every nonzero padding position, the final byte, canceled
prefixes and a fresh subsequent header. Directly setting header memory cannot
stand in for executing its new cache writer.

Freeze sources, recipes, verification fixtures, commands, seeds and independent
auditors before official execution. Rebuild strict standalone Verilator 5.020
models with assertions and fatal warnings, and use strict C++ warnings. Preserve
every failure and any source-bound repair with fresh affected builds.

After focused qualification, run fresh complete decoder and actual V97 transport,
peer fault injection and byte/row ordinary/stalled parents. Require four spatial,
two peer and four parent raw stream sets to equal frozen V127 exactly, including
canonical data, events, keys, first errors, physical debt, HUD/hash/seal/commit and
public cycles. The full independent audit must bind all five current origins and
the complete source/command/artifact closure before native dispatch.

## Physical acceptance

Keep xc7a100tcsg324-1, Vivado 2026.1/build6511674 and the byte-identical V120
implementation core. Load the same 8 ns clock before fresh RTL synthesis;
retain synthesis Default, opt Default, place ExtraNetDelay_high and route Default.
No prior-checkpoint implementation start, guessed I/O delays, new timing
exceptions, clock relaxation, separate phys-opt pass or warning waiver supplies
a pass. Internal placement optimization remains part of the fixed command.

Measure global setup, hold, pulse, internal constraint coverage, routing errors,
fresh methodology, resources/control sets and all retained path families. The
extended read-only query keeps the V127 families and adds epoch sources and a
bounded exact-cell trace. Missing names and trace caps remain gaps. A positive
local path does not qualify global timing. A positive global source needs a
second fresh identical-source/tool/recipe pass; do not reroute an unchanged
negative source to seek a favorable placement.

At most two heavy jobs run, each limited to two CPUs, compiler job1, 8 GiB RAM
and 8 GiB total RAM plus swap, 2,048 PIDs and finite watchdogs. Use available RAM,
memory-pressure PSI and combined use under the [frozen policy](../../experiments/python-gamebub-v128/study-policy.json).
Do not stop unrelated work or change swap.

## Product goals remain separate

The retained row fixtures use 1,145,104 / 1,553,197 last-input-to-commit cycles.
At an assumed complete-parent 125 MHz these are 9.160832 / 12.425576 ms; the
stalled profile still needs at least 303,198 fewer cycles for strictly under10ms.
V128's selected edits preserve cycles. Native component timing, complete-parent
routing/CDC, calibrated physical memory and ESP32 CPU/Wi-Fi/QSPI, actual custom
host/client negotiation, sustained 720×480 at30 distinct displayed frames/s and
validated hardware packet-complete-to-publication decoding below10ms require
their own evidence. Source B100 remains the unchanged hardware-integration control.

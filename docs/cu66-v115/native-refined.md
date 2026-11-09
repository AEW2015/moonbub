# V115 refined native terminal audit

Both refined component runs completed routing and remain **signoff open** because
both miss their setup targets. Hold, pulse-width, and routing checks pass. The
read-only audit and complete hash ledger are in
[refined-native-terminal.json](../../experiments/python-gamebub-v115/audit/refined-native-terminal.json).
It rehashed both receipts, all report/artifact copies, each 18-alias current
source and saved snapshot, plus the launch cards and tooling. No flow was rerun.

| Target | Setup | Worst routed path | Hold | Pulse width | Routing errors |
| --- | --- | --- | --- | --- | --- |
| 100 MHz / 10 ns | WNS −0.777 ns; 1,077 / 98,145 endpoints fail | `owner_sequence_reg[0]/C` → `coefficients/producer_cell_cache_reg[5]/CE` | 0 / 98,145 fail | 0 / 41,830 fail | 0 |
| 125 MHz / 8 ns | WNS −3.228 ns; 33,633 / 97,240 endpoints fail | `owner_sequence_reg[4]/C` → `synchronous.ingress/.../parser/cached_remaining_reg[0]/CE` | 0 / 97,240 fail | 0 / 41,589 fail | 0 |

The routed top-50 destination groups sharpen the next RTL focus. At 100 MHz,
22 paths end in scratch/tile logic, nine in ingress control, five in
admission/cache/storage, four in counters/control, and ten elsewhere. At
125 MHz, 39 end in the ingress parser, five in admission/cache/storage, four
in counters/control, one in other ingress logic, and one in scratch/tile logic.
`owner_sequence` is the source for 39 of the 100 MHz paths and 44 of the 125 MHz
paths; it is not a destination in either report. The 125 MHz critical path
shows parser cached-length enable as the routed endpoint.

Both runs use the same 18 source aliases and hashes, immutable saved snapshots,
source-pinned launch cards, refined policy, report-only flow, and tool image.
The clock was loaded before synthesis, the recipe was unchanged, and each run
used two CPUs with 8 GiB memory and swap limits. Both have zero unconstrained
internal endpoints, but `check_timing` reports 1,101 inputs and 12,887 outputs
without I/O delay. Neither run generated a bitstream or contacted hardware.
These are component-route results, not board timing signoff or full-parent
qualification.

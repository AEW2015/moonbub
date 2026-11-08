# Isolated CDC fabric physical screen

The isolated unit **completed routing with positive constrained timing; CDC/reset/parent signoff remains open**. This is an **isolated experimental unit** screen, separate from [behavioral channel proof](cdc.md) and actual board integration. The prepared top is `v107_cdc_fabric` targeting `xc7a100tcsg324-1`. The three RTL files exactly match the selected strict behavioral PASS. Synthetic unit periods are transport 5 ns, decoder 10 ns, memory 10 ns and display 16.667 ns. These clocks are explicit test constraints, not a board-frequency relationship, PLL/MMCM change, real parent I/O contract or hardware claim.

[Runner](../../scripts/cu66-v107/cdc_native.py) prepares an immutable source/recipe snapshot and separate external build directory. [Native results](../../experiments/python-gamebub-v107/cdc-native/results.json) records the latest executed attempt when available; each attempt retains its own receipt and reports. The initial prepared snapshot is `experiments/python-gamebub-v107/cdc-native/20261108T034324756018Z`. A prepared manifest is not a run or PASS.

The flow uses Vivado 2026.1 from the legitimate existing tool installation and read-only license, with an owned 8-GiB / two-CPU container, two tool threads and a 1,200-second tool timeout. Launch requires 8 GiB available RAM and PSI full avg10 below 1; monitoring stops the owned container if available RAM falls below 4 GiB or PSI full avg10 reaches 5. Swap use alone does not fail the gate. No hardware is contacted and no bitstream is generated.

Clock constraints are read before OOC synthesis, with rebuilt hierarchy and Default synthesis/opt/place/route. After synthesis, the frozen `v107_constrain_fifo` procedure must match all ten four-bit Gray launch/first-stage bundles and ten peer-up first-stage endpoints; missing or merged endpoints fail the attempt. It queries real mapped launch clocks and validates supplied Gray bounds against their periods. Exact endpoint lists survive a failed match. No blanket asynchronous clock groups or functional false paths are added. No HD.CLK_SRC is guessed. Reset recovery/removal, unconstrained external ports and complete-parent relationships remain visible review obligations.

At synthesis, placement and route, the flow retains timing/setup/hold, clocks/interaction, CDC details, bus skew, exceptions/coverage/ignored exceptions, check_timing, methodology/DRC, RAM recognition and synchronizer attributes. It reports each Gray first-stage bundle independently to expose masked constraints. Route status, effective timing XDC and checkpoint hashes survive a completed run; large checkpoints remain in the external build with recorded hashes. A terminal route marker and zero tool exit mean the unit flow completed, not complete CDC/board signoff. Review timing failures, every CDC finding, bus-skew constraints, exceptions coverage and reset paths before selecting the unit for any further integration.

The report commands follow AMD's [report_bus_skew](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_bus_skew) and [constraints coverage](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/Reviewing-Constraints-Coverage) documentation. The [asynchronous-signal](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/Constraining-Asynchronous-Signals) and [bus-skew](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/About-Bus-Skew-Constraints) guidance governs the narrow first-stage constraints. Broad clock groups can override max-delay constraints and must not be used to hide the Gray transport paths.

Reproduce preparation with `python3 scripts/cu66-v107/cdc_native.py`; execute the resulting prepared directory with `python3 scripts/cu66-v107/cdc_native.py --run <prepared-directory>` after obtaining a shared heavy-job slot. If the original strict constraint template does not match a mapped optimization, retain that failure unchanged and create a new candidate constraint file and new attempt. Historical source/receipt bytes remain frozen.

The original template failed on actual mapped names because synthesis merges a Gray MSB with its binary pointer MSB. The first separate mapped-driver candidate correctly discovered the four actual bit sources but used raw Q pins as timing startpoints, producing path segmentation and an invalid false-path command. Both failed attempts remain unchanged. AMD explicitly recommends valid sequential clock pins with datapath-only max delay in its [path-segmentation guidance](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/Path-Segmentation). The repaired candidate uses those exact C pins; it does not relax a requirement or change RTL. Equivalent peer-up registers shared by synthesis are accepted only after their actual driver and source clock are checked.

The mapped-checked recipe adds executable per-stage checks using [timing-path properties](https://docs.amd.com/r/en-US/ug912-vivado-properties/TIMING_PATH): exactly four paths per Gray bundle, all four first-stage destinations, valid exact launch C pins, requirement equal to the launch-period budget, and a nonempty timing exception. These checks, per-bit mapping and exception ignored/coverage reports provide evidence that bounds apply. They do not replace reading route timing, skew, CDC, recovery/removal and methodology findings.

One attempted launch was immediately cancelled on a parent heavy-slot HOLD. Its exit143 receipt is retained with `coordination-stop.json`; it is a scheduling cancellation, not a design, functional or constraint verdict.

## Completed unit result

The [independent portable audit](../../experiments/python-gamebub-v107/cdc-native/native-audit.json) is `PASS_EVIDENCE_WITH_OPEN_CDC_AND_RESET_FINDINGS`. It verifies frozen snapshots and retained receipt/report hashes, parses actual vendor metrics, checks every Gray timing-path exception/requirement and reads exception coverage/ignored reports. Re-run it without Vivado using `python3 experiments/python-gamebub-v107/cdc-native/audit_native.py`. The completed receipt is [035519430556Z](../../experiments/python-gamebub-v107/cdc-native/20261108T035519430556Z/receipt.json).

| Routed unit measurement | Result |
| --- | --- |
| WNS / TNS / failing setup endpoints | +2.025 ns / 0 / 0 |
| WHS / THS / failing hold endpoints | +0.097 ns / 0 / 0 |
| Pulse-width slack / total violation / failing endpoints | +2.000 ns / 0 / 0 |
| Gray max-delay bounds actually applied | All 40 bits; 10 bundles, at synth/place/route; worst routed slack +3.704 ns |
| Bus skew | 10 constraints; worst slack +4.178 ns; largest actual skew 1.149 ns |
| Exception coverage | 10 Gray bounds and 10 peer-up first stages; all source/destination coverage 100%; zero ignored exceptions |
| Routing | 240/240 routable nets; zero routing errors |
| Internal clock/timing coverage | No missing clocks, unconstrained internal endpoints, multiple-clock endpoints or loops |
| Resources | 91 LUT, 196 FF, 3 RAMB36, 4 RAMB18, no DSP |
| Synchronizers | 112 mapped flops retain ASYNC_REG |
| External unit interfaces | 279 missing input-delay and 279 missing output-delay checks; parent timing remains open |

| Attempt (UTC) | Outcome |
| --- | --- |
| 20261108T034324756018Z | Original strict source-name count fails after Gray MSB merge; exact first stages and synthesis checkpoint retained. |
| 20261108T035240511464Z | Actual driver discovery works; raw Q startpoints cause path segmentation / invalid false-path command. Rejected and retained. |
| 20261108T035406829886Z | Stopped immediately on shared-slot HOLD, exit143; no technical verdict. |
| 20261108T035519430556Z | Mapped C-pin repair completes Default synthesis/opt/place/route, exit0; no segmentation or ignored exception. Open CDC/reset findings retained. |

The frozen working recipe is [mapped-checked](../../fpga/experiments/cu66-v107-cdc-flow/mapped-checked/constraints.tcl). Reproduce by preparing with `--constraint-file fpga/experiments/cu66-v107-cdc-flow/mapped-checked/constraints.tcl --flow-directory fpga/experiments/cu66-v107-cdc-flow/mapped-checked`, then run the resulting prepared directory after a shared heavy-job slot is available. The default original template remains historical rejected evidence.

## Findings that prevent CDC/reset signoff

`report_cdc` reports 7 CDC-3 informational crossings, **10 CDC-6 Gray-bus warnings and 8 critical CDC-11 fanout findings**. Mapped driver evidence shows three startup-up sources shared across multiple same-destination synchronizer chains: `writes/rup_reg` (memory -> decoder/display), `commands/rup_reg` (decoder -> memory), and `lines/wup_reg` (display -> memory). Each up flag is reset to zero and becomes constant one on the first post-reset local edge. In this fabric, synchronized copies gate separate FIFO ready/fetch operations; no logic combines the different channel-up copies. The report therefore points to startup/reset fanout, rather than a changing multibit data payload. This scoped review does not prove a real parent's reset ownership/reconvergence contract or justify a waiver. A future variant can share one synchronizer per source/destination pair or explicitly preserve channel-local up logic, then repeat behavior and physical checks; an attribute added solely to clear a report is insufficient qualification.

Methodology retains LUTAR-1 (one ORed asynchronous-reset source), SYNTH-4/6 (seven each, shallow BRAM / BRAM timing advisory), and TIMING-18 (558). DRC additionally retains **REQP-1839/1840**: asynchronously reset address/control registers driving RAMB36/RAMB18 can corrupt reads or memory around reset and are not fully covered by default timing analysis. Each rule hits the report cap at 20 displayed findings, with CHECK-3 warnings; those are lower bounds, not complete counts. The behavioral ownership/flush argument does not establish primitive reset/collision behavior. A technology-qualified reset/enable/address sequence or separately validated FIFO implementation is needed before parent use. CFGBVS-1 remains open because no board configuration voltage is invented for this unit.

Normal constrained local reset recovery/removal paths are present in the min/max timing summary, but asynchronous raw reset input transitions, OR hazards, pulse width and BRAM reset/control effects remain outside that proof. No warning was waived, no broad false path was added and no clock was relaxed. The next work is a separate reset/peer-up architecture variant with actual primitive and parent-owner evidence, followed by the complete-parent closure sequence in [CDC integration](cdc.md).

# Synchronous BRAM control prototype

**Behavioral tests and the routed unit remove the targeted BRAM-control and peer-up fanout findings; complete-parent qualification remains open.** This is a separate experimental repair for the [isolated CDC unit's](cdc-native.md) actual REQP-1839/1840 BRAM-control warnings and CDC-11 merged up-flag fanout. Original fabric RTL, receipts, traces and constraints remain unchanged. The new prototype is not a production parent integration or hardware qualification.

The actual 7-series DRC describes asynchronously reset registers feeding BRAM address/control pins: reset assertion can disturb memory/read values outside normal clock timing. AMD's [7-series memory guide UG473](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content) requires the address setup/hold window whenever the RAM port is enabled, including cycles without a write. Masking only WE therefore does not resolve the address/EN hazard. This prototype isolates the entire RAM control cone behind synchronous local state.

## Implemented architecture and contract

[New FIFO RTL](../../fpga/experiments/cu66-v107-cdc-sync/v107_async_fifo.sv) uses synchronous resets for pointers, Gray registers, pointer/up synchronizer stages, full/valid, staged addresses and physical read/write issue state. Only dedicated channel-local up-notification flops asynchronously clear on the coordinated raw reset; they remain zero while the domain's three-edge reset release is active. Their outputs feed only a peer's first synchronizer D. They never directly drive BRAM controls. DONT_TOUCH is limited to these independent one-bit notification flops so synthesis cannot merge them into the previously observed multi-channel source fanout.

Making those notifications fully synchronous would be unsafe under the existing stopped-clock contract: a stopped peer can retain its old up=1 while a running side completes its local reset and mistakenly samples that stale value. The independent [reset model](../../fpga/experiments/cu66-v107-cdc-sync/reset_contract.py) demonstrates that counterexample. A raw combinational reset gate before a first synchronizer is also avoided. The dedicated asynchronous notification is a deliberate exception to the synchronous-state rule, outside the RAM address/enable cone.

The write stage captures accepted payload/address on the source clock. Physical RAM write enable is only `write_pending`, and its address is only `write_address`, both synchronous local registers. A reservation pointer includes the staged word when deciding full. The advertised write pointer/Gray advances **only on the actual physical RAM write**. Capacity remains eight reserved RAM words, including the one staged word, plus one read-output slot; staging does not add an unaccounted extra word.

A synchronous read-issue register reserves output capacity before a physical read. Physical read enable is only `read_pending`, and address only `read_address`. The read pointer/Gray advances **only on actual RAM capture**, so the writer cannot reuse a slot before its data has been captured. The captured output holds during backpressure. Neither RAM physical enable nor address directly depends on reset-gated public ready/valid, raw ready/valid ports, or asynchronous reset state.

Public ready and valid gate immediately on local reset, including while a clock is stopped. The physical RAM may finish one old, discarded write/read on the first reset clock edge. Subsequent reset edges clear pending work and both pointer owners; the local reset remains active for at least three edges, and peer-up synchronization blocks a restarted side until its peer has also restarted. Memory contents are private and unspecified after flush; a new read can become owned only after its new write was physically committed and advertised. A flush cannot undo a physical memory write or replace the actual parent's transaction/epoch retirement policy.

These changes add a write staging edge and a two-edge read issue/capture schedule. They preserve accepted/delivered/reset-discard semantics, not the old cycle schedule or the same randomized accepted workload. Invalid output payload remains unspecified. No physical throughput, complete-frame latency or board display-rate improvement is claimed.

## Verification and reproduction

[Runner](../../scripts/cu66-v107/cdc_sync.py) snapshots the new RTL, original unchanged C++ scoreboard, original independent trace replay, reset model and commands. The C++ bench is byte-for-byte identical to the original strict passing bench. It uses the same three seeds, four staggered unrelated clocks, independent clock stops, reset while a clock is stopped, six reset epochs, long/random stalls, full backpressure, held output and pointer wrap. Each variant is checked against its own accepted-word sequence; the new schedule is not misrepresented as a cycle-exact A/B result.

`python3 scripts/cu66-v107/cdc_sync.py` prepares without compiling. Run the prepared attempt with `--run <attempt-directory>` after obtaining a shared heavy-job slot. Strict flags remain `--assert -Wall` and C++ `-Wall -Wextra -Werror`, with no warning suppression. Compile/run bounds, RAM/PSI gates, source snapshots, failed attempts and hashes are retained. [Results](../../experiments/python-gamebub-v107/cdc-sync/results.json) appears only after execution; preparation/model success is not an RTL PASS.

The executed native implementation repeats the same synthetic 5/10/10/16.667-ns clocks, exact mapped C-to-first-D Gray constraints, Default synthesis/opt/place/route, actual applied-bound checks and complete reports. Actual mapped reports demonstrate the targeted REQP-1839/1840 and CDC-11 removals; attributes or a behavioral PASS alone would not establish that result. The common reset-request OR, raw reset timing, board I/O, memory/display adapters and complete-parent ownership remain independent obligations even if those targeted findings disappear. No warning is waived.

## Executed behavioral and rate evidence

[Independent audit](../../experiments/python-gamebub-v107/cdc-sync/audit.json): `PASS_BEHAVIOR_CAPACITY_AND_MEASURED_HALF_RATE`. The unchanged three-seed scoreboard and independent accepted-stream replay check **45,243 accepted, 44,702 delivered and 541 reset-discarded words**. Every channel reaches exactly nine owned words in every seed and never exceeds nine. Source snapshots, executable hash and all logs/traces are retained in the [passing receipt](../../experiments/python-gamebub-v107/cdc-sync/attempts/20261108T040906721862Z/receipt.json).

| No-stall measurement, each of five channels | Actual result |
| --- | --- |
| Inputs / outputs | 10,000 accepted / 10,000 delivered |
| Steady accepted rate after warmup | 0.5 word per source test clock |
| Delivered rate | 0.5 word per destination test clock; every gap exactly two clocks |
| Accepted-to-delivered latency | 6 to 13 equal test-clock cycles |
| First acceptance / first delivery | Cycle 18 / cycle 24 |
| Maximum ownership during this no-stall test | Seven; separate held-output regression proves nine-slot capacity |

The [rate harness](../../fpga/experiments/cu66-v107-cdc-sync/tb_rate.cpp) reuses the exact passing compiled DUT library, with source/sink always willing and all four test clocks equal/zero phase. It has its own full-payload scoreboard, watchdog, strict C++ compile, terminal PASS and [rate receipt](../../experiments/python-gamebub-v107/cdc-sync/rate/receipt.json). An independent Python replay checks all 50,000 transfer identities, order, edge timestamps and latency measurements. These are equal-clock unit measurements, not elapsed board latency or an asynchronous-frequency throughput guarantee.

One rate-test attempt incorrectly required full nine-word occupancy while the sink never stalled; it delivered all words but observed seven. That testbench-assumption failure is retained unchanged. The corrected no-stall gate checks the capacity upper bound, while the separate long-stall regression establishes exact nine-word capacity. No RTL changed to satisfy that check.

This repair has a substantial bandwidth cost: the two-edge read schedule halves the destination-domain ceiling. At the existing source-configured panel clock of about 29.362 MHz, a directly connected one-word-per-pixel FIFO of this form would cap near 14.681 million pixels/s. A hypothetical 720×480 display refreshed 60 times/s needs 20.736 million active pixels/s before service overhead, so this prototype cannot directly replace the existing LCD line-bank data path. Existing line banks, complete-burst reservations and real display/memory arbitration remain necessary. No board clock is changed and no full-display service result is claimed.

Prepare native evidence only after behavioral PASS using `python3 fpga/experiments/cu66-v107-cdc-sync/native.py`; the completed attempt is [20261108T041555711433Z](../../experiments/python-gamebub-v107/cdc-sync/native/20261108T041555711433Z/receipt.json). Reproduction execution requires a shared heavy-job slot. Besides the original mapped Gray proof, the native report recipe verifies all ten distinct up-notification registers exist with DONT_TOUCH and actual CDC/DRC reports confirm the targeted repair.

## Routed unit evidence

The [independent native audit](../../experiments/python-gamebub-v107/cdc-sync/native/native-audit.json) is `PASS_TARGETED_REPAIR_WITH_PARENT_TIMING_OPEN`. Run `python3 fpga/experiments/cu66-v107-cdc-sync/audit_native.py` to verify the portable receipt/snapshot/report hashes, actual per-bit timing exceptions and structural findings without Vivado. All three behavioral-passing RTL files remain unchanged through implementation. No warning was waived and no clock or timing requirement was relaxed.

| Finding / measurement | Original unit | New synchronous-control unit |
| --- | --- | --- |
| CDC-11 critical fanout findings | 8 | **0** |
| REQP-1839 / REQP-1840 | At least 20 each, report caps reached | **0 / 0**, no report-limit warning |
| Peer-up notifications | Equivalent flags merged | **10 independent FDCE flags**, DONT_TOUCH retained and each drives its own first synchronizer |
| RAM address and issue state | Async-reset controls reported | **40 mapped FDRE control/address registers**, synchronous reset |
| WNS / WHS / pulse-width slack | +2.025 / +0.097 / +2.000 ns | +2.078 / +0.027 / +2.000 ns |
| Total setup / hold / pulse violations | 0 / 0 / 0 | 0 / 0 / 0 |
| Gray first-stage max-delay proof | All 40 bits | All 40 bits at synth/place/route; minimum routed slack +3.487 ns |
| Bus skew | 10 constraints, minimum slack +4.178 ns | 10 constraints, minimum slack +4.271 ns; maximum actual 0.970 ns |
| Exception coverage | 100%, none ignored | 100% for 10 Gray bounds and 10 peer-up first stages; none ignored |
| Routing | 240/240 nets, no errors | **568/568 nets, no errors** |
| LUT / FF | 91 / 196 | **107 / 527** (+16 LUT, +331 FF) |
| RAMB36 / RAMB18 / DSP | 3 / 4 / 0 | 3 / 4 / 0 |

The resource and bandwidth costs are explicit: this is a demonstrated reset/control repair prototype, not a selected streaming optimization. The rate test still measures one output every two destination clocks, and the new interface schedule differs from the original.

Remaining reports contain 10 CDC-6 Gray-bus warnings, 10 informational CDC-3 single-bit synchronizers, LUTAR-1 for the coordinated asynchronous reset OR, seven SYNTH-4/seven SYNTH-6 shallow-BRAM advisories, and 558 TIMING-18 input/output delay warnings. DRC retains CFGBVS-1 because no actual board configuration voltage is supplied. These are not waived. The unit has no missing clocks or unconstrained internal endpoints, but actual parent interfaces and clock placement remain unqualified: the OOC tool reports missing HD.CLK_SRC and HD.PARTPIN_LOCS. No locations were guessed to hide those warnings.

The raw reset source, glitch/pulse behavior, stopped/unstable physical clock handling, metastability/primitive assumptions and complete-parent transaction/display ownership still require the real integration contract. Positive slack under the explicit synthetic unit screen and removal of the targeted DRC/CDC findings do not establish complete CDC signoff, board timing, hardware display service or frame-rate qualification.

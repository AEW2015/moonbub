# V119 native timing results

Three fresh RTL implementations completed at the fixed 8 ns and 10 ns constraints. Both identical-source 100 MHz implementations pass internal out-of-context timing, qualifying only that exact component/source/tool/recipe. The 125 MHz target fails. No source B was selected: the new dominant ingress/cancellation paths need a separately verified owner/control change, rather than another unchanged-source run.

| Build | Setup WNS | TNS | Failing setup endpoints | Hold WHS | Pulse WPWS | Internal unconstrained endpoints | Routing errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V118 125 MHz control | −1.499 ns | −4570.194 ns | 12,667 | +0.096 ns | +2.750 ns | 0 | 0 |
| V119 A125 | −2.105 ns | −6185.906 ns | 14,720 | +0.082 ns | +2.750 ns | 0 | 0 |
| V118 qualified 100 MHz control | +0.061 ns | 0 ns | 0 | +0.078 ns | +3.750 ns | 0 | 0 |
| V119 A100 initial | +0.024 ns | 0 ns | 0 | +0.028 ns | +3.750 ns | 0 | 0 |
| V119 A100 fresh repeat | +0.024 ns | 0 ns | 0 | +0.028 ns | +3.750 ns | 0 | 0 |

V119 therefore regresses setup margin by 0.606 ns at 125 MHz and by 0.037 ns at 100 MHz relative to these V118 controls. Functional equivalence is positive evidence; the measured routing result is not a frequency improvement. Both V119 initial routes have zero hold/pulse violations, internal timing-coverage failures and routing errors. Their actual clocks match their pre-synthesis constraints.

A125’s worst path is `base_kill_authorized` to child-ingress `prepared_request_addr` D: 14 logic levels, no carry primitive in that worst path. Other retained families include raw-coefficient validity through two CARRY4s into scratch transfer enables, context count/error/BRAM enables, and global cancellation into parser payload enables. A100’s worst path remains upstream raw mode into scratch state. See [mapped path evidence](native-mapping.md) and the [next causal experiments](ingress-control-next.md).

Read-only checkpoint inspection subsequently identified the two range-check carries exactly. Replaying their actual LUT INIT values and wiring using vendor primitive equations matches signed `coefficient > +2048` for all 65,536 inputs, with zero mismatches. The separate full-range prefix prototype also matches −2048 through +2048 for that entire domain. This supports a specific next RTL experiment; neither the prototype nor the inspection modifies Source A or measures an improved clock. General connectivity inspection remains partial for three unrelated reset/abort aliases; the specific carry operands are resolved. See [checkpoint evidence](checkpoint-diagnostic-results.md).

The output plan retains 19 FDREs in each implementation, rather than all 88 source-level tuple bits. The verification-only owner fields optimize away. The full 32-bit input predicates and existing public schedule remain intact.

A125 uses 33,788 LUTs, 43,205 slice registers, 38 BRAM tiles and 42 DSPs. A100 uses 33,010 LUTs, 43,030 slice registers, 38 BRAM tiles and 42 DSPs on `xc7a100tcsg324-1`. These are component resource counts; system memory, I/O and additional parent logic are outside this implementation.

The flow is pinned Vivado 2026.1 build 6511674, fresh default synthesis, default opt/route, and `ExtraNetDelay_high` placement. No timing exceptions, I/O-delay guesses, fanout attributes or strategy search were added. Reports retain actual clocks, before/after constraints, setup/hold, control sets, methodology, CDC, DRC, fanout and primitive mapping. The missing external input/output delay requirements are explicitly expected OOC boundaries; they are not board timing signoff.

Passing the internal clock does not mean methodology warnings are cleared. The A100 report retains 28 `SYNTH-6` RAM-output-register warnings, 1,000 reported `TIMING-18` missing external-delay checks, and one `ULMTCS-1` warning for 1,237 control sets. Its DRC retains 13 `DPIP-1`, 27 `DPOP-1` and 14 `DPOP-2` DSP pipeline warnings, plus missing board configuration voltages (`CFGBVS-1`) and nets without routable loads (`RTSTAT-10`). No warning was waived. A125 additionally reports large setup violations (`TIMING-16`), consistent with its failed setup result.

The next control-owner experiments address measured enable/ready depth and control-set pressure. RAM/DSP register changes need an explicit valid/owner/last alignment and latency contract, followed by the complete functional and implementation gates; they cannot be inserted merely to silence the warnings. Actual board I/O timing and configuration voltages belong to the board wrapper, with verified board requirements. The single-clock component CDC report says all paths are safely timed; it does not cover future ESP32, QSPI or memory-controller clock crossings.

The [handoff](handoff.md) pins the initial and separate fresh repeat, their exact 18-file source contract and identical tool/core recipes. Source A is available as a measured development candidate at 100 MHz. V118 remains the stable comparison: V119 does not improve either clock margin or simulated frame cycles. Full-parent routed timing, sustained hardware 30 fps and validated hardware decoding under 10 ms remain open. The 9.161 ms fast-row arithmetic at 125 MHz is conditional on a full-parent clock that this study has not demonstrated.

The standalone [range-prefix RTL probe](range-probe.md) also passed all 65,536 input patterns and nine explicit boundaries in strict actual Verilator simulation. It is outside the production pipeline and has no routed timing result.

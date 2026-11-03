# Fixed100MHz SDRAM read timing

The original controller sampled DQ on command-clock negedges. Its first actual
routed implementation failed input setup by2.136ns despite3.193ns hold margin.
The FPGA forwarded-clock pad latency plus SDRAM tAC and input-pad latency must
be included in the round trip. Those reports are retained in`attempts/v2-routed`
and`evidence/v2_sdram_{setup,hold}.rpt`; the failure was not waived.

The repaired architecture generates a separate100MHz PLL read clock with
279-degree phase, nominal rise7.75ns relative to the command rise0ns. It samples
the **previous SDRAM data beat**, retimes into the following command negedge,
and transfers to the command response register on the next posedge. READ_WAIT
therefore gained one cycle. Eight successive, distinct words are compared in
the pin-level model, so an off-by-one beat cannot pass as a repeated pattern.

With a forwarded-clock reference rise5ns and period10ns, the setup relationship
for that prior beat is launch5ns→capture17.75ns, or12.75ns. The next data beat's
hold relationship remains launch5ns→capture7.75ns, or2.75ns. The implementation
uses a guarded setup multiplier2 ONLY from the16DQ ports to the16capture D
pins. **There is no hold multiplier.** Adding the common hold1 correction here
would suppress the same-cycle next-beat check and would be incorrect.

AMD[UG903 explains](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/set_multicycle_path-Syntax)
that a setup multiplier also changes the derived hold relationship. The
multiplier here describes the controller's explicit beat association and read
phase.100MHz clocks and the original external7ns max/2ns min input delays are
unchanged. Post-route reports must show both actual relationships and positive
slack; no other path receives this multiplier.

The unit model separately includes representative4ns forwarded-clock pad
flight and tests tAC2ns and7ns. Both test cases retain VCD traces in
`sim/sdram-tac2.vcd`and`sim/sdram-tac7.vcd`; command/address/data, read clock,
capture and retime registers are visible. This is a functional corner model,
not a measured PCB model or full vendor/PVT qualification. Routed FPGA I/O
timing and physical-board tests remain separate gates.

DQ output data and output-enable use32individual ODDRs driving their pad
IOBUFs. D1 and D2 are identical on every SAME_EDGE instance, so the falling
edge cannot change the data or enable. The narrow falling-output exception is
applied only after Tcl checks that exact structure for all32instances. Rising
output timing, internal ODDR input timing and all SDRAM input checks remain.

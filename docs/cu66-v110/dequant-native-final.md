# V110 combined-dequant native route audit

The completed fresh RTL route for `v110-combined-dequant` is hash bound to the
combined-dequant canonical PASS and the busy, fault and dequant focused PASS
receipts. All 18 source origins and snapshots, four recipe files, parent
checkpoint, 98 retained artifacts and 72 external build artifacts match their
recorded hashes. Re-parsing the retained native reports reproduces the receipt
metrics exactly.

The route still fails setup at the fixed 100-MHz target: WNS is −4.845 ns with
23,412 failing setup endpoints. Hold slack is +0.049 ns and pulse slack is
+3.750 ns, with zero hold or pulse failures and zero routing errors. The worst
path is parser `available_reg[5]` to `state_reg[1]`, 19 logic levels and
14.792 ns total delay (3.565 ns logic, 11.227 ns routing). The route DSP report
shows the eight dequant operand-product DSPs mapped with AREG enabled on all
eight and BREG enabled on three. This mapping observation does not qualify
clock timing or performance.

The measured worst path is a Rice parser control cone. The separate Rice
prefix contingency remains unselected until an actual V110 RTL proof exists.
Full-parent, board I/O, hardware 30-fps and strict under-10-ms decode gates
remain open. See
[dequant-native-final.json](../../experiments/python-gamebub-v110/audit/dequant-native-final.json)
for source, raw-report and DSP pins.

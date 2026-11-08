# V110 combined native route audit

The completed fresh RTL route for `v110-combined-initial` finished successfully
with all routable nets routed and zero routing errors. Re-parsing the retained
raw vendor timing, check-timing, routing, clock and setup-path reports exactly
reproduces the receipt summary. All 18 selected source origins, read-only
source snapshots, four recipe files, the parent synthesis checkpoint, 98
retained run artifacts and 72 external build artifacts match their recorded
hashes. The combined canonical Q and busy/fault focused proof pins also match.

This OOC component still fails its fixed 100-MHz setup target: WNS is −1.700 ns
with 12,612 failing setup endpoints. Hold slack is +0.104 ns, pulse slack is
+3.750 ns, hold/pulse failures are zero, and routing errors are zero. The
worst path is `coefficients/state_reg[0]/C` to
`coefficients/child/packet_decoder/synchronous.ingress/buffer_bytes_reg[0]/CE`,
14 logic levels and 11.411 ns total delay (2.192 ns logic, 9.219 ns routing).
The final measured cone is producer state control into ingress byte-buffer CE;
it does not select a Rice-prefix repair.

No complete-parent, board I/O, hardware 30-fps or strict under-10-ms decoding
qualification is claimed. See
[controls-native-final.json](../../experiments/python-gamebub-v110/audit/controls-native-final.json)
for hashes and raw-report checks.

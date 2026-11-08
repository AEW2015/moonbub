# V110 count-domain native final audit

**Result: the routed 100 MHz component timing remains negative.** The route completed normally with exit code 0 and signoff open, but the component did not meet the 10 ns timing target.

The retained receipt reports WNS **−1.022 ns**, TNS **−1125.069 ns**, and 4,620 setup failures across 89,138 endpoints. Hold slack is +0.085 ns with zero hold failures; pulse width slack is +3.750 ns with zero pulse failures. Routing completed with zero routing errors and all 66,245 routable nets routed. The worst setup path runs from `fetch_bytes_reg[23][0]/C` to `counts_reg[1][5]/CE` in the synchronous ingress, with 15 logic levels and 10.769 ns data path delay. This makes the failed count-range/counter-enable path the immediate measured bottleneck; it does not establish a board timing result.

I independently checked that the 72 externally retained implementation artifacts match the receipt hashes and byte sizes, and that the 98 retained run artifacts also match. The pinned report parser reproduces the receipt result exactly. The report set includes both `synth.dcp` and `route.dcp`. The run receipt ties to the audited preflight, policy, predispatch gate, frozen source contract, current focused/canonical proof hashes, 18 read-only source snapshots, and unchanged recipes. The two changed aliases remain the context and synchronous ingress. It used RTL start mode, loaded the 10 ns clock in this run, and left the parent checkpoint unchanged.

The run used the existing read-only license mount; it did not log license contents, change host identity, contact hardware, or generate a bitstream. No hardware 30 fps, board I/O timing, complete custom-top qualification, or strict complete validated decode below 10 ms follows from this OOC component route. The timing report also lists 1,101 unconstrained input-delay and 12,885 output-delay endpoints; board I/O timing remains open.

Machine-readable provenance and hashes: [`count-domain-native-final.json`](../../experiments/python-gamebub-v110/audit/count-domain-native-final.json).

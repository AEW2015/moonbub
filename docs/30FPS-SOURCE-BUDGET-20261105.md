# Source budget for the next30fps stages

This is calculated from the pinned source and synthetic fixtures, **not measured hardware throughput**. It changes no sender, clock, bitrate, firmware or FPGA setting. Exact inputs/formulas are in [the budget JSON](measurements/30fps-source-budget-20261105.json).

| Payload alone | First fixture | Distinct second fixture |
|---|---:|---:|
| CP23 bytes |17,412|17,700|
| Required at30frames/s |4.179Mbps|4.248Mbps|
| Maximum at4Mbps before any overhead |28.72frames/s|28.25frames/s|

The unchanged4Mbps diagnostic cap cannot carry either exact fixture at30fps even with zero transport overhead. A future custom rate budget must include the agreed carriage, audio and recovery overhead plus actual moving-content size tails. No custom carriage/port is assigned by this calculation, and the legacy diagnostic baseline stays unchanged. The private local staging bound49,152B would require11.796Mbps at30 full-sized frames before overhead; it is not the JPEG negotiated limit.

The configured29.361979MHz pixel clock and541×834 totals imply65.076 native refreshes/s. This is a nominal source calculation, not an oscillator/panel measurement. Canonical720×480YUV420 is518,400B: writing30 new candidates/s requires15.552MB/s; the modeled native reader consumes that payload per full canvas, approximately33.735MB/s at the configured refresh. Their payload sum is49.287MB/s. Commands, activation, refresh, turnaround, backpressure and arbitration add cost. The ideal16-bit100MHz SDRAM number200MB/s does not prove delivered bandwidth or line deadlines.

The finite one-/two-frame simulations establish exact reconstruction, modeled storage and presentation ordering within their scope. They do not establish sustained bank reuse or30 unique physical presentations/s. A held image repeatedly scanned65times/s is still one input frame.

After the first local hardware fixture, the practical sequence remains:

1. Prove bounded front/candidate reuse, including old reader/response drain and fresh owner/epoch/frame tags, before accepting a third frame. Writer retirement alone cannot free a displayed bank.
2. Measure FPGA-only sustained service with distinct admitted frame identities, then concurrent receiver/QSPI ingress. Keep byte ingress, decoded result, frame-boundary publication, completed scanout and memory release separate.
3. Agree the custom lab carriage, bounds, credits, cancellation and unknown-outcome recovery with Windows before assigning a network endpoint. CPL1's one-job fixed-ROM/CAPS0 interface is not that endpoint.
4. Use the same moving clip for a measured rate ladder, with complete frame/outcome reconciliation and retained failure reasons.30 acceptance needs30 fresh input identities reaching complete physical presentations over a sustained window, supported by actual scanout identity/counters and visual evidence; ingress ACKs and repeated canvas counts cannot substitute.
5. Add audio and controller coexistence after the video gate, retaining separate timing/underrun/input-sequence results.

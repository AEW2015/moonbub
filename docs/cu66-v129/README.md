# V129 timing and streaming investigation

V129 changes the Rice parser's consumption arithmetic and factors the scratch
buffer's band-count comparison. The selected out-of-context component uses the
V128 composition with exactly those two source substitutions. It preserves
public cycle timing in the exercised tests; it is not a board bitstream.

The [full functional index](../../experiments/python-gamebub-v129/integration/results.json)
and [independent audit](../../experiments/python-gamebub-v129/audit/full-independent.json)
record exact comparisons of four spatial cases, two peer cases and four parent
cases against V128. Focused [parser](../../experiments/python-gamebub-v129/parser/results.json)
and [scratch](../../experiments/python-gamebub-v129/scratch-factor/results.json)
RTL tests also passed. These are finite simulations, not a formal proof.

The fresh 125 MHz out-of-context component [route](../../experiments/python-gamebub-v129/native/20261111T003938700577Z/receipt.json)
finished and its [independent evidence audit](../../experiments/python-gamebub-v129/audit/native-post-route-independent.json)
passed. Timing itself **failed**: WNS was −1.257 ns with 7,258 failing setup
endpoints, versus V128's −1.320 ns and 10,006 failing endpoints. Hold slack
was +0.086 ns, pulse-width slack +2.750 ns, and all routable nets routed
without reported routing errors. The worst setup path goes from
`base_kill_valid_reg` to an admission-buffer RAM enable. No internal endpoint
was unconstrained, but 1,101 inputs and 12,887 outputs lack delay constraints.
This component flow does not qualify the actual board interfaces or complete
board parent. The Vivado installation is a separate host mount; the container
image hash alone does not pin those tool binaries. The retained reports and
source snapshots are in this repository, but the independent post-route audit
also checks checkpoints and other artifacts at their original absolute build
paths. Those external files are not a portable board deliverable; running that
same audit on another host requires restoring them at the recorded locations.

* [Measured parent latency and next investigation](latency-next.md).
* [Passive stall-monitor results and limitations](latency-monitor.md).
* [Standalone dense-owner queue experiment](dense-queue-status.md).
* [Routed critical-path investigation](route-next.md).
* [Separate header-fetch experiment](header-index-experiment.md).
* [Active MSV1 boundary test](negotiation-boundary.md).
* [Portable V97 host-to-receiver test](v97-negotiation.md).
* [Remaining host-to-device integration work](full-system-next.md).

Sustained 30 fps, validated under-10-ms hardware decoding and the complete
Sunshine → ESP32 → FPGA system remain open. The full-parent stalled case
still requires 1,553,197 simulated cycles between its last input and commit;
125 MHz is a target, not an established physical clock for this component.

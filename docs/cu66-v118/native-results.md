# V118 routed component timing

V118 A is qualified for the internal100MHz component clock by two fresh routed runs with identical source, tools and recipes. Its125MHz route still fails. No source B or negative reroute has been selected.

| Fresh RTL trial | Period | WNS | TNS | Failing setup endpoints | WHS | WPWS | Routing errors |
|---|---:|---:|---:|---:|---:|---:|---:|
|[A125](../../experiments/python-gamebub-v118/integrated-study/native/20261109T151432649740Z/receipt.json) |8ns |−1.499ns |−4,570.194ns |12,667 /103,125 |+0.096ns |+2.750ns |0 |
|[A100](../../experiments/python-gamebub-v118/integrated-study/native/20261109T151440332481Z/receipt.json) |10ns |+0.061ns |0 |0 /102,478 |+0.078ns |+3.750ns |0 |
|[A100 fresh repeat](../../experiments/python-gamebub-v118/integrated-study/native/20261109T154034767493Z/receipt.json) |10ns |+0.061ns |0 |0 /102,478 |+0.078ns |+3.750ns |0 |

All three completed routes have zero failing hold/pulse endpoints, zero unconstrained internal endpoints, zero clock loops/multiple-clock checks and fully routed routable nets. Clock targets and waveforms match their8/10ns constraints loaded before fresh synthesis. The external I/O endpoints remain unqualified: no board I/O timing requirements were invented.

The source/tool/recipe and actual report hashes are retained in the [mapping audit](../../experiments/python-gamebub-v118/audit/native-mapping.json). The fixed flow uses Vivado2026.1 build6511674, `xc7a100tcsg324-1`, default RTL synthesis/optimization/routing and `ExtraNetDelay_high` placement. It adds no retiming option, timing exception, forced fanout property or physical-preservation attribute. Native results come from final routing, not synthesis/place estimates.

The worst A125 path is ingress `raw_mode_reg_rep` through selected coefficient-position validation to scratch `busy_owned`:14 logic levels,3 CARRY4 primitives,9.496ns data delay, including6.562ns routing. A100's worst path is the same source/destination family,15 levels and9.886ns data delay. The changed source and tighter target produce distinct physical implementations; these delays must not be treated as a single frequency sweep of one routed netlist.

The earlier read-band/head selection cone is no longer among either retained50 worst paths. All six new per-band predicates survive mapping as FDREs. A125 has several independent failing families, including plane-block/admission-to-producer control, admission mode/header/scan logic, scratch output-block return-state control and reconstruction reference-owner checks into residual enables. Fixing only the single worst raw-mode path cannot establish closure of those other paths. The [next mapping plan](native-mapping-next.md) addresses them under separately verified owners.

V117 C100 failed at−0.317ns; both V118 A100 fresh routes achieve+0.061ns. The repeat verifies the initial source contract, image, tooling, policy and run/report/clock recipes, and reproduces the complete timing/routing result. Fresh RTL synthesis executed again; no checkpoint was used as an implementation start. V117 C125 failed at−1.679ns; V118 A125 improves to−1.499ns. These are combined-candidate results, not an isolated attribution to one RTL edit.125MHz remains open.

The LIVE fast-row fixture measured1,145,104 cycles, which would be9.160832ms at a separately validated125MHz or11.451040ms at100MHz. The OOC component excludes the full LIVE hash/write/memory-service parent. A100 clock evidence therefore cannot validate the parent's physical clock, under10ms hardware decoding, ESP32 transport or sustained hardware30fps. See [parent results](parent-results.md) for measured cycles and limits.

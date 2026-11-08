# V112 native-driver independent review

Review scope: static read-only inspection of `scripts/cu66-v112/native.py`, `scripts/cu66-v112/canonical.py`, `experiments/python-gamebub-v112/study-policy.json`, and the V112 OOC Tcl/XDC recipe. No preparation command, native dispatch, simulation, or source modification was run. Hashes for the reviewed files and detailed assertions are in [`native-driver-review.json`](../../experiments/python-gamebub-v112/audit/native-driver-review.json).

## Gate result

**Static review passes with one low-severity CLI usability finding; native preparation is not yet authorized.** The policy and native driver require a `PASS` actual-RTL candidate focus receipt plus a `PASS_EXACT_V112_CANONICAL` full-component result before `prepare()` can write a card. At review time, `experiments/python-gamebub-v112/control/results.json` exists but is `FAIL` with `actual_RTL_run=false` (`AssertionError(('geometry_probe-compile.log', 1))`); `experiments/python-gamebub-v112/canonical/results.json` does not exist. Do not prepare or dispatch until the candidate focus receipt and full canonical receipt independently pass.

## Source and status checks

- The control receipt/card is the pinned V110 Count-domain 100 MHz route. The static gate verifies its receipt and input-card hashes, actual RTL synthesis/route provenance, 18 source origins and source snapshot hashes, and the complete V110 canonical proof.
- The V112 canonical gate reconstructs the 18-entry source composition from frozen V109 fixtures plus the qualified V110 composition bodies, then native qualification compares every resulting alias/path/hash with the exact V110 Count source origins. It requires the changed alias set to equal policy's two entries: `packed_scratch_v91g2.sv` and `cs88_admission_v91i2a.sv`. It rejects any V111 header source. Thus the prepared native source is the full `cs88_pipeline_v91k` component with exactly those two candidate deltas, not a header candidate or a unit top.
- Full canonical qualification requires seeds 107601/107602, 44 candidate case profiles and 42 directed checks, exact stdout/events/cycles/canonical artifact matching against the frozen control. Candidate focus source hashes must be present in the full-Q source manifest.
- The V110 100 MHz baseline is explicitly required to be `−1.022 ns` WNS and is retained as the measured control. The separate V111 125 MHz route is not substituted as a 100 MHz result.

## Clock, scope, budget and repeat checks

The XDCs create a single 10 ns or 8 ns `component_clk` before synthesis, with no I/O delay guesses, false paths, multicycle paths or clock groups. The Tcl requires fresh RTL OOC synthesis for `cs88_pipeline_v91k`, checks the declared component clock, uses fixed Default synthesis/opt/route and `ExtraNetDelay_high` placement, and adds no retiming directive. The receipt labels results as component-only and keeps full-parent/I/O/hardware gates false. This measures the target period on the source-bound component; it does not claim a 125 MHz board clock or whole-parent CDC integration.

The policy bounds each native job to two CPUs, 8 GiB memory/swap and 3600 seconds; it caps initial trials at the two declared 100/125 MHz targets and permits one fresh repeat only after a positive completed route with matching source, recipe, policy, tools and image. Dispatch rechecks preflight/policy/tool/recipe/snapshot hashes, image identity, license-file presence, host memory/PSI and active container count. Root remains the serialized dispatch owner; the policy correctly says the Docker-name check is supplemental rather than a global scheduler.

## Finding

`canonical.py` advertises `--variant busy` and `--variant fault` in argparse choices, then unconditionally asserts that the variant is `combined`. Those advertised invocations fail by assertion. The intended full V112 proof uses `combined`, so this does not invalidate its evidence gate or allow the wrong source to pass. Remove the unsupported choices or implement their documented behavior before relying on those modes.

## Dispatch decision

No native preflight card or dispatch was created. Review the new focus and full canonical receipts first; then the source/status/scope gates above can be exercised by preparation and independently audited before launch. This review is conditional on the reviewed script, policy and flow hashes remaining unchanged.

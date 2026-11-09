# Read-only V119 A125 checkpoint diagnostic

Root executed two separate read-only inspections of the final routed A125 checkpoint. The original query is partial because empty segment expansion suppressed driver/load inspection. The direct-net follow-up resolves the two specific carry equations while retaining a partial status for three unrelated reset/abort aliases (nine repeated rows). See [the actual results](checkpoint-diagnostic-results.md). It performs no synthesis, optimization, placement, routing, constraint changes, checkpoint writes, bitstream generation or hardware access. It is neither a new physical trial nor a positive repeat.

The immutable input is the A125 `route.dcp` pinned by [the terminal native receipt](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/receipt.json), SHA256 `37cd94f489fbd2c9c0a4983c1812f35f975bd2448d3ba380b8b695802ed2deba`. The wrapper records the hash before and after inspection. The DCP, existing licensed Vivado tools, and diagnostic Tcl are mounted read-only. The existing license path is `/home/lori/acorn-nexys4-ddr/cache/vivado.lic`; the script never reads or records its contents.

The targets come directly from the final routed setup paths:

- Ingress CARRY4s `dbg_coef_valid_INST_0_i_11` and `dbg_coef_valid_INST_0_i_4`, on the raw-coefficient → scratch transfer-enable family.
- Twelve exact named net aliases on the worst cancellation → prepared-request-address path, including the reported fanouts 368, 259, 1,031 and 207.

The direct-net follow-up retains every target CARRY4 input and output pin, net connections, CI/CYINIT/DI/S operands, direct leaf drivers, LUT INIT values and LUT input wiring. Its fifteen actual LUT2s and two CARRY4s prove `i_11/CO[3] = OR(raw[9:0])` and `i_4/CO[2] = signed16(raw) > 2048` over all 65,536 inputs. The original attempt and its narrower evidence remain immutable. Immediate driver-LUT recursion is bounded to two levels; full flat logical-startpoint queries use `-trace_arcs all` and their returned lists are preserved without truncation. Named control nets record attempted segment expansion, explicit direct-net fallback, and the directly observed leaf load pins. Missing objects, unsupported properties and failed startpoint queries remain explicit `UNRESOLVED`/`UNAVAILABLE` entries. A completion marker means inspection finished; it does not certify a comparator interpretation.

AMD documents these object queries in [UG835 get_nets](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/get_nets), [get_pins](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/get_pins), and [all_fanin](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/all_fanin). The full names are matched using literal Tcl list equality, avoiding glob interpretation of bracketed bit indices.

The wrapper uses the exact existing Vivado image `sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`, 2 CPUs, 8 GiB RAM and 8 GiB combined memory/swap. The original wrapper has a 300-second Vivado timeout plus a 10-second termination allowance; the separate direct wrapper lowers that timeout to 240 seconds. Both monitor the existing V119 host memory/pressure gates. Root must dispatch it as one of the existing two heavy-job slots. The native source and consumed flow policy remain unchanged.

The original commands below document the executed procedure. Both original and direct prepared manifests, wrappers, Tcl snapshots and result audits are now immutable; do not rerun preparation into either existing namespace. Any future query needs a new namespace and Root dispatch.

Historical preparation command:

```bash
python3 scripts/cu66-v119/diagnostic/run.py
```

This produced [the original prepared manifest](../../experiments/python-gamebub-v119/checkpoint-diagnostic/prepared.json) without launching Vivado. Root used a dispatch JSON with this schema, copying the two hashes from that manifest:

```json
{
  "status": "APPROVED",
  "scope": "v119-readonly-checkpoint-diagnostic",
  "diagnostic_tcl_sha256": "COPY_FROM_PREPARED_MANIFEST",
  "wrapper_sha256": "COPY_FROM_PREPARED_MANIFEST"
}
```

Historical Root-only launch command:

```bash
python3 scripts/cu66-v119/diagnostic/run.py --run --dispatch /absolute/path/to/root-dispatch.json
```

Each attempt retains its exact Tcl, command, log, operand table, completion status, memory samples, input/output hashes and receipt in `experiments/python-gamebub-v119/checkpoint-diagnostic/attempts/`. The direct-net follow-up uses separate `attempts-direct`/`results-direct.json` artifacts. Its actual INIT/wiring interpretation now confirms that the prefix candidate targets the measured positive upper-bound rejection predicate. The complete signed-range replacement still requires RTL equivalence and fresh physical measurement; no B RTL or timing improvement is selected by either diagnostic.

The separately [verified interpreter](../../scripts/cu66-v119/diagnostic/interpret_direct_verified.py) checks the installed vendor CI/CYINIT input assignments, `CO_fb = {CO[2:0], CI_in || CYINIT_in}`, carry-mux equation, XOR output equation and LUT INIT indexing before exhaustive evaluation. Its [new audit](../../experiments/python-gamebub-v119/audit/checkpoint-diagnostic-direct-verified.json) pins those vendor models and retains all unresolved general-connectivity rows. The original executed interpreter and audit remain unchanged.

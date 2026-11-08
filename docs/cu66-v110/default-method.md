# Prospective single Default synthesis comparison

This namespace is **code prepared only**. No preflight/build has been prepared, control selected or tool run launched. The original V110 policy, RuntimeOptimized flows, qualification helpers, sources, proofs and all native receipts remain unchanged. A prospective extension is isolated in `experiments/python-gamebub-v110/default-policy.json`, `scripts/cu66-v110/native_default.py` and `fpga/experiments/cu66-v110-default-flow/`.

## One method, one matched control

AMD 2026.1 UG901 documents RuntimeOptimized as omitting some RTL/timing optimization for shorter synthesis. One same-source comparison with the standard default process is justified if all five existing V110 routes finish negative and the final source cuts still do not close timing. It does not predict a clock gain. [UG901](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Using-Synthesis-Settings)

Root selects the completed original V110 RuntimeOptimized receipt with the **highest final routed WNS** among exactly five completed, negative component routes. The driver rejects a worse-WNS control, any positive/incomplete/tool-failed control, a checkpoint-mode control, changed source/proof bindings, changed original policy, or different resource/implementation settings. Ties at the highest WNS are permitted. No additional historical-control run is made.

The new flow copies the frozen READY flow. Its sole synthesis-method change is removal of `-directive RuntimeOptimized` from this fresh-RTL command:

```tcl
synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt
```

Omitting `-directive` invokes the documented default synthesis process, avoiding case/alias ambiguity between the UG901 display label `Default` and UG835's CLI spelling `default`. No retiming option is added; retiming is off by default for this Artix-7 device. The fixed 10 ns XDC remains loaded before synthesis. `opt_design -directive Default`, `place_design -directive ExtraNetDelay_high` and `route_design -directive Default` stay unchanged, with no physical optimization step. [UG835](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/synth_design)

`report.tcl` and `component.xdc` are byte-identical copies of READY flow. Tcl settings and inputs/contracts/receipts explicitly say `synth_directive=default` and `synth_directive_cli=omitted`. Fresh RTL is mandatory; the original V109 FETCH synthesis checkpoint remains hash-pinned/read-only provenance and is never selected as the design input. The resulting synthesis checkpoint is new.

## Qualification and binding

The selected control's canonical namespace chooses its original read-only helper:

| Canonical namespace | Helper |
| --- | --- |
| `canonical` | `native.py` |
| `canonical-dequant` | `native_dequant.py` |
| `canonical-ready-rice` | `native_ready.py` |
| `canonical-prefix` | `native_prefix.py` |

The helper's current path/hash and variant are pinned. Its qualification result must equal the selected control's entire source contract and all eighteen source hashes/origins. Actual canonical/focused proofs and every canonical source/proof pin are rechecked. The seventeen-file RTL order, include header/directory, command recipe, original negative RuntimeOptimized receipt/hash and new Default contract/hash are retained. Thus this comparison varies synthesis methodology on the **same qualified source**, rather than mixing a source change with a strategy change.

The new policy SHA-references the immutable original policy. Its new result/prepared/coordination roots are `default-native`, `default-prepared` and `default-coordination`. It permits one fresh-RTL methodology trial and **at most one positive fresh-RTL validation repeat globally**, counting both original `native` and new `default-native` receipts. An exclusive fixed reservation consumes the methodology/repeat slot before dispatch, preventing duplicate or silent retry through two prepared builds. Failed/stopped attempts and reservations remain visible and consume their allocated trial. No additional negative retry or strategy sweep is authorized.

## Resources and expected cost

The limits remain two CPUs, `general.maxThreads=2`, 8 GiB memory **and** memory+swap, 2,400 seconds, at most two concurrent study heavy containers (`gamebub-v*`), and the original available-memory/PSI launch/stop gates. Both dispatcher and runner recheck concurrency; the runner retains the existing read-only tool/license/source/checkpoint mounts, memory telemetry, watchdogs and complete failure/report receipts.

Measured R3 RuntimeOptimized synthesis took 3m55s; its complete route took 12m24s, with approximately 6.0 GiB sampled container memory and a reported synthesis process/fork PSS peak of 6,709 MB. Default has no measured resource ratio here. A 20–30 minute planning allowance is plausible but uncertain; the 40-minute cap remains binding and additional memory may exceed the unchanged 8 GiB cap. A resource stop is evidence, not permission for an automatic memory/time increase.

## Deliberately not executed

After all five originals are terminal/negative and root has selected the matched control, source-only preparation would be:

```sh
python3 scripts/cu66-v110/native_default.py --control experiments/python-gamebub-v110/native/SELECTED/receipt.json
```

That command has **not** been invoked. It would prepare eighteen source snapshots, exact recipes, new contract and preflight only. Root review and an independent preflight audit must precede `--run`. A positive result alone is insufficient: the one allowed global validation repeat must use fresh RTL, the same eighteen sources, same Default flow and identical constraints/settings. Component closure still does not qualify the production parent, board clocks/I/O/CDC, publication endpoint, hardware 30 fps or complete validated decode under 10 ms.

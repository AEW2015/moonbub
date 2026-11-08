# RuntimeOptimized alternative: completed same-source observations

This is one prepared strategy-only alternative, `threshold-runtime`. It uses exactly the eighteen qualified threshold closure files: seventeen RTL sources and one include. No RTL, benchmark, frozen builder, clock or exception changed. The preparation itself launched no native job. After explicit root activation and independent audit, the one authorized runtime attempt started as recorded below.

At the activation decision, Default8 was CPU-active in long synthesis without a checkpoint. That historical observation motivated the bounded alternative; it was not a tool-hang diagnosis. Default8 later completed normally within its unchanged 3,600-second cap. The parent retained the immutable decision observation; mutable live log/receipt hashes are not dependencies.

AMD's [Vivado 2026.1 UG901 synthesis settings](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Using-Synthesis-Settings) describe `RuntimeOptimized` as performing fewer timing optimizations and omitting some RTL optimizations to reduce synthesis runtime. This supports testing one bounded alternative. The documentation does not predict this design’s runtime, QoR or routed clock. Actual one-run observations are recorded below.

## Exact prepared result

The [preflight](../../experiments/python-gamebub-v107/threshold-runtime/prepared/20261108T080509124123Z-2c6754/preflight.json) has status `PREPARED_NOT_ACTIVATED`, SHA-256 `7ad293e41db1cf43f25464954ae99574e14eb0d789240d67e1c7386ba1d5ad6a`. It binds:

- The exact eighteen source aliases, origins and hashes against both immutable Default8 inputs and the current actual canonical qualification.
- The unchanged frozen `threshold_build.py`, hash `e373dbd6203eff4ac6845ffd1b619d6227242a03ae32256650f37f2e1bf2e881`.
- Immutable Default8 `inputs.json`, hash `821b64538f021ffcf14d1841e2d7f76339315e13caaee3f24ba8072385a37d51`.
- Qualified actual canonical result, hash `5b6e718958ed7ef457b0b40d979ac83fe7514cc0d57bebe5ad6286efb7e4002c`; its same RTL proof is reused explicitly, with no new behavioral execution counted.
- Copied before/after `run.tcl`, their exact unified diff, and byte-identical `report.tcl`, `component.xdc` and native runner.

The new flow is [`cu66-v107-threshold-runtime-flow`](../../fpga/experiments/cu66-v107-threshold-runtime-flow/). The only Tcl content difference is:

```diff
-synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default
+synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive RuntimeOptimized
```

The 10 ns clock is read before synthesis. Rebuilt/OOC synthesis mode, Default opt/place/route, two synthesis threads, 8 GiB memory with no extra swap, two CPUs and a 3,600-second watchdog remain unchanged. The new `inputs.tcl` differs only in its prepared build-directory paths. No source-specific waiver, false/multicycle path, relaxed clock, phys-opt change or implementation strategy sweep is added.

The [builder wrapper](../../scripts/cu66-v107/threshold_runtime_build.py) calls the frozen builder for preparation after changing only its in-memory flow and variant override globals. It does not edit that builder. The prepared external directory is `/home/lori/gamebub-build/cu66-v69/v107-threshold-runtime-20261108T080509124123Z-2c6754`.

## Fail-closed activation

The [disabled template](../../experiments/python-gamebub-v107/threshold-runtime/prepared/20261108T080509124123Z-2c6754/activation-template.json) is preparation metadata, not authorization. Before `--run`, the wrapper requires all of the following:

- Root's enabled `coordination/threshold-runtime-activation.json`, mirrored exactly under `study-policy.json` → `threshold_runtime_activation`, with source limit eight, native-attempt limit nine and alternate-strategy limit one.
- An explicit heavy-slot grant, decision timestamp/reason and an immutable observation record with matching SHA.
- The exact reviewed preflight, builder, prepared inputs, eighteen source origins/hashes, original actual qualification, flow and fixed resource/clock settings still matching.
- Independent `coordination/threshold-runtime-pre-native-audit.json` with status `PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED`, binding both activation and preflight hashes.
- No existing one-shot dispatch record. Immediately before runner handoff, exclusive creation of `coordination/threshold-runtime-dispatch.json` prevents a second automatic launch under this activation.

The wrapper runs only the already prepared and reviewed build; it does not silently regenerate a new source snapshot at activation. The native runner is a byte-identical copy of the existing resource-gated runner. Root owns the decision, policy update and independent audit; no activation record or policy change is made by preparation.

At preparation time the alternative’s runtime and physical outcomes were unmeasured. Both completed runs are now recorded below and judged by actual reports under the same constraints. Negative slack remains a timing failure; hardware/full-top I/O signoff remains separate.

## Activated attempt

Root activated the disabled template only after the immutable observation and independent preaudit passed. The one-shot dispatch bound the reviewed preflight and unchanged source set, and the copied native runner started at `2026-11-08T08:12:54Z`. Its [receipt](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json) was `RUNNING` at launch; the policy/audit/dispatch records remain separate from the frozen preparation artifact.

Initial available RAM was 19,177,807,872 bytes with memory PSI full avg10 zero. The runtime container has the unchanged 8 GiB/no-extra-swap, two-CPU/two-thread, 3,600-second limits. At runtime launch, Default8 was an independent active attempt under its original cap; it subsequently completed normally as shown below. No additional job or automatic retry is authorized. Terminal results are recorded below; a started job alone was not counted as a timing result.

## Terminal native result

The authorized runtime attempt completed in 753.494 seconds with exit 0 and status `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. The [immutable terminal receipt](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json) SHA-256 is `8a24372a70162d2968e255f2c0175e15d4bed9d86e7e5578f7cc84e1a38acd47`. Synthesis and route checkpoints are retained; all eighteen source snapshots remained unchanged. Peak observed container memory was 6,913,929,216 bytes, below 8 GiB; maximum sampled memory PSI full avg10 was zero. No resource/time stop occurred, and Default8 was not cancelled or modified.

| Stage | WNS | TNS | Setup failing endpoints | WHS / hold failures | Pulse slack / failures |
| --- | ---: | ---: | ---: | --- | --- |
| Synthesis estimate | −4.877 ns | −2165.519 ns | 1,783 | +0.193 ns / 0 | +3.750 ns / 0 |
| Placement estimate | −1.954 ns | −15309.934 ns | 18,021 | +0.120 ns / 0 | +3.750 ns / 0 |
| Actual route | −2.333 ns | −16494.424 ns | 21,433 | +0.096 ns / 0 | +3.750 ns / 0 |

Synthesis completed in 4m40s, and placement in 2m32s. Route status reports 65,912/65,912 routable nets fully routed and zero routing errors. **The routed design still fails the fixed 10 ns / 100 MHz setup target.** The actual worst path is scratch read_segment[1] → scratch state: 12.281 ns data, thirteen levels, 2.956 ns logic and 9.325 ns route. The setup report SHA is `57f2154b9f65f8efd3066e42fe0354a8b533d40d3c5ba58f697967af8bc30689`. This supersedes the earlier Rice synthesis and coefficient-CE placement paths as the next measured priority.

The completed checkpoint and route establish the recorded outcome of this one runtime attempt. The completed same-source comparison below is observational, not an isolated RTL gain, hardware frequency or full-top signoff. [next-timing-cuts.md](next-timing-cuts.md) records conditional source reasoning and counterexamples only. No additional heavy job is authorized or launched by this wrapper after the one-shot attempt. The parent owns subsequent physical-probe and final selection decisions.

## Both strategies terminal: one run each

Default8 also completed legally with exit 0 and retained source/synthesis/route artifacts. Its [terminal receipt](../../experiments/python-gamebub-v107/native/20261108T073857407909Z/receipt.json) SHA-256 is `9324a96ce33a2ef252846605ec3fb39ed8ab9c70a3e62a829493417d77870caa`. The [final comparison](../../experiments/python-gamebub-v107/threshold-runtime/final-comparison.json) rechecks identical eighteen-file retained source maps, the exact one-line synthesis-directive difference and unchanged XDC/report bytes. Opt/place/route, 10 ns constraints and resource caps were the same planned settings.

| Observed result | Default | RuntimeOptimized |
| --- | ---: | ---: |
| Synthesis elapsed | 51m15s | 4m40s |
| Complete native wall time | 3517.196 s | 753.494 s |
| Routed WNS | −3.137 ns | −2.333 ns |
| Routed TNS | −27490.594 ns | −16494.424 ns |
| Setup failing endpoints | 29,395 | 21,433 |
| Hold slack / failures | +0.082 ns / 0 | +0.096 ns / 0 |
| Pulse slack / failures | +3.750 ns / 0 | +3.750 ns / 0 |

Both routes fail the 100 MHz setup target. Default’s routed worst is context_blocks[4] → scratch assembler reset/control, eighteen levels and 12.624 ns data; its setup-report SHA is `c24795c4c3a3bdaf5d7bda5edfe179aab8ea364e3f6615eee3364b48441c03a2`. Runtime’s worst remains the read-segment cone described above.

There was one run per strategy, with different start and concurrent-resource histories. These are recorded elapsed-time and timing observations, not repeated evidence of runtime causality or reproducibility. Neither result proves hardware frequency, an isolated source-edit gain or complete-frame latency. No further heavy job was launched by this wrapper after its one-shot attempt; the parent owns final freeze, any separately recorded physical probe and future source plans.

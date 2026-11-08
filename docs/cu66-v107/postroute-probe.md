# V107 single runtime9 post-route physical diagnostic

The one authorized post-route probe **failed with a Vivado segmentation fault** during `phys_opt_design -directive AggressiveExplore`. It produced no final timing reports or candidate checkpoint. Intermediate log timing is not a completed implementation result; there is no promotable timing winner, fresh-synthesis result or hardware claim. The parent routed checkpoint, receipt and all 18 source snapshots remain unchanged. No retry or additional strategy trial was run.

[Raw probe receipt](../../experiments/python-gamebub-v107/postroute-probe/20261108T082822749973Z/receipt.json), [tool log](../../experiments/python-gamebub-v107/postroute-probe/20261108T082822749973Z/tool.log), [actual crash stack](../../experiments/python-gamebub-v107/postroute-probe/20261108T082822749973Z/crash/hs_err_pid59.log), [failure audit](../../experiments/python-gamebub-v107/postroute-probe/20261108T082822749973Z/audit.json) and [evidence index](../../experiments/python-gamebub-v107/postroute-probe/20261108T082822749973Z/evidence-index.json) are retained separately from the parent and Default8 attempts.

## Evidence-driven selection and completed parent gate

The probe was prepared only after runtime9 had a terminal exit-0 receipt, a fully routed legal checkpoint and a qualified source closure. The [runtime9 parent receipt](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json) SHA-256 is `8a24372a70162d2968e255f2c0175e15d4bed9d86e7e5578f7cc84e1a38acd47`. Its external route checkpoint SHA-256 is `e4ca9544b7aa45b2e8f9ac8e125462ff24dc887154c50d580912d3bb5ff960cb`. Parent dispatch had returned exit 0; no concurrent writer remained on that checkpoint. The 18 source hashes match [PASS_EXACT_THRESHOLD_CANONICAL](../../experiments/python-gamebub-v107/threshold-pipeline/results.json), SHA-256 `5b6e718958ed7ef457b0b40d979ac83fe7514cc0d57bebe5ad6286efb7e4002c`, with exact same-seed output/event/cycle qualification. Parent input-manifest, source snapshots, report recipe and XDC hashes are bound independently.

The parent's actual worst [routed setup path](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/reports/route-setup-paths.rpt) is scratch `read_segment_reg[1]/C` → `state_reg[3]_rep/D`: 13 logic levels and 12.281 ns data delay, comprising 2.956 ns logic and **9.325 ns routed delay (75.931%)**. Its WNS is −2.333 ns, TNS −16,494.424 ns, with 21,433 setup-failing endpoints. Hold WHS is +0.096 ns with zero hold-failing endpoints; pulse slack is +3.750 ns with zero pulse failures. It is a legal but setup-failing implementation.

This observed routing contribution motivated one bounded physical experiment, consistent with AMD's [UG949 iterative-flow guidance](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Iterative-Flows). That 2026.1 guidance describes post-route physical optimization rerouting affected nets; the 2026.1 [UG835 `phys_opt_design` reference](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/phys_opt_design) documents post-route operation and `AggressiveExplore`. Both primary pages were checked on 2026-11-08. Before launch, the recipe was narrowed to **only** the physical optimization command; the initially contemplated additional `route_design` command was omitted. This was not a parameter/strategy sweep.

## Exact executed flow and resource bounds

The isolated [Tcl recipe](../../fpga/experiments/cu66-v107-postroute-probe/run.tcl) opened the parent DCP read-only, asserted `xc7a100tcsg324-1` and the existing single `component_clk` at **10 ns**, and requested:

```tcl
phys_opt_design -directive AggressiveExplore
```

No RTL read/elaboration/synthesis, new source, clock constraint, exception, PLL/MMCM or board setting was introduced. The exact unchanged parent `report.tcl` was copied for full setup/hold/pulse, clocks, clock interaction, exceptions, check-timing, routing, DRC, methodology, CDC, resource, RAM/DSP, control-set and fanout reports after optimization. The recipe also requested a new candidate checkpoint and route-status report in its own output directory. **Those final operations were not reached because the tool crashed.** Retained parent reports are baseline evidence only and must not be presented as probe-after results.

The existing Vivado 2026.1 tools, legitimate license and parent checkpoint were mounted read-only. Container limits were two CPUs, 8 GiB memory/no extra swap and two Vivado threads, with a 600-second tool cap and a host watchdog. Launch required at least 8 GiB available RAM and memory PSI full avg10 below 1; stopping thresholds were 4 GiB available or PSI full avg10 at least 5. During this actual run minimum sampled available host RAM was **16,909,312,000 bytes**, PSI full avg10 remained **0**, and the host monitor did not stop the job.

The physical probe is a separate diagnostic invocation on source set 8 / runtime synthesis attempt 9's existing routed state. It does not create a tenth fresh synthesis candidate, change source/native attempt caps, alter Default8's independent run or qualify a new production source set.

## Actual failure and retained warnings

The process exited **139** after **83.023 seconds**, before the 600-second bound. Vivado reported `Abnormal program termination (11)`. The crash stack enters `HDLHInstTerm::getInstanceLH()`, `HAPSRouteMgr::route`, `HAPSPathLenReduct::optimizeSingleNet`, then physical-optimization path passes. This identifies the failing tool stage; it does not establish a root cause or implicate a particular RTL expression.

The log contains an intermediate in-memory WNS value of −2.042 ns during critical-path optimization. There is **no final legal-route report, full setup/hold/pulse analysis or candidate checkpoint supporting that value**. It is neither an improvement result nor a selectable implementation.

Actual retained warnings include:

- `Timing 38-242`: OOC `HD.CLK_SRC` is unset; no parent buffer location was guessed.
- `Physopt 32-745`: the negative slack magnitude is large for post-route optimization; the tool says this flow is most effective above −0.5 ns.
- `Constraints 18-8777`: unable to split tiles because required files were unavailable. No speculative installation/constraint repair or additional run followed.

Before optimization, the query retained existing clock settings, effective timing constraints and legal route status. After failure, the parent DCP hash and receipt hash still match their before values, and all parent source snapshots are unchanged. The only new output reports are `settings.tsv`, `before-effective-timing.xdc` and `before-route-status.rpt`. Neither requested `post-physopt.dcp` nor final `route.dcp` was produced. The crash file is copied verbatim and separately hashed; the raw failed receipt is unchanged.

## Portable failure audit

Raw failed probe receipt SHA-256: `25ce115c7660c84d6cd6bad9963db43367b79f71ebcc6e1e4aa671cd03247567`.

Crash-stack SHA-256: `a5d93d49c210318b57f76ef10305ef11b8d0e0eb2fc1be8a510e3e6234f3f509`.

The separate audit verifies raw retained hashes, all 18 exact source bindings, completed parent/dispatch gates, original clock/XDC/report recipe, unchanged parent hashes, nonempty SIGSEGV stack and absence of final probe timing/checkpoint artifacts. Its status `PASS_FAILURE_PROVENANCE_AND_CRASH_RETENTION_AUDIT` means **the failed experiment is auditable**, not that optimization or timing passed. The actual outcome remains `FAIL_TOOL_SIGSEGV_NO_COMPLETED_TIMING_RESULT`.

```sh
python3 scripts/cu66-v107/postroute_probe_audit.py
# Export the evidence area; no Vivado or external DCP is needed:
python3 /export/postroute-probe/20261108T082822749973Z/audit_native.py --area /export/postroute-probe
```

All small baseline/output reports, query/report Tcl, constraints, source snapshots, tool log and crash stack are indexed with SHA-256. The external parent checkpoint is represented by hash/path and remains untouched. The runner has a one-dispatch guard; no automatic retry is authorized. Promotion would require a separately authorized completed legal implementation and all target/signoff checks, rather than accepting partial console timing.

# Repeat-only Default log evidence correction

`native_default_repeat.py` is a **new, repeat-only validator/launcher**. The frozen initial `native_default.py`, Default flow, policy, sources and parent receipt are unchanged. No repeat preflight or native run has been prepared by this work. The initial Default run's eventual timing result is a separate gate; the pure guard fixtures below do not assert it passed.

The actual Vivado log emits this command for an omitted/default synthesis directive:

```
Command: synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt
```

It emits no `Directive used...` message in this format. The frozen runner honestly records an absent message as `observed_synth_directive_log=None`; the new driver never replaces that value with an invented `default` string.

Instead the new guard requires the actual positive parent's `vivado.log` SHA-256 to match its immutable receipt. It extracts tool-emitted `Command:` lines, parses them with Python `shlex`, and requires **exactly one** `synth_design` command with precisely the fixed top/part/OOC/rebuilt arguments above. The only permitted alternative is those exact arguments followed by the documented `-directive default`. RuntimeOptimized, retiming, changed part/top/mode/hierarchy, additional switches, missing commands or duplicate synthesis commands reject. Any actual directive-info message or non-null observed metadata must independently identify default, case-insensitively.

Every previous positive-parent requirement remains: completed positive component result; original fresh RTL Default trial; exact RuntimeOptimized control pin; policy SHA/path; eighteen source hashes and canonical/focused contract; default/omitted-CLI declaration; unchanged implementation directives; and current `run.tcl`, `report.tcl` and XDC hashes. Only build-dependent `inputs.tcl` path bytes remain excluded from the parent functional-recipe comparison. Both preparation and launch require `clean_repeat_of`; this new driver cannot launch another methodology trial.

The returned evidence records the actual log path/SHA, parsed command/argv, method of proving effective default, raw directive messages and unchanged observed value. It is pinned in the new preflight, contract, inputs and dispatch, and recomputed at launch. The unchanged runner retains/hash-pins the full inputs, thereby retaining the evidence without requiring a runner or flow edit. Existing exclusive repeat reservation and global one-positive-repeat policy remain authoritative.

[Pure test receipt](../../experiments/python-gamebub-v110/default-repeat-log-guard-tests.json): **PASS**, four valid cases accepted and twenty-five invalid cases rejected. Tests use a temporary snapshot of the actual omitted-command log and temporary mutated JSON/log fixtures. A positive status is deliberately mocked only for testing the guard. Valid cases include the actual omitted command with observed None, explicit documented default, an actual default info message, and different build-specific inputs-Tcl bytes. Rejected cases cover wrong log SHA, RuntimeOptimized/retiming commands, wrong part/top/OOC/hierarchy, duplicate/missing commands, undocumented CLI case, conflicting info/metadata, changed functional recipes, control, policy, method, source/proof contract, mode, directives and nonpositive status.

Driver SHA-256: `46e5f6a4836f0b6076bd660bad2ae35e8abd1e9372052fc66bd8791be9c0034d`. Test receipt SHA-256: `46764f2e947c16462714eeb9071c1e4837a54dd28a7b2913389b795eeb9cd877`. All frozen initial driver/flow/policy hashes were checked unchanged. This validation-format correction changes neither synthesis methodology nor RTL timing/behavior.

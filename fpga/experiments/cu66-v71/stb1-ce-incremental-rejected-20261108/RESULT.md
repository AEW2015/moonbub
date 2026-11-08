# Incremental CE candidate ? native placement FAIL

The root-approved attempt used the same CE constrained DCP and opt_design, then the immutable passing V001 routed reference with standard RuntimeOptimized. It exited1 after656.907s, before placement completed. No route, final setup/hold/pulse/DRC/CDC report, checkpoint or BIT was produced. No hardware action occurred. All pinned reference/input hashes and79source hashes remained unchanged; V028 remains selected.

Actual native evidence:

- Vivado12-9151 selected incremental RuntimeOptimized and explicitly overrode ordinary place/post-place-physopt/route directives. Vivado_Tcl4-24 confirmed Incremental Placer for unplaced cells. No full-flow fallback was observed.
- Reference-read reuse report: matched cells95.18%, nets89.28%; current reused cells95.01%, nets78.76%, pins78.54%; ports100%. These are pre-placement measurements, not final reuse.
- Report Target WNS is0.0; the reference checkpoint separately records+.005ns setup/+.020ns hold.
- Place46-13 could not place more than5% of movable instances. Place30-99 says 'Need spiral search for more than5% of movable instances'; Common17-69 terminated placement. The first20include command_state, staging ACK, parser and entropy/receiver/base state cells. The generic tool text mentions tight pblocks as a possible cause; this does not prove a pblock problem. No pblock commands were found in the frozen input Tcl/XDC search. Reused placement limits legal space for changed cells; exact causal diagnosis is not established by this failed attempt.
- Ordinary algorithm reuse/preservation cannot be inferred from unchanged script commands: the tool explicitly overrides directives in this mode. No automatic retry, alternate seed, forced-incremental mode or constraint relaxation followed failure.

Clock report content is identical before/after reference read once provenance/design-state headers are excluded. Exception indices/types/values remain the same, but replay changes object/path coverage: index12 false-path Paths19?6, and index16 max_dpo10 From32125?32144 pins. Exact differences are saved. Source constraints were unchanged. A final whole-design comparison is unavailable because placement failed.

The fresh CE attempt separately completed routing with setup?.382ns and the intended ticket CE improved to+.289ns with zero HUD-metadata feedback. That functional/local result remains useful for future source work, but neither fresh nor incremental CE candidate passed whole-design timing. See source bindings, execution.json, reuse-after-read.rpt and full native logs.

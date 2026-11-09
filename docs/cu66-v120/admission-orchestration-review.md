# Admission repair orchestration: preparation review

The new B orchestration passed **137 static checks**. This review does not qualify the admission source, focused unit, full decoder, peer tests, LIVE parent or native implementation; their results are still required.

Evidence: `experiments/python-gamebub-v120/audit/admission-orchestration-static.json`, SHA-256 `f73d3c4995662a82b87f56671d4fd08be27eab9553ab26f685d79e267dd0ffa5`.

All five new scripts reproduce and reverse their recorded derivations exactly and pass in-memory Python syntax compilation. Their original functional checks, strict simulation flags, exact V119 stdout/event/cycle comparisons and V113 canonical goldens remain present. The repair policy pins the actual prefix-only A125 routed failure and changes only the admission source alias while retaining range A. Address and context-terminal proposals remain unselected.

New results use `repair-study`. The new native runner accepts only `--composition repair`, so it cannot write B native records into the A namespace. Qualification still requires the new focused proof, full/actual transport, peer and LIVE results before native preparation. The shared trial budget, source-identity check, memory limits and fixed implementation recipe remain intact.

This preparation review preceded the negative A100 result and the later declaration of both B100 and B125 trials. The current plan measures those two B clocks after their functional and parent gates; V118100 remains the stable fallback if B100 fails. This historical review makes no hardware, timing-closure or decoding-latency claim.

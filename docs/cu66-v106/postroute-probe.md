# V106 bounded post-route physical diagnostic

The single physical probe completed, but **100 MHz setup still fails**. Routed WNS improved by 0.257 ns, from −4.034 to −3.777 ns; 44,630 setup endpoints still fail. This remains an unselected diagnostic, separate from the six Default full-flow experiments.

## Actual outcome

| Measured routed result | Reopened parent | After AggressiveExplore |
| --- | ---: | ---: |
| WNS | −4.034 ns | −3.777 ns |
| TNS | −58,190.652 ns | −58,145.145 ns |
| Setup failing endpoints | 44,630 | 44,630 |
| Worst hold slack | +0.122 ns | +0.122 ns |
| Worst pulse-width slack | +3.750 ns | +3.750 ns |
| Fully routed / routable nets | 71,007 / 71,007 | 71,011 / 71,011 |
| Routing errors | 0 | 0 |
| Slice LUTs | 46,062 | 46,066 |
| FF / DSP | 36,919 / 27 | 36,919 / 27 |

The native run exited 0 in **380.251 seconds**, within the unchanged **600-second in-container watchdog**. Routing remained complete after physical optimization, so the conditional `route_design -directive Default` was not needed and did not run. Hold and pulse checks remained positive; these do not close the setup or board-level gates.

The worst path moves from the old Rice parser's `available_reg[0]/C` → `out_value_reg[5]/D` to `transform/inverse/k_reg[1]_replica/C` → `transform/inverse/products_reg[3]/A[0]`. The final path has 9.971 ns data delay: 2.640 ns logic and 7.331 ns routing. This is the original `closure` IDCT, not the newer shared-selector candidate being evaluated separately. No Fmax, sustained hardware FPS or complete decoding-latency result follows from this probe.

## Exact execution and scope

The parent is `experiments/python-gamebub-v106/native/20261108T013032873883Z/receipt.json`. Its external checkpoint is `/home/lori/gamebub-build/cu66-v69/v106-closure-20261108T013032719249Z-8cf646/results/route.dcp`, SHA-256 `7c626d0f79ba2c9546d4ac69557fc5541623f4592c7c848c7b65800961efbfd0`. The checkpoint was mounted read only and its actual checksum matched before and after execution. The original `closure` source alias and earlier paired qualification remain the provenance.

The exact sequence reopened that checkpoint, verified xc7a100tcsg324-1 and the single inherited 10 ns clock, collected baseline reports, ran `phys_opt_design -directive AggressiveExplore` once, and collected final reports/checkpoint. The reopened baseline exactly reproduces the retained parent's timing summary. Effective timing commands before/after are identical; the XDC files differ only in the output-filename comment written by Vivado.

AMD documents post-route physical optimization and provides `AggressiveExplore` as an aggressive exploration strategy. Retiming requires separate explicit options/directives; none were requested. See [AMD UG835 2026.1: phys_opt_design](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/phys_opt_design).

The owned `--rm` Vivado 2026.1 container used an 8 GiB memory limit, two CPUs/threads and the existing RAM/memory-pressure gates. Tools and the legitimate existing license were mounted read only, with actual host identity unchanged. No RTL, clock period, timing exception, blanket fanout property, retiming option or board connection changed. There was one attempt, no automatic retry and no further vendor run.

The tool retained warning `Physopt 32-745`: the starting negative slack is much larger than the range where post-route physical optimization is usually most effective. Warning `Constraints 18-8777` reports unavailable files for tile splitting. The existing out-of-context `HD.CLK_SRC` warning and missing real I/O delays remain open. DRC and methodology summary counts are unchanged: 89 DRC warnings and 2,405 methodology warnings, including large-setup and missing-I/O-delay findings. No warning was waived. Real I/O arrival/required times, clock-source/board relationships and CDC qualification remain inherited and open.

## Retained evidence and portability

- Attempt: `experiments/python-gamebub-v106/postroute/20261108T031341008267Z`.
- [Execution receipt](../../experiments/python-gamebub-v106/postroute/20261108T031341008267Z/receipt.json), schema `v106-postroute-physical-diagnostic-v1`, SHA-256 `700f6dac3f5dd42ed6b70aa1fecbcec0f823f88e0317e95fb799aca497b65450`.
- [Independent report audit](../../experiments/python-gamebub-v106/postroute/report-audit.json), schema `v106-postroute-independent-report-audit-v1`; hashes below bind the finalized portable auditor and result.
- [One-attempt ledger](../../experiments/python-gamebub-v106/postroute/attempt-ledger.json) records the 600-second cap, actual elapsed time and unselected status.
- External output checkpoint: `/home/lori/gamebub-build/cu66-v69/v106-postroute-20261108T031341008267Z/results/postroute.dcp`, SHA-256 `f2382e1f94edbd5971ebfb7aba48c015ec37df45498f0ba5319b85a9da2ede73`. It is retained for review, not selected for hardware.

The default [auditor](../../scripts/cu66-v106/audit_postroute.py) verifies recorded execution before/after checkpoint hashes against the retained parent artifact receipt, plus every copied report, recipe and timing/route summary. It requires neither the external checkpoint nor a license. `--verify-external-checkpoint` additionally verifies current external bytes when explicitly requested; it produces the same canonical report JSON. Both modes passed here, including a default-mode check that actively rejected all `.dcp` file reads. See [portability evidence](../../experiments/python-gamebub-v106/postroute/audit-portability-check.json). Earlier external-file-required audit evidence is preserved under `postroute/audit-history`; no vendor job was rerun for that audit-only change.

Final auditor SHA-256: `ef6ba7359c1a835c773957dd1eaf21be15632bc2dca97fef934da9a6a58cb9ac`. Final portable report SHA-256: `f2ffc6433d54644cac0f7f7b684860fa2223ade3f4c0e5b2e67f70c42314f5f2`.

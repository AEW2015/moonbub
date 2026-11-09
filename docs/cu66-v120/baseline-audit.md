# V120 Independent Baseline Audit

Date: 2026-11-09. Read-only inspection of branch `study/gamebub-v120-range-ingress-timing-20261109` at `155b8c64f588af90fcfffd61201bfea14e574386`. The original baseline manifest is `experiments/python-gamebub-v120/audit/baseline.json`. Detailed independent checks are in `experiments/python-gamebub-v120/audit/baseline-independent.json`; the earlier alias-path comparison was preserved in `baseline-alias-comparison.json`.

## V119 source and timing provenance

The V119 handoff pins the initial 100 MHz receipt (`6efbbb5f484b108aae9534b582b830844ef413ff230b3d4ccb1daabb909f32df`), its repeat (`66ad8d7742faf5852049f8415ec2cb76356aca4da9e1d0548f5c622fbf7f9d0b`), and failed 125 MHz receipt (`6ffc39f31acc756eb96536ba7d3e3e511bddd1369e15ad4e7dd81372562b3664`). Both 100 MHz receipts use the same 18-entry source pin map (digest `1f498aa58144836ac39ba72422781532cbe51329b36d958eee97f96328c0df8b`), the same pinned Vivado image, 10 ns target, completed component routing, zero setup/hold/pulse failures, and **+0.024 ns WNS**. The 125 MHz route completed with zero routing errors but failed setup: **−2.105 ns WNS**, with 14,720 / 103,689 setup endpoints failing. This is internal component evidence only; it does not qualify a full parent or hardware.

The V119 receipt's source keys are compile aliases. For each of the 18 aliases, `source_origins[alias].path` identifies the selected source content and SHA. All **18/18 selected origin files match their pinned SHA**, and all three native run `source-snapshot/<alias>` copies match their receipt alias pins (**18/18 per run**). The initial comparison of current canonical alias-path files against those pins produced 14 differing paths; that comparison is preserved in `baseline-alias-comparison.json` and is expected from the alias-to-origin mapping. It does not indicate source or baseline corruption.

## Protected files and repository state

Both existing untracked marker testbenches match the V120 baseline manifest by SHA-256, byte size, and nanosecond mtime. Tracked and index diffs are empty. At the initial snapshot, the untracked paths were the V120 experiment directory and the two protected marker files. `fpga/experiments/cu66-v120-range/` appeared during concurrent root work after that snapshot; this audit did not modify it. No `AGENTS.md` is present in this repository.

## Host and container snapshot

At the initial audit snapshot, host available memory was 23.89 GiB, memory PSI full avg10 was 0.00, and the combined memory-plus-swap used ratio was 0.270; each dispatch gate passed. Docker stats then showed the existing `acorn-nexys4-ddr` container at 151.83% CPU and 1.909 GiB memory. At the later refresh, the same running container was idle at 0.01% CPU and 639.5 MiB; host available memory was 23.91 GiB, memory PSI full avg10 was 0.00, and combined used ratio was 0.270. Recheck the gates at each job launch; root may dispatch up to two study jobs when the gates pass and the container is idle. No user container was stopped.

Both required pinned images are locally available by exact digest: Vivado 2026.1 `sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742` and Verilator `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`. The stated native tool directory and license path exist; license contents were not read. Vivado MCP session listing returned `Transport closed`, so CLI inspection was used as the fixed fallback.

No builds, compilers, simulations, native flows, source modifications, or Git mutations were run.

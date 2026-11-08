# V113 scratch phase-validation check

The focused V113 scratch check completed on the source-pinned candidate. It
changes no public cycles and retains the frozen V112 scratch equivalence and
physical-owner checks. The prepared candidate's reversible edit recipe, source
hashes, adapter hashes, compile commands, logs, traces, and per-artifact hashes
are retained in the selected [result](../../experiments/python-gamebub-v113/scratch/results.json)
and its immutable [attempt](../../experiments/python-gamebub-v113/scratch/attempts/20261108T210553869440Z/results.json).
The read-only [evidence rehash](../../experiments/python-gamebub-v113/scratch/audit.json)
rechecks the nine pinned input files and all sixteen retained attempt artifacts,
and records the runner and independent phase-driver hashes.

## Observed checks

| Check | Seed 113301 | Seed 113302 |
| --- | ---: | ---: |
| Full scratch transactions | PASS, 72 | PASS, 72 |
| Corrupt-response cases | PASS, 128 | PASS, 128 |
| Read-owner cases | PASS, 4 | PASS, 4 |
| Bank / offset coverage masks | PASS, 15 / 65535 | PASS, 15 / 65535 |
| DC-line boundary transactions | PASS, 48 | PASS, 48 |
| Begin-sideband noise edges | 128,532 | 128,602 |
| Historical accepted-write/drain hazard checks | PASS, 9 directed checks | PASS, 9 directed checks |

The additional phase-table check source-extracts the candidate's generated
`phase_input_bad` logic and compares its selected bit with the independent
frozen V112 predicate for all eight 3-bit phase encodings. It passed 800,192
comparisons, including 100,000 seeded random vectors and directed width,
count, rank, value, epoch, and position boundaries. The reference preserves the
special `phase == 0` case for phase 0; phases 4–7 use the low two bits for
band/count selection while retaining the nonzero-phase sparse rule.

Compilation used Verilator `--assert -Wall`, C++ `-Wall -Wextra -Werror`, and
`-j 1`. No warning suppression or disabled assertion was used. The runner
default is preparation-only; `--run` requests the bounded RTL execution. Native
timing, synthesis, hardware, and full decoder throughput were not measured.

Seven earlier attempts are retained; the first six stopped during compile
preflight, and the seventh completed the scratch checks before the strict
phase-probe compile caught an unnamed generate block. The selected PASS is the
later attempt linked above.

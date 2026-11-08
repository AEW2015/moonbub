# V112 retained attempts and gate history

Each selected summary identifies its exact passing receipt and source hashes.
Earlier attempts remain evidence of their own source/verification versions;
they are not overwritten or relabeled.

| Record | Outcome and scope |
| --- | --- |
| Initial static native-driver review | Correctly refused preparation while focused proof was FAIL and full-Q absent. Its unsupported CLI-choice finding was fixed before the actual full-Q run. Later prepared-card audits bind the final driver. |
| Focus attempt `20261108T193302716067Z` | Scratch and admission checks passed; strict geometry-probe compilation failed on a probe-port/function-argument name collision. Retained FAIL. |
| Focus attempt `20261108T193449002942Z` | Probe-only naming repair and explicit replay-helper pins; unchanged production candidates. All six seeded runs PASS with assertions and strict warnings. |
| Harness attempt `20261108T193144067344Z` | Monotonic chronology assertion rejected an overflowing real-to-integer time conversion before publication. Retained FAIL. |
| Harness attempt `20261108T193232891986Z` | Integer-context-time correction passed ten repeated presentations and fault controls. Retained intermediate PASS. |
| Harness attempt `20261108T193646980851Z` | Final selected PASS: unused declarations removed and actual QSPI abort status/drop readback added. Fresh compile and all integration controls rerun. |
| Full-Q attempt `20261108T193657906227Z` | Complete candidate PASS: both original seeds, 44 case profiles and 42 directed checks; exact old stdout/events/cycles/canonical pixels. |
| Native pre-dispatch rejection | PSI full avg10 was 7.06 despite ample available RAM. The original gate refused before any dispatch reservation or native process; no initial trial was consumed. |
| Subsequent native dispatch | PSI settled to 0.00, and the same audited cards were launched without source, clock, method or resource-policy changes. |

The selected [focused](../../experiments/python-gamebub-v112/control/results.json),
[harness](../../experiments/python-gamebub-v112/harness/results.json),
[canonical](../../experiments/python-gamebub-v112/canonical/results.json) and
[native resource-rejection](../../experiments/python-gamebub-v112/coordination/launch-gate-rejections.json)
records distinguish their scopes. A native route that completes but misses
setup is a completed measurement with an open timing gate, not a positive
clock result. Only a genuinely positive actual route can consume the one
fresh-repeat slot.

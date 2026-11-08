# V110 count-domain focused audit

**Audit result: focused evidence and its current source bindings pass.** This is a read-only receipt audit. The focused simulation is not the full canonical qualification and gives no native timing or hardware claim.

The selected attempt is `20261108T165838042001Z`. Its summary (`count-domain/results.json`, SHA-256 `4fd457a7…`) and immutable attempt results (SHA-256 `1dde963b…`) report `PASS`, an actual RTL run, strict warnings with no warning suppression, unchanged assertions, and zero added public cycles. I checked all 52 hashes listed in the attempt artifact manifest; each matches its retained artifact. The selected context and ingress source hashes are pinned in the summary, and the count adapter now matches the current policy pin (`f8cfe2c5…`).

The focused run records 14 actual commands: 8 successful positive commands and 6 expected original-assertion rejections, total across the run. The negatives cover mode 1 and mode 2 at indices 33, 37, and 41, with expected exit 134. Both context simulations were freshly run for seeds 111401 and 111402. Each checks the inherited 55 cases across 8 configurations and 172 directed checks, 4,260,918 geometry cases, and 8,064 domain starts (6,300 enabled and 1,764 excluded AC-count cases). Each capture run records 607 captures and 8 actual raw packets. Each whole-ingress run records 76 packets, 36 cancel retries, and 754,644 golden coefficients.

The selected context executable was **reused, not newly compiled**. The receipt binds it to the prior retained attempt `20261108T164816692533Z` (SHA-256 `d02dab2d…`), the same six compile-input hashes, source order and compiler flags, and executable SHA-256 `080b4246…`; both selected-run context simulations are fresh. The ingress was freshly compiled from the selected focused sources (binary SHA-256 `43266004…`). The pinned tool image content ID is `sha256:b35d0961…`; its receipt explains that the earlier receipt records only the tag and was not changed retroactively.

Two earlier failed attempts remain retained. Attempt `20261108T164045103852Z` stopped at a strict `DECLFILENAME` fixture warning; attempt `20261108T164816692533Z` stopped on stale flattened C++ fixture member bindings. Both report `actual_RTL_run=false`. Neither failure is a DUT mismatch, and neither is omitted from the audit trail.

The current driver’s read-only parent closure, specialization-input validation, and focused-receipt closure all pass. The refreshed pure guard receipt is tied to the current policy and driver, with 64 checks (7 positive and 57 negative); these are guard tests, not new RTL runs. The current full canonical result file was absent at audit time, so the count-domain route remains ineligible for native preparation pending the required canonical PASS.

The specialization scope remains conditional: generic context comparison is unconditional; only the selected enabled context comparison excludes an owner that violates the explicit AC consumed-start count precondition. The whole ingress retains unconditional public, invalid, error, counter, debug, and memory comparisons. The result explicitly does not claim all private state is exact.

Machine-readable pins and checks: [`count-domain-focused-final.json`](../../experiments/python-gamebub-v110/audit/count-domain-focused-final.json).

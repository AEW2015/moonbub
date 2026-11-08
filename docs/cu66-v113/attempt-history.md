# V113 retained attempt history

This inventory summarizes retained V113 focused and spatial attempts from their attempt receipts and compile/simulation logs. Failed attempts remain preserved. No attempt directory, log, source or selected proof artifact was deleted or rewritten by this inventory.

## Focused geometry, scratch and inverse

| Area | Attempt | Status | Failure/result |
| --- | --- | --- | --- |
| Geometry | `20261108T205255315701Z` | PASS | Both geometry/context probes compiled; actual RTL result is PASS.
| Scratch | `20261108T210216045674Z` | FAIL | `need` was unavailable to separately compiled historical hazard translation unit.
| Scratch | `20261108T210251891353Z` | FAIL | `scratch_helpers.hpp` preinclude missing.
| Scratch | `20261108T210305215538Z` | FAIL | Unused `need` helper treated as error by `-Werror`.
| Scratch | `20261108T210333576618Z` | FAIL | Same strict unused-helper warning.
| Scratch | `20261108T210406860401Z` | FAIL | Harness-generation assertion before any compile command or RTL run.
| Scratch | `20261108T210419567827Z` | FAIL | Duplicate `historical_hazards_main` at link from compiling wrapper and included hazard source separately.
| Scratch | `20261108T210511102717Z` | FAIL | Main scratch compile passed; separate predicate probe stopped on fatal `GENUNNAMED` warning.
| Scratch | `20261108T210553869440Z` | PASS | Selected. Seeds 113301/113302 each pass 72 full transactions, 128 corrupt responses, 48 DC-line boundary transactions and the original oracle set. Independent predicate probe passes all 8 phase encodings and 100,000 random vectors (800,192 comparisons).
| Inverse | `20261108T205300321394Z` | FAIL | Verilator rejected reserved identifier `cell`.
| Inverse | `20261108T205312711311Z` | FAIL | Fatal strict `UNUSEDPARAM` warning for stale `M_EMIT`.
| Inverse | `20261108T205323248625Z` | PASS | Both seeds pass 48 boundary rows and 25 directed checks. Retained PASS attempt; not the selected receipt.
| Inverse | `20261108T205423994425Z` | PASS | Selected. Both seeds pass 48 boundary rows and 25 directed checks.

The scratch compile recipe was simplified to compile `tb_bank.cpp` as the single wrapper translation unit; it already includes the scratch test and historical hazard checks. The absent helper preinclude and separately compiled duplicate entry points were removed from the final recipe. The phase probe's generated block was given a label to satisfy strict warnings. Inverse compile issues were corrected by renaming the reserved identifier and removing the obsolete parameter.

## Full spatial and custom transport

| Attempt | Status | New full component profiles / checks | Disposition |
| --- | --- | ---: | --- |
| `20261108T210733724256Z` | FAIL | 44 / 42 | Both component seeds passed 22 cases and 21 directed checks. Transport-model compile passed; adapter compile failed because a Verilator header's unused `obits` parameter was promoted by `-Werror`. This attempt is the retained source of final reused component evidence.
| `20261108T212312585460Z` | FAIL | 44 / 42 | Both component seeds passed again. Receipt records `KeyboardInterrupt()` during the transport phase; no transport verdict was committed.
| `20261108T212355592057Z` | PASS_V113_SPATIAL_CANONICAL | 0 / 0 | Selected. Reuses the earlier actual-RTL component result, records 44 qualified profiles and 42 qualified directed checks, and executes both transport seeds successfully (12 profiles plus two abort/reset retries per seed, exact canonical bytes).

The adapter compile uses system include treatment for Verilator headers. The selected attempt does not count reused canonical tests as new execution: its new component counts are zero, while its qualified inherited component counts remain 44/42.

## Selected proof artifacts

- Geometry: `experiments/python-gamebub-v113/geometry/attempts/20261108T205255315701Z/results.json`
- Scratch: `experiments/python-gamebub-v113/scratch/attempts/20261108T210553869440Z/results.json`
- Inverse: `experiments/python-gamebub-v113/inverse/attempts/20261108T205423994425Z/receipt.json`
- Spatial: `experiments/python-gamebub-v113/spatial/attempts/20261108T212355592057Z/receipt.json`

The machine-readable per-attempt statuses, failure categories and accounting are in `experiments/python-gamebub-v113/audit/attempt-history.json`. This inventory does not pin mutable root summaries or native `RUNNING` receipts.

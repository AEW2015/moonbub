# Reproduce V120

These commands record the campaign. Use a disposable worktree and a new explicitly declared output namespace/ledger for another campaign; published inputs, receipts and result selectors remain immutable. Root alone dispatches heavy work, with at most two global jobs and the RAM/PSI/combined-use gates in the plan.

```bash
python3 scripts/cu66-v120/range/qualify.py --run --root-grant ROOT_V120_RANGE
python3 scripts/cu66-v120/peer.py --run
python3 scripts/cu66-v120/spatial.py --run
python3 scripts/cu66-v120/live_guard/qualify.py --run --root-grant ROOT_V120_PARENT
```

First qualify focused, full-component/actual transport, physical-debt peer/retry and guarded byte/row parent evidence. Then prepare, audit and dispatch a fixed clock trial:

```bash
python3 scripts/cu66-v120/native.py --trial integrated-125
python3 scripts/cu66-v120/audit_native.py PREPARED_PREFLIGHT_PATH --auditor REVIEWER_NAME
python3 scripts/cu66-v120/native.py --run --preflight PREPARED_PREFLIGHT_PATH --audit PREPARED_AUDIT_PATH
```

Use `--trial integrated-100` for the independent declared 10 ns control. The preflight helper shares qualification/budget logic with the dispatcher; it separately validates source, clock, recipe, tool image and constraints. It is a second pass, not an independent reimplementation of the full proof checker. Terminal agent audits separately read source/artifact pins and raw tool reports.

A positive source/clock is qualified only after a new preparation with `--repeat-of INITIAL_RECEIPT_PATH` and its separate audit/launch. Reserve these repeats until the selected source is known. The policy bounds two compositions, four initial source/clock trials and two positive repeats, at most one per clock. A repair composition needs its own policy/proofs and actual earlier routed cause. No unchanged-source negative rerouting or strategy search.

The final selected repair study uses range A plus admission header-total equality preparation. Its historical commands, in prerequisite order, are:

```bash
python3 scripts/cu66-v120/admission_match/qualify.py --run --root-grant ROOT_V120_ADMISSION_MATCH
python3 scripts/cu66-v120/admission_repair/peer.py --run
python3 scripts/cu66-v120/admission_repair/spatial.py --run
python3 scripts/cu66-v120/admission_repair/live_guard/qualify.py --run --root-grant ROOT_V120_ADMISSION_REPAIR_PARENT
python3 scripts/cu66-v120/admission_repair/native.py --trial integrated-125
python3 scripts/cu66-v120/admission_repair/audit_native.py PREPARED_B_PREFLIGHT_PATH --auditor REVIEWER_NAME
python3 scripts/cu66-v120/admission_repair/native.py --run --preflight PREPARED_B_PREFLIGHT_PATH --audit PREPARED_B_AUDIT_PATH
```

Use `--trial integrated-100` for B's independently declared 10 ns measurement. These legacy trial identifiers describe clock trials; the repair dispatcher accepts only the repair composition, uses `repair-policy.json` and writes `repair-study/`. Its qualification logic also checks the new admission file's own lossless packaging. The original root dispatcher remains frozen for Source A. The older `scripts/cu66-v120/repair/` preparation (address plus context) is unselected and was never executed; it does not describe Source B. A100 failed and receives no positive repeat. Any positive B clock requires its own fresh repeat.

```bash
python3 scripts/cu66-v120/collect.py
python3 scripts/cu66-v120/failures.py
```

The pinned backends remain Verilator 5.020 (`--assert -Wall`, C++17 `-O2 -Wall -Wextra -Werror`, compiler job one) and Vivado 2026.1 build 6511674, fresh default synthesis/opt/route with ExtraNetDelay_high placement. Clocks load before synthesis. No guessed I/O delay, timing exception, fanout attribute or clock relaxation is added. Model cycle conversions are conditional; they do not validate hardware 30 fps, full-parent routed timing or under-10-ms hardware latency.

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

```bash
python3 scripts/cu66-v120/collect.py
python3 scripts/cu66-v120/failures.py
```

The pinned backends remain Verilator 5.020 (`--assert -Wall`, C++17 `-O2 -Wall -Wextra -Werror`, compiler job one) and Vivado 2026.1 build 6511674, fresh default synthesis/opt/route with ExtraNetDelay_high placement. Clocks load before synthesis. No guessed I/O delay, timing exception, fanout attribute or clock relaxation is added. Model cycle conversions are conditional; they do not validate hardware 30 fps, full-parent routed timing or under-10-ms hardware latency.

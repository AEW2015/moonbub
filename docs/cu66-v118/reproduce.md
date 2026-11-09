# Reproduce V118

Use the study branch at its published commit. Earlier-version sources, proofs and checkers are immutable controls. See [plan](plan.md) and the machine-readable policy for the resource and physical-run budget. Root is the sole dispatcher; commands below document the executed campaign and are sequential unless the two-slot grant explicitly permits overlap. Run new simulations in a disposable worktree so their selected-result pointers do not replace the published selectors. Use the [handoff preparer](handoff.md) for portable source-only preparation.

```bash
python3 scripts/cu66-v118/reconstruct/qualify.py --run --root-grant ROOT_V118_R
python3 scripts/cu66-v118/scratch/qualify.py --run
python3 scripts/cu66-v118/response_priority/qualify.py --run --root-grant ROOT_V118_RESPONSE
python3 scripts/cu66-v118/peer.py --run
python3 scripts/cu66-v118/spatial.py --run
python3 scripts/cu66-v118/live_guard/qualify.py --run --root-grant ROOT_V118_PARENT
```

These are new executions. Each creates a fresh attempt and snapshots source/recipes before use. The full and LIVE runners deliberately measure V118's new latency; the original V117 exact-cycle checkers are retained. Successful full-decoder accepted-event tuples are compared after excluding only timestamps and interleaving, and the original per-transfer ordered goldens remain enabled. Error/cancel prefixes retain the independent benchmark oracles rather than a fixed old prefix length.

Only after all selected focused, canonical, peer and guarded-parent receipts qualify:

```bash
python3 scripts/cu66-v118/native.py --trial integrated-125
python3 scripts/cu66-v118/audit_native.py PREPARED_PREFLIGHT_PATH --auditor REVIEWER_NAME
python3 scripts/cu66-v118/native.py --run --preflight PREPARED_PREFLIGHT_PATH --audit PREPARED_AUDIT_PATH
```

Measure100MHz separately with `--trial integrated-100`. The audit checks that the copied XDC bytes match the canonical clock file; the launch rechecks this identity. Native uses the pinned Vivado2026.1 image and existing read-only license. No license contents are needed in chat or source control.

Do not reroute a negative unchanged composition/clock. A positive component result needs a separately prepared fresh run with `--repeat-of INITIAL_RECEIPT_PATH`, identical source/tool/recipe, and a new audited launch. Retained dispatches consume the frozen budget, so a new physical campaign needs a separately named output namespace, ledger and explicitly budgeted runner. The frozen runner deliberately rejects a duplicate source/clock launch in the published ledger. Preserve that runner and all existing receipts; do not remove dispatch records to bypass the budget.

```bash
python3 scripts/cu66-v118/collect.py
python3 scripts/cu66-v118/failures.py
```

The replay-owner candidate is dormant unless its dedicated source-bound proof and integration are explicitly selected. A prepared source is not a tested feature. Native OOC results qualify only the measured component clock, not complete-board I/O, CDC, memory, ESP32 transport, hardware30fps or hardware decode latency.

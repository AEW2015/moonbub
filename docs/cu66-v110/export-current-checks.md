# V110 current preflight source exports

Prepared four source-only replay trees with `scripts/cu66-v110/export_current_replay.py`. The exporter copies the 18 hash-pinned sources (17 RTL and one header), plus the preflight-bound `run.tcl`, `report.tcl`, and XDC. Its generated inputs resolve source and include paths relative to the replay build directory and select fresh RTL. The export needs no original build directory or synthesis checkpoint.

| Composition | External source tree | Bound watchdog | Synthesis declaration |
| --- | --- | ---: | --- |
| Default | `/home/lori/gamebub-build/cu66-v69/v110-current-replay-default-20261108T1624` | 2400 s | Default, directive omitted |
| Cursors | `/home/lori/gamebub-build/cu66-v69/v110-current-replay-cursors-20261108T1624` | 2400 s | RuntimeOptimized, explicit |
| Address cursors | `/home/lori/gamebub-build/cu66-v69/v110-current-replay-address-cursors-20261108T1624` | 3600 s | Default, directive omitted |
| Count domain | `/home/lori/gamebub-build/cu66-v69/v110-current-replay-count-domain-20261108T1722` | 3600 s | Default, directive omitted |

Each README uses the watchdog from its prepared input card. The 3600-second address-cursor and count-domain values are the bound prepared method budgets; it does not change synthesis, placement, clock, or functional sources. The export checks verified copied source and recipe hashes, all manifest artifact hashes, relative Tcl paths, fresh-RTL mode, and `PREPARED_NOT_RUN` status flags.

The count-domain check also evaluated the actual inputs with plain Tcl at the real build root and a virtual relocated path containing a space. All 17 source paths, header include path and XDC resolved relative to the selected root. Its manifest preserves the exact public/invalid/counter contract, conditional internal count-domain specialization and existing private-payload scope.

The trees are source packaging only. They do not report a Vivado run, native timing result, clock-closure pass, or hardware qualification. A separate authorized execution must retain and review the implementation reports.

- [Default export check](../../experiments/python-gamebub-v110/audit/export-current-default-check.json)
- [Cursor export check](../../experiments/python-gamebub-v110/audit/export-current-cursors-check.json)
- [Address-cursor export check](../../experiments/python-gamebub-v110/audit/export-current-address-cursors-check.json)

- [Count-domain export check](../../experiments/python-gamebub-v110/audit/export-current-count-domain-check.json)

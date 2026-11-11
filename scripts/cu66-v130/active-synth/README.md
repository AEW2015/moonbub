# Exploratory active-scan synthesis-only trial

This is **not** a board implementation, timing signoff, 30 fps or latency
measurement. The preflight snapshots all 18 V130 source origins while replacing
only the admission source with the independently tested active-scan candidate.
It pins the positive/negative focused RTL receipts and validates the exact
reversible two-edit derivation. Full-parent qualification and the external
invalid-data contract remain open.

The prepared `run.tcl` is byte-for-byte the retained V120 125 MHz flow through
`synth_design`, its checkpoint and `v120_reports synth`. The post-synthesis
suffix only collects a read-only `active_cell` / `active_scan_value` mapped-cell
and registered-input fan-in inventory and terminates. The original report Tcl,
8 ns XDC, part and ordered source aliases are unchanged. The inventory may not
resolve an original RTL name after optimization; an absent mapping must be
reported as unknown rather than inferred as BRAM. Synthesis-only slack uses
estimated placement/routing and is not post-route timing.

Preparation and source/recipe audit:

```sh
python3 scripts/cu66-v130/active-synth/native.py prepare
python3 scripts/cu66-v130/active-synth/audit_preflight.py PATH_TO_PREFLIGHT --auditor REVIEWER
```

The actual exploratory run, only after independent review of those files:

```sh
python3 scripts/cu66-v130/active-synth/native.py run --preflight PATH_TO_PREFLIGHT --audit PATH_TO_AUDIT --license-file PATH_TO_LICENSE
```

The launcher checks current host memory and pressure, caps the container at two
CPUs and 8 GiB total RAM/swap, enforces a watchdog and stops on the same pressure
limits as the earlier runs. It retains failures, source snapshots, reports,
logs and hashes; it does not print license contents. Vivado itself is mounted
from the host, so the container image hash does not pin the installed binaries.
A complete timing claim still requires complete-parent functional testing and
fresh fully constrained physical routes on the actual target.

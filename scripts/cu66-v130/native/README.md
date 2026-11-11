# V130 speculative admission: exploratory component timing

`native.py` builds an out-of-context component from the exact V129 source order,
part and 8 ns clock recipe, replacing only the speculative admission source.
It snapshots all 18 source origins and validates the V129 baseline proofs and
V130 focused/mutation receipts. The generated audit checks source/recipe and
resource bindings independently of the launcher implementation, but an
independent reviewer should inspect both before execution.

The candidate's invalid data output can differ when response-valid is false;
the external consumers have not been proven to respect that contract. A focused
pair PASS is **not** full-parent qualification. Even a positive route would be
an exploratory component measurement, with no board bitstream, board timing,
30 fps or under-10-ms hardware claim. Do not use it as a hardware release.

The currently prepared card and audit are:

```
experiments/python-gamebub-v130/spec-read/prepared/v130-spec-read-125-20261111T024532679570Z-764e39/preflight.json
experiments/python-gamebub-v130/spec-read/prepared/v130-spec-read-125-20261111T024532679570Z-764e39/audit.json
```

The earlier `024502...` preflight predates final audit hardening; its pinned
script hashes no longer match and it is not runnable. For a new preflight use
`python3 scripts/cu66-v130/native/native.py prepare --mhz 125`, then audit that
exact output with `audit_native.py <preflight> --auditor <reviewer>`. The run
command takes `run --preflight <path> --audit <path> --license-file <path>`.
The license contents are never printed. Execution uses the existing pinned
Vivado container with a separate read-only host Vivado mount; the container
hash does not authenticate those mounted binaries.

The launcher samples host memory and PSI, starts only with at least 8 GiB
available, full PSI avg10 below 1 and combined used fraction below 0.85. It
stops below 4 GiB available, after two samples of full PSI avg10 at least 5,
or at combined used fraction at least 0.90. Each container has 2 CPUs, 8 GiB
memory including swap, 2,048 PID limit, and a bounded 3,600-second watchdog.
No timing exception or guessed I/O delay is added. Fresh failed/aborted receipts
are retained and are not silently treated as successful runs.

After a completed route, run `python3 scripts/cu66-v130/native/audit_post_route.py
--receipt <finished-receipt>`. The post-route auditor checks recorded source,
recipe, tool transcript, timing, routing, methodology and internal coverage
against raw reports and the V129 baseline. Its integrity PASS is separate from
`component_internal_target_pass`; neither result qualifies V130 full-parent
functionality or a board. Its retained baseline/negative self-tests are in
`experiments/python-gamebub-v130/spec-read/audit/post-route-auditor-self-test.json`.
Like the prior audit, it checks external checkpoint bytes at original local build
paths; those files and path staging are needed to repeat that check elsewhere.

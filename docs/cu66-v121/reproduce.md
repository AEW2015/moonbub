# Reproduce V121

Use Linux, Python 3.10+, Git, Docker and the retained pinned simulation image
(`Verilator 5.020`). Native timing uses the existing `acorn-nexys4-ddr:2026.1`
image and the user's installed Vivado 2026.1/build6511674 tools and legitimate
license. No board, ESP32, Sunshine service or hardware cable is required for
these component experiments.

Keep at most two heavy jobs, each two CPUs/8 GiB with no extra swap allowance.
The runners also gate on available RAM, memory pressure and combined RAM/swap
use. Existing unrelated marker-recovery files must remain unchanged and unstaged.

## Functional gates

Validate the retained reversible derivations, then run the focused queue test:

```bash
python3 scripts/cu66-v121/request/prepare.py
python3 scripts/cu66-v121/integration/prepare.py
python3 scripts/cu66-v121/request/qualify.py --run --root-grant ROOT_V121_REQUEST
```

The grant names are local scheduling guards, not authentication credentials.
They assert that the operator has reserved the required resource slot.

After focused PASS, run these independently in separate terminals if two slots
are available. Each uses strict compilation and fresh candidate models:

```bash
python3 scripts/cu66-v121/integration/peer.py --run
python3 scripts/cu66-v121/integration/spatial.py --run
```

Then run the guarded byte/row parent and collect/audit the four-stage result:

```bash
python3 scripts/cu66-v121/integration/live_guard/qualify.py \
  --run --root-grant ROOT_V121_REQUEST_PARENT
python3 scripts/cu66-v121/integration/collect.py
python3 scripts/cu66-v121/audit_functional.py
```

Check each explicit terminal PASS and selected receipt. A compiler exit0 alone
does not pass the functional gate. Older reference binaries/receipts remain
comparison evidence; none qualifies a newly edited candidate.

## Fresh native timing

Only after the four-stage functional index passes:

```bash
python3 scripts/cu66-v121/native.py prepare --mhz 125
```

The printed path is a unique `preflight.json`. Set the following path placeholders
to that output and its sibling `audit.json`; provide your existing license path
without copying its contents into logs or Git:

```bash
python3 scripts/cu66-v121/audit_native.py PREFLIGHT_JSON --auditor REVIEWER_NAME
python3 scripts/cu66-v121/native.py run \
  --preflight PREFLIGHT_JSON --audit AUDIT_JSON --license-file LICENSE_PATH
```

The fixed implementation Tcl/report recipe retains historical `V120_*` log
markers. The surrounding V121 preflight and receipt identify the new source
composition. Clock definition precedes fresh synthesis; no checkpoint is used
for implementation. Reports and recipe/source snapshots are retained in
`experiments/python-gamebub-v121/native/`; larger checkpoints remain in the
receipt's external build directory.

A negative route is not retried unchanged. If all component timing gates pass,
prepare a separate positive fresh repeat with `prepare --mhz 125 --repeat-of
INITIAL_RECEIPT`, independently audit it, then run it as above. No new clock
qualification or hardware handoff is inferred from an initial pass alone.

The optional post-route request query is a separate read-only checkpoint
inspection. It must not be represented as a fresh-RTL run or used to alter
constraints. See [inspection instructions](request-inspection.md).

The original [V120 hardware export](../cu66-v120/handoff.md) remains available
and source-identical to the remote team's pin. V121 does not automatically
replace that handoff or provide a complete board bitstream.

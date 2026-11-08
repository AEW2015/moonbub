# CU66 V108 audit

## Frozen V107 starting point

`experiments/python-gamebub-v108/audit/baseline.json` is a generated,
read-only audit of the selected V107 routed frontier. It binds the exact
selection receipt and constraint snapshot, checks the SHA-256 of each selected
logical source against its actual origin and retained run snapshot, and parses
the routed timing and route-status reports.

The source closure is 18 files (17 SystemVerilog files and one included
quantization header). `selection.json` records both each canonical logical
path and its actual source origin. In particular, the logical V69 IDCT path
maps to `fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv`; that file is
derived from the V106 area implementation with reset changes, not a claim that
the older V69 file supplied the routed source. The `source-snapshot` in the
retained V107 run uses canonical logical paths, so the audit checks those
copies separately from the actual-origin files.

The retained V107 route used the `xc7a100tcsg324-1` part, a fixed 10 ns
component clock, Vivado 2026.1, two threads, and an 8 GiB container limit. Its
route completed with 65,912/65,912 routable nets routed and zero routing errors.
Timing was WNS -2.333 ns with 21,433 setup endpoints failing, WHS +0.096 ns,
and pulse-width slack +3.750 ns. `no_clock`,
`unconstrained_internal_endpoints`, and `loops` each report zero. This is a
component route with the 100 MHz target unmet; it does not establish board I/O,
full-top, hardware 30 fps, or validated decode-under-10-ms qualification. No
Fmax is derived from slack.

The V108 trial input is expected to reuse the exact V107 SYNTH checkpoint and
the same 18-source/constraint binding for each of its six initial placement /
routing strategy rows. The matrix audit will independently check those frozen
input bindings, per-run directives and resource receipts, completed and failed
attempts, native timing checks, routing completion/error counts, and the
selected clean repeat. A failed route remains a failed observation and remains
in the matrix. The predispatch plan and its hashes are immutable evidence; a
later audit result belongs in a separate artifact.

## Running the baseline audit

From the repository root:

```sh
python3 scripts/cu66-v108/audit.py
```

The command reads checked-in V107 selection, receipt, retained snapshots, and
reports. It writes nothing unless `--output PATH` is supplied. Exit status is
zero only when the source, constraints, receipt, timing, and routing checks
match the recorded baseline.

## Baseline artifact

The machine-readable record is
[`baseline.json`](../../experiments/python-gamebub-v108/audit/baseline.json).
It records source-level provenance and the raw signoff facts needed to compare
the V108 runs without converting timing slack into a frequency claim.

## Native launch gates

Before dispatch, the same auditor independently checks each prepared
checkpoint trial against the frozen six-row matrix, exact V107 source aliases
and hashes, parent SYNTH checkpoint, 10 ns constraint/recipe hashes, parser
evidence, approved per-run limits, and active dispatches against the global
two-heavy-job cap. Historical grants do not consume slots after terminal
completion records and receipts exist. For m3–m5 the gate records the required
predecessor and its state at audit time; dispatch still requires a fresh live
check for both predecessor receipt and completion. It returns nonzero if any
binding differs. Gates are retained as `m0` through `m5` under
`experiments/python-gamebub-v108/coordination/`; they are immutable and must not
be regenerated after dispatch.

To inspect a preflight without writing a gate:

```sh
python3 scripts/cu66-v108/audit.py --preflight m0
python3 scripts/cu66-v108/audit.py --preflight m1
python3 scripts/cu66-v108/audit.py --preflight m2
python3 scripts/cu66-v108/audit.py --preflight m3
python3 scripts/cu66-v108/audit.py --preflight m4
python3 scripts/cu66-v108/audit.py --preflight m5
```

Gate files are created once with `--output` only after the audit passes. A
later run audit must be stored as a separate artifact.

## Terminal native receipt audits

The terminal receipt mode verifies the immutable dispatch/gate chain, source
and recipe snapshots, unchanged parent SYNTH checkpoint, run limits and memory
samples, output artifact hashes, then reparses the copied native reports with
the runner retained by that run. Its `PASS_V108_NATIVE_RECEIPT_AUDIT` status
means the evidence is internally consistent; the timing result remains a
separate design qualification field. For example:

```sh
python3 scripts/cu66-v108/audit.py --receipt m0
```

The audit outputs are saved separately as
[`receipt-audit-m0.json`](../../experiments/python-gamebub-v108/audit/receipt-audit-m0.json)
and [`receipt-audit-m1.json`](../../experiments/python-gamebub-v108/audit/receipt-audit-m1.json).
Both initial routes completed with zero routing errors and all routing
completed. Setup remains negative: m0 WNS -2.758 ns with 24,107 setup failures;
m1 WNS -2.788 ns with 24,747 setup failures. Hold slack is +0.096 ns and pulse
slack +3.750 ns on both. Neither trial passes the internal 100 MHz gate, and no
hardware 30 fps or validated decode-under-10-ms result is claimed.

The source-only capacity canonical harness review is in
[`canonical-preflight-review.json`](../../experiments/python-gamebub-v108/audit/canonical-preflight-review.json).
It confirms the original benchmark, packaging and golden inputs match the
selected V107 control, and documents the exact same-seed comparison and bounded
execution plan. The capacity candidate has not yet passed actual RTL checks;
the report does not authorize a run. The separate fresh-RTL capacity-native
builder and runner review is in
[`capacity-native-builder-review.json`](../../experiments/python-gamebub-v108/audit/capacity-native-builder-review.json).

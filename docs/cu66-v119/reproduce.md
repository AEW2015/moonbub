# Reproduce V119

The following commands document this campaign. Use a disposable worktree and a separately declared output namespace/ledger for a new campaign so the published result pointers and receipts remain immutable. Root alone dispatches at most two heavy jobs; each uses 2 CPUs, 8 GiB and no additional swap, with available-RAM/PSI gates.

```bash
python3 scripts/cu66-v119/owner/reconstruct.py --run --root-grant ROOT_V119_R
python3 scripts/cu66-v119/owner/response.py --run --root-grant ROOT_V119_RESPONSE
python3 scripts/cu66-v119/scratch/qualify.py --run
python3 scripts/cu66-v119/owner/producer.py --run --root-grant ROOT_V119_PRODUCER
python3 scripts/cu66-v119/owner/admission.py --run --root-grant ROOT_V119_ADMISSION
python3 scripts/cu66-v119/owner/nonce_boundary.py --run --root-grant ROOT_V119_NONCE_BOUNDARY
python3 scripts/cu66-v119/peer.py --run
python3 scripts/cu66-v119/spatial.py --run
python3 scripts/cu66-v119/live_guard/qualify.py --run --root-grant ROOT_V119_PARENT
```

The nonce supplement explicitly reuses the exact producer model archive/headers/runtime objects identified by its positive parent receipt; it strictly compiles and links a new test bench. It makes no fresh-model claim. The complete producer proof and full component/transport/peer proofs separately compile fresh asserted Verilator models. No production RTL or qualified producer test was modified to add that supplement.

After all selected focused, full, peer, response, nonce and parent proofs qualify:

```bash
python3 scripts/cu66-v119/native.py --trial integrated-125
python3 scripts/cu66-v119/audit_native.py PREPARED_PREFLIGHT_PATH --auditor REVIEWER_NAME
python3 scripts/cu66-v119/native.py --run --preflight PREPARED_PREFLIGHT_PATH --audit PREPARED_AUDIT_PATH
```

Use `--trial integrated-100` for the independent 10 ns control. A positive source/clock result requires another fresh preparation with `--repeat-of INITIAL_RECEIPT_PATH` and a new audit/launch. The runner rejects unchanged-source negative reroutes and enforces the declared campaign budget. Do not delete or overwrite dispatch records to bypass it.

The native flow uses the pinned Vivado 2026.1 image and the existing legitimate read-only license. Simulation retains Verilator 5.020 with assertions, fatal warnings and C++ warnings as errors. Native constraints are the fixed 8 ns or 10 ns OOC clock, loaded before fresh synthesis; actual board I/O, CDC and full-parent timing remain separate requirements.

```bash
python3 scripts/cu66-v119/collect.py
python3 scripts/cu66-v119/failures.py
```

Receipts retain source/recipe snapshots, actual commands, failures and report hashes. Conditional milliseconds derived from model cycles do not qualify a hardware clock, sustained 30 fps or validated board decoding under 10 ms.

Additional isolated candidate preparation from this campaign:

```bash
python3 scripts/cu66-v119/raw_range_model.py
python3 scripts/cu66-v119/range_probe.py --run --root-grant ROOT_V119_RANGE_PROBE
```

The Python model enumerates the complete signed16 range. The standalone Verilator probe also enumerates every input, but is outside the selected pipeline and native source composition. Its published result does not qualify a clock or protocol change. Read-only checkpoint diagnostics retain the failed segment-query attempt and its separate corrected query; their specific operand replay and the general unresolved reset/abort aliases are documented in `checkpoint-diagnostic-results.md`.

The five failed focused campaigns remain in `orchestration/failures.json`. The completed-but-failing A125 timing result and both partial-connectivity diagnostics are retained separately in their native/diagnostic receipts. The successful handoff export and unsupported-period/duplicate-receipt rejection checks are in `audit/handoff-preparation.json`; export invokes no implementation tools.

# Receiver phase summary candidate

Offline-only candidate for one source-bound, validated structured `NETWORK-RESULT.json`. It reads no serial data, connects to no device, does not recompute the telemetry CRC, and does not combine sessions. The input's existing `both_independently_validated` receipt is required; `--expected-input-sha256` must match the checked-in trusted binding. Derived intervals use only timestamps inside that one session.

## Current evidence

The only qualifying physical network result presently found is the V48 V027 run, copied byte-identically into `fixtures/v48-network-result-validated.json`. Its input SHA-256 is recorded in `source-hash-pins.json`. The summary is `v48-phase-summary.json`. V54 has candidate build/host evidence and V55 has native-oracle/host-decoder records, but neither has a physical `NETWORK-RESULT.json` timing export here. They have no physical rows, and this tool calculates no V48-to-V54/V55 speed comparison.

The three V48 retained-frame `native_wall_us` values are 212382, 196723, and 124060 for ordinals 9, 10, 11. They are elapsed wall spans around the native call, not CPU-exclusive time. HU extraction is only its observed stage wall span; no QSPI transaction timing is inferred. Timing missing/invalid/negative values are emitted as `unknown`. Missing raw rows, duplicate ordinal-stage records, missing source identity/validation receipt, and input hash mismatch are refused.

A `model` evidence tag remains `execution_scope=model`; it is never reported as physical. The tool accepts exactly one input/session per invocation, so cross-session joins are not implemented. No CRC recomputation is claimed.

## Run

```powershell
python summarize.py fixtures/v48-network-result-validated.json --expected-input-sha256 E3FAB580BE4788D9ABA6D9988985B2A01B8388A6974FC99EEC1F9F4215A98CBC --output v48-phase-summary.json
python -m unittest discover -s . -p test_summarize.py -v
```

The input, parser, tests, and comparison evidence are bound in `source-hash-pins.json`. See `test-results.json` for the executed test result and the corrected initial fixture-path test discovery failure.


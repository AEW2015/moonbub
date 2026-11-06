# V78 direct canonical receiver

`fpga/experiments/cu66-v78/receiver/cu78_receiver.sv` explicitly forks the frozen V70 receiver. It removes the painter state machine, painter command/result interfaces, RGB slot allocation and all RGB slot ports. Actual compressed-packet parsing, qmap lookup, entropy/inverse reconstruction, canonical hashing, semantic HUD acknowledgement, external HUD write drain and the three-bank owner remain in the transaction.

The API is defined in [interface-contract.md](interface-contract.md). The receiver production SHA-256 is `0bdc872da096cdd070774fa72b90462083fc64da3ab03ec6ecf402d56a6e584a`.

## Validation and irreversible commit

`validated_ready` asserts only after the actual base pipeline has validated its canonical tag, the processor HUD result has matched the active generation/frame/reference/tag/word count, the HUD transfer acknowledgement has matched the candidate bank/tag/word count, and all decoder/reference/HUD memory operations have drained. It remains high while this active transaction is validated and committing, including processor acknowledgement reconciliation. Identity is `active_generation` and `active_frame_id`. Consumers should sample its first assertion per transaction rather than count every asserted cycle as another frame.

Validation does not release reference/front/pending storage. A validated candidate can wait in `COMMIT_READY` for a pending presentation to retire. Hardware canonical/reference acceptance is irreversible: on `commit_fire`, the parser and bank controller commit and a presentation descriptor containing the candidate canonical bank is registered. The processor receives idempotent COMMIT opcode 5 and must acknowledge the matching active generation/frame. Missing acknowledgements are retried using `COMMIT_RETRY_CYCLES`; no dependent frame is admitted until the processor state reconciles. Candidate abort cannot undo a committed frame during `COMMIT_ACK`.

Precommit failure or explicit abort enters `DRAIN`. Candidate operations drain and the processor acknowledges ABORT opcode 6 before reuse. Accepted canonical/reference and committed HUD state remain unchanged. All external adapters must flush on reset; start generations must be nonzero and strictly increase.

## Canonical bank leases

The frozen V69 `cu66_frame_bank_control` allocates from three canonical banks, excluding reference, visible front, pending and active candidate storage. A pending descriptor may coexist with decoding a candidate in the third free bank. `memory_drained` excludes independent front scanout operations, whose ownership remains covered by the front/pending lease.

`presentation_generation`, `presentation_frame_id` and `presentation_bank` are latched together at canonical commit and held until descriptor acceptance. The visible `front_bank`, `front_frame_id` and `front_generation` change only when all of these hold:

- a globally committed bank is pending;
- `presented_generation`, `presented_frame_id` and `presented_bank` exactly match it;
- `vblank` is asserted at the qualified display boundary;
- `scanout_drained` confirms the old front's accepted readers have retired.

Wrong generation, frame ID or bank cannot publish the pending frame. A matching notification with `scanout_drained=0` cannot retire the old front. Finishing a local cache raster never releases the committed bank. Candidate abort must not be connected to cancellation of a committed front's independent scanout work.

## Diagnostics

Numeric stages retain their frozen values where applicable:

| Stage | Value |
| --- | ---: |
| IDLE | 0 |
| PARSER_START | 1 |
| METADATA | 2 |
| WAIT_BANK | 3 |
| BASE_START | 4 |
| BASE_RUN | 5 |
| VALIDATED_READY | 6 |
| COMMIT_READY | 9 |
| COMMIT_ACK | 10 |
| DRAIN | 11 |

Diagnostic magic at `0x000` is `0x43553738` (CU78), and version at `0x004` is `0x00020000`. The 64-bit timestamp at `0x080/0x084` now records validated readiness; it no longer represents RGB painting. Event code 5 means validated readiness, 6 canonical commit, 7 front presentation and 10 successful processor COMMIT acknowledgement. Existing first-fault capture, stale completion count, packet/base diagnostics and eight-entry event ring remain.

## Qualification

Run from the repository root:

```sh
python3 scripts/cu66-v78/run_receiver.py --seed 7801 --per-chain 2
```

The finite Verilator 5.020 behavioral regression builds with `--Wall`, uses `-j1`, and runs in the existing four-CPU/four-GiB `gamebub-cu66-v69-build` container under `/build/v78-receiver`. Source lists are explicit in `receiver/sources.json`. `receiver/lint.json` records the strict lint command and source/log hashes. `receiver/results.json` records exact source/input hashes, execution commands, log hashes and every frame-case counter. The first 29-case qualification is preserved in `receiver/baseline-qualification/`; the current regression adds the concurrent third-bank case.

Current result: **PASS**, 32 frame cases and 39,867,266 simulated clocks, seed 7801. The corpus includes the first key/P pair of each of four independent fixture chains (eight corpus frames). Seven fault/control modes and the concurrent lease sequence are also checked:

| Case | Observed requirement |
| --- | --- |
| Malformed packet CRC | Rejected without changing accepted reference/HUD |
| Abort with a pending canonical write | Candidate drains; accepted reference/HUD retained |
| HUD drain failure | Candidate rejected before publication |
| Canonical write error | Candidate rejected before publication |
| Stale packet/HUD/software replies | Four stale identities discarded; valid frame then commits |
| Wrong displayed bank/generation/frame ID | Three mismatches fenced |
| Correct presentation without old-reader drain | Front retained for eleven blocked boundaries |
| Lost first processor COMMIT acknowledgement | COMMIT retried twice; new admission blocked until reconciliation |
| Front A, committed pending B, candidate C | C uses bank 2; front/reference/pending retained while C is validated and blocked for 37 cycles, then exact B acknowledgement releases the next commit |

Every successful frame produces 8,100 actual RTL output tiles checked byte-for-byte against an independent native decode. The RAM model stores those RTL tile outputs; P-frame references are read back from this storage. The native semantic HUD processor produces the actual HUD data, which is written and read back before its drain tag is acknowledged. `validated_ready` is checked against completed base/HUD/memory work.

These standalone tests use transactional RAM with the frozen V70 raster packed-u8 layout and a controlled presentation acknowledgement endpoint. They do not model the production V74 tile-major SDRAM controller or the continuous direct scanout component. Parent V78 full-system evidence must separately cover those actual components. No target timing closure, physical hardware result, CDC proof, sustained 30 fps or under-10-ms decoding follows from this receiver regression. Simulated clock counts include bounded endpoint delays and are not a measured FPGA Fmax or physical latency.

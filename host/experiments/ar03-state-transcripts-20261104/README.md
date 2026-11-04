# Receiver ownership state transcripts

Schema `ar03-receiver-state-lab-v1` adds explicit model events and expected
receiver state to serialized FG19 controls. It supplements the original 1,725
message histories, which lack physical-drain events. It does not retrofit missing
drain evidence into those histories.

`generated/receiver-state-transcripts.json` contains ten scenarios / 51 steps.
Each records the event, expected state/reply bytes from the actual pinned Python
`frame_credit.Protocol`, and the older native C helper's reply. The native C
receiver states match every compared step. One intentionally retained reply
difference is important for shared-contract review:

- A duplicate REQUEST with the same epoch/frame/nonce/length/body CRC but a
  different requested slot gets GRANT for the original owned slot in the frozen
  Python reference. The older C helper returns BUSY. Both retain the same owner,
  but their reply bytes differ. The new dormant Rust core follows the reference
  behavior; this statement must be checked against its replay results before
  calling conformance complete. The older C files are preserved unchanged.

Scenarios cover normal DATA/FINISH/drain/release, early drain, two owners, a busy
request consuming its serial, stale completion, wrong identity/kind/epoch,
cancel-before/after DATA, nonce exhaustion and unknown-outcome safe stop.
`drain` is an explicit supplied model event bound to a precise owner, never
inferred from time, fragment count, FINISHED or an ingress ACK. Reverse-worker
completion is synchronous in this harness. A lost-reply annotation and safe-stop
event do not simulate a radio or prove sender recovery.

Expected receiver state includes both owner identities and observed-fragment
sets, FINISH state, request/release serial watermarks and safe-stop state.
Packet permits/FIFO ownership, real DMA/read drain, AF03 reference publication,
production reset/rekey and complete sender/receiver networking remain separate
proof obligations. A release poll is not evidence of presentation.

## Reproduce

On Linux/WSL with GCC, Python standard library, and the pinned kit checkout:

```sh
python3 export_states.py --source /path/to/pinned/moonbub \
  --output generated
```

The exporter verifies the actual reference source against its Git blob, compiles
the native C helpers under UBSan, checks the ctypes/native ledger size and asserts
there are no unrecorded state/reply divergences. WSL uses Windows Git for a
Windows-owned worktree's metadata. The native helper sources are in sibling
`ar03-gateway-contract-20261104` and are recorded by SHA-256 in the result.

The normative messages are their hex bytes. Consumers must preserve unsigned
64-bit nonce values exactly; do not load them through floating-point JSON numbers.
Model step numbers are ordering indices, not microsecond or radio timestamps.

Source pin: MoonBub `27a4dde6a7e2ea4fab09d892551ef542f05c8965`.
Output transcript SHA-256:
`5b108cd8f869f4834d81659f91cefd64857cabfc2af5d1a3561e93b44fb023cc`.

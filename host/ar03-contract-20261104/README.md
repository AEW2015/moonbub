# AR03 offline contract bundle

Versioned deterministic export for offline integration work. Contract inputs are bound to MoonBub source commit `27a4dde6a7e2ea4fab09d892551ef542f05c8965`. The coordinated Windows plan is verified from the Windows repository at commit `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`.

`wire-contract.json` and `development-profile.json` are byte-for-byte copies from the pinned kit. `gb_wire.h` is regenerated from the wire JSON and checked byte-for-byte against the kit export. `fg19-history.jsonl` contains all 1,725 retained model-history serialized controls; the index records each message SHA-256 and the JSONL digest. These are reference-model records, not radio captures.

`plan-source/` preserves exact copies of the plan's `MOONBUB-30FPS-PROMPT-20261104.md` and `30FPS-DEVELOPMENT-PLAN-20261104.md`; `plan-source.json` records their Git paths, blob hashes, and commit. Encoder baseline `19cdd7080e7ee181b9bd7a73f4ba5ac5400a36fc` is recorded separately and is not the plan commit or an AR03 endpoint.

`negative-wire-vectors.json` exercises the pinned lab parser's epoch-1 grammar for CRC, truncation, epoch, kind, slot and length failures. The verifier loads the source kit's existing `frame_credit.parse`; it does not introduce a new message type or handshake. Generated JSON files use UTF-8 with canonical LF newlines; the copied contract/profile inputs remain byte-identical to their Git blobs.

## Capability boundary

| State | Identity | What it means |
| --- | --- | --- |
| Last confirmed installed | app UF2 `d43b3137fde1d95358181b23c80d71d3ef908b074510c3d5ae0271d4b46e37d3`; selected FPGA `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9` | Existing MSV1 JPEG application/FPGA. No custom AR03 endpoint. |
| Unflashed candidate | v22 UF2 `329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542` | Not installed and not a custom endpoint. |
| This bundle | Lab contract data + deterministic export only | Lab epoch 1 is not live negotiation. No live custom port, capability negotiation, production reset/rekey, FPGA endpoint, or complete decoder endpoint. |

No handshake bytes, capability response, reset exchange, or readiness acknowledgement are proposed here. Existing retained history lacks a physical full-state/physical-drain transcript; that proof remains separate. `capability-matrix.json` and `plan-source.json` carry the machine-readable status and source binding.

## Rebuild and verify

Use Windows Python when the source and plan repositories are Windows-owned Git worktrees. GNU Git inside WSL cannot read a Windows `.git` pointer file; use a native Linux clone if running under Linux.

```powershell
python host/ar03-contract-20261104/build_bundle.py `
  --source C:/Users/lavat/codex/moonbub-ar03-v20-20261104 `
  --plan-repo C:/Users/lavat/codex/sunshine-gamebub-dxgi-work `
  --out host/ar03-contract-20261104
```

The script checks source-kit HEAD and each relevant input against `git show <pinned-commit>:<path>`, validates every retained control, checks negatives, verifies canonical JSON newlines, and compares all generated outputs byte-for-byte. `test_bundle.py` verifies that a modified bound input is rejected, `--verify-only` leaves bundle and source inputs unchanged, and bundle JSON has canonical LF newlines. Results and exact hashes are preserved under `evidence/coordinated-ar03-20261104/contract/`.

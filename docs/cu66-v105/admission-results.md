# V105 admission coordinate recurrence

The focused candidate passes a clocked comparison of the complete production admission module against the selected V102 baseline. It removes the Y-plane dynamic cell-index division from residual marking, using an 11-bit cached index, 7-bit Y column, row parity, and an 11-bit row-pair base.

Production source: `fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv`.
Frozen SHA-256: `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a`.
Baseline: `afc073e36f813cbcedaec9b21b61cda239453a5b:fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv`, SHA-256 `c300f1bd819a906bfebd64e47648fe08d71f072d88d25cccc15c9a197d305187`.

## Contract

All public interfaces, validation ordering, parser counters, lookup values, packet-RAM read-first behavior, and cycle counts remain unchanged under the tested reachable transactions. The existing 32-bit tile/group state and original 32-bit `cell_index` function remain intact. The original function is used as a non-synthesis assertion oracle. No write queue or new parser cycle was introduced.

Reset, replacement start, and abort invalidate the cache. Only successful HEADER_CHECK initializes live coordinates. Each existing tile increment advances the cache by one; the hidden-only-group shortcut advances it by its existing `group_end - tile` difference, bounded to 1–16. Plane starts clear the coordinate fields. MODE_END invalidates them before the quantizer/chunk parser reuses `plane`. End-only sentinel positions remain representable, and assertions forbid residual marking at those positions.

Every original `modes` declaration, write, and lookup line remains byte-identical. `edit-recipe.json` provides 13 unique literal edits, allowing the root workflow to compose this change independently with the modes-memory candidate. Recipe SHA-256: `9a76577709a92c40486264efa866ac5752352930445bfb109ae81d5568fa1c34`.

## Focused evidence

Selected receipt: `experiments/python-gamebub-v105/admission/attempts/20261107T233813308938Z/results.json`.
Reproduce with `python3 scripts/cu66-v105/admission.py`.

| Check | Result |
| --- | ---: |
| Retained packet cases | 86: 52 accepted, 34 rejected |
| Clock edges | 6,376,122 |
| Distinct directed control checks | 22 |
| Metadata lookup responses compared | 550,808 |
| Dead-cache perturbation edges | 5,140,425 |
| Residual marks independently checked | 530,288 |
| Retained trace rows replayed | 1,352,010 |
| Active-array bits checked | 116,100 |
| Multi-tile hidden-group jumps | 300 |
| End-sentinel observations | 473 |

The corpus includes 14 key and 38 delta packets. Delta mode tags exercised 3,721 all-copy, 4,604 all-residual, 10,751 mixed, and 228 hidden-only groups; these are fixture occurrences, not distinct gameplay captures. Negative cases cover malformed CRCs, tags, bounds, identities, quantizer maps, and chunk descriptions. Directed cases cover reset/abort at live coordinate states, active scanning, queued fetch, registered fetch response, and held receipt; replacement starts; input framing; rejected sizes; snapshot input noise; and receipt backpressure. Packet input delivery contains seeded gaps.

The comparison adapters preserve each complete production body byte-for-byte after removing the module rename and added observation ports. The testbench checks all production outputs before and after every clock edge, exercises every metadata tile index during exhaustive finished-state lookup sweeps, and perturbs the candidate's four coordinate-storage registers only while their valid flag is false. The valid flag and production RTL are never forced. An independent Python decoder checks positive packet residual-coordinate order; integer geometry checks all live trace rows, and a set of residual cell indices checks the active-array scan.

Verilator 5.020 runs with `--assert -Wall`; the C++ testbench uses `-Wall -Wextra -Werror`. Compile/runtime watchdogs are finite, compilation uses two jobs, and the inherited available-RAM/PSI gate remains enforced. All source snapshots, commands, compiler output, binary hash, compressed traces, and failed attempts are retained. `attempt-ledger.json` explains three fixed harness/width diagnostics and preserves both passing attempts.

A separate offline auditor, `fpga/experiments/cu66-v105-admission/audit_trace.py`, independently reparses the retained positive packet maps and checks the compressed trace without importing the simulation runner. Its PASS sidecar is `experiments/python-gamebub-v105/admission/trace-audit.json`; it binds the selected receipt, source/artifact hashes, compressed/raw trace hashes, auditor hash, and all replay counters. It also confirms all three planes, all 90 Y columns, and all 30 Y row pairs were exercised. This audit does not rerun RTL or alter the frozen source.

## Limits

This is reachable-state behavioral evidence, not formal equivalence over arbitrary forced 32-bit parser states. The existing V104 coordinate model supplies the bounded mathematical recurrence argument; the V105 trace connects it to actual packet execution. The inherited real-packet corpus contains repeated source identities, and this focused run does not replace the root workflow's fresh/canonical full-pipeline tests. Routed area/timing, sustained hardware 30 fps, and validated complete decode latency below 10 ms require their separate evidence.

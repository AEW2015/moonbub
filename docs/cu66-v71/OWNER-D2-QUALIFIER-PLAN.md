# D2 owner qualification: narrow exact-cycle changes

Read-only plan; no receiver RTL change is implemented here. D2/v005 final setup
is−1.779ns. Its report traces active_generation through completion identity /
write_pending logic into base result-ready and SHA CE, and hud_expected through
the128-bit HUD comparison / fatal priority into hud_expected CE and event CE.
These are actual routed D2 cones, unlike the older hash-only path.

The frozen receiver already connects `base.abort_i(kill)`, not kill||fatal.
Do not implement an internal-fatal abort register or change its latency.

## Base completion feedback

Owner write_match includes write_pending, generation64, bank and tile identity;
base receives `write_done_valid&&write_match`. Its highest-priority write error
then feeds fail_now, tag_valid, base_tag_fire, tag_ready and canonical/SHA ready.

The complete original base RTL now has a proved invariant:
`fs==RESULT_HOLD -> !write_pending`. Reset establishes it; one-step induction
preserves it with all external inputs and real child-interface outputs
unconstrained. The audit checks704anyseq cells/884bits, including14 relevant
child outputs. This proof does not assume a friendly completion generation or
valid handshake sequence. HASH_WAIT may enter RESULT_HOLD only with no pending
write, and write_fire requires RUN_PLANE, so cannot introduce one in RESULT.

The isolated `tag-phase-cut-v003` candidate therefore computes tag_valid's error
qualifier independently without the write-error or HASH_WAIT tag-error clauses.
Main fail_now/fail_code, write-failure priority0x61, abort/drain and tag mismatch
0x50 remain verbatim. No state, FF or cycle is added. Removing assignments inside
the old priority chain is insufficient: write error would remain an inhibiting
fanin to lower branches. The separate procedural prefix avoids that fanin and
preserves procedural-if handling of X inputs.

This is reachable-state equivalence, not arbitrary forced-state equivalence:
RESULT_HOLD+write_pending1 is an explicit retained counterexample. The control
registers become known after reset; payload/error inputs may remain X/Z.
Conditional tag equivalence and unconditional fail/code/kill equivalence have
separate SAT proofs. Actual base, normal KEY/P, bad-tag/native ABORT and clean
closed-feedback OOC remain distinct gates before root selects a board successor.

## HUD payload self-enable

Simply moving `hud_expected<=p_hud_tag` outside global fatal gating is **not**
an exact public change: expected_hud_tag is continuously exposed, so a fatal
metadata edge could expose a new tag where the original retained its old value.
Do not waive this as an invalid private output or let fault snapshots change.

A narrower candidate can preserve the original capture condition while removing
the impossible HUD-compare feedback from that condition:

1. Prove on actual owner RTL that PARSER_START or METADATA implies
   hud_requested0. These states follow a START that clears the flag; only
   BASE_START/BASE_RUN can assert hud_prepare_valid and set it. The two-state
   phase set, rather than METADATA alone, is the useful inductive invariant.
2. Since hud_match/hud_write_match both require hud_requested, both HUD tag-error
   clauses are false during meta_fire for arbitrary result/drain inputs. Compute
   a metadata-capture fatal qualifier that omits only those phase-impossible
   clauses, retaining every other priority/check. Keep main fatal/fatal_code
   untouched for error decisions and event records.
3. Capture HUD payload on `meta_fire&&!fatal_for_metadata`. meta_fire already
   requires METADATA and !kill. Prove this enable equals original
   `meta_fire&&!fatal` under the phase invariant, including external abort and
   off-spec/stale responses. This preserves accepted and rejected-edge payloads,
   unqualified expected_hud_tag, and old-value nonblocking fault snapshots.
4. Keep metadata state transition, allocation, all publication/leases and other
   payload fields unchanged in the first isolated experiment. If STA shows their
   shared global enable next, extend only with a separately proved exact capture
   condition. No unconditional rejected-edge capture.

Event-ring writes still use the full original fatal priority, timestamp, sequence
and overwrite behavior. Do not delete records, remove their reset visibility,
or delay event_valid without pending-record read bypass and an exact diagnostic
proof. Reassess that cone after the narrow payload/qualifier experiments.

Accepted packet/reference/write tracking updates occur above the fatal branch,
so a same-edge fatal does not generally skip bookkeeping. However a one-bit
pending flag alone does not prove arbitrary simultaneous old-completion/new-
request schedules safe; the actual single-outstanding adapters and identity
rules must be checked before any future abort/drain retiming. No such retiming
is proposed now. COMMIT_ACK's irreversible publication and lost-ACK recovery
remain untouched; no committed cache/context may be rolled back.

# HUD request CE factoring ? isolated candidate

The offline local-equivalence gate **passes**. Exact baseline V001 receiver source is copied under control/, with candidate/ differing in exactly one assignment:

`hud_prepare_valid`: replace `!fatal` with the existing `!fatal_non_hud`.

Control SHA `c8a6e98925b52793f36ca109978d25bb3c17fc02ae77e0a330ea98b89c515eeb`.
Candidate SHA `316123fb1db92d67a797b2a49263500314d5173561a2eff52ef451734f94deb9`.

No global fatal, fatal_code, error reporting, state transition, HUD result/drain validation, bank/reference/commit rule, reset, register or protocol expression is changed. There is no new latency or storage. The selected V001 sources and image are untouched.

## Why this is the correct local cone

The controller captures HUD metadata/ticket on `hud_prepare_valid && hud_prepare_ready`, with `hud_prepare_ready = !hud_pending`. Its separate `hud_identity_match` governs HUD_RESULT/DRAIN and bulk identity. The measured V001 feedback path runs from captured HUD identity through result validation, receiver fatal/eligibility logic, then back to HUD request capture CE. This candidate factors the request eligibility cone; it does not register or weaken command identity validation.

Receiver request eligibility already contains `!hud_requested`. Both excluded fatal causes require hud_requested through the actual hud_match/hud_write_match assignments. All non-HUD fatal predicates remain in the existing fatal_non_hud block. Thus whenever a request can be offered, those two HUD fatal terms are false. Full global fatal/code priority remains unchanged for every other consumer.

## Proof and executed scope

A universal two-state Boolean proof exhausts all 64 assignments of independent base-phase, requested, kill, non-HUD fatal, HUD-result failure and HUD-drain failure variables:

`B & !R & !K & !(N | R*H1 | R*H2) == B & !R & !K & !N`.

The miter extracts the actual state enumeration, kill, HUD match/write-match, prepare assignment and complete fatal/fatal-code/non-HUD blocks from each exact source. It compares request eligibility, effective controller capture, global fatal, fatal_code and fatal_non_hud.

Icarus passes 266,704 stimuli in each of three watchdog configurations (0,1 and the selected 3,000,000,000):

- 262,144 combinations cover every 4-bit state encoding (12 legal/four illegal), 1024 simultaneous HUD/non-HUD fault masks, and 16 requested/abort/reset/pending flag combinations.
- Additional cases cover 17 identity/tag/length/bank/watchdog boundaries, disabled abort permission, both packet-request sources, and 192 directed X/Z stimuli.

The exact source-extracted miter is combinational. Predicates such as reference match and cache match are independent input cuts, so this local test covers a superset of reachable binary values. It is not a full receiver/decoder sequential equivalence proof, a hardware reset test or a timing model. Reset is varied and the effective controller capture gate observes its reset priority; complete sequential reset behavior remains unchanged text and requires system verification.

Four-state caveat: directed X/Z checks use case comparisons and pass, but the64-row proof is two-state and the192 unknown patterns are not exhaustive. This does not establish metastability behavior, all uninitialized-state histories or arbitrary unknown propagation. Preserve that distinction rather than turning local equivalence into a full-system guarantee.

## Evidence and next gate

verify.py generates/executes the source-extracted wrappers and testbench with explicit Icarus commands, owned compiler temporaries, timeouts, return codes and hashes. evidence/run.log contains the pass counts; evidence/bindings.json binds sources, generator, wrappers, stimuli and logs. The initially failed outer command constructing the generator never wrote or compiled a source; the actual saved generator compiled and ran successfully.

Root independently reviewed the exact delta/proof and authorized a new synthesis-only build at C:/moon/builds/stb1-ce-v001 from V001's 79 frozen source files, replacing this file only. Do not reuse V003 physical replicas. All clocks/pins/XDC/Tcl and 78 other files remain identical. Root must review fresh synthesis/source/CDC evidence before implementation. No BIT identity is assigned and no hardware or new full-system test was run for this candidate.

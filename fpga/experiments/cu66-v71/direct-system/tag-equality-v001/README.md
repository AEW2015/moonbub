# Exact-cycle tag comparison experiment

Isolated candidate only. No selected source, hardware manifest, clock, PHY, state
or handshake timing was changed. Candidate base SHA:
`6d9e57bd55da26b83ccf8027bb2e4c704329d670b1a73201b0dc40c9ed185433`.

The actual HASH_WAIT predicate compares `hash_value[255:128]` with `wanted_tag`
before publishing tag error0x50. The candidate substitutes eight kept16-bit
equalities and a kept balanced AND tree for the wide inequality. All other
source text reverses exactly to the selected validpipe base. No register, state,
cycle, priority, digest bit order or qualified output changes.

`qualification-functional-v001.json` binds:

- Yosys SAT proof for all256 compared binary input bits. This is the exact
  combinational predicate, not an unbounded whole-base sequential proof.
- Four-state grouped-identity exhaustion and full128-bit X/Z tests, plus20,000
  random full-input comparisons.
-322 actual elaborated-base priority/abort cases. Verification copies explicitly
  use wire qualifiers for14 child-driven parent nets to support Icarus force;
  no child implementation is substituted. This is fault injection, not a claim
  that malformed compressed packets exercised every error.
- Actual native KEY/P with the exact unmodified candidate and qualified SDRAM
  pin model: canonical/HUD/pixels checked, zero black lines/underruns, zero RGB
  activity. Control log and timeline through P transaction are byte-identical to
  the selected validpipe control. KEY/P transactions take2049755/3437934clocks.
- A real full-KEY wrong-tag experiment: only the verification receiver's expected
  tag input is XOR1. Actual decoding/SHA reports0x50 at1936762clocks, the native
  HUD endpoint performs ABORT, and drain completes by1936765. Accepted0/rejected1;
  no front/reference/HUD publication. DUT base/codec/SHA are unchanged.

The original measured board cone returns through owner tag_ready. A bare-base
OOC cuts that dependency and reports no digest→working-CE path; it is retained
as a boundary control, not used for the targeted timing comparison. The explicit
`cu71_tag_feedback_ooc` wrapper restores the exact dependency
`tag_ready=tag_valid&&owner_accept_enable`; the other owner predicates remain an
arbitrary external qualifier. Original and balanced use the identical wrapper,
100MHz clock and1ns maximum IO budgets, no new exceptions. Full routed-board
timing and other owner cones remain outside this component boundary.

Failed verification attempts remain: predicate01 exposed Icarus's force/net-type
restriction; predicate02 was superseded by an explicitly annotated03 freeze;
bad-tag01 incorrectly waited for positive done rather than aborted after the
actual error had already drained. These were harness corrections, not DUT fixes.

Timing OOC is a separate gate. The original closed-feedback run logged a raw
Common17-1257 directory error before continuing synthesis; retain that message
and review native-tool integrity before treating its reports as clean evidence.
No routed timing, physical playback or30fps result is claimed here.

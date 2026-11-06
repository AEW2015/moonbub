# Independent AB38 header-pipeline review

Frozen candidate SHA:
`8715c9f29c481d8a02bfa3e86eccb57efdea21b3fb1d4cc36110724a85d02893`.
The parent is the actual frozen v4 decoder, not an alternate behavioral model.
No candidate or selected source was edited by this review.

Static review confirms the reset block and all STREAM_BEGIN/later logic are
byte-identical; original54 state numbers remain, with HEADER_SUM54 and
HEADER_INSTALL55 appended. CRC02 and fixed-header03 condition text is unchanged.
Length04 is checked after two private work cycles. Early lengths/events/limits
writes are private: neither new state performs coefficient, probability, read
request or arithmetic operations before length validation. Six new32-bit payload
registers have no reset. This is not a public-cycle equivalence claim.

Executed independent evidence in `evidence/qualification01`:

- SAT proves total, all prefixes and the zero-extended16-bit packet comparison
  for every combination of unsigned32-bit lengths. Expressions are extracted
  from the actual parent/candidate sources, preserving modulo32 arithmetic.
-122 fixtures include three golden controls and119 resealed mutations of an
  actual encoded Mass Effect plane (1350 blocks,45 columns,519 packet bytes).
  Two seeded runs per actual decoder compare exact error, completion, tile count,
  coefficient CRC, decision/renormalization/read counts. All mutations reject;
 93 known expected-error/control cases independently enforce the specified code.
 29 total-preserving wrap cases reject later with28 error08 andone error07,
  rather than spuriously changing to length04. Error02>03>04 priority passes.
- Every mutation is followed by a full alternate golden decode,120 retries per
  model/seed. Header02/03/04 rejections leave probability RAM and coefficient
  payload unchanged and perform no coefficient/arithmetic work.
- Candidate direct reset ineach new state passes at both seeds:352 probability
  bytes andsix private header registers remain retained; reset dominates
  simultaneous abort/config; control/counters quiesce and alternate golden retry
  succeeds. Valid setup uses dirty RAM and Verilator randomized initialization.

There is no zero-RAM assumption. These are two-state seeded simulations plus
universal combinational field-math proof, not four-state-X/probability-RAM formal
proof or exhaustive malformed-packet enumeration. Whole-decoder1371/31/120
campaigns, abort tests, OOC/routed timing and any hardware remain separate gates.

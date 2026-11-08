# Prospective Rice PREFIX availability control cut

This is **conditional algebra/model preparation only**, with no RTL copy/edit, simulation, native run or performance claim. It starts from frozen V110 PREFIX source SHA-256 `c07d936e807a09ee332b5df4c3f743f88f284784fbcf1e704d1a8db770c33eac`. The latest final PREFIX route's worst path moved to scratch bank selection; this note does not promote Rice to the current measured first priority.

The proposed control simplification is stronger than moving `min(remaining,15)` into a new window register: it removes the variable remaining/window comparison from PREFIX readiness using an exact input-completion owner. It still leaves prefix-empty and tail-truncation remaining tests operational. It therefore does not prove removal of every cached-remaining path or predict a clock gain.

## Legal-state identities

For an initialized legal stream let S=`size_bits`, L=`loaded`, C=`consumed`, A=`available`, R=S−C and W=min(R,15). The source's accepted input and consumption updates inductively preserve:

```
0 <= C <= L <= S <= 2^32-1
A = L-C <= R
A <= 64
```

Reset/start establishes L=C=A=0. A winning good word increases both L and A by the same `in_bits`; input readiness restricts A<=32 and a good word is at most32 bits, preventing reservoir overflow. PREFIX/SUFFIX consumption increases C and decreases A by the same bounded take. Errors, held responses and other branches preserve these quantities. The existing source assertions cover bit bounds, reservoir capacity and zero padding; a new implementation must additionally assert the A=L−C and redundant-completion identities during initialized legal operation.

Under those invariants:

```
A >= min(R,15)  <=>  A>=15 || L==S
```

If A>=15, both are true. If A<15, the original readiness can be true only when R<15 and A=R; since A=L−C and R=S−C without wrap, that equality is exactly L=S. Conversely L=S makes A=R and satisfies the original comparison. R=0 is included: both predicates are true, but the existing earlier prefix-empty error still wins and no bits are consumed.

A prospective `load_complete_owned` bit can therefore replace the L==S test on the right. It must be co-registered with **both actual loaded writes**:

| Original winning write | New bit |
| --- | --- |
| Reset or stream start: `loaded<=0`, `size_bits<=stream_bits` | `stream_bits==0`, including reset plus start conflicts |
| Actual active good-input branch: `loaded<=loaded+in_bits` | `in_last` |
| All other branches, including request acceptance and malformed accepted words | Hold |

`word_bad==0` already proves in_last iff the accepted width exhausts `cached_load_remaining`; the unchanged modular cache invariant and legal bounds make that precisely new L==S. Do not sample registered loaded one edge later, assign from raw in_last on every accepted word, or treat an attempted input as accepted. A malformed word with S=64,L=0,in_bits=1,in_last=1 is a counterexample to the raw-last shortcut: loaded must stay zero and completion false.

## Owned first-one and selected take

The parser stores valid bits at the reservoir MSB and asserts zero padding below A. Any detected first-one rank below15 must consequently be below A. Combined with A<=R, it is below min(R,15). Thus on legal padded states, `found_one` equals `prefix_rank!=15`; restricting the replacement to the original consuming PREFIX branch is sufficient and preserves deliberately inconsistent inactive fixture behavior.

A direct OR of `reservoir[63:49]` is equivalent to rank!=15. It may be called an owned has-one predicate only when the consuming owner/invariants apply. It must not replace the original unqualified combinational reference globally. Selected parallel take becomes `has_one ? rank+1 : window`; the no-one tail still consumes exactly window bits before the original truncation error, and a fifteen-zero window still enters escape handling. Serial PREFIX remains one-bit consumption; SUFFIX remains unchanged.

A future source cut should retain original `can_step`, `found_one`, `take_bits`, zeros and all assertions as independent references. New aliases would drive only the existing selected PREFIX updates and its wait event, preserving active/reset/start/request/input/failure/empty/truncation priority, every raw register, counter, invalid public field and response edge.

## PREFIX wait counter

The original PREFIX contribution is `needed!=0 && !can_step && !(in_valid&&in_ready) && remaining>=needed`. For parallel mode, nonzero window already implies remaining>=needed. For serial mode, needed is one and remaining>=1 is exactly nonempty prefix. Therefore both modes reduce to:

```
!prefix_empty && !prefix_step_ready && !(in_valid&&in_ready)
```

Here serial readiness is A!=0 and parallel readiness is A>=15 or load_complete_owned. Keep the outer active/state qualification and the original accepted-input suppression, including malformed accepted words. Leave the SUFFIX wait predicate byte-equivalent. Otherwise replacing quotient CE alone could leave the same remaining-to-wait-counter cone intact.

## Model and counterexamples

The [analysis receipt](../../experiments/python-gamebub-v110/availability-analysis.json) checks 2,210 exact threshold classes: remaining0..64 and available0..min(remaining,64), plus the analytical remaining65..2^32−1 class. For that large class A<=64 makes completion false and window15, so it is represented exactly without pretending to enumerate all32-bit stream sizes. It checks 8,840 wait classes, 28,000 padding-consistent first-rank classes, 21,319 selected take classes and 1,344 reset/start/active/request/good/bad/hold completion-priority cases. These are algebraic checks, not HDL formal equivalence or RTL execution.

The assumptions are material. With S=L=2,C=0 but A=1, completion is true while original readiness is false. With S=5,L=A=10,C=0, A<=R fails and original readiness is true while the proposed predicate is false. With R=A=3 and an unowned one at rank5, padding fails and rank!=15 differs from original found-one. These deliberately invalid geometries/raw bits appear in supplemental inactive fixtures; they must remain inactive, retain old combinational references and all raw/public comparisons, and initialize any added completion bit coherently with their prepared loaded/size values. No old assertion or fixture may be silently masked or reclassified as a legal stream.

Any later RTL proposal needs a new source/proof namespace, paired write inventory, coherent new-bit preparation, complete original/new public/raw parser miter including serial/tail/truncated/zero-size/malformed cases, unchanged counter goldens and full canonical qualification before a separately authorized native comparison. None is authorized or run by this note.

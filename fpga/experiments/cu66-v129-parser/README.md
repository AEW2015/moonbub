# V129 Rice response experiment

The V128 worst routed path begins at the Rice parser's 32-bit remaining count
and ends at a consumed-bit response register. This experiment separately forms
PREFIX and SUFFIX consumed-position candidates and replaces the SUFFIX unsigned
comparison with a full-32-bit-preserving decomposition. Each result is consumed
at the original state-machine edge. No sequential state, reset, public port,
assertion waiver, or intended public cycle changes.

The decomposition is exact for every 32-bit unsigned `remaining` and five-bit
`suffix_left`: when any high bit `[31:5]` is set, `remaining >= 32` and cannot
be smaller than `suffix_left <= 31`. With all high bits clear, the original
comparison reduces to the full five-bit comparison. The original assertion
and independent error oracle remain unchanged. The [finite model](model-results.json)
checks the complete low-bit partition plus high-bit boundary and random cases;
it does not claim a sequential, RTL, formal, or timing result.
The algebra and Verilator comparison use two-state values; unknown/X propagation
equivalence is not claimed.

The actual prior source is the V128-selected V116 parser. [prepare.py](prepare.py)
records five exact reversible edits and confirms all four original guarded
assertion blocks survive. The [paired verification preparer](prepare_verification.py)
reuses the historical probe, independent golden corpus, view/cancellation tests,
and oracle bodies. One reversible prepared-state fixture edit initializes the
same hidden-payload owner fields in both V116 models; the inherited V115 model
previously used a directly writable output. Prepared internal states are not
claimed as naturally reachable packets.

Run the read-only reconstruction with `python3 qualify.py`. A coordinator may
authorize a fresh strict Verilator model with
`python3 qualify.py --run --root-grant ROOT_V129_PARSER`. The runner binds its
actual sources and corpus, preserves failed attempts, and only emits a selected
`PASS` after both specified seeds complete. Full decoder, transport, peer and
publication regressions, followed by a fresh fixed-recipe 125 MHz implementation,
are separate gates. Source-level parallelism is not proof that synthesis keeps
separate adders or that routed timing improves.

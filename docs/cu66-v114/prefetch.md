# Optional V114 scratch prefetch preparation

The independent [source review](../../experiments/python-gamebub-v114/audit/prefetch-source-review.json)
is **PASS_SOURCE_REVIEW_AND_BOUNDED_PAIRED_PROOF**. Optional candidate SHA-256:
`332da2058fd3e6413e8cc6336c1aab13eba7cddaaa76bb9d49c8426b1727854a`.
The reversible recipe transforms frozen V113 scratch
`efc3e61ac94d6c336164026c2865b70dee832c53a328bce720278719f6693f0f`
without changing its module interface, original assertions, ownership states or
request/response/output control. This candidate is separate from primary A.

DC/raw next-line addresses, AC next-line addresses and their count eligibility
are prepared on existing clock edges. Their expressions preserve the original
32-bit arithmetic, line alignment and subsequent 18-bit truncation. The sparse
next-block comparison retains 17 bits: block 65,535 plus one is 65,536, with no
16-bit wrap. Raw index 63 advances to the next block's first sample address.
AC starts plus cursor times four retain modulo-2^32 behavior. Additional scalar
checks covered 770,896 boundary/wrap cases; these were Python algebra checks,
not new RTL simulations.

The state transitions provide a real warm-up edge. An AC cache hit increments
its cursor in AC_EXTRACT, then AC_CHECK precedes EMIT; changes to the output block
pass through CLEAR_TILE/DC_FETCH/DC_EXTRACT. Raw block/index changes pass through
RAW_FETCH and DC_EXTRACT before RAW_EXTRACT. During held sparse output the block
and cursors remain stable. New assertions compare prepared operands to the old
full-width algebra at every eligible EMIT/RAW_EXTRACT edge, including held output.
No extra public bubble is introduced in the retained paired campaign.

Cache hit decisions and priority remain live: current DC miss wins before AC
banks 1, 2 and 3. Current sealed/mode/offer/outstanding/cancel/error eligibility
still gates launch. Prepared registers have no reset and hold no ownership;
they mature before eligible use. They cannot release an accepted memory request.
Reset/abort/error priority, held request payloads, real matching-response drain,
wrong-response handling and immediate cancellation gates are unchanged.

The [selected focused proof](../../experiments/python-gamebub-v114/prefetch/results.json)
pins raw receipt `e4e8679ecfce7ce96b58a01130d49b1f44e9253b38b95a7cc8a1f7f0ed6969ee`.
Two actual strict Verilator seeds, 114301/114302, each passed 72 inherited complete
transactions and 48 additional DC-line-boundary transactions, 128 corrupted
responses, four read-owner scenarios and nine historical accepted-write hazards.
All four banks and 16 byte offsets were checked, with random held service/output
and over 128,000 live unowned begin-sideband mutations per seed. The scratch probe,
full original bench, additive boundary bench and historical hazards are
byte-identical frozen V113 verification files. Both observed modules derive from
actual full scratch bodies through reversible renaming/direct-view adapters.
Public cycles and invalid payload/debug/request/state fields remain compared;
independent value, cursor, owner and physical-drain oracles remain enabled.

All source/artifact pins, compiled source copies, binary hash and parsed stdout
verdicts were verified. The bounded RTL cases use block counts 1/3/8 and 9/17;
they do not demonstrate an actual 65,536-block or 32-bit wrapping-start/cursor RTL
traversal. Full-width conclusions also rely on source algebra and consuming
assertions. Separate boundary traces remain in the external build and are
hash-pinned by this review; they are absent from the focused receipt's retained
artifact manifest, which retains the original traces and stdout verdicts.

The old prefetch arithmetic-to-return-state cone motivates this optional cut.
Live cache/priority/control and routing can still limit timing. Full optimized
composition/peer checks and actual native timing remain separate gates. This
review performed no builds, source/proof edits or hardware actions and claims no
achieved clock, placement gain, extra physical ports/lanes, board FPS or complete
production PCTL1 qualification.

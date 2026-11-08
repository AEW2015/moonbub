# Frozen-source clean repeat

The [preparation template](../../experiments/python-gamebub-v108/clean-repeat-template.json)
binds the unchanged V107 eighteen-file source closure, exact parent RTL/include
read order and fixed 10 ns clock. It chooses no trial and creates no native
preflight or build.

After all six initial rows have terminal native receipts and separate completion
records, choose the actual best eligible routed strategy. Then prepare using
`scripts/cu66-v108/native_clean.py --trial WINNER --repeat-of WINNER_RECEIPT`.
The exact selected receipt must have the same matrix/source hashes and directives.
Root's new heavy-slot grant and independent preflight audit are required before
`--run --preflight PREFLIGHT --grant GRANT --audit AUDIT`.

The repeat starts from the original seventeen RTL bodies and one include header,
with the same parent source/include order. It reads the same XDC before fresh
RuntimeOptimized synthesis, then executes the selected optimization, placement,
optional pre-route physical optimization and routing directives. It never reuses
a synthesis, placed or routed checkpoint for computation. The original checkpoint
is retained read-only as ancestry evidence.

Limits remain two CPUs, two threads, 8 GiB without extra swap and 2,400 seconds.
The one-repeat cap includes failures; failed outcomes remain recorded. A negative
setup result remains a failure. Full clocks, setup/hold/pulse, internal timing
checks, route completeness/errors, methodology/DRC, source/recipe invariance and
resource evidence must be assessed independently of the exploratory winner.

The outtile/capacity composite changes five source origins and has its own native
contract. Its fresh build cannot replace this unchanged-source repeat. Neither
flow proves board I/O timing, sustained hardware 30 fps or complete validated
decoding below 10 ms.

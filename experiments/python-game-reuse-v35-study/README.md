# Exact GM27 reuse inside HM34 (v35)

This isolated host component study keeps the v34 HM34 wire, all child vectors,
all candidate complete-byte costs, and stable mode/Rice ties exactly unchanged.
`model.pack(parent, child, width, height, *, parent_bytes=None,
child_bytes=None, return_info=False)` accepts already-paid canonical GM27 maps.
Absent maps use the frozen GM27 encoder; partial reuse is supported.

Cache bytes are untrusted. The independent v34 syntax-only GM27 decoder checks
lengths, domains, modes, Rice/padding, order and run bounds; decoded arrays must
match exactly. A vectorized local cost planner checks the frozen GM27 canonical
mode, sparse default, run length and Rice parameter ties. Syntax-valid but
nonminimal maps raise `ValueError`: accepting those directly would violate
byte identity. This planner computes all real GM27 parameter costs without
serializing candidate maps or calling the frozen GM27 encoder on cached maps.

The new HM34 path computes the exact complete sizes of flat child, sparse gaps
and parent masks, then serializes the winning representation and CRC once. All
three formats and every Rice parameter trial remain charged. Counters separate
cost trials, emitted bits, validated caches, uncached encoder calls, HM34
candidates sized, HM34 candidates serialized and CRC calls.

`benchmark.py` uses every 184 P-frame child field from the two retained v34
causal controller histories (full/select25, two scenes, 46 P frames each).
Each parent is the matching half32 attempt, never another reference/history.
Original map bytes come directly from each GM27 frame at HEADER+qmap_bytes;
child legacy map bytes match both residual variants. It compares the frozen
HM34 encoder against the new encoder with those caches in three paired runs,
alternating order. Timings include field validation, cache syntax/equality and
canonical checks, setup, every size cost, winner bit emission, serialization,
CRC and info construction. Array acquisition before the pair is common to both.

The excluded initial map generation is explicitly retained under
`already_charged_analysis` in every result row, including parent/child analysis
wall times and their original GM27 candidate/Rice work. This is a component
speed comparison; substituting these numbers into old full-sender wall times
would mix different runs and machines/load. No full sender speedup is claimed.
Original sender component timing also included separate motion verification;
that older root number is retained for context and is not the paired baseline.

For each field, both original child residual variants are passed through the
actual frozen `frame.wrap` serializer with the new HM34 component. All 368
GM34 frame bytes must match the retained original frame byte for byte. The
independent `verify.py` imports no reuse encoder, verifies source/archive hashes,
syntax-decodes each component, checks all decoder fields and independently
replays the accepted original reference histories. It decodes each of the 368
variants on that causal reference and validates its reconstructed pixel tag.
Byte identity means old and reused frames have identical decoded pixels.

Run with `/home/lori/gamebub-streaming-prototype/.venv/bin/python`:

```
python -m unittest discover -s experiments/python-game-reuse-v35-study -v
python experiments/python-game-reuse-v35-study/benchmark.py
python experiments/python-game-reuse-v35-study/verify.py
```

`results.json`, compressed content-addressed `objects/`, `benchmark.log`,
`tests.log`, and `verify.log` retain the evidence. The JSON pins all source files
and the complete original controller result. Existing <=v34 modules and globals
are never modified. No controller integration, changed-pixel experiment,
hardware fit, physical 30 fps or heldout-content claim is made here.

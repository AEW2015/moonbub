# AKD1 independent I/O, CDC and BRAM/reset reviews

These are versioned, immutable review records and executed read-only checkpoint
queries. They inventory local source/checkpoint/report dependencies; complete
candidate checkpoints and source trees are not distributed here.

- Initial review: asynchronous input/held-payload/Gray crossings and active I/O.
  QSPI's 10 ns max-datapath budget is not a finite external hold proof or maximum
  bandwidth qualification. Audio electrical budgets remain provisional.
- V2: exact fixture-ROM netlist counterexample. Its enables are high during reset
  before PLL lock. This is a startup protection gap, not observed physical corruption.
  SHA-256 `8569cd8d48588c9d3c878008164b0bde79b07eba59d50fe32c5ad81dfae8a748`.
- V3: classifies the complete 199-warning inventory by actual RAM role. Mutable
  stores have conditional fresh-write-before-visible reasoning; this is not a
  blanket warning waiver. SHA-256
  `f10512f9458743413d5086057d3304247c4e1e34f77fc8743fba5d2c1555bb79`.
- V4: all 44 overlay ENB LUTs independently prove reset forces read enable low,
  and the warning-cell set equals all 106 RAMB36 cells (zero RAMB18). This resolves
  the earlier unknown overlay pre-lock polarity. Recursive evaluator unknowns
  remain preserved; positive evidence comes from direct actual-LUT enumeration.
  Manifest SHA-256
  `3663e6cfd9f0a14d2dadb2d0ca87d4b15728d7bb6b3d8ac86d318ac199063716`.

Warm PLL-loss/ROM or overlay retention and physical I/O remain unqualified.
No candidate, checkpoint or hardware was modified by these reviews.

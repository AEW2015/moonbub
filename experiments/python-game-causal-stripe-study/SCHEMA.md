# `gamebub-actual-stripe-service-v1`

`results.json` contains relative source/object SHA-256 pins; exact reconstructed
frame evidence; legal fixed-point width bounds; and ten conditional schedule
profiles. There are sixteen frame decisions: twelve native cohort decisions
sharing six unique source acquisitions, plus four flat partial-geometry controls.
No frame sequence is scheduled as a continuous physical playback experiment.

A frame records cohort/id, complete AR03 and source hashes, geometry/key/publication,
zero/DC/GENERAL counts, dense-all and existing-bypass GENERAL MAC counts, sparse
MACs, dequant products, exact sample/UI counts, canonical reference tags before and
after uint8 physical packing, display hash and plane residual/YUV proof hashes.
Plane proofs compare exact frozen arrays and record observed dequant/intermediate
widths and biased accumulator bounds.

`stripes` preserve plane and raster stripe order. Each records real newly refilled
selected-token bytes, actual logical bits, valid cropped sample count and per-block
GENERAL-pass product/index/dequant work. Full parsed input and output are retained
by the Python verifier outside the proposed local-buffer plan.

Each case contains a named `Budget`, per-frame schedule, same-plane uniform-demand
counterfactual and summary. Schedule entries give entropy and consumer start/end
instants, coefficient bank, reference reads, YUV writes and paid cycle components.
Start/end values follow a declared causal bounded producer/consumer model; they
are not RTL measurements. Source/intermediate scans, dequant, both dependent
matrix passes, pass overhead and 64 sample outputs are distinct.

Separate byte counters cover external staging, assumed four complete preflight
passes, local compressed-cache load, selected entropy refills, reference reads,
reconstruction writes, canonical tag reads, canonical hashed bytes, color reads,
RGB565 output and display-only UI writes. Physical compact-YUV8 tag reads are one
byte/sample, while canonical tag hashing remains two bytes/sample plus geometry.
Expansion/hash cycles are charged without a fictitious second external read.

Local footprint includes full 49,152-byte compressed cache, configurable coefficient
stripe banks, one reconstruction stripe, inverse/index scratch, basis/table ROM,
color line buffers, UI palette and entropy reservoirs. Parser/control metadata and
external/reference/display/Python oracle storage are explicitly outside the claim.
Multiplier primitive counts and memory/clock rates are conditional assumptions.

`analysis.json` binds the result and analyzer SHA-256, matched same-packet baseline/
sparse/compact comparisons, operation counts, profile summaries and explicit scope
limits. Use `analyze.py --check` for read-only reconciliation. All prior study
sources/results remain unchanged.

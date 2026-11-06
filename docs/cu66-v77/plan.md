# CU66 V77 direct cache and pixel conversion prototype

## Scope

V77 implements a standalone structured cache with streamed x16 memory writes
and clocked neighborhood reads, plus an elastic RGB565 conversion pipeline.
Its component interface and exact limits are specified in
[`interface-contract.md`](interface-contract.md). The cache uses 29,184 bytes
of data storage, excluding tags and pipeline/output state. V76's benchmark
for a software LRU service model remains a frozen comparison; it is not V77
RTL evidence.

The V77 component benches use one common memory/core clock. They do not
implement a real pixel-clock CDC bridge or complete receiver/display
integration. Do not describe their results as physical 30 fps, sub-10 ms,
target-device fit, or target frequency evidence. The target parts are not
installed in this environment.

The full-system benchmark uses the actual frozen controller and native pixel
deadline path. Its evidence is distinct from standalone cache/render checks.
Functional correctness and measured performance are separate verdicts;
the evidence auditor may report a performance FAIL while retaining a valid
functional PASS. Any timing statement must name its measured boundary and
clock assumption.

## Baseline and evidence

Run `python3 scripts/cu66-v77/verify_baseline.py` to check the frozen V69–V76
bundle manifests, pinned V75 source hashes, and V76 parent ancestry. This is
an integrity check only. The V77 evidence auditor will bind source, logs,
derived data, and input identity hashes to the actual retained test results.
It will also check held-response ownership and data identity rather than
accepting completion markers alone.

## Packaging

Once the V77 evidence and documentation are final, create and check the
manifest with `python3 scripts/cu66-v77/bundle_manifest.py --write` followed
by `python3 scripts/cu66-v77/bundle_manifest.py`. The package scope is only
`docs/cu66-v77`, `scripts/cu66-v77`, and `fpga/experiments/cu66-v77`; the
manifest excludes itself and Python bytecode.

## Completed iteration and selected variant

The streamed cache, elastic converter, native cache-backed render campaigns and
actual-controller/native LCD matrix passed. A separate bounded address variant
retains every tested case counter and cycle while reducing the unplaced
cache/converter mapping from 29,462 to 2,970 cells. Select the bounded cache for
next integration; retain the original as comparison evidence. The FPGA decoder
and seamless source/lease owner are not integrated with this display path yet.
See [the measured handoff](hardware-handoff.md) for source selection, all limits
and the next 30-fps / strict under-10-ms milestones.

# V82 evidence scope

V82 evaluates a Python/native design study for Game Bub frame preparation and
content commitment. The native collector exports actual decoded tiles and
classifies visible COPY_REF only from encoded all-zero quantized coefficients.
The commitment prototype builds a domain separated incremental content tree;
the execution model prices reference reads, certified stores, tree state and
hash work. The proposed profile is a new opt-in profile. Its unkeyed SHA-256
commitments do not authenticate a sender and do not replace the older canonical
SHA profile.

Across 457 frozen sources, the native oracle retained the original picture,
resolution, packet data and HUD output. The study reports 2,216,647 safe
visible COPY_REF tiles, 113 synthetic protocol checks, and 3,656 full-tree and
seal comparisons. At 16 tiles per leaf, the modeled data-plus-HUD command count
is 34.85% lower than the V81 modeled baseline. This is an accounting result,
not a measured or physical performance gain. Tree traffic, hash resources,
ports, fitted timing, transport and scanout remain unqualified.

The modeled cold-delta maximum data-service floor is 11.70174 ms, conditional
on the frozen memory service assumptions and before omitted work. It does not
prove strict validated completion below 10 ms. V82 adds no RTL, ESP32 firmware,
physical 30-fps qualification or under-10-ms claim.

The frozen V81 reference is
`83efb7ae627757aefdfd22e2a355720ff01bfb72`. Its RTL produced 457 correct
results, 327 modeled ACK completions within the 30-fps budget, and zero strict
validated-under-10-ms results. Those simulator observations do not establish
physical frame rate or hardware performance.

Run from the repository root:

```sh
python3 scripts/cu66-v82/verify_baseline.py
python3 scripts/cu66-v82/verify_evidence.py
python3 scripts/cu66-v82/bundle_manifest.py
```

The baseline verifier checks that the frozen V81 commit is an ancestor and
reruns the V81 baseline, bundle and evidence checks. The V82 bundle covers
files under `docs/cu66-v82`, `scripts/cu66-v82` and
`experiments/python-gamebub-v82`. It excludes its own manifest and Python cache
files. The manifest records file integrity only, not functional or performance
verdicts.

The completed audit verifies 457 native sources, 1,828 execution-accounting rows,
3,656 complete tree/seal comparisons, 113 synthetic checks and eight exact SHA
serialization vectors. It independently replays normal three-bank certificates,
recomputes reference/materialization/hash-only reads and metadata accesses, checks
all published summaries, and binds execution roots/seals to the separate
commitment run. It imports no producer residency or execution implementation.
The native loader and frozen native codec remain trusted input dependencies.

```sh
python3 scripts/cu66-v82/verify_execution_inputs.py
python3 scripts/cu66-v82/verify_evidence.py
```

`verify_execution_inputs.py` rebuilds the original flat canonical SHA from actual
tile bytes and compares every equality/COPY bit. Its per-corpus equality result
is not assumed for future clips. Original packet, HUD and display digests and the
instrumented-versus-frozen full-plane equality remain native collector evidence.

For fresh model replays, preserve the published bundle and use a separate
working copy:

```sh
python3 scripts/cu66-v82/prototype_commitment.py --native --output /tmp/cu82-new-commitment-attempt
python3 scripts/cu66-v82/prototype_execution.py
python3 scripts/cu66-v82/export_vectors.py
```

Choose a new output path; do not overwrite retained attempts. The native
collector refuses to overwrite its existing index. New replays add artifacts and
therefore change the bundle manifest; verify the original package before adding
local results. `bundle_manifest.py --write` is for a newly frozen package, not a
way to repair evidence after changing it.

Exact binary message vectors are in
[`compact-message-vectors.json`](../../experiments/python-gamebub-v82/compact-message-vectors.json).
They are SHA input serialization, not network packets. The first exporter
attempt used an incorrect Python property name (`context` rather than
`profile_context`); its source and failure record are retained under
`vector-development/`. Correcting only that verification helper produced all
eight matching vectors. Older TREE-1 development attempts remain archived under
their own profile identity and source snapshots; TREE-2 is the qualified current
profile. No codec/native/RTL source was edited to repair the exporter.

# Runtime v28 experiment schema

The wire remains GM27/version1, CP27/version1 and JA27/version1 with HU25.
Base/pair/ACK fixed sizes remain80/60/65bytes; complete CP27cap49,152bytes.
Range/escape/padding/reference/output-tag rules are frozen v27. The new encoder
and decoder must emit/consume the same canonical bytes for the same prepared
source, motion vectors, reconstructed reference and quantizer map.

Exact legacy cost:

- All-zero plane: one zero dispatch byte.
- Dense: one dispatch plus the exact CP02 complete packet size.
- Split: one dispatch plus SP01header, ceil(N/4) mode bytes,2bytes per DC block,
  and complete CP02 for full blocks if present. Dense wins ties.
- SP01dense is strictly dominated by the direct dense encoding; its construction
  is unnecessary. Original/pruned decisions compare these exact sizes before
  selecting final coefficients; original wins only on a strict size advantage.
- EC26block-major plus dispatch costs at least55bytes. It is built unless that
  lower bound cannot strictly beat the incumbent; legacy wins a final tie.

`gamebub-lazy-parity-v28` records96 actual selected frozen v27 decisions with
old/new leaf timings, exact packet objects and both work ledgers.
`gamebub-runtime-v28` records six full cohorts with per-source `attempts`,
`analyses`, selected actual CP27/JA27objects, original source association,
quality/hash fields, complete-body arithmetic and paid timing/count summaries.
Each raw object descriptor is relative to this folder except old `hud_packet`
descriptors, which additionally declare a repository-relative source directory.
Zlib is artifact storage, not a new compression tool in the wire codec.

The source-side search name is not transmitted: sample4_refine2 samples each
plane at stride4 for81coarse candidates and stride2 for25half-pixel refinements;
sample2 uses stride2 in both phases. Every chosen vector is decoded at the
original full-resolution geometry. All candidates, sample reads and full final
prediction/forward transforms are charged. No future source is used.

# Moving toward an application-specific codec

The useful application-specific change is a **COPY-aware execution and
validation profile**, preserving existing quantized residual coding rather than
replacing it with raw tiles. Its new content commitment makes some unchanged
pixels unnecessary to fetch merely for full-frame hashing.

The three internal operations are:

- **COPY_REF**: visible delta tile with encoded all-zero coefficients under the
  implemented zero-motion profile. Its pixels equal the accepted reference.
- **CONST128**: profile-defined hidden tile; generate its 64 bytes locally.
- **RESIDUAL/DATA**: existing entropy/dequant/inverse/reconstruction produces
  the tile bytes. DATA in the protocol prototype is this decoded result.

The bank certificate answers a different question: whether the chosen physical
candidate bank already contains those bytes. COPY eligibility alone does not
permit skipping a store. A mixed hash leaf may still require a resident COPY's
bytes, which is why granularity and metadata placement matter.

## New opt-in commitment

`CU66-V82-CONTENT-SHA256-TREE-2` and capability
`cu66-v82-content-tree-sha256-v2` use a compact binary domain with profile context,
geometry/grouping, tile identity, node position and frame/reference/generation
binding. The frame seal also binds the semantic HUD digest and accepted previous
content root. It is an unkeyed content commitment, **not sender authentication**.
Old CU66 canonical SHA tags do not silently gain new meaning; receivers without
the explicit new capability reject this profile.

The independent native flat-SHA oracle remains in this study. A deployed new
profile would deliberately replace that image commitment only after host and
FPGA implementations agree bit for bit. The prototype has no finished network
serializer, negotiated deployed header or new Sunshine/ESP32 build. Preserving
AB38 coefficient coding does not mean preserving CU66/GU66 reference-tag
envelopes: their old flat-SHA requirements must be explicitly replaced under
the new profile before these avoided hash reads are real. Wire size,
fragmentation, receiver limits and actual forwarding costs remain to be defined.

## Next implementation experiment

1. Keep g=4/16/64 as explicit profiles. Start with g=16 for balanced logical
   state/hash work, retaining g=4 when larger on-chip state is affordable and
   g=64 as the smaller-state/external-metadata comparator. Target resource and
   port reports must decide actual placement; Python byte totals cannot do so.
2. Build an RTL tile-operation interface that derives COPY from decoded
   coefficients, not an unverified host hint. Preserve independent raw-pixel
   oracle and canonical candidate-memory comparisons in tests. Keep a bounded
   group buffer and request missing COPY bytes for dirty group hashes.
3. Implement real candidate-bank residency certificates. Invalidate the old
   candidate bit before the first store; never restore it on abort. Publish the
   content root, reference identity and shadow certificates together only after
   successful content/HUD verification and actual write/drain fences. A certified
   resident-store completion must prove existing contents, not fabricate a
   physical-write acknowledgment.
4. Prototype bounded memory descriptor queues/pipelining separately. Cold deltas
   still violate the current conditional 10-ms service floor even with COPY.
   More DSP/hash lanes or lower average traffic cannot erase that constraint.
5. In a host prototype, compute the expected tree from the **same reconstructed
   quantized canonical pixels**, not unquantized capture RGB. Retain AB38 residual
   coding initially. Define binary header/capability/fallback and error recovery
   before changing Sunshine or the ESP32 relay.
6. Require bit-exact leaf/node/seal comparison, stale/abort/reset/lost-ACK tests,
   source/physical-memory/raster checks, both SDRAM corners and real ESP32 ingress
   limits. Then qualify distinct-source sustained 30 fps before claiming strict
   maximum validated decoding below 10 ms.

This study changes neither resolution nor picture quality. It demonstrates a
specific route to less hardware work; it does not establish compression or
quality superiority to HEVC/AV1, a fitted bitstream or a real-time streaming client.

# Next measured optimization: bounded chroma rows

The V91k uncached RGB565 baseline is exact, but its nine individually
acknowledged byte reads per output pixel dominate the sequential service count.
Keep this qualified control unchanged. The first optimization changes local
read reuse, not wire bytes, quantization, image quality or ESP32 forwarding.

## Read and storage targets

| Quantity | Qualified uncached control | Proposed two-row reuse |
|---|---:|---:|
| Luma byte reads/frame | 345,600 | 345,600 |
| Chroma byte reads/frame | 2,764,800 | 172,800 |
| Total external byte reads/frame | 3,110,400 | 518,400 |
| Additional logical chroma payload | 0 | 1,440 bytes |

The sixfold total-read reduction is an exact architectural count, not measured
cached-RTL performance. Local RAM read cycles, row fills, output stalls and
conversion work still count. A future burst interface can reduce transaction
setup further; qualify the byte-service cache first so reuse and burst effects
have separate controls.

## Ownership and schedule

1. Before the first luma row, load chroma rows 0 and 1 for both Cb and Cr.
2. For luma y, use `cy=y//2`, top row cy and bottom `min(cy+1,239)`.
3. Reuse that row pair for both even and odd luma rows. When cy advances, retain
   the old bottom as the new top and fill only the newly needed bottom.
4. At cy=239, alias bottom to top; do not read an extra row or beyond the plane.
5. Never set a row tag valid until its whole fill has been acknowledged. Track
   epoch, plane/paired-chroma ownership, row, slot, accepted address and offset.
6. On abort/reset, invalidate local row tags and output. Retain any accepted
   physical read until the matching response drains; replacement cannot reuse
   the row slot or bank early. Wrong-tag and matching-error responses retain
   the qualified fail-closed semantics.

A placement-friendly starting arrangement is four 180×16-bit arrays: two row
slots × column parity, with each word containing Cb and Cr. Neighboring columns
use opposite parity banks; top/bottom rows use different row slots. Edge
replication selects the same value rather than requiring a duplicate port.
Account for how paired Cb/Cr bytes are assembled from their separate external
planes. Use registered reads and an explicit response-valid stage; do not model
BRAM as a zero-cycle combinational read. Exact inferred RAM/DSP/logic counts
and routed timing belong to target synthesis/implementation qualification.

Interpolation remains horizontal `(left+right+1)//2`, then vertical
`(top+bottom+1)//2`, with the original signed color conversion. Combining the
rounding points into a single weighted average can change pixels and is not a
representation-preserving optimization.

## Promotion tests

- Run all six frozen canonical memories through cached and unchanged uncached
  RTL controls, under both finite service profiles and both retained seeds.
- Compare all RGB565 words, pixel identities, accepted-request provenance and
  actual read addresses/data. Require no reads on an unowned/incomplete row.
- Check exactly 518,400 external byte reads for the simple no-prefetch cache
  schedule; count any extra fetches explicitly if a different design wins.
- Add odd/even x/y boundaries, right/bottom replication, row-slot wrap,
  cancellation during every fill phase, partial row fill, held RAM response,
  held RGB output, stale tags and clean retry after error.
- Charge row loading, registered local lookups, arithmetic, bus service and
  output drain. Retain separate first-byte, last-byte and complete-service
  fences. Compare cycle distributions and added storage against the control.
- Promote only exact-output winners with bounded ownership. Keep hardware
  30 fps and complete validated sub-10-ms gates open until the full physical
  pipeline is measured.

After this gate, consider 128-bit candidate-memory bursts using an explicit
line gather/reuse queue. Report accepted beats, actual payload and any padding
or duplicate row-boundary reads. Do not simply divide byte transactions by 16
and call that a measured bus result. HUD validation/publication and the
monolithic finite-service join still require their separate V91l/V91m gates.

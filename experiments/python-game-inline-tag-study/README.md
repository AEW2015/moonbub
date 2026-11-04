# Canonical publication SHA with one bounded tile stripe

This Python prototype computes the **same 16-byte canonical YUV reference tag**
as v15 while receiving ordered reconstructed 8×8 tiles. It owns one eight-row
int16 stripe rather than a full reconstructed plane. It is an algorithm/order
proof for a future inline decoder path; the simulated producer currently reads
already reconstructed full planes. **No memory reread is actually removed from
the current decoder, and no FPGA/native bandwidth or 30 fps result is claimed.**

## Results

Twenty cases match the frozen `reference_tag()` exactly:

- Ten retained deterministic golden-frame reconstructions, including GM/SR and
  full 720×480 output.
- Six actual native-derived AR02 decodes from the budget study: three related
  Mass Effect source IDs in GM and exact modes, not six independent acquisitions.
- Four seeded canonical YUV controls at 2×2, 34×18, 66×50 and 720×480. Partial
  luma/chroma edge tiles and incomplete eight-row stripes are exercised.

All eight full 720×480 cases require exactly **11,520 bytes of owned stripe
storage**, calculated as `8 × 720 × 2`. Hash input remains **1,036,804 bytes**:
`<HH width,height>` followed by C-order Y, Cb and Cr little-endian int16 samples.
Packing future reference memory to eight bits does not change that canonical
SHA input or remove SHA compression work. SHA/control state and producer storage
are outside the stripe allocation; this is not total process/FPGA memory use.

Eight tests pass, including strict order, duplicate/extra/truncated tile streams,
invalid dtype/shape/range, partial edges, big-endian producer conversion,
finalize-only visibility and non-retention of producer tile objects. Source pins
are frozen before the run and checked afterward. The retained read-only verifier
replays all twenty cases and independently reproduces the conditional budget.

## Streaming contract

`StripeTagger(width,height)` accepts even bounded dimensions. `push(plane,y,x,tile)`
requires planes Y→Cb→Cr and raster tiles in each plane: eight luma/chroma rows at
a time, left to right, then the next stripe. Plane edge tiles have their exact
partial shape. Samples must be signed 16-bit values in 0…255; either input byte
order is accepted and stored canonically little-endian.

Each tile is copied into its stripe columns. Once the stripe is complete, rows
are hashed through contiguous memoryviews without `tobytes()` or a full-stripe
copy. The same allocated stripe is reused for subsequent stripes and narrower
chroma planes. The tagger retains no producer tile or full-plane reference.
A weak-reference test verifies that a caller-owned tile object can be collected
after `push()`.

Malformed input poisons the stream: later input/finalization fails and no tag is
visible. Truncation is detected by `finalize()`. Extra tiles must be rejected
before finalization. `tag` raises until a complete explicit `finalize()` succeeds;
re-finalization and later pushes fail. Once finalized, the tag stays published;
this object cannot retroactively revoke it. A future AR02 consumer must validate
the complete packet, all parser/UI/CRC conditions and expected stored tag before
publishing a reference bank. This helper alone does not publish a bank or validate
an entire AR02 stream. Tags identify content; they are not authentication.

## Conditional reread budget

If a future decoder emits canonical ordered tiles directly into this helper, it
could avoid the separate **518,400-byte packed-eight-bit publication-tag reread**
per full-resolution key/promotion. Reconstruction writes, color reads, SHA input
bytes, arithmetic and other traffic remain unchanged in this experiment.

For the retained native GM promoted-P trace, removing **only** that tag read from
the frozen budget equations gives:

| Assumed service scenario | Baseline planning ms | Conditional planning ms |
| --- | ---: | ---: |
| Nominal | 69.724 | 60.691 |
| Optimistic | 37.227 | 33.815 |

Neither conditional case reaches a 33.333 ms serialized planning budget. The
conservative scenario still cannot serve its assumed panel scanout. The unchanged
SHA stage costs 1,296,080 assumed cycles in all three profiles. The counterfactual
requires inline production without new stalls, valid canonical stripe order,
proper late-error cancellation and atomic bank ownership. It is not an implemented
fusion or a measured SDRAM bandwidth saving; average service still does not prove
line deadlines, arbitration, clock closure or resource fit.

## Reproduction

Use the project NumPy/Pillow/PyAV environment from this directory:

```sh
python verify.py
python -m unittest -v test_inline.py
```

Verification consumes retained packet/golden objects and does not require the
external video file. `benchmark.py` regenerates this small algorithm-evidence
snapshot, not performance measurements. External Python/library time is recorded
only as run duration, not speedup. `failed-initial-import.log` retains the initial
missing local fixture-module import; the search path was corrected before final
source pins and the fresh successful run. No frozen v15/v16 source was edited.

Next integrate this producer contract with an actual bounded decoder stripe
schedule, preserve private reconstruction until all validations finish, and prove
SHA backpressure does not violate display/reference ownership or buffer bounds.

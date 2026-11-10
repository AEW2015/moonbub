# V128 sparse-ingress verification options

This is a pre-selection verification design, not executed proof. The baseline is
V127 commit `c196ad83e4c077bb50f9706058fb6416425d4fc5`, integration index
`d16589645d3824399a4df4559a84405051547a48e236dc0aa0e1841812f5ce39` and independent
audit `494ddd3433304c8bd9e08cd63802646edca9c8ba00a23f48e364ce44eaf38ad6`.
Old production, test fixtures, receipts and protected marker files remain immutable.
No heavy job or source change is authorized by this note.

## Candidate interface being reviewed

The RTL lead proposes four new origins: synchronous ingress, its capacity wrapper,
child pipeline and scratch. Synchronous ingress exports one selector and two direct
72-bit tuples `{epoch32, block16, index6, signed_value16, band2}`. The wrapper and
child pass those exact views to scratch. Scratch evaluates its entire original
eight-phase validation expression independently for each tuple, then selects a
Boolean. A separately factored epoch mismatch retains error2 before format error3.

The ingress selector and scratch's stored `raw_mode` are different inputs to this
logic. The selector chooses which tuple the original ingress output exposes;
scratch's `raw_mode` chooses RAW versus sparse/DC/AC validation format. Tests must
vary them independently. A standalone legacy fixture must connect both views to
its original selected tuple and select a defined lane. Unconnected new ports or
lint suppressions are not an acceptable adapter.

## Explicit invariants and difficult domains

- Every selected tuple view must equal the original public ingress block, index,
  coefficient, epoch and band on **all** evaluations, including invalid/unready,
  reset, start, abort and context-failure cycles. Do not assume equality only when
  a transfer is accepted.
- Preserve full32 epochs, full16 coefficient blocks, original 17-bit `blocks`
  storage and the actual `16'(blocks)` comparison cast. Do not rewrite unusual
  out-of-domain encodings to mathematically cleaner semantics.
- Exercise all eight phase encodings. The original count/band lookups use low2
  phase bits, whereas the DC test uses the full `phase == 0` decision. Phases4–7
  therefore cannot be substituted for0–3 in the extracted Boolean domain.
- Preserve signed16 values around−2049/−2048/−1/0/1/2048/2049 and full signed
  extremes. A packed72-bit tuple is not a signed72-bit coefficient.
- Retain full32 written/count/previous-position domains, full16 block boundary and
  full6 index/raster/zigzag behavior, every band match, previous_valid/order case,
  zero AC rejection, and both good/bad owner lanes with only the selected lane
  eligible to determine the decision.
- At the real INGEST edge, a foreign epoch remains error2 even if the same tuple
  also has format/range faults; an owned malformed tuple remains error3. This
  behavior is independent of downstream readiness.
- Preserve cancel/reset/response-failure priority over INGEST and retain actual
  outstanding-request ownership. Wrong-epoch ACKs must not retire real debt;
  pending request acceptance on the fault edge must still enter DRAIN where the
  original controller requires it. Do not erase debt to prepare a fixture.
- Keep band-end epoch/error4, seal/epoch checks, first-error behavior, local visible
  write retirement, ownership fences and retry/start ordering unchanged. The
  candidate cannot use ready/valid or its selector as an ownership certificate.

## Recommended layered proof

1. **Read-only baseline lineage.** Run the unchanged V127 independent auditor
   against the frozen V127 index with a new V128 output path. Rehash its original
   focused receipt and every inherited earlier proof. This retains the scalar,
   producer, owner, tile, bounds, rank and queue assertions/counters exactly; it
   does not claim those old executions bind changed V128 children.
2. **Extracted Boolean domain.** Extract the original selected validation and
   candidate two-lane expressions from the exact selected source hashes. Compile
   a strict scalar probe and compare both against a separate literal reference.
   Require deterministic boundary/random cases, lane/selector/phase coverage,
   true/false and selected-only mismatch cases. Counters and seeds are frozen
   before official execution. This proves finite algebra samples, not controller
   reachability or sequential behavior.
3. **Paired actual scratch.** Instantiate renamed old V127 scratch and actual
   V128 scratch with common old public inputs; only the candidate receives the two
   independent tuple inputs. Drive the original tuple from the selected input
   views in the verification wrapper. Compare every public result and original
   observable private view cycle by cycle. Drive new tuple inputs, never force
   new validation results or owner certificates. Use actual begin/INGEST/fault,
   memory request/response and retry edges. Prepared unreachable phase domains
   belong to the scalar probe and must not be labeled natural packets.
4. **Natural interface binding.** Run actual child/producer callers so the newly
   exported tuple views are checked against the original selected outputs. All
   original C++ require bodies and DUT assertions remain. The existing full
   decoder/peer benches execute the real child/producer; an additional frozen
   V127 generic/caller fixture replay may be used to retain the prepared-producer
   coverage on the changed dependencies. If reused, identify it as a fresh replay
   with the new source map; do not publish the old focused receipt as new proof.
5. **Fresh composition.** Rebuild and execute decoder107601/107602, actual V97
   transport107601/107602, peer115501/115502, then byte/row ordinary/stalled parent
   116701/116702. Require exact V127 stdout and decompressed event/canonical/hash
   streams, full keys, error/debt oracles and zero public-cycle delta. Expected
   independent raw comparison counts remain4 spatial,2 peer,4 parent.

## Keep the adapter and auditor small

Use V127 as an immutable module dependency, not a global `v127`→`v128` replacement.
A new contract can first invoke the existing V127 contract and old independent
full audit read-only, then verify the exact four-origin overlay and V128 recipes.
The eighteen source aliases/order and complete twenty-four-entry parent order
come from the frozen V127 index; fourteen other origins remain byte-identical.

The existing V127 auditor's `compare_spatial`, `compare_peer`, `compare_parent`,
`compare_packed` and `payload` functions are pure with respect to the baseline
index: they accept both receipt paths and raw dictionaries. Import those exact
functions from the source-hash-pinned old module without changing globals. Pass
V128 and V127 actual receipts explicitly. Their historical error-label strings
may remain unchanged; their byte/cycle comparisons must not be weakened. A new
short auditor owns V128 source identity, recipe reconstruction, focused checks
and status/schema inventory. Self-compare the actual V127 receipts to exercise
all4/2/4 helper paths before freezing V128.

Derive full runners by explicit single-occurrence structural edits of top-level
area/selector/source-map/status/contract bindings. Reconstruct every edit forward
and backward and inventory retained checker bodies. The current-source proof map
must assign all four new origins to the new raw-focused proof. Inherited V127
owner and V120 range proofs remain separately pinned as prior evidence; they
cannot be made to match new paths by changing their source-hash maps. Unchanged
producer assertions and functions remain source-identical. No mutable module
monkey-patching or arbitrary auditor source-text execution is needed.

Freeze the selected recipes, fixtures, scripts, seeds and independent auditors
before builds. Default command mode verifies preparation only. Root grants every
heavy dispatch, with at most two known jobs, each2CPUs, compilerj1,8GiB RAM and
8GiB total RAM+swap; launch requires availableRAM≥8GiB, fullPSIavg10<1 and combined
use<.85. Preserve failures and apply only reviewed, source-bound repairs with new
applicable builds. Native125MHz remains held until complete independent functional
PASS; a positive route requires a separate fresh identical-source/tool/recipe
repeat. No functional or Python result establishes physical30fps or<10ms decoding.

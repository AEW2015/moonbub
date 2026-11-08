# V110 busy and combined canonical controls

The actual busy-only and busy+fault full canonical receipts both pass: each
records 44 candidate case profiles and 42 directed checks over seeds 107601 and
107602 (22 profiles and 21 checks per seed). The 18-source order is preserved
with the declared replacement set: one busy source in the busy lane and one
busy plus three fault sources in the combined lane. All recorded current-source
and retained-snapshot hashes match.

For both seeds in both lanes, candidate stdout matches the frozen V109 FETCH
actual-control stdout, including public cycles. Compressed event and canonical
artifacts match their recorded pins, and their decompressed bytes equal the
V109 FETCH artifacts. The V109 control was reused, not rebuilt or counted as a
new execution. These canonical checks do not establish native timing, full
parent integration or hardware performance.

See [canonical-controls-final.json](../../experiments/python-gamebub-v110/audit/canonical-controls-final.json)
for receipt hashes and per-seed comparisons.

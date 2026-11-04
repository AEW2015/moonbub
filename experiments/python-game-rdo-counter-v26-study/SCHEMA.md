# gamebub-rdo-counter-v26

`results.json` records host versions, coded/active geometry, exact source-file
SHA-256 pins, `counter`, native `rows`, and `summary`.

`counter` records native coefficient and int64-size hashes, block count,
logical complete CP02 bytes, five oracle/counter timing samples, medians,
speedup, zero actual counter packet constructions, and sample manifests
(scene/frame/plane, original retained packet descriptor, block indices,
coefficient SHA-256). `general_packets` records whole-plane count/oracle byte
checks for each sampled native GM25 plane.

Each native row records scene/frame/key/reference identity, chosen background,
shared analysis clock, and every paid candidate attempt. Attempts retain the
old blob descriptor, exact GM25 hash/bytes, parsed coefficient hashes,
reconstructed-plane hashes, call order, both outer encode clocks and inner
RDO clocks, and fast RDO work statistics. No duplicate packet blobs are made.

The RDO statistics preserve old logical decision fields. `cp02_probe_calls`
and `cp02_probe_bytes` count actual constructed probes (both zero).
`cp02_logical_probe_calls` and `cp02_logical_probe_bytes` equal v25's old probe
counts and complete bytes. `cp02_size_counter_calls` counts batched per-plane
counter invocations; `cp02_size_counter_blocks` counts independent one-block
packets measured. These logical bytes are not transmitted GM25 traffic.

`summary` totals measured work over the native history: sources, paid attempts,
packet/coefficient/reconstruction parity, logical probes, both encode/RDO
times and speedups. Analysis-plus-attempt clocks charge shared analysis to each
variant. Verification rechecks pins and repeats the complete fast history,
native size oracle checks, and deterministic result/stat/hash assertions.

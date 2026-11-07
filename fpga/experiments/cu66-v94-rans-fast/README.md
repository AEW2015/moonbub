# V94 no-refill bypass experiment

This separate RTL fork retains the [staged control](../cu66-v94-rans/README.md)
and its complete 55-vector input byte-for-byte. UPDATE forms the widened
product-plus-remainder, checks its guard bits, and enters EMIT immediately when
normalization already holds. Other categories retain the refill path.

The new exact fence is:

```text
start → terminal clocks = 3×categories + refill bytes
                          + categories needing refill
                          + observed input/output stall clocks
```

Matched no-stall clocks improve **278,096 → 217,826**, saving **60,270
(21.67%)**. Independent replay proves each case saves exactly one clock per
zero-refill category. Both implementations check 203,019 main-sweep outputs;
their normalized states, byte cursors, table/state configuration and terminal
outcomes match the same independent goldens. Eight negative controls, three
active retries, two cancel/configuration races and three corrupted-oracle
checks pass. Stalled-seed runs prove correctness; their changed per-clock
credit schedule is not used for a matched speed claim.

For the actual-source subset alone—19 context encodings /30,809 categories—
clocks fall **130,622 → 107,198 (17.93%)**. The other 36 cases are synthetic
and have a larger no-refill fraction. These are selected category streams,
not full frames or a sustained video workload.

The combined multiply/update/normalization check can lengthen the critical
path. There is no routed clock, resource, board-fit or hardware-throughput
result. The staged implementation remains the control; no default promotion
is made. Packet parsing, literals, reconstruction, memory/display and full-frame
validated publication remain outside both kernels.

Reproduce with `python3 scripts/cu66-v94/run_fast_rtl.py`, followed by
`python3 scripts/cu66-v94/audit_fast_rtl.py`. Receipts retain source/vector and
control-report hashes, raw logs, focused compressed VCD and exact cycle pairs.

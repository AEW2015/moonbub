# V130 header verification: independent evidence audit

**Review mode:** read-only artifact and source review. No test, build, or
Vivado flow was run as part of this audit. The archive was streamed and
verified without extracting it.

## Scope and pinned artifacts

Reviewed the paired ingress RTL, testbench, runner, manifest, source freeze,
receipt, compile/simulation logs, and compressed object archive for attempt
`20261111T023151282166Z`.

| Artifact | SHA-256 |
| --- | --- |
| Attempt receipt | `f93d6d23b6ede9a89c101cbd3e15537e57988918d417ff151dea8eba6ec2f27f` |
| Frozen source manifest (`freeze.json`) | `b65e004c2c6e4226167bad56b94dfcd9a97fef6180aeec56370b9240dcb22b46` |
| Compressed object archive (`obj.tar.zst`) | `4ed5a9f5776d95c6972568b662e640c5ce9d5142ece6c1eba659e4e94454c6fe` |
| Selected V128 baseline ingress | `908aff5e690200ded17a6148fcbc0bbd5978ff658eee0c1a084df0bae6a8436b` |
| V130 candidate ingress | `87db883a38290dc72ade264648a18aed6a45f76bdb8270adf0d2176146e7af7b` |
| Paired-output wrapper | `2c46efd57391bd098c7d857a8dbe89eeea34f0804644861a5764700a479221e7` |
| C++ testbench | `0897551f103b5fdd482ab1cfec53f5d2663b7d7a3fef7f1c5fb2720b829a8a89` |
| Test runner | `83b34382954d74712558d9d2e5284061dec2113f54c770849d2560bfea516daa` |
| Pair manifest | `81d574805c4c5e653cf3a2438f7869dbcbd01cb01fa5957236dc3917e5779eff` |
| Built test binary | `281fcf49db6743723380c2050f8f3636e282d8ad5cf6a019025474ae364a7336` |

All nine frozen source hashes match both the attempt snapshots and current
repository files. The receipt is PASS with `actual_RTL_run: true`; all 105
receipt-listed artifacts match their hashes. The compressed archive contains
exactly the 93 receipt-listed `obj/` files. Streaming decompression completed
successfully, and each file's hash matched the receipt; no extra, duplicate,
or unsafe path members were found. The repository archive manifest agrees on
the receipt and archive hashes and the 93-file count.

## Build and test evidence

The receipt records a network-disabled Docker run using image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`,
2 CPUs, 8 GiB memory and swap limits, and a 900-second build watchdog. The
Verilator command enables assertions and strict warnings
(`--assert -Wall --language 1800-2017`); C++ uses
`-std=c++17 -O2 -Wall -Wextra -Werror`. The simulator is run from the same
image with a 120-second timeout. Both commands exited successfully; the
retained simulation log reports `TEST_PASS`.

The V128 baseline is a module-renamed copy of its frozen ingress source. The
candidate diff changes `begin_fetch` so it does not reset `fetch_index` for
`F_HEADER`, while all other fetch types retain the reset; it adds a simulation
assertion that `fetch_index` remains zero in `RECEIVE`. The paired wrapper
compares all 67 public outputs every evaluation, with no masked outputs.

The testbench and receipt support these directed coverage claims:

- 10,753 clocks and 41,677 evaluations.
- 1,254 input-gap cycles and 3,195 cycles with at least one of coefficient,
  metadata, or band-end output interfaces stalled. This is an aggregate OR
  count, not separate per-interface counts.
- Fetch-purpose mask `15`, covering all four enumerated fetch purposes.
- Six malformed final-marker cases: early `in_last` at indices 0, 1, 12, 41,
  and 69, plus omission of the final marker. Each checks error code 2.
- Four abort cases: during receive, while a header fetch is pending, while
  metadata is held, and while a coefficient output is held. The test follows
  each with successful traffic.
- Ten successfully completed recovery packets.

The runner's resource samples stayed above the available-memory floor; the
recorded maximum full-memory PSI avg10 is 4.36%, below its two-sample stop
threshold. This evidence does not establish system timing or runtime behavior.

## Limitations

This is a finite, directed, two-implementation ingress comparison. It is not a
formal proof, full decoder or full-parent qualification, routed timing result,
or hardware test. The pair checks equivalence and completion/error behavior,
but the testbench has no independent golden coefficient or metadata payload
oracle; a behavior shared by both instances could escape detection. The
malformed cases, packet shapes, stalls, and cancellations are selected
directed scenarios, not exhaustive or broad randomized interleavings.

No source, test, runner, or RTL was modified during this audit.

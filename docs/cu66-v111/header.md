# V111 existing-edge header validation pipeline

The isolated candidate is `fpga/experiments/cu66-v111-header/br88_packet_ingress_sync_v91h.sv`, derived exactly from the actual V110 Count ingress. The context specialization, Rice body, public interface, original assertions and original state/control assignments remain intact. Its source hash is `6c35433093feff81946df00af016289664b13cac0d6ce2d2b7207c668bb8a4b3`.

The only operational branch change is the original HEADER length-sum test. Two unsigned33 pair sums and an unsigned34 packet-size-minus46 target are captured on one edge; the widened unsigned34 total and aligned target on the next; equality on the third. All 169 payload bits update unconditionally without reset, cancel or global enables. Length bytes14..29 are stable before sixteen more sequential header reads, so this preparation precedes the existing HEADER consumption edge. No public cycle is added. A new consuming-edge assertion compares the prepared predicate against an independent unsigned64 sum and the original unsigned34 subtraction semantics. It is gated by the same immediate cancellation and higher-priority context/error conditions as actual HEADER consumption.

The source edit recipe is reversible and hash-bound. HEADER retains CRC error3, then basic-header error4, then length-sum error4 priority. Only after those pass does it assign lengths/counts/raw-mode and perform raw-specific rejection. Those assignments intentionally survive a malformed raw header's failure on that edge, including public count/raw views when metadata-valid is low. The private pipeline has no ownership outside consuming HEADER; equality of every private register on unowned cycles is not claimed.

## Focused test contract

`python3 scripts/cu66-v111/header/qualify.py --run` compares the actual old Count ingress against the new header ingress, with two distinct module-name-only copies of the identical enabled Count context and the same prefix Rice implementation. The existing probe compares every original public/invalid/debug/counter/memory signal. Existing capture, whole-packet, high32 metadata, prepared-address, reset/abort, corruption, retry and stale-owner assertion checks remain. Original goldens and assertions are not regenerated from the candidate.

The new extension checks real header packets with CRC/basic/length/raw conflicts, malformed-raw partial writes, cancellation on existing read/request edges around bytes21/29/30/31/45 and the HEADER edge, and 5,896 synthetic boundary/random header arithmetic rows per seed. Synthetic fixtures explicitly provide three preceding stable real clock edges to model completed header preparation; they do not assign the candidate's private pipeline registers or read its predicate to create expected verdicts. An independent C++ unsigned64 calculation derives expected branch outcomes and stored/public metadata writes. Synthetic directly forced HEADER states are additional arithmetic tests, not actual packet/API traces.

Commands are bounded and source-snapshotted, using Verilator5.020 with `--assert -Wall`, C++ `-Wall -Wextra -Werror`, compile `-j1`, two CPUs and 4GiB memory=swap. Launch requires available RAM≥8GiB and PSI full avg10<1. Stop requires available RAM<4GiB or PSI≥5 twice. The first compile attempt (`20261108T182117147983Z`) failed on two `-Wmisleading-indentation` errors in newly written C++ statements. It is preserved. The repair only added braces in the new extension; no RTL, assertion, golden, inherited comparison or expected value changed.

Qualification results are recorded separately in `experiments/python-gamebub-v111/header/results.json`. Full canonical qualification, routed100/125MHz results, production integration and hardware performance are separate gates; this document does not pass them.

## Actual focused result

Qualification is **PASS**, `actual_RTL_run=true`, `added_public_cycles=0`.
The summary SHA256 is `c4e7ede917cfc39a490f3619b73333d5e8de16e3dd34f737f9cdf6c63f0758a6`;
the selected attempt is `20261108T182139549017Z`, with receipt SHA256
`a5bb1ece67d9b40cfd6d5958a84ee42f64fdb163960087427dd3eac8adda723e`.

For **each** seed111501/111502:

- Inherited capture: 1,728 prepared cases, 128 high32 metadata owners, eight actual raw packets, 2,312 held metadata edges, all threshold/capacity/capture/flush/retry checks.
- Inherited whole ingress: 76 packets, 36 cancellation/retry pairs, 754,644 golden coefficients, eight actual prepared-address requests and all four request-purpose/boundary classes. Checked edges: 7,747,774 / 7,747,713.
- Added header suite: 5,896 synthetic arithmetic rows, 17 actual received-header cases, 30 additional request/response boundary cancellations and three HEADER cancellation/start/reset cases. The independent checker observed 31 / 33 malformed-raw partial metadata failures and 1,346 / 1,350 CRC-priority conflict cases across the synthetic and actual tests.

Six original stale-response subprocesses **total**, all using seed111501 and modes1/2 at indices33/37/41, reached the expected assertion and exited134. They are not six per seed. All 14 actual commands are recorded: eight successful commands and those six expected negatives. The final attempt took252.815s; observed available host RAM remained above23,110,901,760bytes and PSI full avg10 stayed0. Strict compile warnings/assertions remained enabled, with no new warning suppression or assertion downgrade. The actual source and fixture snapshots match their before/after pins. The failed first fixture compilation remains a separate failure record.

This focused result does not execute the complete canonical decoder, native implementation, clock closure, production parent or hardware tests. Those gates remain separate.

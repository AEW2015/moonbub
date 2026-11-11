# Independent review: header-index exploratory candidate

The paired ingress experiment passed for its finite directed inputs. It is **not** an integrated V129 functional qualification, a formal invariant proof, a routed timing result, or hardware evidence. The candidate is separate from the selected V129 source composition.

## Candidate and invariant

The [candidate ingress RTL](../../../fpga/experiments/cu66-v129-header-index/br88_packet_ingress_sync_v91h.sv) changes `begin_fetch`: for `F_HEADER` it holds `fetch_index` instead of writing zero; other fetch kinds still write zero. On reset, abort, and start, the existing sequential logic initializes `fetch_index` to zero. Start enters `RECEIVE` for valid parameters; the receive path initiates header fetch, and the candidate adds a simulation assertion that `fetch_index == 0` in `RECEIVE` when `cancelled` is false. This is a plausible local invariant, exercised by the passing test, not a proof over all possible state histories or a guarantee of improved mapped timing. The assertion is under `ifndef SYNTHESIS` and is not a hardware check.

The test's baseline module is byte-identical to the selected V128 ingress RTL except for the single module-name change. Both paired instances use the same context and V129 parser dependencies, which isolates this ingress edit in the tested setup; it is not a comparison against the entire frozen V128 composition.

## Recorded attempts

- [Initial compile failure](../header-index/attempts/20261111T010320704422Z/receipt.json), SHA-256 `3123c94ef99baa80b64e199bf35a461ee9ff92fe52e9c6356f492e0125dfd417`: `FAIL`, `actual_RTL_run=false`. Its retained log shows Verilator `DECLFILENAME` warnings because wrapper filenames did not match their module names; strict warning handling terminated compilation. No simulation result is attributed to this attempt.
- [Corrected passing receipt](../header-index/attempts/20261111T010410691169Z/receipt.json), SHA-256 `bf11ec9c006380b99de50d16c7526a739b98ed33a591cd6611aee57f043bf8c5`: `PASS`, `actual_RTL_run=true`; the corrected filenames match the modules. Its compile uses `--assert`, `-Wall`, and C++ `-Werror`. The retained simulation verdict reports 1,704 modeled cycles, 6,793 comparisons, four control-race trials, four coded packets, one raw packet, and fetch-purpose mask 15.

For each receipt, the frozen-input hashes, frozen-input snapshots, and every receipt-listed artifact hash matched. The failed attempt's historical source snapshots differ from current source files, as expected after correcting its filenames; its evidence remains bound to its own freeze. All ten passing-attempt current inputs also match their recorded hashes. The passing simulation log exactly matches its recorded verdict.

## Comparison and limits

The generated wrapper connects common inputs to both actual ingress instances and compares **all 67 original public outputs** on every bench evaluation; the extra 68th wrapper output is the comparison result itself. The directed bench exercises reset, abort, start, and simultaneous control cases while input valid is held, checks the four fetch-purpose bits, completes the five packets, and fails on any compared output mismatch. Both the public comparisons and the invariant assertion were enabled in the strict simulation.

This is a small deterministic paired test: four repeated coded packets and one raw packet, with output/meta/band readiness held enabled. It does not establish coverage over arbitrary malformed packets, all lengths or parser states, prolonged backpressure, arbitrary reset/abort timing, all reachable states, or the full streaming parent. A successful pair comparison also cannot detect an error shared by both instances. Stronger source-bound randomized/backpressure and fault tests, full 18-origin functional comparisons, and fresh place-and-route are still needed before selecting the edit or claiming timing benefit. No monitor, candidate source, test receipt, or recorded artifact was modified for this review.

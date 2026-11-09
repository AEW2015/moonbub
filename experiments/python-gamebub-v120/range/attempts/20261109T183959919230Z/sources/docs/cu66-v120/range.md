# V120 isolated signed16 range candidate

The first V120 production candidate changes only the ingress raw-value range predicate. It replaces both the output qualification and reason-5 rejection with a complete bit-prefix predicate for signed values −2048 through +2048 inclusive. The +2048 endpoint is intentional. Output mode/owner/ready/cancel, physical synchronous RAM requests, error priority and public cycle timing retain their original logic. Every original assertion block remains byte-for-byte, and a new assertion checks the prefix against the original signed comparisons.

The source is derived reversibly from the ingress used by V119, `fpga/experiments/cu66-v117-ingress-bytecount/br88_packet_ingress_sync_v91h.sv`. `edit-recipes.json` pins every source and adapter. This isolated candidate does not incorporate speculative payload control changes. Its measured timing effect requires a new full-component/native campaign.

## Focused qualification

The strict Verilator runner retains all original V117 packet, malformed/CRC, cancellation, descriptor-extent, ceil-byte, and caller oracles. Verification references are regenerated from the actual V119-used ingress, V116b control and V119 scratch source. No old assertion or expected predicate is removed; the complete public pair compares even invalid-cycle tuples and counters. The inherited current-source caller also retains its private pending-tuple comparison, physical debt/drain/replacement, staging timing and golden dense output checks.

The additional exhaustive predicate test prepares a declared RAW owner with no packet RAM request or pending response, and checks every one of 65,536 bit patterns against independent signed C++ bounds. Each context clocks the actual candidate and current reference through the original output qualification and same-edge reason-5 rejection. These are synthetic predicate contexts, not naturally decoded frames or a transport throughput result.

Separate natural tests feed complete one-block RAW packets with all nine signed endpoints at coefficient zero and coefficient 63 under two input/output stall profiles. Valid packets must complete with exact coefficient tuples and owners. Invalid packets must reject at the first invalid coefficient with reason 5, without accepting it or emitting a band-end. The first valid coefficient is deliberately held for thirteen edges. Additional natural tests cancel/reset/start at the first actually fetched RAW owner for each endpoint and then perform clean nonreset retries. Invalid RAW values with CRC/header faults retain earlier reason-3/reason-4 priority.

Per seed, the new tests require 36 natural boundary packets (20 valid, 16 reason-5 rejections), 27 natural prepared cancellations, 67 nonreset retries, 364 explicitly held output edges, two CRC-priority cases and two header-priority cases. Every natural synchronous read must have its actual accepted request/response owner, with complete read conservation. The old per-clock public comparison is never skipped.

## Dispatch

Root alone launches the heavy command:

```bash
python3 scripts/cu66-v120/range/qualify.py --run --root-grant ROOT_V120_RANGE
```

Preparation without `--run` only verifies static source derivation and immutable baseline evidence. The runner uses the pinned Verilator 5.020 image, `--assert -Wall`, one compiler job and C++17 `-O2 -Wall -Wextra -Werror`. It enforces available-RAM/PSI/combined-use gates and two-CPU/eight-GiB/no-added-swap limits. Each fresh attempt preserves source/compile snapshots, raw logs, exact commands, binary/source/artifact hashes and failed receipts. `actual_RTL_run` is persisted before model invocation. Only the complete ingress-and-caller suite can publish a `PASS` selector; partial suites use separate nonqualifying selectors.

This document is part of the focused source pins and must remain unchanged after the first dispatch. Put measured results in a separate `range-results.md`. Simulation proves only the tested functional contract. It does not establish synthesis mapping, 125 MHz, a full-parent clock, sustained 30 fps or under-10-ms hardware decoding.

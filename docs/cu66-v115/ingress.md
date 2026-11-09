# V115 owned ingress descriptors and parser continuation caches

Selected focused proof: [`ingress/results.json`](../../experiments/python-gamebub-v115/ingress/results.json).
The [source/evidence review](../../experiments/python-gamebub-v115/ingress/source-review.json)
rehashes the selected raw receipt, all 22 source pins and 31 retained artifacts.
This is implementation-author review, not an independent timing or integration signoff.

## Changed contract and sources

Two replacements preserve their module names and ports:

- `fpga/experiments/cu66-v115-ingress/br88_packet_ingress_sync_v91h.sv`, derived
  reversibly from the frozen V110 Count ingress used by V114 B.
- `fpga/experiments/cu66-v115-ingress/br88_rice_elastic.sv`, derived reversibly
  from the frozen V110 Prefix parser used by V114 B.

IV115.ingress adds one private `SELECT_BAND` edge before each descriptor and
before each context start: eight inserted edges per compressed packet, none for
raw packets. This is a latency-changing ingress contract. Cycle-varying stalls
can shift schedules; a universal whole-frame cycle delta is not claimed. The
old exact-cycle checker remains unchanged in its original path.

A complete active-band tuple captures length, length-minus-one, count, offset,
bit size, Rice parameters, band and count-validation result. The descriptor's
last-byte address is registered at fetch admission, so request bounds no longer
combine a live band-array selection, wide addition and bounds comparison in one
edge. Full unsigned32 address arithmetic and the hardware bounds checks remain.
The original independent live-address and request-owner assertions remain active.
The reparenthesized last-byte formula is the same modulo2^32 expression; 100,169
supplemental Python boundary/random checks are arithmetic checks, not RTL cases.

Replay words capture their bit count and last-word flag during their existing
synchronous fetch wait. A registered nonzero predicate controls the next owned
replay operation. Context delivery uses the captured descriptor tuple. Every new
payload is qualified by its original state/word-valid ownership; it has no bulk
payload reset. Start, reset, context fault and abort retain their original public
revocation and local synchronous-read cancellation behavior.

The Rice parser caches the PREFIX window across the existing request boundary
and maintains exact remaining/load eligibility bits on their update edges. The
parser's original public outputs, stored state and counters remain cycle-exact
in the paired tests. New independent assertions validate every owned cache use.
All original synthesis-guarded assertion blocks are retained byte for byte.

## Actual focused results

Both strict Verilator 5.020 builds use `--assert -Wall`, fatal SV warnings, and
C++17 `-Wall -Wextra -Werror` for the owned testbench. No assertion or fatal
severity is disabled. Each of the two parser seeds passes:

- 6,096 parameter cases and 189,105 prepared-state edges;
- all 1,520 historical cases over eight serial/word/stall configurations, with
  173,061 requests per configuration and 104 directed checks;
- the original independent scalar reservoir/counter oracle and every old
  public/private stored-state comparison.

The single prepared-state adapter initializes the three new private cache
fields from the prepared operands. All original comparisons remain; prepared
states are supplemental and are not called protocol reachability proof.

Each of the two actual ingress seeds passes 160 ordinary corpus profiles (all
four serial/word16 combinations under two service profiles), 54 cancel/retry
cases and four malformed-frame cases with clean retries. Each seed completes
218 successful packets and 1,904,808 independently golden-checked coefficients.
The request ledger records 1,602,892 requests = 1,602,874 responses + 18 explicitly
canceled local read owners. This is a private synchronous RAM port, not an AXI
transaction that can be silently abandoned.

Cancellation covers header indices 41/42/45, descriptor-tail byte 6, replay/raw
fetches, descriptor selection, context selection and the held replay-word tuple.
Reset, abort and replacing start all execute; subsequent clean retries do not
require a blanket reset. Corruption covers CRC, impossible descriptor length,
invalid descriptor bit count and invalid Rice parameter. The new checker uses
the unchanged historical dense-to-sparse golden function and independently
checks every returned RAM byte, request epoch/address, held output, complete
held metadata, band ordering and final counters. It does not compare shifted
cycles against the old ingress.

## Reproduction and limits

With a Root heavy-job grant:

```sh
python3 scripts/cu66-v115/ingress/qualify.py
python3 scripts/cu66-v115/ingress/qualify.py --run
```

The first command verifies the reversible source and test adapters only. The
second runs bounded fresh builds and simulations under the pinned tools image,
two CPUs and `--memory=8g --memory-swap=8g` (no additional container swap), with
host available-RAM/PSI gates and finite watchdogs. Both production replacements,
their recipes, runner and selected proof are frozen after PASS. No native timing,
full component/parent, CDC, Sunshine/ESP32, displayed-frame rate or hardware
claim follows from this focused campaign. Root must qualify the complete chosen
composition and route actual 10/8 ns targets.

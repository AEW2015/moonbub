# V124 focused owner-lane results

Focused qualification is **PASS**, with actual RTL execution on the first
attempt. The [selector](../../experiments/python-gamebub-v124/owner/results.json)
names [attempt 20261110T040103948600Z](../../experiments/python-gamebub-v124/owner/attempts/20261110T040103948600Z/receipt.json),
schema `v124-owner-lanes-existing-edge-operands-focused-v1`. It completed in
628.842 seconds. This note is post-run reporting; no frozen focused input was
changed after dispatch or PASS. There were no failed execution attempts.

| Artifact | SHA-256 |
| --- | --- |
| Selected V123 reference controller | `3517bda5016d7c2920e20fbc0767bbb1146e091cea4a5216db9a8b9a6532ee30` |
| `fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv` | `963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53` |
| `fpga/experiments/cu66-v124-owner/packaging.json` | `85e2ffc9b3e0cb2de6526ff32434a584f025cdd059dab2f97f38c7ee3baf9e74` |
| `fpga/experiments/cu66-v124-owner/edit-recipes.json` | `ea3a47f12e476a1c52c374a9d678f36c314080e4e75e4bb1732c75c344ff50d0` |
| Selected attempt `receipt.json` | `0a807acc5de0e3d44ed09b22848d58badbfbd8467cacb6aef3aebe5ef1f33e01` |

The reference is the selected V123 controller in
`fpga/experiments/cu66-v119-owner/cs88_coefficients_v91k.sv`. All other V123
origins remain pinned, including scratch `12ad7721…`, V122 admission and the
V121 queue. Production changes only full32 epoch/full16 block comparison
before the one-bit emit-bank selector, its scalar non-tile fallback and the
three consistent ready/valid/error-67 consumers. The only new synthesis
attribute is KEEP on the two combinational `tile_owner_match` result bits.
It introduces no FF, DONT_TOUCH, placement, hierarchy, timing exception or
native recipe change. Attribute presence is not evidence of physical placement
or routed timing improvement.

One fresh whole-producer model compiled under Verilator 5.020 with assertions,
`-Wall --public-flat-rw` and C++ `-std=c++17 -O2 -Wall -Wextra -Werror`.
The compile log contained no Verilator warnings, and no warnings/assertions were
downgraded or disabled. The same new binary ran both generic seeds
**124101/124102** and actual-controller seeds **124201/124202**. Containers
used the frozen two-CPU/8-GiB memory-plus-swap policy with host memory/pressure
gates, bounded command/watchdog timeouts and no additional swap.

Every original V119 producer/cache/nonce check remains through reversible
source and fixture derivations. The original probe still compares every public
field, private producer control/owner registers and all raw scale-store words;
it additionally compares internal child-ready directly. Both real controllers
and their actual child RTL clock together. The production assertions check both
complete lane expressions, their selected scalar identity and raw bank-view
identity on every tile-mode clock, including invalid and unready cycles.

The retained baseline coverage passed per generic seed:

| Retained check | Actual result |
| --- | --- |
| Trusted cache beats / physical scale commits | 14,892 / 12,838 |
| Cache preloads / start attempts | 13 / 19 |
| Prepared full11-bit counter cases | 2,048 |
| Complete public comparisons | 60,515 for seed 124101; 60,377 for seed 124102 |
| Entropy/nonce reason matrix | 9,216 cases: 6,966 error-64, 74 error-66, 2,176 accepted predicate contexts |
| Additional full32 nonce checks | 250,000 deterministic random RTL-wire cases |

The additive bank-owner coverage passed with these counts per generic seed:

| New check | Actual coverage |
| --- | --- |
| Full-width raw-bank wire/state cases | 466,944 total: 393,216 boundary/mode cases, 65,536 random full-width cases, 8,192 parent-state cases |
| Modes/selectors/readiness | All four raw/tile configurations, both bank selectors, all four bank-ready masks and all four reset/abort masks; all 256 parent-state encodings |
| Ready remains independent of validity | 9,856 ready-true cases while child-valid is false; 1,792 ready-true cases while the selected tile bank is unready |
| Clocked DISPATCH contexts | 1,152, crossing eight full32 epoch and six full16 block boundaries, good/bad epoch/bad block and all eight reset/abort/start overlaps |
| Same-edge outcomes | 192 error-67 cases, 864 cancellations and 16 expected-block wraps |
| Held output / terminal return | 336 held edges with opposite unready-bank poison; index-62 then index-63 acceptance and final scratch FINISHED/busy timing |
| Response/debt priority | 224 prepared matching, wrong, unsolicited, error/owner and reset/abort contexts, with independent state/error/outstanding checks |
| Added public/error cycles / skipped pair edges / removed checks | 0 / 0 / 0 / 0 |

These generic full-width and clocked control contexts are **prepared-domain
fixtures**. They bind the original controller and child raw-bank state and
owner operands coherently; they never force `tile_owner_match` or
`child_owner_match`. Reserved/high-bit tags, arbitrary block boundaries and
unready raw views are deliberately tested without claiming those states came
from naturally received packets. Prepared response debt is explicitly
synthetic and retired with a matching response. Its priority checks are
separate from naturally accepted physical request/ACK ownership.

Actual-controller tests derive reversibly from the complete frozen V91i2b
packet/controller bench. Only its model class/header and entry-point name are
adapted; every original packet, coefficient, mapping, memory and recovery
check remains. Each actual-controller seed passed:

| Natural retained-vector check | Actual coverage per seed |
| --- | --- |
| Packet vectors / memory profiles / case rows | 11 / 2 / 22 |
| Dense coefficient comparisons in case rows | 4,058,368 |
| Additional directed dense comparisons | 913,984 |
| Tile trace rows | 63,412 |
| Directed checks | 12 |

The directed checks cover queued/pending refill cancellation and warm reset;
real accepted-write ACK drain blocking a replacement start; held mapped output
cancellation; good retry after late CRC failure without reset; partial trusted
cache-load abort; one-shot cache reload; zero frame epoch rejection; snapshot
and first-cache-byte tags; and exact mapped coefficient tuple fields. Every
case row completed with matching accepted request/ACK counts and no pending
drain. The original bench also checks memory-line ownership/write-before-read,
stable stalled requests/output, queue highwaters and refill conservation.
Its producer outputs remain provisional coefficients; this focused test does
not claim full-frame publication or physical hardware memory service.

The declared and tested contract is **zero added natural public cycles relative
to selected V123**, including unchanged error-67 timing, expected-block wrap,
ready/valid qualification, scratch final-case override and abort/response/debt
priorities. No predicate is qualified by bank-ready, child-valid or an assumed
current tag/block. Payloads, counters, state/error and all applicable pair
outputs remain checked on every eval. Packaging is a lossless single whole
module, with no fragment transformation beyond the separately recorded module
name adapters used by verification.

This is finite two-state simulation over the enumerated generic values and
retained natural transactions. It is not exhaustive over all pairs of 32-bit
bank epochs, 16-bit blocks and control histories; it does not establish
four-state X/Z equivalence or formal proof. No focused result establishes
mapped lane placement, 125 MHz timing closure, CDC, system throughput, frame
rate, physical memory performance or hardware qualification. Independent
functional audits, full-parent integration and the fixed native experiment are
separate parent-owned evidence.

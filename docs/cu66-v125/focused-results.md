# V125 focused results

The first focused attempt passed all three strict builds, both scalar seeds,
both complete admission-pair seeds and both actual-controller seeds. No failed
V125 focused attempt or runtime fixture repair preceded this selected receipt.
This is finite functional evidence; native timing is a separate qualification.

## Selected evidence

Selected pointer: `experiments/python-gamebub-v125/tile/results.json`.
Selected receipt: `experiments/python-gamebub-v125/tile/attempts/20261110T060144640227Z/receipt.json`.
Receipt SHA-256: `4ec296015f29a2f20a202a132077abef6d95207b91e43fe0a39355a0ad89cd69`.
Schema: `v125-tile-existing-edge-predicates-focused-v1`; `actual_RTL_run=true`, terminal `PASS`.
Root launched the bounded run with `ROOT_V125_TILE`; this report launched no job.

| Frozen input | SHA-256 |
| --- | --- |
| Production `fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv` | `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb` |
| Selected V122/V124 admission baseline | `54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf` |
| `fpga/experiments/cu66-v125-tile/edit-recipe.json` | `d811713b4b467acc7aa66faa640477285443a6689ad6641a9e6b549091fa3dbd` |
| `fpga/experiments/cu66-v125-tile/packaging.json` | `96c4683277db3d2ddf8bc710af2808b09949b9e9ba6979d9c3f43eb7be154144` |
| `fpga/experiments/cu66-v125-tile/verification-recipe.json` | `fd5acdb803a59614d6de433a8856c4924aafac6f4f63981f48ce2ed94fbd841d` |
| `docs/cu66-v125/tile-design.md` | `5e488a067f3ff602a39c222fb3b36d8cbc730e5b4e9b806af6055032da172628` |
| `scripts/cu66-v125/tile/qualify.py` | `39814e729ad63b93014f60c8682121cf197194434f3c18e9e4279042f46b42cd` |

The receipt retains all root/snapshot/compiled-source/artifact hashes and the
three executed binary hashes. Packaging losslessly reconstructs the complete
production source from its main admission module and unchanged scale/mode
helpers. Adapters reconstruct the full baseline/candidate source; inherited
assertion blocks and require bodies remain intact. No new predicate or owner was
forced. The source adds three unreset scalar payload bits and no public port,
state, cycle, synthesis attribute or timing exception. Other selected V124
origins remain unchanged, including its owner-lane KEEP bits, V123 rank scratch
and V121 refill queue.

Verilator 5.020 used assertions and strict warnings, with C++
`-std=c++17 -O2 -Wall -Wextra -Werror`. Root's launch caps were two CPUs and
8 GiB RAM-plus-swap, no extra swap, with host RAM/PSI/combined-use gates and
watchdogs. All compile/run commands exited zero. The approximately
698.5-second host wall time includes compilation and is not
modeled device service or hardware latency.

## Extracted full32 scalar domain

For each seed 125501 and 125502, the losslessly extracted production register/task
and hidden/count logic passed 232652 boundary cases and 65536 random full32
cases: 298188 total, with 5665589 actual clocks, 596376 hold edges, 2087316
cancel cases, 101652 high-bit cases, 112 uint32 plus16-wrap input cases and eight
terminal-call transitions. Plane3 cases were 74557 and 74567 respectively.
Each key exercised all seven nonempty reset/start/abort overlaps. Literal
terminal successor expressions checked plane3 two-bit wrap and the plane2
GROUP_NEXT no-write branch.

This is an isolated registered scalar domain, not a whole reachable coordinate
state domain. It does not clock an arbitrary high32 tile through an original
coordinate-advance state or disable the V105 coordinate assertions. The plus16
wrap count is an input-domain count, not a recomputation of GROUP_BEGIN's min.
That min remains byte-identical; real GROUP_NEXT→GROUP_BEGIN→tag-commit tests
check the original newly registered end and partial-plane boundary behavior.
Independent Python algebra, maintained separately by the auditor, is additional
finite corroboration and is not an RTL execution or formal equivalence proof.

## Retained checks and honest primer clocks

Both seeds retain all original V122/V119 admission, header, coordinate, quant,
mode/scale, request/response, receipt and fault-priority checks. Retained floors
per seed include:

- 158228 semantic mode-port cases and their original 158230 clock component;
  all initialized/read/write/held mode entries and final 8100-entry oracle remain.
- 40585 scale, 738933 header and 348673 quant/prepared edges.
- V119 mode-bound 540 cases; V116 chunk-bound 25344 cases and 294 cancellations.
- V120 full35 67664 cases, including 65536 random and 4096 owned consumes,
  36 natural packets and 36 nonreset retries.
- V122 full32-bound 16384 cases and 56 cancellations, retaining full64 overflow
  and distinct wrapping uint32 number checks. High32 full64-sum cases were
  6756/6741 and number-wrap cases 3277 per seed.

A prepared-key primer clocks the actual non-jump MODE_BIT tag writer, then
reapplies only the old fixture's already-forced old context. It never sets a new
payload/owner, writes mode RAM or advances coordinates. It is explicitly not a
natural packet/state chronology. The extra clocks update actual counters and
are reported, rather than keeping a fictitious old raw clock total.

| Clock ledger | Seed 125501 | Seed 125502 |
| --- | ---: | ---: |
| Retained semantic mode cases | 158228 | 158228 |
| Original mode-clock component | 158230 | 158230 |
| Additional retained-mode primer clocks | 40879 | 40891 |
| Actual retained-mode clocks | 199109 | 199121 |
| New directed semantic clocks | 852 | 852 |
| New directed primer clocks | 411 | 411 |
| New directed actual clocks | 1263 | 1263 |
| Total primer clocks, all prepared fixtures | 41290 | 41302 |
| Prepared clocks covered by new ownership monitor | 200370 | 200382 |
| Natural Bench clocks covered by new monitor | 13637393 | 13635637 |
| Total new-monitor clocks | 13837763 | 13836019 |

Each seed's raw primer trace has sequential real-edge IDs and target states
{0,6,10,11}, with the actual writer transition 8→10. Monitor prepared clocks
are 158228 + all primer clocks + 852; total monitored clocks are natural plus
prepared. Other retained generic loops have their own original ledgers and are
not silently included in this monitor's denominator. Natural clock totals vary
with seed-driven traffic; exact-cycle equality is between the two models given
the same seed/input schedule, not between different seeds.

The new directed campaign passed 411 prepared contexts, 189 cancellation cases,
19 first-followup consumes, three malformed contexts and two checks preserving a
speculative mixed-mode write before a later error8. It distinguishes old versus
new group end, equality versus greater-than behavior, plane boundaries and
terminal/error priority. Every one of 33 original states has positive raw
coverage for all seven cancellation overlaps in the 33×8 matrix.

## Writer/first-consume ownership matrix

Natural writer counts below are identical for both seeds. Slash-separated
prepared, first-consume and overwritten counts are seed 125501 / 125502. These
are private key/scalar checks, not counts of independent packets; a single
GROUP_TILE edge can consume both tile and group keys.

| Boundary | Natural events | Prepared events | First key/scalar consumes | Overwritten before consume |
| --- | ---: | ---: | ---: | ---: |
| Header success | 196 | 0 / 0 | 142 / 142 | 51 / 51 |
| KEY step | 1,150,200 | 8,316 / 8,301 | 1,150,202 / 1,150,202 | 8,122 / 8,118 |
| KEY terminal | 426 | 27 / 27 | 286 / 286 | 3 / 3 |
| Tag commit | 25,101 | 41,326 / 41,338 | 123,861 / 123,900 | 58 / 58 |
| Hidden-only jump | 300 | 8 / 8 | 301 / 301 | 0 / 0 |
| Mixed-bit step | 233,988 | 16,270 / 16,258 | 467,984 / 467,984 | 16,204 / 16,202 |
| GROUP step | 166,212 | 16,877 / 16,886 | 332,432 / 332,432 | 16,795 / 16,796 |
| Plane clear | 100 | 17 / 17 | 0 / 0 | 101 / 101 |
| GROUP_BEGIN invalidation | 25,401 | 20 / 20 | 0 / 0 | 0 / 0 |

GROUP_BEGIN invalidates group ownership but captures no new comparison. Group
equality samples the already registered end on real tag commit. Plane-clear's
snapshot is overwritten by tag commit before a predicate consumer; its zero
first-consume count is intentional and the 101 overwrites are explicit. No
unused snapshot is relabeled as a successful consume. Writer categories 0–6
all have positive first-consume coverage; held/private payload and owner keys
are checked independently against original full32 expressions.

## Actual controller pair and scope of zero-cycle evidence

Seeds 125601 and 125602 each passed 11 vectors, 22 cases/two memory profiles and
12 inherited directed checks. Each compared 4058368 dense coefficient tuples,
913984 directed dense tuples and 63412 tile rows. All case rows passed with
requests equal to acknowledgements and no pending drain. The retained directed
checks include queued/pending refill cancellation, warm reset, accepted-write
drain blocking start, held coefficient abort, retry after late failure, partial
cache abort, one-shot cache ownership and zero frame epoch rejection.

The two full producer/controller models use selected V124 sources and differ
only in admission. Public/private/scale comparisons and existing physical-debt,
coefficient, held-data, memory, CRC and publication checks remain active. No new
fixture primer is used in these caller packets. Raw pair checks report zero
added natural public cycles and no divergence for the tested input schedules;
they do not assert a general formal theorem about all possible transactions.

All evidence is finite two-state simulation. Extracted/high-bit prepared cases
are not natural packets or proof of arbitrary four-state/X behavior. This run
is not physical reset/CDC, board I/O, real SDRAM/LCD, hardware service, native
125 MHz closure, sustained 30fps or complete validated decode under10ms
qualification. Full integration/independent audits and native routing have their
own receipts; this focused PASS does not substitute for them.

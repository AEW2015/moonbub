# V118 scratch functional result and mapping checks

The per-band registered decision candidate passed the completed strict Verilator campaign. The [receipt](../../experiments/python-gamebub-v118/scratch/attempts/20261109T143730523578Z/receipt.json) binds source SHA `45972143e61b8c4a5eaa6f37fb7f81dd0625acaf0416607eb2ef584c907fb179`. An [independent architectural review](../../experiments/python-gamebub-v118/audit/scratch-architecture-review.json) rechecked every live source pin, retained artifact pin, reversible production edit, inherited assertion block and both explicit fixture adaptations.

| Suite | Observed evidence |
|---|---|
| Generic, each of seeds117301/117302 |1,048,576 full coefficient-domain cases;983,031 invalid cases;90 prepared-abort cases;36 foreign abort cases |
| AC acquisition, each seed |10,496 cases;8,960 cache hits;192 misses;192 same-edge prefetch forwards;768 kills;192 response errors;192 wrong owners;192 physical drains |
| Selected payload, each seed |9,344 independent bytewise comparisons;all16 offsets,3 AC bands,4 physical response segments and4 formats |
| Actual caller, seeds117401/117402 |80 case rows across20 packets and2 configurations per seed;9,003,776 dense comparisons;112 directed checks |
| Existing private tile ownership, each generic seed |8 natural pending kills and8 same-object full retries;9 prepared event contexts;5 outer-priority guards;2 held-bank edges |

These counts include repeated coverage across seeds. They are not counts of distinct real gameplay frames or hardware events. The original inherited certificate names and JSON verdict types remain unchanged.

The source adds six reset-free predicate registers: fetch-needed and head-applies for each of three AC bands. Each lane compares its local full32-bit cursor/count and head geometry before `read_band` selects a narrow decision. The head-install edge forwards the accepted selected head; the head-consume edge forwards cleared validity and the unchanged next cursor frontier. Existing fetch/read/DC control edges mature predicates for stable ownership. Every eligible AC_CHECK compares the selected predicates with the complete original expressions, including current target block.

The focused pair compares current V116/V117-compatible control and V118 on every real edge. It retains public and raw payload/owner observations, error priority, cancellation and physical response debt. The V118 change adds zero public cycles. The inherited `old_public_cycle_equivalence:false` field describes historical V115 descriptor preparation: its adapter clocks **both** current pair sides during all three warmup edges. It does not mean the V118 checker skips reference clocks or hides a new delay.

Two old tests deliberately deposit complete private contexts. Their reversible adaptations initialize the six new redundant predicates once alongside those deposited heads/counts/cursors. The AC acquisition fixture initializes only its first deposited AC_CHECK; subsequent AC_FETCH, response acquisition, AC_EXTRACT and head retirement use actual RTL. Natural packet/caller transactions never call these initializers. There is no per-evaluation predicate refresh, disabled assertion or weakened independent value oracle.

The first attempt stopped before RTL execution on a tautological `read_band<=3` certificate for a2-bit field. Its failed snapshot remains. The successful source removes only that upper-bound test and keeps the meaningful nonzero-band check under fatal warning enforcement.

The intended mapping improvement is removal of selected32-bit counter mux/carry logic from AC_CHECK publication feedback. Actual native reports must establish whether the six predicates survive mapping, where their fanout lands and whether the routed critical path moves. Inspect `*ac_lane*` cells, actual setup paths to scratch state/bank-ready/status counters, and all fanout/control-set reports. New lane-install paths through validation may become the next bottleneck. No timing exception or source-only claim substitutes for a nonnegative fresh routed result and required positive repeat.

Replay extents remain unchanged in this integrated scratch candidate. The separately prepared [replay proposal](replay-proposal.md) is dormant and has no qualification claim.

Final native review confirms all six predicates survive as FDREs. Neither completed target has an `ac_lane` source/destination in its bounded worst50 paths. Both fresh 100 MHz component routes pass at +0.061 ns; 125 MHz still fails through other families. See [native results](native-results.md) for the measured clock qualification and remaining paths.

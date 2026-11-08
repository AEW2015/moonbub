# V107 combined mode and scale tables

**The frozen TABLES source passes complete paired admission tests and actual mapped UNISIM qualification of both memories.** Whole-pipeline canonical comparison and decoder routing are separate parent-owned gates; the focused evidence here does not substitute for them.

The candidate [production file](../../fpga/experiments/cu66-v107-tables/cs88_admission_v91i2a.sv) is SHA-256 `b149c94ba1a5dd7f1d09384126c762d0bb0de5aa664baa4b76c29c631aeb652e`. It composes the previously proved V105 mode-write consolidation onto frozen [SCALE1956](scale.md), which already contains HEADER7a417. Original HEADER, SCALE, V105 sources and their receipts remain unchanged. [Exact edit recipe](../../fpga/experiments/cu66-v107-tables/edit-recipe.json) and [portable audit](../../experiments/python-gamebub-v107/tables/audit.json) establish that reversing only the mode edits recovers SCALE1956 byte-for-byte and its scale helper remains identical.

The change follows actual routed evidence. A read-only probe of the frozen Elastic route found mode[0] slack −2.508 ns (12.455 ns data, twelve levels) and scale[0] −2.587 ns (12.534 ns, fourteen levels), both from `coefficients/tile_cursor_reg[5]/C`. The checkpoint was mounted read-only and its SHA stayed unchanged. Consequently the planned SCALE-only global canonical/native trial was explicitly deferred in favor of both table cuts. No unperformed SCALE-only global result is claimed; the separate HEADER-only native trial was actually launched.

## Source behavior preserved

The five mode write guards, their ordering and full-width address expressions are copied **byte-for-byte** from the retained [V105 recipe](../../fpga/experiments/cu66-v105-memory/edit-proof.json):

1. ACTIVE_CLEAR writes value 1 when full 32-bit `active_index != 8100`, using the original low 13-bit address.
2. KEY_TILE writes hidden 1/visible 2 when full 32-bit `tile != tile_count(plane)`.
3. MODE_BIT writes selected 0/2 only when `bits_left != 0 && mixed_bit`.
4. GROUP_TILE writes hidden 1/tag-zero 0 when `tile != group_end` and its first branch qualifies.
5. GROUP_TILE tag 1 writes 2 only after the preceding hidden/tag-zero branch does not apply.

All plane offsets and tile addition remain full-width until the original final 13-bit truncation. Tile updates, residual tasks, coordinate caches, metadata guards, packet capacity 49,152, error priority, counters and clock schedule are unchanged. An independent modular-address model checks 196,608 combinations of high 32-bit prefixes, low 13-bit bits and all plane encodings; it does not claim arbitrary unreachable coordinate states are valid parser states.

The mode store retains **8,100×2 bits**. Parser writes use the consolidated port; FINISHED lookups keep their original one-edge synchronous read. Lookup outputs hold through every parser write, idle edge and reset/start/abort; the memory/output are not cleared. Mode write and FINISHED read predicates are mutually exclusive in the caller. The helper also gives write priority if both raw helper requests are asserted, preserving hold behavior in its standalone test.

The **1,350×2 scale TDP helper is unchanged**: external cache write on logical A, Q_FILL write / FINISHED read on logical B, same-address Q_FILL write priority, old-data return on same-edge A-write/B-read, and output hold during writes/cancellation. Its source helper SHA remains `62b9d4754dfe3ba5c2bacb766bc11a463abada38619a619e341a799066a239b3`.

## Executed actual primitive qualification

[Selected native unit receipt](../../experiments/python-gamebub-v107/tables/unit/20261108T051111105011Z/receipt.json) binds the same final b149 source. Vivado 2026.1 synthesizes the actual helpers on `xc7a100tcsg324-1`; XSim 2026.1 runs the resulting UNISIM netlist with a common 10-ns clock, real primitive models and collision checking enabled. No behavioral substitute or explicit primitive branch is used.

| Actual mapped cell | Primitive / mode | Width read A/B, write A/B | Write modes A/B | Optional output registers |
| --- | --- | --- | --- | --- |
| `modes/words_reg` | RAMB18E1 / TDP | 2/2, 2/2 | READ_FIRST / WRITE_FIRST | 0/0 |
| `scales/words_reg` | RAMB18E1 / TDP | 9/9, 9/9 | READ_FIRST / READ_FIRST | 0/0 |

There are exactly **two RAMB18E1 primitives**. The physical mode settings are not mislabeled NO_CHANGE: the actual inferred clock-enable/hold mux implements the required public hold behavior, and the complete mapped netlist passes that contract. AMD's [UG473 memory guide](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content) and [RAMB18E1 library reference](https://docs.amd.com/r/2024.2-English/ug953-vivado-7series-libraries/RAMB18E1) define the common-clock and write-mode assumptions. Actual 2,048/8,192-row physical rounding is not an increase in the source's valid address domain.

The mode unit performs 72,947 clocks: all 8,100 valid words, all four 2-bit values, 32,439 known-held-output checks and all seven nonzero reset/start/abort combinations. Its last known lookup is held through complete 8,100-word write sweeps. The same netlist also repeats the 27,033-clock scale unit: 5,400 old-data collisions, 1,350 distinct concurrent writes, 5,400 same-address Q_FILL wins and 6,782 hold checks. Both terminal PASS markers and `TEST_PASS_TABLES_UNIT` are required. This is post-synthesis functional simulation without SDF, not physical timing or board qualification.

Cold output values, unwritten words and out-of-range lookup addresses remain undefined/unqualified. Mode addresses 8,100…8,191 and scale addresses outside 0…1,349 are not assigned invented values. The physical test initializes every valid word through actual writes before data checks. The prepared full-controller test separately uses explicitly initialized arbitrary memory states, including reserved value 3; it does not claim such initial contents or that value are accepted packet grammar.

## Paired full-controller and independent oracles

The [selected focus receipt](../../experiments/python-gamebub-v107/tables/attempts/20261108T051532111480Z/results.json) compares the complete old SCALE controller and new TABLES controller every clock. Strict Verilator 5.020 `-Wall --assert` and C++ `-Wall -Wextra -Werror` pass with no warning suppression. Two seeds cover 172 historical case/seed runs, 88 directed checks, the existing header/quant/coordinate suites and **23,029,486 total clock edges** across historical and prepared scopes.

Per seed, the original V105 mode oracle now drives 158,228 prepared cases plus a real priming lookup. Every valid mode address is read, all five write branches execute, and the complete 8,100-word final store is checked. The first four branches each cover all 8,100 write addresses; tag 1 covers its 7,806 visible addresses. High32 ACTIVE_CLEAR indices retain low 13-bit address interpretation. Lookup holds, no-write guards and all reset/start/abort combinations are checked independently from the DUT. The existing 40,585-edge scale oracle checks all 1,350 words/four values, concurrent writes, same-address priority, old-data reads and cancellation. Separate Python replays recompute all mode/scale events; packet-coordinate and quant-run oracles remain active.

The first TABLES focus attempt is retained as a **fixture failure**: the reused V105 all-state preparation forced HEADER_CHECK without binding later HEADER cached sums. The existing assertion correctly fired in the original SCALE side. The correction binds both sides' cached sums to their prepared header bytes and binds the consumed Q_RUN byte cache; no DUT, source guard or assertion changed. Production b149 and its matched native unit stayed unchanged.

[Packaging metadata](../../fpga/experiments/cu66-v107-tables/packaging.json) gives two byte offsets and three exact filename/hash fragments: main `cs88_admission_v91i2a.sv`, unchanged `cu66_scale_tdp_v107.sv`, and `cu66_mode_store_v107.sv`. Their binary concatenation must reproduce b149. Paired compilation deduplicates the identical SCALE helper across old/new controllers. Native compiles the original combined admission file. The parent records 19 RTL compilation fragments plus its header; the source-file/module distinction is explicit, with no filename-warning waiver or production rewrite.

Run `python3 scripts/cu66-v107/tables/audit.py` for the portable source/receipt/trace/primitive audit. It checks the exact reversible recipe, unchanged scale helper, copied V105 generator, lossless packaging, paired oracles, actual primitive parameters and mapped terminal PASS. Reproduce focused simulation with `python3 scripts/cu66-v107/tables.py`, and native unit qualification with `python3 scripts/cu66-v107/tables/unit.py`, only when the shared heavy-job gate allows a run. No full-device timing, CDC, external-memory/display service, hardware fps or validated-decode-latency claim follows from this focused work.

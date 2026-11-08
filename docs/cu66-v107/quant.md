# V107 admission quant run-byte prefetch

The candidate captures the quant run byte on the existing edge before Q_RUN, separating the large qbuffer selector from the Q_RUN validity/control/decode cone. Public ports, state sequence, latency, counters, errors and external-memory behavior are unchanged. Rice remains frozen independently.

The actual resumed sixth-source PLACE report identified `coefficients/admission/qbuffer_reg[167][0]/C` → `q_value_reg[0]/D`: setup WNS −4.168 ns at the unchanged 10 ns constraint, 14 logic levels, 14.161 ns data delay (3.411 logic / 10.750 estimated routing). This is placement evidence, not a routed result. The retained report is in `/home/lori/gamebub-build/cu66-v69/v107-resume-20261108T033536487942Z/results/place-setup-paths.rpt`. The path crosses the dynamic qbuffer selector, run-bound addition and decode enable before q_value.

The exact starting point is the inherited V105 complete production admission module. Only Q_BYTE writes qbuffer. There are exactly two Q_RUN entry edges:

- Successful Q_CHECK mode 2 sets q_index=12 and now captures qbuffer[12]. Q_CHECK follows the last Q_BYTE write, so nonblocking write timing is already settled.
- The last Q_FILL edge (`q_remaining==1`) now captures qbuffer[q_index[8:0]]. Q_RUN advanced q_index before entering Q_FILL, so this selects the next run without another increment.

The Q_RUN references to dynamic high/low byte slices use the private 8-bit register. Full-width q_index terminal comparison, modular 32-bit run arithmetic and all original guards/error priority remain intact. Mode 6 follows its old bypass and does not consume the register. A terminal Q_RUN ignores the byte, including when the previous edge prefetched the first CRC byte. No qbuffer write occurs between either capture and consumption.

The register has no reset assignment: every consuming Q_RUN entry captures it first. Reset/start/abort priority prevents capture/use on cancellation edges; subsequent live entries initialize it again. The enabled selected-state assertion checks equality with the original dynamic expression only in nonterminal Q_RUN with all cancellation guards clear. No public validity flag or extra cycle is introduced. All header/mode/scales/cache-write/lookup/replay logic stays byte-for-byte unchanged.

Candidate source SHA-256: `58d0fcb876692c2ad38fa0585a5d2e13cd83079f64a84538f8de5a5c4d139d61`. The [exact recipe](../../fpga/experiments/cu66-v107-quant/edit-recipe.json) reproduces the edits against its pinned baseline hash. Verification adapters strip exactly back to both complete production bodies; only observation ports and explicitly identified Verilator access annotations are added for testing.

The explicit simulation backend is historical Verilator in the native build container. Root's Vivado simulation MCP transport is closed. Behavioral testing uses strict Verilator `-Wall --assert` and C++ `-Wall -Wextra -Werror`, bounded command timeouts and testbench watchdogs. Both complete production modules run together, comparing every public output and counter every edge; the quant index/run/remaining/value and selected backing byte are also compared. The private cache is compared only when consumed, matching its declared contract.

Independent verification uses original packet bytes to replay the complete Q_RUN/Q_FILL address, value, remaining-count and cached-byte sequence. An in-simulator scale oracle tracks external cache writes and Q_FILL writes, with Q_FILL priority and read-first lookup semantics. The inherited full packet corpus checks receipts/descriptors/errors, synchronous read ownership/epochs, held receipts, reference snapshots, modes and all lookup addresses. Reset/abort/replacement start are extended to Q_BYTE, Q_CHECK, Q_RUN and Q_FILL, followed by complete positive recovery packets.

Prepared-state supplements explicitly initialize a Q_RUN cache to its selected byte. They do not claim arbitrary internal-state reachability. All 256 byte encodings are checked across full32 run/index boundaries, with terminal priority and modular arithmetic retained. All 354 in-range physical byte addresses and all 256 byte encodings also enter actual Q_RUN from actual Q_FILL, starting with an incorrect dead cache and verifying its capture before use. Out-of-range physical addresses are tested only in the terminal branch, which does not consume them; no deterministic out-of-range array-read semantics are claimed.

## Actual RTL result

**PASS**, Verilator 5.020, seeds 107501 and107502. Strict compilation has no Verilator warning suppression and assertions remain enabled. All42 production public outputs across64 ports match each pre/post edge. The adapters also compare selected quant controller state and backing byte; supplemental prepared accesses are verification-only. Exact adapter removal recovers both whole production bodies.

| Selected campaign | Seed107501 | Seed107502 |
| --- | ---: | ---: |
| Public-interface edges | 9,410,899 | 9,410,490 |
| Prepared-state edges | 348,673 | 348,673 |
| Base packet cases (positive / negative) | 86 (52 /34) | 86 (52 /34) |
| Directed checks | 35 | 35 |
| Independently replayed live Q_RUN edges | 2,776 | 2,776 |
| Independently replayed Q_FILL writes | 103,950 | 103,950 |
| Independent scale lookup checks | 907,213 | 907,217 |

The selected campaign checks **19,518,735 actual clock edges**. The run/fill replay includes77 terminal edges and the expected rejected invalid-value run per seed, with no public cycle tolerance. Public-interface cases include32 additional complete mode2 recovery packets, each rewriting all1350 cells amid external cache writes before registered lookup checks.

The [selection](../../experiments/python-gamebub-v107/quant/results.json) points to the immutable [results](../../experiments/python-gamebub-v107/quant/attempts/20261108T034801856278Z/results.json), SHA-256 `a71f5dbd32a11db8c12c0b986536c4dae57058eb9ec5538dcd9f20351c1da478`. Its sources, strict compile/tool/binary logs, complete case transcripts and compressed traces are retained and hashed. The [audit](../../experiments/python-gamebub-v107/quant/audit.json) checks23 artifact hashes, current source hashes, both verdicts/replay results and the complete two-attempt history.

The first attempt remains FAIL: actual seed107501 and all packet semantic checks passed, but the predeclared greater-than100,000 fill-edge coverage floor was unmet at60,750. Added stimulus raised this to103,950; the coverage floor, semantic checkers and production source were unchanged. Both new seeds pass. No failed evidence was removed or reclassified.

Reproduce the exact-source/adapter check with `python3 scripts/cu66-v107/quant/recipe.py`, the serialized actual campaign with `python3 scripts/cu66-v107/quant.py`, and its artifact audit with `python3 scripts/cu66-v107/quant/audit.py`. Physical timing, parent fresh/canonical production integration, hardware throughput and complete decode latency are separate gates.

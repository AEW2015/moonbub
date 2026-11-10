# V128 owned header-padding cut

Root selected this bounded second cut before the first V128 freeze. It addresses the measured V127 `header[124][0]` → admission `tile/R` cone, −1.165 ns, in parallel with the separately prepared four-origin RAW validation factor. The raw-only component history remains unchanged. The final aggregate selects five aliases and retains the other thirteen origins.

The [candidate admission source](../../fpga/experiments/cu66-v128-padding/cs88_admission_v91i2a.sv) adds exactly one unreset Boolean payload: `prepared_header_padding_ok`. On the existing HEADER_BYTE116 edge it captures `byte_value==0`; on HEADER_BYTE117..127 it ANDs the previous prefix with the **current** byte comparison. This forwards byte127 while the old header[127] array value has not yet received its nonblocking update. HEADER_CHECK then assigns its original static local `padding_ok` from the owned flag. That local view still holds on all other states and cancellation edges.

There is no added public cycle, payload reset, synthesis attribute, public port or module. The original ordered error4→5→6→7→8 chain, full64 generation comparisons, rejected-header behavior, frame metadata and logical counter views stay unchanged. Both isolated RAM modules at the original source's tail remain byte-identical. The [lossless packaging](../../fpga/experiments/cu66-v128-padding/packaging.json) is one complete file containing all three existing modules, not an assertion that the source has only one module.

The payload capture is intentionally not gated by reset/start/abort, matching the established unreset total-match cache style. A cancellation may change this new, unowned payload; it cannot authorize HEADER_CHECK. The actual parser reaches HEADER_CHECK only after this transaction's ordered header-byte writes. The new verification-only owner tracks the complete receipt epoch, size and next padding index, invalidates on cancellation, and requires all116..127 writers before consumption. It also compares the cached result with an independent literal96-bit current-header fold. Those owner registers and assertions are under SYNTHESIS guards and add no production state.

The new cache does not promise arbitrary forced-state equality when a caller skips its required writer sequence. Existing prepared-state tests that jump to HEADER_CHECK must first execute the actual padding-byte writers rather than force the cache or an owner flag. Natural full-component tests execute the original fetch/load FSM and provide the separate reachability evidence.

The [source recipe](../../fpga/experiments/cu66-v128-padding/edit-recipe.json) records two exact reversible edits and retains all sixteen old guarded assertion blocks verbatim. Its [preparer](../../scripts/cu66-v128/padding/prepare.py) checks source/attribute/RAM-tail identity and refuses overwrite. The source adds one production sequential block and one logical payload bit; physical resource counts remain to be measured.

## Focused source-kernel contract

The [verification preparer](../../scripts/cu66-v128/padding/prepare_verification.py) extracts source fragments for the original and candidate HEADER_BYTE write, old/new padding consumer, existing total-match writer and original ownership assertions, h16/h32 helpers, and the entire ordered header rejection predicates. The candidate also includes the exact new cache and ownership fragment. The repaired verification wrapper evaluates the exact source padding fold or cache expression in combinational `evaluated_padding`, then NBA-captures the observable held local view only on the original noncancel HEADER_CHECK edge. Ordered reject predicates read the current evaluated expression, rather than the previous observed register. This preserves the source's consumer edge, old-view hold and error priority with no additional DUT clock. Reject task actions become the corresponding error assignments; success emits error0. Full metadata installation and the fetch/load FSM are not part of this reduced kernel.

The two kernels and top are emitted as three matching module/filename files, with a byte-exact reconstructed bundle recorded in the extraction recipe. This avoids relying on a multi-module filename exception under strict lint.

Both kernels receive the same **prepared** state/index/byte events. New payloads or owner flags are never forced. Every low/high/low evaluation compares the old padding/error views. An independent C++ scoreboard checks the full header fold, signed-free byte writer/hold behavior and complete original error priority. It records all eligible HEADER_CHECK consumptions and tests all error classes0,4,5,6,7,8. Runtime counters are not FPGA decode or network latency measurements.

| Required per seed (128701 /128702) | Count |
| --- | ---: |
| One-byte padding position/value cases (12 ×256) | 3072 |
| Random full headers and error/snapshot/generation contexts | 4096 |
| Cancellation at every padding index ×all seven reset/start/abort combinations | 84 |
| Incomplete writer-prefix eligibility checks | 12 |
| Nonwriter-state cache-hold checks | 558 |
| Full-width out-of-range index writer checks | 6 |
| Explicit byte127 nonzero→zero forwarding checks | 2 |
| Observed unowned payload changes on canceled byte edges | 84 |
| Complete owned header consumptions | 7268 |

Incomplete prefixes are observed as ineligible and canceled before any impossible forced consume; this is not a claim that a public malformed packet can skip FSM writers. Nonwriter checks include all33 original state encodings except BYTE/CHECK, multiple full32 indices and byte values. Out-of-range byte writes can alias an array slot through the original low7 header index; the cache's full32 writer enable must still hold, and a later complete retry refreshes the header before consumption.

The strict [runner](../../scripts/cu66-v128/padding/qualify.py) defaults to read-only reconstruction. `--run --root-grant ROOT_V128_PADDING` is required for the finite actual Verilator run. It freezes its source snapshots, builds freshly with assertions/Wall and C++17/O2/Wall/Wextra/Werror, executes both seeds, retains raw verdicts and compressed case traces, and applies the same two-CPU/8-GiB combined-memory/finite-watchdog policy as the rest of V128. The selected fresh run below has executed; source preparation alone was not counted as RTL proof.

This proof is a source-extracted clocked kernel, not full admission execution. The complete selected five-origin decoder/transport, peer and byte/row publication parent must still be freshly run and independently compared to V127. Source-kernel PASS alone cannot release native implementation, qualify125MHz, or establish hardware30fps/under10ms.

## Executed focused results and preserved repair

The selected [receipt](../../experiments/python-gamebub-v128/padding/attempts/20261110T205028675118Z/receipt.json), SHA-256 `8856bb3bd578bbeeb9edd1cf2572057ea73ee4fa889ab378ada0b6a39dd395d9`, is PASS after one fresh strict compile and both selected seed runs. All four commands exit zero; all13 source pins and19 artifacts close, and source/snapshot bytes are unchanged. Each seed completes all7,268 headers and all table counters above, including87,828 payload captures and84 observed unowned cancellation-edge payload changes. Error classes0,4,5,6,7,8 are all positive.

| Seed | Actual kernel clocks | Equality evaluations / view checks |
| --- | ---: | ---: |
| 128701 | 1,072,456 | 3,217,368 |
| 128702 | 1,072,334 | 3,217,002 |

These counters are prepared source-kernel work and cannot be presented as gameplay throughput or decoding latency. Host orchestration takes8.090 seconds, including the5.0-second compile. The actual full admission FSM is not executed by this focused kernel; the selected five-origin complete-component regression is the separate caller proof.

The [first attempt](../../experiments/python-gamebub-v128/padding/attempts/20261110T203914447394Z/receipt.json) stopped before RTL simulation when strict BLKSEQ lint rejected three assignments to the verification projection's module-level blocking temporary. Its13 source pins,15 artifacts, original freeze and failed log remain preserved. It is a verification-adapter compile failure, not a production RTL test failure. The [official-warning research](../../experiments/python-gamebub-v128/padding/warning-research.json) records the actual5.020 diagnostic and matching release source, while distinguishing the current online guide version.

The authorized [projection repair](../../experiments/python-gamebub-v128/padding/repair-history/20261110T204309401260Z-BLKSEQ-projection/repair.json) preserves all before files, failed receipt/log and exact patch. It changes only the verification generator, recipe and two kernel projections; the top, C++ cases/oracles, runner, strict flags, both seed contracts and all five production sources remain unchanged. The new combinational evaluation and original-edge NBA observation do not suppress a warning or add a DUT clock. The original [design prose](plan-history/padding-design.before-BLKSEQ-projection-repair.md) remains an historical pre-repair record.

Root's [revision-2 functional freeze](../../experiments/python-gamebub-v128/audit/functional-tooling-freeze-revision2.json) precedes the selected fresh build and binds the approved padding repair alongside the separate RAW fixture settle correction. The successful fresh strict build and both complete selected runs above verify the padding workaround. Full native125MHz signoff and hardware goals remain unqualified by this unit result.

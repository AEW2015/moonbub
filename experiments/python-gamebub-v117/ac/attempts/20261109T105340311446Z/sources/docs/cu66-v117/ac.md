# V117 selected AC record capture

Status: prepared for Root-dispatched qualification; no RTL execution or timing result is claimed by this document. This note and source recipes are frozen inputs once the run starts. Terminal receipts and audits supersede this preparation status without rewriting pinned files.

The baseline is V116 C's `packed_scratch_v91g2.sv`, SHA256 `1ac70499489acbdb00e682696a5783cf178c3e703e3b16d2138f275f7de59839`. Its actual 125 MHz route failed setup at −1.847 ns WNS. The worst path begins at scratch `read_address[2]` and selects/validates a cached AC record before retiring error/ownership state into `busy_owned/D`; 75.424% of its 9.794 ns data delay is routing. This candidate targets that measured cone, preserving V116's pending-record banks and selected caller.

## Production change and owner contract

One private 51-bit payload holds the selected 32-bit word and 19-bit predecoded position. The existing transaction registers—address, segment, band, epoch, cursor and head frontier—remain its hardware owner. There is no added queue, public port, transaction slot or state edge.

- On the existing AC_FETCH edge, select using the exact future address `starts[read_band]+cursors[read_band]*4`. The same edge still writes the original `read_address`/`read_segment` and enters AC_EXTRACT.
- If a same-edge successful prefetch response overwrites that selected bank, forward `mem_rsp_data` and its literal all-offset position decoding. Selecting the old cache value would be stale.
- On READ_WAIT's AC response edge, capture the selected word/position directly from the response, on the original return to AC_EXTRACT.
- AC_EXTRACT validates the registered payload using the original block/rank/signed13/monotonicity expressions and writes the head tuple on the original successful edge. Cache misses, error priority, immediate cancel/reset, physical debt and `busy_owned` state equality retain the old behavior.

Private payload capture uses acquisition-state enables without adding the late cancel/validation cone to their CEs. It may capture garbage on a canceled or invalid response edge; the original state/tag ownership prevents consuming that data. A new owner reacquires before use. This is not permission to accept a wrong response or release physical debt.

An additive verification-only acquisition certificate copies the existing owner fields and proves them coherent at every actual consuming AC_EXTRACT edge. It also proves selected word/position equal the original cache algebra and selected invalid flag equals the unchanged per-bank predicate. Original `read_word`, `read_position`, local-bank predicate and every old assertion block remain independent. No busy flag is delayed to improve slack.

The new payload has no explicit reset assignment. This is an RTL property only; physical synthesis may still infer format-zero reset controls. Native mapping and routing must be measured before describing mapped resets or claiming a clock benefit.

## Focused proof

`python3 scripts/cu66-v117/ac/qualify.py --run --suite all` is dispatched only by Root. It uses two strict generic seeds (117301/117302) and two unchanged real-caller seeds (117401/117402), preserving all original assertions, `--assert -Wall`, C++ `-Werror`, and zero skipped paired edges.

The generic pair uses frozen V116 C as the independent original. All inherited generic/private storage/abort/physical-debt suites and the full 16-bit × eight-phase × raw/sparse pending-record suite remain byte-identical. The real-caller pair retains every old public/raw/counter and private-pending-tuple comparison, preparation faults and complete packet replay.

An additive bench contributes 2,304 explicitly prepared acquisition cases across all 16 byte offsets (including offsets 13–15 and zero-filled overflow), three AC bands, four physical cache segments, four record classes and hit/miss/forward/reset/abort/error/response-owner paths. They use real predecessor acquisition edges rather than forcing the new payload or certificate. Protocol reachability is not claimed for cross-segment or unusual matching-error/no-owning-prefetch contexts; the original controller's behavior is still checked exactly there.

Another 8,192 cases acquire every signed13 word value through the real AC_FETCH/AC_EXTRACT sequence at a legal geometry. Independent bytewise selection and mathematical retirement check 4,096 legal nonzero values and 4,096 invalid zero/out-of-range values. Total additive cases per generic seed: 10,496. Physical wrong-owner responses retain their lease until matching late response drain; no checker is disabled to inject those cases.

The runner preserves each attempt, copied compile inputs, raw transcript, compressed traces, exact source/recipe hashes and terminal result. `actual_RTL_run` is recorded before invoking a simulation, including failed runs. The compact selector points to the selected raw receipt.

## Scope

This is a same-cycle timing candidate. It supplies no cycle-latency savings for the V116 1,416,449-cycle parent interval. The separately proposed II=1 inverse and two-owner reconstruction work must pass its own proofs. Focused success alone does not qualify the complete decoder body, transport, C2/HUD/SHA parent, routed timing, ESP32 execution, physical SDRAM/display, sustained hardware 30 fps or validated under-10-ms decoding.

## Retained initial fixture failure

Attempt `20261109T104901153683Z` executed actual RTL. All inherited suites passed, then the new acquisition cases hit the frozen original's sealed-owner assertion (observed_original.sv:1099; the assembly-bytes assertion is line1098). A prepared AC_FETCH context incorrectly combined `sealed=1` with an outstanding prefetch/error lease outside the original allowed sealed states. The bench now sets `sealed=0` for those explicitly non-reachable private contexts. Every old assertion, pair comparison and acquisition/response/drain check remains enabled; production RTL is unchanged. Case labels are flushed before each directed case. The failed snapshots, raw log and actual-RTL receipt remain intact; `fixture-repair-1.json` pins the cause and bench-only correction. A fresh run is required.

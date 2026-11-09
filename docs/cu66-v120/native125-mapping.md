# V120 A: routed 125-MHz path mapping

The prefix-only A design completed fresh synthesis, placement and routing, but **does not meet 125 MHz**. The independent audit verified 749 checks, including retained artifacts, consumed sources, recipes, logs, functional proof pins and all 450 reported path records. No additional tool runs or source edits were performed.

Evidence:

- Native receipt: `experiments/python-gamebub-v120/integrated-study/native/20261109T193132372767Z/receipt.json`
- Mapping audit: `experiments/python-gamebub-v120/audit/native125-terminal.json`
- Audit SHA-256: `2e1d8cbb25be311ea7f05562b623b7685958a8407aa5d126ab3fbab334af6385`
- Actual part/top: `xc7a100tcsg324-1` / `cs88_pipeline_v91k`.

## Actual implementation result

| Metric | Result |
| --- | ---: |
| Clock period | 8.000 ns |
| Setup WNS / TNS | −1.847 / −8,745.703 ns |
| Failing setup endpoints | 18,274 |
| Hold WHS / failing endpoints | +0.084 ns / 0 |
| Pulse-width slack / failing endpoints | +2.750 ns / 0 |
| Routing errors | 0 |
| LUTs / registers / BRAM tiles / DSPs | 33,802 / 43,089 / 38 / 42 |
| Routed CARRY4 primitives | 4,198 |

All 18 consumed source origins match the full A simulation map. The native flow used Vivado 2026.1 build 6511674, fresh RTL, Default synthesis/optimization/routing and `ExtraNetDelay_high` placement. The 8-ns clock was loaded before synthesis. No checkpoint reuse, retiming option, timing exceptions or guessed external I/O delays were added.

Compared with V119, WNS improves by 0.258 ns, but TNS worsens by 2,559.797 ns and failing setup endpoints increase by 3,554. This is not timing closure. Physical placement changes affect many cones; a better single worst slack does not imply uniform improvement.

## Which cones actually fail

| Retained report | Paths | Worst slack | Measured worst path |
| --- | ---: | ---: | --- |
| Normal setup | 50 | −1.847 ns | Admission `header_packet_total[0]` → `tile[4]/CE` |
| Extended setup | 200 | −1.847 ns | Same admission path |
| Kill source family | 50 | −1.402 ns | `base_kill_authorized` → Rice `cached_remaining[4]/CE` |
| RAW-mode source family | 50 | −1.558 ns | Ingress `raw_mode` → scratch `error[0]/D` |
| RAW-coefficient source family | 50 | −1.257 ns | Ingress `raw_coefficient[1]` → scratch `error[0]/D` |
| Context-emitted source family | 50 | −1.313 ns | `emitted[9]` → geometry BRAM enable through position/parser logic |

These samples overlap and do not enumerate all failing paths. The normal 50 are an exact prefix of the extended 200.

The normal 50 are entirely admission paths: 42 start at `header_packet_total[0]` and eight at `tile[0]`. In the extended 200, 196 start in admission, three start at ingress `raw_mode`, and one at scratch read-address state. Neither optional proposal changes admission.

The global worst path has 9.594 ns of data delay: 2.220 ns logic and **7.374 ns routing**. It crosses three CARRY4 stages and seven LUTs. Its launching register has fanout one; the later coordinate-enable net has fanout 57. This is a late validation/control cone with long physical travel, rather than a simple high-fanout source register. Actual carry-cell names and locations match the routed inventory.

In the RTL, `HEADER_BYTE` prepares the full 35-bit packet total at header index 55. `HEADER_CHECK` later combines its equality test, other header checks and fault ordering with same-cycle key-frame/coordinate/tile initialization. That late control propagates through the measured `state230_in`, `key_frame` and coordinate-enable cone.

## What the existing proposals can change

The combined address proposal has a real secondary target. Kill-family ranks 27–29 terminate at `prepared_request_addr[18,25,8]/CE` with −1.345-ns slack; rank 31 reaches bit 5 at −1.327 ns. Its phase-local writer removes cancel/start gating from exactly two unowned private payload fields. Its unit proof is valid for the default 49,152-byte configuration, with independent transition/owned-request/cache checks. It does not directly change the worse parser storage-enable cone or the global admission cone. Any placement benefit elsewhere remains unmeasured.

The context-terminal proposal also has a narrower direct target. Ten emitted-family paths, ranks 33–39 and 48–50, run from `emitted[7]` to `out_epoch/CE` at −0.514 to −0.475 ns through seven CARRY4 stages. In the RTL, the output-epoch acceptance enable depends on `emitted` through the trailing-last-event test. The proposed `terminal_last_event` moves that predicate to an existing request phase, so it targets this subset.

The worse emitted-family path instead crosses first-RUN position selection and parser position arithmetic before reaching BRAM enables, with five CARRY4 stages and −1.313-ns slack. The existing proposal leaves `emitted==0` and the run-position computation unchanged. A source-family name match alone is insufficient to credit the terminal predicate with fixing this path.

RAW-coefficient paths still cross two CARRY4 stages feeding the independent scratch range/format checks. RAW-mode paths cross three. A changed only the two ingress range sites; scratch still validates coefficient bounds, ordering, position, phase and ownership. The total inventory of 4,198 carries is not evidence that every coefficient-related carry chain disappeared. Merged hierarchical cell/net names also cannot identify an RTL expression by themselves.

Neither proposal is selected by this audit. Their unit PASS results establish functional contracts, not routed improvement or 125-MHz closure.

## Next measured experiment

The highest-priority new candidate is an isolated admission validation cache, prepared during existing header-load cycles after the relevant full-width totals and fields are stable. It should replace late wide validation with an owned one-bit decision at `HEADER_CHECK`, preserving the original first-fault priority, all overflow behavior, invalid inputs and public cycles. The long interval between header byte 55 and the final header check provides preparation opportunities without adding a public edge.

Before routing it, prove cache ownership across reset/start/abort/retry, retain the original full-35-bit assertions, and compare malformed-header and full-decoder cases against A. Follow with tile/coordinate control and scratch format/range validation if their measured paths remain critical. The address and terminal proposals can be routed separately as bounded secondary-cone experiments, using the same recipe and reports; their global benefit must be measured.

The separately authorized 100-MHz hardware effort can proceed using its own qualified map and checks. This OOC 125-MHz result provides no board bitstream, sustained hardware 30-fps result or validated under-10-ms decoding claim. External I/O timing, parent integration, real memory service and display behavior remain separate qualifications.

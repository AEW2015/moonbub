# V109 fetch response cut and remaining routed cones

The initial A/B routes both fail the unchanged 10-ns component clock. These are final routed reports, not synthesis estimates. Neither run contains the fetch-address candidate: both use the actual V108 capacity ingress body SHA `6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6`. A uses the qualified V108 scratch; B uses the V109 prefetch plus bank-decode scratch (`1ff4901cdaa98ef5267215f7454042a95d2dc001234caf5b4e4d44f0c6283843`). Both use the same V109 fault top. Their difference therefore does not measure the fetch-address cut.

| Actual final route | A: fault only | B: fault + prefetch + bank decode |
| --- | ---: | ---: |
| WNS | −1.589 ns | −1.737 ns |
| TNS | −8,342.999 ns | −5,988.869 ns |
| Setup-failing endpoints | 14,204 | 12,615 |
| Worst hold slack | +0.087 ns | +0.088 ns |
| Worst pulse-width slack | +3.750 ns | +3.750 ns |
| Routing errors | 0 | 0 |
| Worst launch → endpoint | ingress fetch_index[3] → fetch_bytes[8][0] CE | ingress fetch_return[2] → error[0] CE |
| Data delay | 11.300 ns | 11.448 ns |
| Logic / routing | 3.541 / 7.759 ns | 3.273 / 8.175 ns |
| Logic levels / CARRY4s | 14 / 4 | 15 / 7 |

Both reports identify Vivado 2026.1 build 6511674, routed Artix-7 `7a100t-csg324`, speed grade −1, with component clock edges at 0 and 10 ns. The receipts use `xc7a100tcsg324-1` and report component-internal 100-MHz pass as false. B has lower total setup deficit but a worse worst path; neither is setup closure.

Evidence:

- [A receipt](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/receipt.json), SHA `4d06f300ec2da7f2747591e71fab9991a4caf30885d2f63caf4afe038ae9a18d`; [A setup paths](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-setup-paths.rpt), SHA `b5ff4fca46d8a7eff4b1936e122dd6d6295932a7feece54e9306056c0b5c3906`.
- [B receipt](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/receipt.json), SHA `db2269be508ad111716e86c63f76e2d0b45a16bc2e651fe81d259a5fcae07680`; [B setup paths](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/reports/route-setup-paths.rpt), SHA `71559aed655c2931af025d429315a2143a85073e154281a4aab4b48609963485`.

## Exact scope of the prepared response cut

The [frozen fetch candidate](../../fpga/experiments/cu66-v109-fetch/br88_packet_ingress_sync_v91h.sv) has SHA `4d6a16d0b89aa067fe3e7acc01351ea0bacac694cc63fb681a1471ee4683d044`. Its [focused receipt](../../experiments/python-gamebub-v109/fetch/results.json) records actual RTL PASS. That establishes the exercised exact behavior; native placement and routing must establish its timing effect.

The original request address has three full-width forms: `fetch_base+fetch_index`, the header trailer jump `size_bytes-4+fetch_index-42`, and the descriptor last-byte address `fetch_base+lengths[band]-1`. FETCH_REQ uses this live expression for bounds, public stage_read_addr and the synchronous RAM read. The candidate's independent, unreset expected_fetch_addr captures this same expression at the existing FETCH_REQ edge, with state-only enable. An accepted request enters FETCH_WAIT on that edge. Its base, index, kind, owned packet size and descriptor length remain unchanged until response consumption; immediate cancellation makes any intervening private capture unowned.

Only the following two production comparisons change:

1. The FETCH_WAIT address mismatch branch compares ram_addr against expected_fetch_addr. The epoch check, current response/cancellation/context-failure gates and original byte-consumption edge remain intact. This removes the live address adders from the response qualification feeding fetch_bytes byte CEs, replay_word and word_valid qualification, raw/descriptor completion, and next-state selection through this branch. It does not remove the other inputs to those endpoints.
2. prefix_header_capture uses the same cached address comparison. This removes live address arithmetic from the header count-prefix capture and its threshold/capacity pipeline capture enables. It does not move count high-byte forwarding or any pipeline commit edge.

A's top fifty contain eighteen ingress paths launched by fetch_index[3]: ten fetch_bytes CEs (eight at byte8 and two at byte42), two state D endpoints, four replay_word CEs, one word_valid D and one context_active D. The measured worst route traverses stage_read_addr carry logic before shared response/state control and byte CE logic. The response comparison is an explicit source dependency into these actions; caching its arithmetic is therefore a specific logical cut motivated by A. A fresh native report is still required to show which paths remain and where Vivado places the new registers.

The direct fetch_index dependencies remain: selecting which byte register is written, the fetched_word byte-selection mux, `fetch_index+1`, high-water update, and last-byte comparison against fetch_count. These can still reach the same endpoint families after address arithmetic is separated. Do not equate removal of one branch of the cone with removal of every fetch_index→CE path.

## What remains outside that cut

**Registered response address and epoch.** ram_addr and ram_epoch still capture on actual stage_read_req; ram_valid still follows request acceptance and immediate cancellation. Their full 32-bit address and epoch equality checks remain live on the response edge. A slow ram_addr→address-equality→byte/state/error enable route would remain possible. Neither A nor B has ram_addr as a launch register among its fifty reported worst paths; that is not a census of all endpoints. The public stage_rsp_addr and stage_req/stage_rsp epochs remain unchanged. The retained original stale-response assertion still checks ram_addr against the live original fetch_address; simulation also checks cached expectation equals that expression on an owned response. These checks are not timing exceptions.

**Request address and bounds.** At [candidate lines270–274](../../fpga/experiments/cu66-v109-fetch/br88_packet_ingress_sync_v91h.sv#L270), fetch_address still feeds stage_read_req's size/MAX_PACKET_BYTES comparisons, RAM addressing and the FETCH_REQ out-of-bounds failure branch. The new response register cannot shorten this earlier request cone by construction. B's actual worst route passes through stage_read_addr carry cells, then stage_read_req comparator/control cells, then ingress error CE; its fourth ingress path reaches a RAM port enable at −1.368 ns. Those are concrete reasons to inspect the request cone if the adaptive result remains negative. The RAM primitive's ENBWREN endpoint name is a port-enable name and does not itself establish a new write transaction.

**Continuation and last-byte control.** fetch_return is captured by begin_fetch and still loads `state<=fetch_return` on the last successful response at [candidate lines457–462](../../fpga/experiments/cu66-v109-fetch/br88_packet_ingress_sync_v91h.sv#L457). Its value, last-byte comparison and kind-specific descriptor/replay/RAW completion controls remain. No continuation register or error-code timing changes in the fetch candidate.

B's launch register is fetch_return[2], but the RTL fetch_address expression does not directly read fetch_return. The implemented path demonstrates a dependency through optimized shared control/address logic; it does not prove that a particular source-level fetch_return expression is an address operand. B's three −1.737-ns error CE paths traverse request-named comparator cells. At source level, FETCH_REQ bounds failures and FETCH_WAIT response ownership failures can both call fail_packet(4). The cached response comparison changes only the latter address operand. It must not be presented as a demonstrated removal of B's entire fetch_return→error CE path. Cell-to-expression attribution beyond these source connections would require the adaptive netlist and route, rather than interpreting optimized cell names alone.

The ingress error/state priority also retains current start/reset/abort, active-context error/done, malformed header/descriptor semantics and the public error values. The new private register never delays any of those fences.

## Existing-edge follow-ups if the adaptive route remains negative

Select a follow-up from its actual new routed path, with a separate reversible edit and fresh focused and canonical proof. No following item has been implemented or measured here.

1. **Prepare request address and bounds before FETCH_REQ.** begin_fetch already provides the first index, kind, base and continuation one edge before the first request. Each successful nonfinal FETCH_WAIT already provides the next index one edge before the next request. Those edges can prepare an owned next-request address and its size/MAX bounds without changing request acceptance. Handle the discontinuities explicitly: header index41→42 jumps to owned size_bytes−4; descriptor index5→6 jumps to owned base+length−1; other bytes advance with exact modulo-32 arithmetic. Precompute trailer and descriptor-end operands on earlier owned preparation edges when useful. Keep current cancellation, context error/done and epoch fences live at the request edge. Preserve public stage_read_addr even in inactive/invalid cycles by retaining its original view, and assert the prepared address and bounds equal the full original expressions whenever consumed. Full-width wrapped and malformed addresses remain part of the oracle; narrowing to the physical RAM index is not equivalent.
2. **Prepare byte and completion decode with the accepted request.** If the remaining route is fetch_index→byte CE or last-byte/continuation control, capture a 46-bit one-hot byte selector and the full original last-byte predicate alongside the request. Decode all six index bits, retain out-of-range behavior and preserve fetched_word's current-byte forwarding. Retain live response address/epoch validation and immediate cancellation before enabling any public state or byte store. A one-hot payload selector is a separate timing hypothesis; it must not bypass ownership checks or silently change buffer/high-water and error timing.
3. **Narrow continuation decoding on an existing preparation edge.** If the new routed source remains fetch_return, consider co-registering its required decoded continuation terms in begin_fetch, or its last-byte ownership qualifier at the existing request edge. The response still changes state on the original edge. First establish the actual cone: B alone does not justify replacing arbitrary state/error enables or adding a control pipeline. Merely copying fetch_return into another equivalent register can be merged by synthesis and provides no measured benefit.

Do not remove the ram_addr comparison because the internal RAM normally echoes its own request: the stale-address rejection contract is intentional and remains tested. Do not narrow address/epoch fields, delay public error/reset/counters, mark the cone false/multicycle, or add a clock period exception. Each follow-up needs the same header/trailer/descriptor boundary, full-width wrap, replay/RAW, held metadata/output, live external context and request/response cancellation/retry checks.

## Portable source export check

[export-check.json](../../experiments/python-gamebub-v109/export-check.json) records a clean source-only export of initial A's preflight into `/home/lori/gamebub-build/cu66-v69/v109-export-check-20261108T115744978132Z`. All eighteen source hashes, seventeen-file RTL order, table include directories and exact build/report/XDC recipe hashes match. Plain `/usr/bin/tclsh` evaluated the generated inputs.tcl with build set to that new directory and resolved every source/include/constraint path locally in fresh-RTL mode. The export totals 608,433 bytes of small text files. No Vivado process, checkpoint, bitstream, hardware access or native timing qualification was performed. This checks initial A's source export, not the pending fault-plus-fetch adaptive result.

# V116 C mapped record banks and final routed cause

**C completed routing but failed 125 MHz setup.** The [terminal receipt](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/receipt.json) records exit 0, `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`, and `component_internal_target_pass=false`: WNS **−1.847 ns**, TNS **−7365.672 ns**, 16,725/99,007 setup endpoints failing. Hold WNS is +0.092 ns with zero failures; pulse margin is +2.750 ns with zero failures. All 74,357 routable nets are routed, with zero routing errors. Report availability was not treated as runner completion; these are the terminal receipt values. The intermediate route-log −1.851 ns is superseded.

C source remains `1ac70499489acbdb00e682696a5783cf178c3e703e3b16d2138f275f7de59839`. This analysis used existing textual reports only; it launched no Vivado instance or heavy job and changed no pinned source, runner or receipt.

## Actual mapped C banks

Both banks survived synthesis **and routing**: 64 record FDREs, four byte-count FDREs and 44 position FDREs, plus the bank-selector and seen FDREs. Constant byte bit zero and high position bits reduce the nominal 134 payload bits to **112 mapped payload FFs plus two view FFs**.

The routed control sets retain the same three groups per bank:

| Payload FFs per bank | Reported set/reset net |
| ---: | --- |
| 34 | None |
| 16 | `pending_storage[b].record_payload[b][31]_i_1_n_0` |
| 6 | `pending_storage[b].position_payload[b][21]_i_1_n_0` |

Bank 0's CE is `record_view_bank_reg_n_0`; bank 1's CE is `pending_storage[1].position_payload[1][15]_i_1_n_0`, whose mapped driver is a LUT1 with inverter INIT `2'h1`. The four format-reset drivers are LUT5s. Thus **44/112 payload FFs retain format-derived reset control**, while 68 have no reported set/reset net. The local bank-enable structure survived, but source-level unreset storage must not be described as all physical R pins tied off. These textual reports name controls and drivers; they do not enumerate every driver input pin.

## Final routed path and reported families

The [worst routed path](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-setup-paths.rpt) is scratch `read_address_reg[2]_rep__0/C` → `busy_owned_reg/D`, **9.794 ns** data: 2.407 ns logic and **7.387 ns routing (75.424%)**, nine levels including one CARRY4 and one MUXF7. The initial read-address net has 73 loads. Mapped selection/format logic feeds `ac_bank_invalid2`, then error/state/busy control.

This matches the source's [offset-selected cache word and position, followed by AC validation](../../fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv#L380), consumed in [AC_EXTRACT](../../fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv#L947). Invalid selected records set error, revoke sealing and write FAILED/`busy_owned=0`; valid records write the head tuple and advance to AC_CHECK. The [same-edge busy/state equality assertion](../../fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv#L1106) remains mandatory. Delaying or omitting busy's error transition would change ownership semantics.

The second path is cursor payload `[2][27]` → `output_index[2]/R`, −1.627 ns, nine levels and 77.158% routing. The report's 50 paths group as follows; these counts describe this capped report, not all failing endpoints:

| Destination family | Paths | Worst slack | Routing fraction on that family's worst path |
| --- | ---: | ---: | ---: |
| Scratch busy/error/head write, selected AC validation | 5 | −1.847 ns | 75.424% |
| Scratch output-index reset/enable, cursor/frontier | 3 | −1.627 ns | 77.158% |
| Scratch FSM state | 5 | −1.572 ns | 75.021% |
| Admission q-index reset, qbuffer header validation | 32 | −1.555 ns | 60.365% |
| Admission active-cell write | 2 | −1.496 ns | 80.167% |
| Scratch transfer-data enable | 3 | −1.415 ns | 74.568% |

No record-bank or view-register endpoint appears in these 50 paths. The worst reported cone therefore moved away from B's pending-record endpoint; this does not prove every C bank path has positive slack. A's actual worst was active epoch through cancel/dense-valid into producer metadata CE at −2.219 ns; B's was raw mode through record formatting/validation into pending-record R at −2.238 ns. C improves the composition's WNS by 0.391 ns over B, but global mapping/routing also changes, so this is not an isolated-cell delay attribution. Setup remains negative.

## Synthesis evidence is separate

Before placement, the synthesis worst was admission `qbuffer[9][6]` → `q_index[1]_rep/R`, −2.409 ns, 14 levels including five CARRY4. It did **not** predict the final worst path. The completed synthesis register/control reports already showed the same 112+2 FF inventory and three control groups per bank; routing retained them.

## Next source cut, outside V116's exhausted budget

The next setup candidate should separate **selected AC record acquisition from validation/state retirement**, directly addressing the actual read-address → selection → `ac_bank_invalid` → busy/error/head cone. Try to capture a complete owned word/position tuple on the existing AC_FETCH hit edge and matching READ_WAIT fill edge, then validate that registered tuple at AC_EXTRACT. Include exact same-edge cache-fill forwarding and full epoch/address/segment/band/cursor/head ownership; assert tuple equality with the old selected word/position at every consumption. Preserve arbitrary offsets, full-width corruption/domain checks, original main-branch error priority, immediate reset/abort masks and matching physical-debt retirement. If no coherent existing-edge capture is possible, a declared extra validation edge requires a new schedule contract and proof; it cannot be hidden in a delayed busy flag.

This cut alone cannot promise closure. The independent 32-path admission family points at [Q_CHECK's header length expression and validation priority](../../fpga/experiments/cu66-v116-admission/cs88_admission_v91i2a.sv#L554), including `32'({qbuffer[8],qbuffer[9]})+16!=qmap_bytes` before constant q-index initialization. A later independent candidate can prepare stable header predicates on existing predecessor edges, retaining full 32-bit comparisons and CRC-first/error priority. Do not narrow q-index, waive paths, invent multicycle exceptions or reroute unchanged inputs. All four initial native measurements are consumed; no additional V116 trial is proposed.

Cycle latency is separate: the measured row-fast post-final-input interval still needs 166,450 cycles saved. The [II=1 inverse plus two-owner reconstruction co-design](latency-next.md) addresses that schedule bottleneck; neither C's representation nor a selected-read timing cut supplies those cycle savings. Fresh functional, full/peer/LIVE and newly authorized routed evidence are required for any V117 implementation.

## Retained evidence

All links below point to reports archived in the repository; hashes match the terminal receipt's retained artifacts.

| Report | SHA256 |
| --- | --- |
| [Routed timing summary](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-timing-summary.rpt) | `a83f9a79418df21325b505c63114874cf57ced141cf3802e52f428bb81116755` |
| [Routed setup paths](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-setup-paths.rpt) | `4a879803a5b9172816532dcf91377d55e221a34d4992b6ebd10cd05c4fb82d7a` |
| [Routed control sets](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-control-sets.rpt) | `28e901933874695b81e3af09347dcba492ade80383d2b2d74765ebbd96a6c96d` |
| [Routed register inventory](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/route-local-predicates.tsv) | `0ccb95c65203d4d6009743d24c8ec3e1c020c051d130a8b7ebafeffb9392a7a8` |
| [Synthesis control sets](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/synth-control-sets.rpt) | `07895d0b29453259213056262db44a3b2e2e6cf8597514cceca6f50bdcda44e4` |
| [Synthesis register inventory](../../experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/reports/synth-local-predicates.tsv) | `f72ee7e255ccfc5222db283bc1a876b4220133c2048defe888f22d5a64458b28` |

Terminal receipt SHA256: `0538b8b2c533638851923ba2508cb51d0f30c25c8607f6961fe038e6258b4ffc`.

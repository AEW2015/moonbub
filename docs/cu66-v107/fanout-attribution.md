# V107 retained PAYLOAD routed fanout attribution

The read-only routed query shows that the three net names do **not** identify their consumers. The largest reset fanout predominantly reaches child telemetry; the net named under the coefficient boundary predominantly reaches reconstruction. This is exact physical pin attribution, not proof that any reset is safe to remove.

The [actual receipt](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/receipt.json) records exit 0 in 23.507 seconds. [Grouped summary](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/summary.json) and [complete evidence index](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/evidence-index.json) retain exact load/driver pin CSVs, groups, reports, Tcl, source snapshots and hashes. No RTL, test, checkpoint, clock or exception changed; no ninth source was activated.

## Exact checkpoint and query

Parent is the retained [PAYLOAD native receipt](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/receipt.json), whose route completed with setup WNS −2.735 ns and positive hold slack. Its external `route.dcp` SHA-256 is `3927616b0e3305e1ee9c665037d4b889251259ad99fb09061fc0c2435d2b39fc`. That hash matched **before and after** this query, as did the parent receipt hash. Parent input-manifest and all 18 source-snapshot hashes are independently checked against the parent receipt; this is the selected PAYLOAD origin, not the concurrently running THRESHOLD candidate.

The checkpoint, existing Vivado 2026.1 tools and legitimate license were mounted read-only. The query asserts `xc7a100tcsg324-1`, exactly one existing 10 ns clock and two maximum threads. Container limits were 8 GiB memory/no extra swap and two CPUs; tool time was bounded to 180 seconds, with available-memory/PSI launch and stop gates. Only `open_checkpoint`, object/property queries and reports ran: no synthesis, optimization, placement, routing, new constraints or checkpoint write.

Each target matches exactly one existing net. `get_pins -leaf -of_objects` collects its actual primitive pins, partitioned by `DIRECTION`. Every pin has one concrete primitive cell. Full CSV rows include net, direction, pin, primitive reference pin, cell, primitive type, actual parent hierarchy, LOC and BEL. Grouping uses those actual parent/type/pin fields; register-stem grouping only replaces numeric indices with `[]` and does not rename hierarchy or infer RTL equivalence.

| Existing net | Exact load pins | Slice SR pins | Other primitive loads | Worst routed setup through net | Worst reported hold through net |
|---|---:|---:|---:|---:|---:|
| `coefficients/child/scratch/cancelled` | 7,141 | 7,128 FDRE/R | 13 LUT inputs | −1.340 ns | +1.263 ns |
| `transform/inverse/reset_0` | 2,354 | 2,249 FDRE/R | 62 DSP reset pins, 43 LUT inputs | −1.180 ns | +1.907 ns |
| `coefficient_boundary/running14_out` | 2,242 | 2,217 FDRE/R + 1 FDSE/S | 24 LUT inputs | −1.753 ns | +1.129 ns |

All load totals exactly match the retained original `route-high-fanout.rpt`; each target has one actual LUT output driver. Load **pins** are counted: the second net has 2,308 unique load cells because a DSP can contribute several reset pins. The setup/hold values above are from fresh reports through the unchanged routed nets; setup agrees with the retained high-fanout report. They are not all direct-reset recovery/removal endpoints. Paths can continue through combinational loads into other control endpoints.

## Actual drivers and consumers

**7,141-load net:** driver `coefficients/child/scratch/count_cycles[63]_i_1/O`, LUT3, `SLICE_X48Y125 / SLICEL.D6LUT`. Its 7,128 reset loads are all at actual parent `coefficients/child`, not inside the scratch primitive hierarchy. Another eight LUT inputs are under `coefficients/child/packet_decoder/synchronous.ingress`; five are under `coefficients/child/scratch`.

The exact child reset FF list separates **7,125 named telemetry data FFs** from **three operational FFs**:

| Actual mapped register family | Reset load pins |
|---|---:|
| `count_scratch_state_reg[][]` | 1,920 |
| `count_packet_state_reg[][]` | 1,024 |
| `count_emitter_state_reg[][]` | 256 |
| Three per-band timestamp arrays: `ts_band_end`, `ts_first_coef_band`, `ts_last_coef_band` | 768 |
| 49 scalar 64-bit count/timestamp fields | 3,136 |
| Seven high-water fields: stage-buffer 6, assembly 4, cache 3, head 2, owned-lines 2, tile-owned 2, tile-ready 2 | 21 |
| **Telemetry subtotal** | **7,125** |
| `allocation_reg`, `done_reg`, `seal_sent_reg` | **3** |

This table counts actual mapped bits; it does not expand declared but trimmed histogram bits. [Full load pins](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/reports/net0-pins.csv), [actual hierarchy/type/pin groups](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net0-groups.csv), and [every indexed register family](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net0-register-stems.csv) are retained. Worst setup is `transform/error_reg[1]/C` → scratch `state_reg[0]_rep__0/D`, −1.340 ns, rather than a claim that all 7,125 data-reset sinks are individually critical.

**2,354-load net:** driver `transform/inverse/out_tile[1535]_i_1/O`, LUT2, `SLICE_X73Y61 / SLICEL.D6LUT`. Of its 2,249 FDRE/R pins, **1,536 are public IDCT `out_tile`**, 318 are `even_sum`, 318 `odd_sum`, 32 public `out_id`, and 45 state/state-replica FFs. DSP reset pins are RSTA 16, RSTB 16, RSTM 15, RSTC 14, RSTP 1. The actual parent is `transform/inverse` for 2,353 loads and `transform/dequant` for one LUT input. [Exact pins](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/reports/net1-pins.csv), [groups](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net1-groups.csv), [register families](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net1-register-stems.csv). Worst setup through this net is child `running_reg/C` → IDCT `intermediate_reg[53][17]/CE`, −1.180 ns. This does not establish that the CE endpoint is a direct load of the reset net.

**2,242-load net:** driver `coefficient_boundary/out_valid_INST_0_i_2/O`, LUT3, `SLICE_X57Y103 / SLICEL.D6LUT`. Its actual parent loads are reconstruction 2,232, reconstruction/reconstruct nine, coefficient-boundary one. The 2,218 slice SR pins comprise **1,536 `reconstruction/residual` bits**, **512 `reconstruction/reference_pixels` bits**, and **170 other controls**: block/child/token ownership, coordinates, indices, mode/scale, error, state, done and discard-reference. [Exact pins](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/reports/net2-pins.csv), [groups](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net2-groups.csv), [register families](../../experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/net2-register-stems.csv). Worst setup continues from child `running_reg/C` through this net to admission `mode_store/words_reg/ENBWREN`, −1.753 ns. Do not mistake that downstream RAM enable for a direct reset load or infer from the driver hierarchy that coefficient payload is the main consumer.

## Prioritized next investigation, not an implemented reset deletion

The **telemetry data bank** is the most concrete next reset/fanout candidate. Its cell names and pin connectivity are now measured; its source semantics and readsites are separately documented in the [status inventory](status-pipeline-inventory.md). In the selected [child source](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv#L209), reset/start/outer abort clears the telemetry bank. Its telemetry block samples pre-edge running events, including the final `store_done` observation edge. The separate [operational block](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv#L318) owns allocation, seal-sent and done. Those three operational reset cells and their original cycle behavior must remain; this shared physical net must not simply be delayed or disconnected.

The 7,125 FFs are **data-reset investigation candidates, not 7,125 proven removable resets**. There are important internal reads:

- `count_cycles` supplies the timestamp timebase; it cannot become an uninitialized free-running feedback value after packet clear.
- First-event timestamps compare their old value with zero; last-event timestamps and high-water fields read existing data to choose updates.
- Each counter reads its own prior value for increments, and histograms can update the same bin on consecutive cycles.
- Assertions consume totals, and focused public comparisons include every counter/timestamp/debug value even outside valid data cycles. There is no existing relaxed “eventual status” contract.

The reviewed source readsites found no synthesized datapath/ownership decision based on these 7,125 telemetry data fields; their internal dependencies above remain part of the telemetry behavior, and the original assertions and public tests still consume them. This is a source consumer review tied to exact mapped register names and snapshots, not a netlist-to-RTL equivalence proof or proof that all resets can be removed.

A possible separate prototype would leave counter payload FFs without global reset while resetting **local per-counter/bin valid or epoch controls** and forcing the existing public observation to zero immediately when unowned. Every internal feedback read must use the same effective initialized value: on the first increment after clear use zero plus the event, on first high-water update use zero as the baseline, and on first timestamp capture preserve the original event/time definition. Output masking alone is wrong if stale private data still feeds the next increment, maximum or first-event test. Epoch reuse/wrap and reset/start/abort priority need explicit treatment; local validity also creates real logic/fanout costs requiring measurement.

Any such proof must preserve per-child fresh ownership, reset/abort/retry, accepted-start versus old fault ordering, timestamp `count_cycles+1`, consecutive same-bin updates, 64-bit wrap, final output/store-done accounting, and physically matched ACK/discard events. The parent stage counters deliberately survive internally generated ingress cancel, so their clear generation must remain different from ingress-local counters. A data-valid reset scheme must not flush physical response ownership. No RTL for this scheme is added here, and no timing/resource gain is assumed.

Lazy reset alone does **not** infer BRAM while every histogram bin remains a parallel live output. A future versioned snapshot/read-port API could permit RAM-backed histogram banks with per-bin valid/generation, same-bin consecutive-update forwarding and freeze or ping-pong ownership for a coherent snapshot that includes the last event. A few microseconds of diagnostic readout latency could be allowed by that new API without stalling the datapath. Port/update collisions, capture-versus-update arbitration, epoch/wrap and physical mapping must be analyzed and measured before claiming a resource gain. This is unimplemented and does not imply an automatic saving of 7,125 FFs. Current live outputs remain cycle exact.

The IDCT sum registers and reconstruction's private residual/reference buffers are separate potential overwrite-before-use investigations. This load query alone proves neither their first-write coverage nor safe public reset behavior. IDCT `out_tile`/`out_id` are public outputs with exact reset/invalid-cycle checks and cannot be treated as hidden payload. State, ownership, error, valid and publication controls retain required reset semantics unless a separately qualified architecture changes them.

An alternative **new versioned tagged snapshot API** could permit delayed/serialized host observation, as proposed in the status inventory. That is unimplemented and distinct from preserving the current immediate public-zero contract. Adding an output snapshot alone does not remove existing data reset/CE fanout. No operational status is blindly pipelined.

## Audit, warnings and limits

The query retained the OOC `HD.CLK_SRC` warning; no parent clock-buffer location was guessed. It asserts the existing single clock/part but adds no board I/O constraints. The selected parent still fails setup, and positive hold on these sampled paths does not qualify reset recovery/removal, board clocks, all decoder timing or hardware operation. No source change, full canonical rerun or new native candidate follows automatically from this attribution.

Raw receipt SHA-256: `5e9a950e1ec7356a4b1e25cfff94b9418997bdc6cdcb36bcf9a0f4214106b25e`. Reproduce the portable audit/grouping without Vivado or the external checkpoint:

```sh
python3 scripts/cu66-v107/fanout_attribution_audit.py
# Export the evidence area; use its retained audit script:
python3 /export/fanout-attribution/20261108T075501402480Z/audit_native.py --area /export/fanout-attribution
```

The audit verifies all raw retained hashes, parent manifest/source bindings, unchanged DCP/receipt hashes, settings, exact drivers/load totals, primitive pin classes and the above telemetry/control split. Its result is `PASS_EXACT_MAPPED_PIN_ATTRIBUTION`. A new query using `scripts/cu66-v107/fanout_attribution.py` requires a scheduled heavy-job slot. External DCP bytes are indexed by hash/path only; all small reports, source snapshots and actual load lists are portable.

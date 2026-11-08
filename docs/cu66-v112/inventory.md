# V112 local-control baseline inventory

Read-only source and report audit prepared for the V112 local-control experiment. It creates no RTL, simulation, native timing, parent integration, or hardware result. The compact source and metric pins are in [`control-baseline.json`](../../experiments/python-gamebub-v112/inventory/control-baseline.json).

## Frozen control

The control is the V110 Count-domain composition, `cs88_pipeline_v91k`, using the 18-file source set frozen in `experiments/python-gamebub-v110/count-domain-native/20261108T172431599061Z/inputs.json`. V111 independently snapshots and reuses that set for its fresh 8 ns Count diagnostic; see `docs/cu66-v111/count-125-audit.md` and `experiments/python-gamebub-v111/audit/count-125-final.json`. The paths are source aliases resolved to pinned origins, so the snapshot/origin mapping in the JSON is part of the control identity. V110's focused context/ingress proof and later complete canonical composition are described in `docs/cu66-v110/count-domain.md` and `experiments/python-gamebub-v110/canonical-count-domain/combined/results.json`.

This is a component OOC control. It is not the board `moonshine_top` parent. The Count source has no production-parent wiring to the actual SDRAM controller, QSPI ingress, LCD scanout, or full board I/O timing. Historical JPEG resources and Count OOC resources cannot be added or called device allocation; `docs/cu66-v111/control-contract.md` inventories why replacement/sharing and ports remain unresolved.

## Measured critical cones and broad controls

At 100 MHz / 10 ns, the V110 Count route has WNS −1.022 ns, TNS −1125.069 ns, and 4,620 setup failures. Its worst routed cone is synchronous ingress `fetch_bytes_reg[23][0]` to `counts_reg[1][5]/CE`: 10.769 ns, 15 logic levels, 68.576% routing. This is the actual 100 MHz control path, not an extrapolation from another candidate. See `docs/cu66-v110/count-domain-native-final-audit.md` and `experiments/python-gamebub-v110/count-domain-native/20261108T172431599061Z/reports/route-setup-paths.rpt`.

V111 freshly routed the unchanged Count source at 125 MHz / 8 ns. It failed with WNS −3.264 ns, TNS −40607.203 ns, 34,864 setup failures, and worst path `scratch/read_segment_reg[1]` to `scratch/busy_owned_reg/D` (11.211 ns, 15 levels). It did not rerun 100 MHz. This points to scratch read-segment/ownership control at the stricter clock and does not erase the separate 100 MHz ingress cone. See `docs/cu66-v111/count-125-audit.md` and `experiments/python-gamebub-v111/native/20261108T183002986106Z/reports/route-setup-paths.rpt`.

The V110 routed high-fanout report has `scratch/cancelled` fanout 7,148; `scratch/reset_1` 2,396; `coefficients/fault_pending_o0` 2,237; `coefficient_boundary/fault_o_reg` 1,327; `coefficient_boundary/reset_3` 1,280. `report_control_sets` records 1,229 total sets and 1,251 unused register locations in register-containing slices. These are broad control/fanout facts, not proof they cause the measured worst path. The routed cone points must govern experiment selection. See `experiments/python-gamebub-v110/count-domain-native/20261108T172431599061Z/reports/route-high-fanout.rpt` and `route-control-sets.rpt`.

## Current board clocks and CDC boundary

`fpga/rtl/moonshine_top.sv` takes 50 MHz and currently derives 200 MHz QSPI/overlay, 100 MHz core/decoder and SDRAM controller, and phase-shifted nominal 100 MHz SDRAM capture. LCD pixel clock is nominal 29.361979 MHz. There is no current 125 MHz production decoder domain. The 125 MHz in V111 is an OOC component target only; `fpga/experiments/cu66-v111-flow/clock-125.xdc` creates one 8 ns `component_clk` and explicitly supplies no board I/O delays or timing exceptions.

The board parent's existing `moonshine_bus_cdc` crosses 200 MHz SPI writes into 100 MHz core with a 64×44-bit Gray-pointer FIFO, plus a held read-address/response toggle/ack mailbox. The retained whole-parent report is `fpga/build-final/cdc.rpt`; it reports 29 CDC-3, 4 CDC-6 and 54 CDC-15 findings across existing parent domains. `fpga/scripts/timing.tcl` scopes exceptions to named first synchronizer stages/reset pins and uses bounded datapath-only max delays on held bundled-data mailboxes. This is not a V112 125-to-100 MHz decoder CDC qualification.

## Concrete V112 CDC experiment boundary

A useful source-bound experiment can use an isolated wrapper around the pinned Count RTL, with independently constrained 125 MHz decoder and 100 MHz memory-service clocks while retaining the actual 100 MHz memory/pixel domains and 200 MHz QSPI domain assumptions. Put a finite, owner-tagged command/data FIFO or stable mailbox at the decoder→memory boundary. Check Gray-pointer synchronization, reset release, bounded backpressure, accepted-request drain through abort/reset, old-generation quarantine, stale/wrong replies, retry, simultaneous enqueue/dequeue and clock phase drift while memory and scanout continue running.

Use generated clocks tied to the chosen PLL/VCO configuration and preserve the actual clock relationship. Constrain the two domains and report CDC plus timing; exceptions, if required, should cover only synchronizer first stages and explicit Gray/bundled-data paths. Do not add broad asynchronous clock groups, false-path functional logic, multicycle paths, or relaxed targets. Report the 125 MHz decoder and 100 MHz service paths separately.

Without the parent integrating a 125 MHz clock output and the new owned memory boundary, this experiment can establish protocol behavior and an isolated dual-clock CDC/timing result only. It cannot claim that the board uses 125 MHz, that complete-parent CDC/resource/timing is clean, that board I/O is qualified, or that the hardware meets a frame-rate or latency target. Keep full-parent integration and board timing as open gates.

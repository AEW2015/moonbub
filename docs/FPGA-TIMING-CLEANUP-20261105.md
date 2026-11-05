# FPGA timing cleanup — initial checkpoint

This initial three-candidate checkpoint is historical. See [the current status](FPGA-TIMING-CLEANUP-STATUS-20261105.md) for later source and routed results.

The goal is positive actual-board routed setup, hold and pulse timing at the original clocks and I/O budgets. Installed v30/build50 is unchanged. No hardware programming or streaming is part of this development run.

Three fresh source-frozen candidates preserve the previous failed route and all sealed experiments:

| Candidate under `fpga/candidates/` | Change | Current evidence |
|---|---|---|
| `cp23-timing-cleanup-20261105` | Qualified address-strength arithmetic and registered child cancellation in actual CPL1 board | Full native model and route running; post-placement setup still negative |
| `cp23-timing-dispatch-20261105` | Register the accepted SDRAM request before row lookup/command selection | Controller unit tests and accepted-burst cancellation pass; full model and route running |
| `cp23-timing-header-20261105` | Split the four-component HC header-size calculation into registered validation phases | 34-job HUD regression and six new phase cancellation/reset/foreign-abort cases pass; full model and route running |

The controller change adds one cycle per accepted BL8 transaction. It retains the entire request until completion, drops READY during dispatch, and does not replace an accepted request with refresh work. Actual pad-branch units cover randomized masked writes/refresh, poisoned request inputs after acceptance, line readback, scanout priority, discard and physical drain. The native composite abort test completes eight physical writes and releases 16 cycles after cancellation.

The header change preserves modulo-34 arithmetic, individual component bounds, failure priority and the wire format. Inputs remain stalled through both new phases. Exact target tests cover cancellation, reset and foreign-owner abort in each new phase; the private candidate tag remains cleared on failure.

Read-only constrained synthesis for the dispatch candidate reports controller address-to-state slack +5.480 ns and HUD SHA block-enable slack +1.312 ns. Its global worst path is HC size validation at −1.355 ns. These are synthesized estimates, not routed results, and do not establish timing closure. The SHA engine was not modified.

Use `fpga/prepare_timing_cleanup.py`, `prepare_timing_dispatch.py`, `prepare_timing_header.py` to reproduce fresh candidate construction from the preserved parents. Each refuses an existing destination. `run_timing_cleanup.py` snapshots the selected board inputs into a unique evidence directory and runs either implementation or the actual-board digital model. `report_cleanup_result.py` binds the actual copied implementation inputs and fails closed unless all setup/hold/pulse endpoint counts are zero, slacks are positive and all routable nets route without errors. The exact commands and logs remain in each candidate’s evidence directory.

Final routed gates, source/asset manifests, full native/CRC checks, DRC coverage and any programming image are pending. No candidate is currently advertised as hardware-ready or as verified 30 unique displayed fps.

# V115 final native component-route audit

Independent read-only audit of the two final native receipts, source snapshots, launch cards, route reports, and retained artifact hashes. The machine-readable ledger is [final-native-terminal.json](../../experiments/python-gamebub-v115/audit/final-native-terminal.json). No native rerun or checkpoint inspection was performed.

| Target | Routed result | Setup failures | Hold failures | Pulse failures | Routing errors | Top level area |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 125 MHz / 8 ns | WNS −2.974 ns; TNS −16,389.996 ns | 24,606 / 98,053 | 0 / 98,053 | 0 / 41,792 | 0 | 36,330 LUTs; 41,098 FF; 32 RAMB36 + 12 RAMB18; 42 DSP |
| 100 MHz / 10 ns | WNS −0.263 ns; TNS −0.391 ns | 3 / 98,235 | 0 / 98,235 | 0 / 41,864 | 0 | 35,577 LUTs; 41,170 FF; 32 RAMB36 + 12 RAMB18; 42 DSP |

Neither target passes setup, so neither is eligible for a positive repeat. The 125 MHz critical path is `base_kill_authorized_reg/C` to the parser `out_value_reg[12]/R` (10.366 ns data delay). The 100 MHz critical path is admission `plane_reg[0]/C` to admission `state_reg[1]_rep__0/D` (10.098 ns). Both reports have zero unconstrained internal endpoints; each also reports 1,101 inputs and 12,884 outputs without I/O delay.

The routed top-50 sample at 125 MHz contains four normalized source/destination groups, all from `base_kill_authorized_reg/C` into parser state: 7 available, 12 cached-load-remaining, 10 output-value, and 21 reservoir endpoints. At 100 MHz it contains 20 normalized groups; the largest are transform accepted-value to coefficient-bank value (16 paths), admission plane to fetch address (8), and admission plane to word index (6 across CE/R groups). No sampled path has `owner_sequence` as source or destination. This top-50 data is a diagnostic sample, not an exhaustive path census.

The audit matched the same 18 source aliases across both runs, current source files, and saved snapshots; verified 99 retained file hashes and 72 archived/external report artifacts per run; and matched launch preflight, audit, dispatch, policy, recipe, tooling, and selected final functional proof references. Both runs used the pinned Vivado image, loaded the 8 ns / 10 ns clock before synthesis, and used 2 CPUs with 8 GiB memory and swap caps. Neither produced a bitstream, read a checkpoint, contacted hardware, or qualifies board I/O or the full parent.

**Result:** `PASS_AUDIT_COMPONENT_ROUTE_FINISHED_SETUP_SIGNOFF_OPEN`. The audit passed provenance and routing-integrity checks; setup timing remains failed at both frequencies.

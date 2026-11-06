# CU71 implementation03 routed timing triage

Native Vivado2025.2 opened the immutable routed checkpoint with two threads. No design, clocks, I/O budgets or exceptions were changed. This is implementation03, before the new tile-address/reset-light successor; it predicts candidates rather than claiming implementation05 results.

| Area | Non-reset/tile-source slack ns | Levels | Logic / route ns | Primitive breakdown |
|---|---:|---:|---:|---|
| entropy | -4.515 | 20 | 4.546 / 9.736 | CARRY4:9, LUT4:2, LUT5:4, LUT6:5 |
| dequant | -2.793 | 3 | 0.828 / 11.422 | LUT2:1, LUT4:1, LUT5:1 |
| IDCT | -6.271 | 10 | 2.629 / 9.886 | CARRY4:2, LUT3:2, LUT5:2, LUT6:3, MUXF7:1 |
| reconstruct | -3.716 | 9 | 3.001 / 10.884 | CARRY4:7, LUT3:1, LUT4:1 |
| canonical_SHA | -7.613 | 26 | 6.763 / 10.738 | CARRY4:10, LUT3:4, LUT4:3, LUT5:4, LUT6:4, MUXF7:1 |
| CSR_control | -5.259 | 17 | 3.036 / 11.594 | CARRY4:6, LUT2:1, LUT3:2, LUT4:1, LUT5:3, LUT6:4 |
| QSPI_CDC | -5.017 | 5 | 3.074 / 11.572 | LUT5:1, LUT6:4 |
| line_scanout | 0.840 | 11 | 2.375 / 6.506 | CARRY4:8, LUT4:2, LUT6:1 |

The clean worst functional global path is SHA words_reg[1][4][6]?a_reg[31]:?7.613ns,26levels and10CARRY4s. IDCT is next at?6.271ns into a rounding DSP input; its10levels are79%route, with maximum path fanout436. Exact source/endpoints and full reports are in summary.json.

Reset-inclusive views separately show entropy?8.623ns, canonical rows?8.448ns, CSR?5.484ns, QSPI bridge?5.523ns and line scanout?5.330ns, all from joint_core_reset_reg[3]. These must not be confused with the functional logic paths above.

The dequant exclusive result still ends at a coefficient R pin driven by receiver state/abort logic. The exclusion removes explicit reset-source FF starts, not functional abort/clear semantics. No R/CE/D path has been false-pathed for this report.

Scope:100paths/view,5perendpoint. Sequential component endpoints are targeted; separate external-port signoff is not claimed. Global views include physical output ports. Raw TSV unavailable logic/net properties are supplemented from the actual native full reports and worst-path property dumps. Lower-ranked alternatives were not exhaustively enumerated.

Measured candidates: stage SHA schedule/round arithmetic; inspect IDCT operand/control fanout and rounding input; separately stage command validation/BRAM response and reconstruction add/saturate paths while preserving protocol semantics. No implementation or hardware change was made.

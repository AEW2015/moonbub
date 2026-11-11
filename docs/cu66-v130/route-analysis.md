# V130 exploratory route: path analysis

The [completed route receipt](../../experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json)
and [independent report audit](../../experiments/python-gamebub-v130/spec-read/audit/native-post-route-independent.json)
retain these results. This is an out-of-context component experiment. Four
finite [full-parent cases](../../experiments/python-gamebub-v130/full-parent/results.json)
passed their recorded checks, but external invalid-cycle data-consumer
behavior remains unverified. No board, sustained 30 fps or under-10-ms hardware
claim follows.

The V130 route's worst setup slack is **−1.974 ns** at an 8.000 ns
clock, from `coefficients/admission/active_index_reg[1]/C` to
`coefficients/admission/required_cells_reg[10]/CE`. The reported 9.685 ns data
path consists of 2.531 ns logic and 7.154 ns routed delay; it has 10 logic
levels: five LUT6, three MUXF7 and two MUXF8. V129's retained worst setup was
**−1.257 ns**, from `base_kill_valid_reg/C` to
`coefficients/admission/memory_reg_0_5/ENBWREN`.

| Path grouping in reported top 50 | V129 count / worst | V130 count / worst |
| --- | ---: | ---: |
| `base_kill_valid_reg` → admission RAM `memory_reg` | 2 / −1.257 ns | 0 / not reported |
| admission `active_index_reg` → admission `required_cells_reg` | 0 / not reported | 26 / −1.974 ns |
| scratch `request_epoch_reg` → `prepared_successor_tile` | 20 / −1.076 ns | 0 / not reported |
| other paths to scratch | 23 / −0.984 ns | 8 / −1.922 ns |
| other paths to admission | 4 / −0.929 ns | 4 / −1.857 ns |
| other paths to parser | 0 / not reported | 0 / not reported |
| other paths | 1 / −1.000 ns | 12 / −1.791 ns |

For each report, this table groups the 50 `Slack (VIOLATED)` entries by their
reported source and destination strings, in the order shown above. A path is
classified by the first matching explicit source/destination pattern; remaining
scratch, admission and parser destinations are grouped next, then all others.
The reported worst is the minimum slack within that group. The table counts
reported timing paths, not unique logical nets or all failing endpoints.

The V130 top-50 report ends at **−1.747 ns**. Its separate top-200 report ends
at **−1.508 ns** and contains no path matching the V129 worst path's source and
admission-RAM destination family. This does **not** establish that the V129
path improved from −1.257 ns: a V130 path with slack between −1.508 ns and
−1.257 ns would also be outside the top-200 report. A targeted source-to-endpoint
query is needed to compare it, subject to changed or optimized netlist names.

The two implementations use the same 8 ns component recipe, but they are
independently placed and routed. Placement and routing variation, and changes
in synthesized paths, mean this comparison does not isolate the cause of the
WNS regression or quantify the candidate's causal effect on any path. It does
not prove that the original cancellation path is fixed. Both builds report
other negative paths, so removing one family alone would not establish closure.

## Targeted checkpoint query

A subsequent read-only [checkpoint comparison](../../experiments/python-gamebub-v130/spec-read/checkpoint-inspect/comparison.json)
queried the same named `base_kill_valid_reg/Q` source against 16 named admission
RAM `ENBWREN` pins in each routed design. Vivado returned timed setup paths for
all 16 V129 pairs and **no timed path** for those 16 exact pairs in V130. The
same reviewed preflight and unchanged checkpoint hashes were checked for both
queries. With no pair timed in both designs, the comparison is explicitly
`QUERY_INCOMPLETE` for a numeric slack delta. These results do not prove logical
disconnectivity, rule out renamed paths or establish global timing closure.

## Input reports and SHA-256

The following hashes identify the files read for this analysis. The V130
reports are also retained with the completed route receipt; the external
checkpoints and original build directory remain local to the build machine.

- V130 `route-setup-paths.rpt` at
  `/home/lori/gamebub-build/cu66-v69/v130-spec-read-125-20261111T024532679570Z-764e39/results/route-setup-paths.rpt`:
  `61a2dc4b7d089e2a8c49380180dbc78baf8d04e25d4e788b3c9366d0e21f6f25`.
- V130 `route-setup-extended.rpt` in the same `results` directory:
  `fd415c3b64c42d4984cf27478ac34e859a1b718bdb34248fc6bcc18ba62b40c6`.
- V130 `route-timing-summary.rpt` in the same `results` directory:
  `d56016a13b519ce39c394d361986e2a1a8ae6878109c94e91a4ab8ccfd1927cb`.
- [V129 route-setup-paths.rpt](../../experiments/python-gamebub-v129/native/20261111T003938700577Z/reports/route-setup-paths.rpt):
  `c04c095e2d6532546fcfad472a12f827e124b2e609ba14a6d411e7a4ef42eb9d`.

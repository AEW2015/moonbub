The independent final audit passes for the retained evidence and fails clock closure. Default receipt `default-native/20261108T151932078619Z/receipt.json` is `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`: WNS −1.199 ns, TNS −1582.964 ns, 6203 failing setup endpoints; hold +0.079 ns and pulse width +3.750 ns with zero failures. All 63,947 routable nets are routed with zero routing errors. This is an OOC component result, with no hardware execution, bitstream, 30 fps qualification, validated decode under 10 ms, or positive repeat.

The machine-readable [audit](../../experiments/python-gamebub-v110/audit/default-native-final.json) is `PASS_FINAL_NATIVE_RECEIPT_AUDIT_TIMING_NEGATIVE`, SHA256 `ee0e8de3e8002f2e8c17c82a96484e030d810d571586978fd30abc96c889936e`. It binds the final receipt, exact selected Runtime R5 receipt, frozen policy, preflight, contract, tooling, five focused proofs and canonical proof. Every retained artifact hash (98 files), every external report/checkpoint hash (72 files), all 18 actual source origins and both source snapshots verified. The imported frozen qualification helper passed again; all five completed Runtime trials are negative and R5 has their highest WNS. The actual `inputs.tcl` has the same 17-source read order and include directory. Current source/proof files were read, never edited.

The actual log has exactly one synthesis command:

```tcl
synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt
```

The directive is omitted, selecting the documented default behavior ([AMD UG835](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/synth_design)). There is no retiming argument. No explicit synthesis-directive informational message occurs, so `observed_synth_directive_log: null` is retained honestly; recipe/settings metadata is not promoted into a log observation. Against Runtime R5, only the operational synthesis directive changes. Other `run.tcl` changes are comments, the fresh-RTL guard and method metadata. `report.tcl` and input XDC bytes are identical. Both before/after effective XDC files have only the same 10.000 ns component clock and instance reset command: no false/multicycle paths, invented I/O delays or clock relaxation. Part, top, fresh RTL synthesis, Opt Default, Place ExtraNetDelay_high, no phys-opt, and Route Default match R5. The provenance parent DCP is unchanged and does not supply the executed fresh-RTL design.

The retained native parser independently reproduced both complete result objects. Default improves WNS by 0.455 ns and TNS by 2133.446 ns, with 2125 fewer failing setup endpoints. It remains negative. Check timing reports zero missing clocks, unconstrained internal endpoints, timing loops and multiple clocks, but 1101 inputs and 12,885 outputs lack delay constraints; board I/O and full parent timing remain open.

| Routed utilization | Runtime R5 | Default |
| --- | ---: | ---: |
| LUTs | 35,928 | 35,089 |
| FFs | 35,564 | 35,369 |
| BRAM tiles | 46.5 | 38 |
| RAMB36 / RAMB18 | 38 / 17 | 32 / 12 |
| DSP48E1 | 34 | 42 |

The DSP increase is already present at synthesis and remains through placement/route: ingress 17→17, dequant 8→8, inverse 9→17. Default inverse DSPs all report AREG/BREG/MREG=1 and PREG=0; Runtime inverse DSPs all report AREG=0/BREG=1, eight MREG=0/PREG=1 and one MREG=1/PREG=0. Both dequant implementations have AREG=1 and MREG/PREG=0 on all eight DSPs; BREG=1 rises from **2/8 in this exact R5 control** to 7/8 in Default. BREG=0 alone does not prove absence of a logical operand register, since FFs may remain outside DSPs or serve shared operands. These are observed mapping/resource changes, with no new public pipeline-latency or decode-speed claim.

The worst Default path is ingress `band_reg[0]_rep__0` to ingress `state_reg[0]/D`: 15 logic levels, five CARRY4s, 11.072 ns data delay (3.241 ns logic, 7.831 ns route, 70.728% routing). Its launch net has fanout 94 and 1.421 ns net delay. The mapped chain passes through `stage_read_addr` selection/addition, bounds/request logic and context control before state D. Optimized net aliases do not uniquely identify source equations. Runtime R5's worst path was scratch `read_segment_reg[1]` to `cursors_reg[1][29]/R` (−1.654 ns, 14 levels).

All 50 reported setup paths were counted. Runtime launches 40/50 from scratch read_segment and has 39/50 cursor-reset destinations. Default launches 36/50 from ingress band, 12/50 from scratch read_segment, one from context memory and one from transform fault_pending. This establishes a shift in the measured critical-path family; scratch cursor reset still appears. Top-50 samples do not establish exclusive occupancy or a single universal bottleneck.

The 8 GiB memory/swap ceiling, two CPUs/threads and 2400 s timeout match policy and R5. The run finished normally in 2132.492 s. Its 71 recorded samples peak at 6,748,057,600 container bytes, minimum available RAM 17,750,892,544 bytes and maximum memory PSI full avg10 0.4; no recorded pressure or timeout stop occurred. Dispatch binds the exact independent preflight audit and policy. This audit performs no new native run and authorizes no repeat.

For reproduction, stream SHA256 over the receipt's retained/external artifact maps and source origins, verify preflight/tooling/dispatch pins, invoke retained `run_native.py.parse_reports` on both report folders, and invoke frozen `native_default.qualification(control)` plus `selection(control, policy)` read-only. DSP counts come from every TSV row at synthesis/place/route; path counts use all 50 Source/Destination/Slack entries. Full rows, hashes and computed groups are retained in the audit JSON.

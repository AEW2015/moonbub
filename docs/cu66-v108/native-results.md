# V108 native results

All eight native jobs completed routing at the unchanged 10.000 ns clock on
`xc7a100tcsg324-1`, with zero routing errors and positive hold/pulse slack.
**Every route still fails setup timing. No result qualifies 100 MHz.**

| Build | WNS ns | TNS ns | Failed setup endpoints |
| --- | ---: | ---: | ---: |
| m0 Default checkpoint control | -2.758 | -21,278.961 | 24,107 |
| m1 Explore placement | -2.788 | -23,398.332 | 24,747 |
| m2 ExtraNetDelay_high placement | -2.038 | -16,629.514 | 22,688 |
| m3 AltSpreadLogic_high placement | -2.667 | -25,030.396 | 26,420 |
| m4 pre-route AggressiveFanoutOpt | -2.758 | -21,278.961 | 24,107 |
| m5 AggressiveExplore routing | -2.698 | -19,829.510 | 22,737 |
| m2 unchanged-source fresh RTL repeat | -2.342 | -17,923.600 | 23,783 |
| m2 qualified outtile/capacity fresh RTL variant | -2.020 | -11,717.641 | 16,953 |

The six checkpoint trials share the exact V107 RuntimeOptimized synthesis
checkpoint. m2 is the measured strategy frontier. Its fresh RTL repeat preserved
the original source/include order and exactly reproduced the V107 synthesis
timing summary, but its final WNS was 0.304 ns worse than the checkpoint trial.
The original checkpoint result therefore does not establish repeatable closure.
m4 completed safely before routing, but reported zero optimized cells/nets and
zero timing gain; its final metrics exactly match m0.

The five-body outtile/capacity composition passed all five current functional
proofs and then ran fresh RuntimeOptimized synthesis with the selected m2
directives. Compared with the unchanged-source fresh repeat, this measured route
improves WNS by 0.322 ns, reduces absolute TNS by 34.6%, and reduces failing setup
endpoints by 28.7%. These are one-route observations; robust timing closure remains
unproven.

The composite's worst path moved to `transform/error_reg[1]` → context parser
`reservoir_reg[45]/CE`: 14 logic levels and 11.731 ns data delay, including
9.539 ns routing (81.3%). The unchanged-source repeat's worst path is scratch
`read_segment_reg[1]` → scratch `state_reg[0]_rep__0/D`: 13 levels, 12.290 ns,
including 9.262 ns routing (75.4%). Both retain the scratch `cancelled` net with
7,143 sinks, including 7,130 set/reset sinks. Local control ownership and private
payload reset/enable isolation remain measured follow-up targets.

The [path/fanout table](native-diagnosis.md) and its
[bound report records](../../experiments/python-gamebub-v108/native-diagnosis.json)
identify every actual receipt and raw report. The fresh runs used 1,106.6 seconds
(unchanged source) and 1,147.4 seconds (composite), with measured cgroup peaks
6.45/6.18 GiB, minimum measured host available RAM 13.33 GiB, and full PSI average10
always zero. Source snapshots, recipes and the read-only parent checkpoint
remained unchanged. No watchdog/resource stop occurred.

No clock relaxation, exception, guessed I/O delay or hardware operation was used.
Parent I/O/clock integration, complete-system implementation, sustained hardware
30 fps and complete validated decoding below 10 ms remain open.

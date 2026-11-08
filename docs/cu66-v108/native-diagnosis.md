# Native critical paths and control fanout

These are actual routed component reports at the unchanged 10 ns clock.
Placement estimates are not used. The complete reports and receipt hashes are
bound in [native-diagnosis.json](../../experiments/python-gamebub-v108/native-diagnosis.json).

| Trial/mode | WNS ns | Failed setup | Critical path levels | Critical source → destination | Peak fanout | Peak SR loads | Peak CE loads |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| m0/checkpoint | -2.758 | 24,107 | 17 | `coefficients/child/packet_decoder/synchronous.ingress/fetch_index_reg[2]/C` → `coefficients/child/packet_decoder/synchronous.ingress/state_reg[1]/CE` | 7,143 | 7,130 | 1,536 |
| m1/checkpoint | -2.788 | 24,747 | 12 | `reconstruction/error_reg[2]/C` → `transform/coefficient_banks[0].words[27].value_reg[0]/CE` | 7,143 | 7,130 | 1,536 |
| m2/checkpoint | -2.038 | 22,688 | 12 | `transform/error_reg[0]/C` → `transform/inverse/out_tile_reg[1506]/CE` | 7,143 | 7,130 | 1,536 |
| m2/rtl | -2.342 | 23,783 | 13 | `coefficients/child/scratch/read_segment_reg[1]/C` → `coefficients/child/scratch/state_reg[0]_rep__0/D` | 7,143 | 7,130 | 1,536 |
| m3/checkpoint | -2.667 | 26,420 | 16 | `coefficients/child/packet_decoder/synchronous.ingress/context_blocks_reg[7]/C` → `coefficients/child/scratch/assembler_reg[10]/R` | 7,143 | 7,130 | 1,536 |
| m4/checkpoint | -2.758 | 24,107 | 17 | `coefficients/child/packet_decoder/synchronous.ingress/fetch_index_reg[2]/C` → `coefficients/child/packet_decoder/synchronous.ingress/state_reg[1]/CE` | 7,143 | 7,130 | 1,536 |
| m5/checkpoint | -2.698 | 22,737 | 20 | `coefficients/child/packet_decoder/synchronous.ingress/context_blocks_reg[0]/C` → `coefficients/child/scratch/assembler_reg[105]/R` | 7,143 | 7,130 | 1,536 |
| outtile-capacity-m2/rtl | -2.020 | 16,953 | 14 | `transform/error_reg[1]/C` → `coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/reservoir_reg[45]/CE` | 7,143 | 7,130 | 1,536 |

Large set/reset and clock-enable sink counts remain candidates for later RTL
localization or payload-reset removal, subject to exact behavioral qualification.
The critical path depth also matters: directive changes alone do not remove the
underlying combinational dependency. No constraints were waived or relaxed.

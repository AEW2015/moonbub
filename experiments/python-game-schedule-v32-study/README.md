# V32 conditional block-bank schedule

This Python dependency model tests the explicit input/compute/output overlap
missing from v31. It is **not a newly simulated RTL pipeline**. Its one-bank
controls exactly reproduce all four v31 real component-frame cycle counts.

Measured v31 no-stall services are 64 cycles to load, 0/4/132 cycles to compute
zero/DC/general blocks, and 64 cycles to emit. The two- and three-bank models
reserve each bank from load start through output end, serialize each shared
stage, enforce block order, and allow different stages on independent banks.
No bank is reused while its previous result is still being emitted.

| V31 component frame | One-bank measured/model cycles | Two-bank modeled cycles | Three-bank modeled cycles |
| --- | ---: | ---: | ---: |
| 2600 / 0 | 1,455,796 | 779,044 | 712,144 |
| 2600 / 12 | 1,205,700 | 638,104 | 596,568 |
| 7200 / 0 | 1,643,988 | 876,708 | 808,188 |
| 7200 / 12 | 1,369,896 | 738,960 | 675,180 |

On the v32 control's 48-frame windows, one-bank projections average 11.78/13.71 ms,
two-bank 6.20/7.39 ms, and three-bank 5.83/6.76 ms **if 100 MHz closes**. Different
residual choices barely change these counts. A bank's logical coefficient,
prediction, intermediate and residual payload is `64*(20+8+24+24)=4,864 bits`.
Two/three banks require 1,216/1,824 payload bytes, excluding flags, DSP registers,
port replication, expanded logic and physical RAM mapping. This is not BRAM fit.

The 288 selected v32 frames supply 2,332,800 decoded coefficient blocks. All three
bank-count schedules per frame are validated. Quantizer entries are nonzero,
so zero/DC/general classifications are unchanged by dequantization.

Assumptions requiring actual RTL/memory validation: independent bank memory and
stage ports; one sample/cycle on input/output; ordered compute; classification
known during load; no external stalls; identical stage work after adding banks.
Entropy/dequantization, predictor/reference fetch, memory arbitration, color/HUD,
CRC/commit, RF/QSPI, display and a routed clock are excluded. No elapsed Python
simulation time is reported as FPGA execution time or physical FPS.

```sh
python -m unittest discover -s experiments/python-game-schedule-v32-study -v
python experiments/python-game-schedule-v32-study/verify.py
```

Eight tests cover closed-form dense/zero cases, measured sequential costs,
resource/bank exclusion, bounded malformed schedules, exact six-cohort and
48-ID packet lineage, complete four-control coverage, and storage accounting. Retained
replay re-parses accepted GM27 coefficients, reconstructs all stage schedules,
checks frame summaries, and repeats the four actual RTL controls.

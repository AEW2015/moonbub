# V42 / V023 mailbox batching hardware: receiver PASS

Two original KEY/P frames were accepted and presented with0rejects/underruns;42240HUDwords written and readback-verified. Same V023 BIT, fixtures, DYN1 and SDK; V42 ELFb7b947b1... verified. Windows final status2 receipt is pending its report. Source was reported as.47:63389, session12897668036887929759.

| Measurement | V41 scalar | V42 mailbox batch |
|---|---:|---:|
| Pair elapsed |58.043306s|35.050912s|
| Sum HUD write/readback phases |49.982510s|28.430830s|
| QSPI transaction attempts |678031 (single-register calls)|392927 (new counter)|
| Native allocation peak |92235bytes|92235bytes|
| Sampled native-allocation minimum free |16380bytes|16380bytes|

Elapsed improvement39.61%, HUD-phase improvement43.12%, transaction-attempt reduction42.05% on these two short runs. Elapsed includes source/network waiting; per-phase deltas use each receiver local clock. These are not isolated SDRAM/QSPI bandwidth or a sustained FPS acceptance result.

KEY HUD write7.094448s/readback7.132252s; P write7.097397s/readback7.106733s. Native HU CPU0.304230/0.209963s remains far above the30fps frame budget. Final held free74568/largest30208; stack-low5644rawSDKunits. No allocation failures, rejects or underruns recorded. Current pre-panel RGB querying is not available under the network-held lease; actual per-word HUD memory verification and fresh camera are separate observations.

The camera shows the same expected held scene and HUD. Lease/native endpoint stay retained; do not force release or reconfigure beneath them. Raw USB and camera remain local. Next development: true bulk HUD service/readback and native HU CPU optimization, then continuous sessions/live host encoding. This app-only test does not change the FPGA.

[Structured measurements](V42-MAILBOX-BATCH-HARDWARE-20261107.json).

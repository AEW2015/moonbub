# V41 / V023 first DYN1 network KEY/P: receiver PASS

The existing V41 app and exact V023 BIT were used; no new firmware image or FPGA rebuild was needed. A fresh power-on reset was verified, CPU HU probe passed and exact V023 was reloaded volatile-only with DONE1/USERCODE4459373b. The running Windows uploader was reported as.47:55896, session17522181616841232893, using the original key/P pair and extended first-ACK wait.

Receiver completed2accepted/2presented,0rejected/0underruns,42240HUDwords written and verified. Total scalar elapsed58.043306s. Native allocation tuple[98304,42408,92235,15360,639,0]. Sampled native-allocation free-heap minimum16380bytes (not a global lifetime minimum); final held free74624/largest30208. Stack-low5652rawSDKunits. The actual packet/decoder/HU/HUD/drain/commit/presentation checks passed; no fabricated completion acknowledgments were used.

HUD write phases12.787878/12.801608s; readback phases12.153101/12.239923s. Combined49.982510s out of58.043306s. These software-controlled intervals include CSR/QSPI/lock waits and are not isolated SDRAM throughput or decoder-only timing. This identifies scalar HUD transport/readback as the next measured optimization target. Native HU CPU0.303841/0.210627s remains an additional future latency limit.

Fresh camera shows the held expected game scene and HUD; no filters/controls changed. This is not exact full-frame pixel verification or a sustained/interactive/30fps test. Windows reports both matching status2 replies in session17522181616841232893, source.47:55896: KEY0/24758bytes and P1/ref0/18873bytes. Uploader exit0; no timeout/status3/whole-run retry. This is user-relayed host evidence; its remote JSON is not locally accessible.

The final native endpoint and maintenance lease are intentionally retained. Do not force release, repeat USB~, reload FPGA or restore another core underneath them. A normal cold boot is needed before a later image switch. Source/report data are in NETWORK-RESULT.json; raw USB and original camera image remain local.

[Structured measurements](V41-DYN1-FIRST-KEY-P-20261107.json). Raw USB and camera artifacts remain local.

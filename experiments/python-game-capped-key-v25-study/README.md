# Causal capped-key GM25/HU25 admission

Two fixed policies, zero-MV lambda0 and lambda1, run all48 retained IDs in both
native scenes. Epoch25, keys0/24, ROI8/bg16, and publication every successfully
ACKed frame are fixed. Keys disable RDO and reset HUD references independently.

Each decision creates actual HU25 bytes from original RGB565 patches using the
frozen full-patch selector and HD25. P frames use bounded HUD motion; keys have
no HUD reference. A private copied legacy selector commits only after ACK.
Source/prepared base analysis runs once. Actual bg16 base bytes compete against
`len(base)+len(HU25)+60 <= 49152`; on failure, the same analysis encodes bg32.
Every rejected fine candidate packet and paid work remain in `attempts`.
Selected packets form actual CP25 bytes and pass Receiver/JA25 validation before
any sender reference or cache state advances. Downstream P frames use the
selected decoded reference, including after any coarse fallback key.

`results.json` keeps native-compatible selected GM25 rows and descriptors plus
actual HU25, CP25, ACK descriptors and cap-attempt details. `summary` is the base
summary; `joint_summary` gives actual complete bytes, cap fit and joint quality.
Whole receiver time includes HUD validation. Base encoder clocks include one
analysis and every prepared encode attempt; fixture loads/export and HUD/bind/
receive clocks are separate. All clocks are Python host component costs.

```sh
python benchmark.py > run.log
python verify.py > verify.log
python -m unittest -v test_replay.py > tests.log 2>&1
```

Replay checks all selected complete packets and ACKs, independently decodes all
rejected fine packets, verifies quantizer maps and reference lineage, and
recomputes exact display hashes and RGB565 quality. These are offline projections;
there is no physical30fps, native ESP32/RF/QSPI, fitted FPGA or timing claim.

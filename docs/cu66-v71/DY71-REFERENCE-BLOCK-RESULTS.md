# DY71 reference wait: unchanged replay02

The second wrapper-only replay preserves every DUT/model hash, every original profiling field, and the exact public baseline logs, full canonical/HUD goldens, stage cycles and presentation times. All subdivision/cross-matrix/overlap/physical-command conservation assertions pass. No DUT, PHY, map, quota or math change was made; this is unrelated to the separate timing-only IDCT successor.

**The missing outside-pending time is previous canonical writeback serialization.** Every16.00631ms admission-blocked clock has a valid reference request, not-ready tile adapter, active same-generation previous-tile write and pending canonical writeback. Full-run identity assertions verify the adapter tile differs from the current reference tile; bounded examples show current tile1 waiting on tile0, then2 on1, etc.

| P2 completed-IDCT reference-block subdivision | ms |
|---|---:|
| Not yet offered |0|
| Request valid, admission not ready |16.00631|
| Accepted reference in flight |19.02676|
| Return held/backpressured |0|
| Return transfer edge |0.07502|
| Request acceptance edge |0.06951|
| Other/identity mismatch |0|
| **Conserved reference block** |**35.17760**|

Accepted-reference pending time19.68210ms from replay01 includes0.58032ms before IDCT became blocked. The actual outside-pending portion of this blocking bin is16.07582ms =16.00631ms admission plus0.06951ms acceptance edges; this explains the earlier15.49550ms lower bound without mixing overlapping intervals.

## Adapter and controller observations

The admission bin divides into previous-write ISSUE0.19253ms, WAIT_WORD15.74427ms and RESULT0.06951ms. There is no admission time caused by an idle adapter or another read. Accepted-reference in-flight time divides into read ISSUE0.28625ms and WAIT_WORD18.74051ms. Returns are delivered, not held. Maximum consecutive admission wait is595clocks(5.95us); in-flight609clocks(6.09us).

These adapter waits are **not** all physical DRAM busy time: the controller is IDLE5.46058ms during admission and6.21785ms during in-flight (11.77567ms across the entire reference-block bin including transfers). Orthogonal reservation observations overlap that bin7.10840ms: LCD-class6.01092ms and BG-class1.09748ms. Admission overlaps3.29720ms reservation; in-flight3.80567ms. Do not add these overlaps to the35.17760ms total or treat them as guaranteed removable delay.

P2 physical accepted commands remain99360LCD +87384BG =133224READ +53520WRITE commands, exactly the baseline. Every physical acceptance is cross-checked against the existing grouped counters. The selected adapter admits only one tile transaction until its complete result is acknowledged; the observed previous-write identity confirms this serialization, while controller sharing/handshake overhead determines how long that write remains active. The replay does not yet partition client service latency inside those intervals.

## Evidence and scope

`fpga/experiments/cu66-v71/direct-system/profiling-v001/evidence/replay02` contains `profiles.json`, `observer-schema.json`, full raw matrices, eight bounded admission examples per frame, frozen wrapper/test sources and commands. Adapter matrix columns are IDLE,write_ISSUE,write_WAIT_WORD,write_RESULT,read_ISSUE,read_WAIT_WORD,read_RESULT; row order is the seven reference bins above. Controller matrices use the exact frozen controller FSM codes recorded in the schema.

`analysis.json` independently verifies all replay01 profiling fields are identical, seven reference bins sum to the original blocking bin, every adapter/controller row conserves, overlaps stay within their bins, and physical command classes balance. The native test also retains complete KEY/P/P goldens, latency/pending conservation and all previous checks. New wrappers only read existing hierarchy signals; no per-clock text stream was added.

P2 remains45.52368ms with46.10029ms presentation interval and zero underruns. This identifies blocking/admission behavior, not a selected fix or promised16ms speedup: those previous writes still require physical service. No independent read/write buffering, reordering, new lanes, PHY/map/quota change, hardware or sustained30fps result is claimed.

| New evidence | SHA-256 |
|---|---|
| `profiles.json` | `8f0ce604043df68a70857858c9f5abd74a9d8026a73e8f3931137eed9c89fc44` |
| `analysis.json` | `8d624e494088cd8a7d6c60ded54151c4894de1f5a11111ae86f8e612e1bdc51f` |
| `frames.log` | `37ce8a30cf7fe2b456dff48b4dcfb930759f098f79d34bc7d7219e2481c39ab5` |
| `source-freeze.json` | `91da4a958f514b4543159c56a2af3a071c109c83e2a490423bf4fdcf74e943b7` |
| `tb.cpp` | `546bb17f66f46930cf0dec424d32728b92a4e619652fe3018a13bfaf63acac77` |
| `cu71_direct_system_sim.sv` | `887ac54fce7880587906b565268d91429dc4d56533bf6de170e8f1e33483e41f` |

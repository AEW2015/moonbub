# Grouped DY71 candidate handoff

The isolated 8-LCD/4-background bridge removes observed native LCD underruns under real same-bank reference-copy traffic. It preserves the nominal 2:1 accepted physical-command quota while grouping row-local work; bounded reservation grace is explicitly 18 LCD / 4 background clocks. No live PHY, map, controller, codec or base-owner source was modified.

Selected integration candidate: `../pipe-v001/sources.json` (SHA-256 `5e64f707bff1e07f5febf6110cb0fda6b55a3c26a8cdc99cfa84be727e1e9caf`). It binds the pipelined owner `825ffcd0b134a894ab21612edb4d2aafce299abb3cf15c2d29fdd13fbef9c6dc` and grouped bridge `8c73e1f3bac525e51db7777416c6a291a7e061c8e9e2ed0d23a532c9097c7a9a`. This is a native functional candidate, not a board release.

Executed gates:

- Fast/slow actual-controller component: 5,277 checks and 94 abort probes per run, all four full BL8 tile commands and masks checked.
- Contended policy/data isolation: exact 384 LCD / 192 BG physical commands in 8:4 sequences across four clients; cache hits and invalid replies uncharged. Stronger observer checks require stable held response and actual LCD plus BG progress during its 100-clock hold.
- Matched reference-copy/display: baseline 669 missing lines becomes zero; maximum Y/C page service falls 114.73/114.69→88.98/88.96 µs. ACT/PRE falls 35,913/33,914→14,566/12,572. Completed background copies fall 4,526→3,995 in the identical 1,518,173-clock active window. It is a clean-scanout tradeoff, not a general throughput win.
- Full native KEY/P/P: all canonical/HUD tags and readbacks, real LCD pixels, identity leases and lost software COMMIT-ACK recovery pass. Grouped base-owner run has zero underruns versus 2,261 in its baseline. PIPE-owner/grouped run also has zero and complete clean rasters for all three generations.

PIPE-owner/grouped transaction cycles are 2,049,238; 3,438,483; 4,552,368. Fresh presentation intervals in this small cohort are 30.73353 ms and 46.10029 ms. **30 unique clean displayed fps is not demonstrated.** Native HUD CPU service remains outside HDL time; there is no ESP32, live QSPI or network qualification here.

Relevant bindings:

- `qualification-components-v001.json`
- `qualification-fairness-v002.json`
- `comparison-reference-v001.json`
- `comparison-three-v001.json`
- `../pipe-v001/qualification-three-v001.json`

The `*_expiry` registers count timer expiry with an opponent pending, including times when the controller is busy. They are not actual idle-reservation-expiry counters. `group_reserved_idle` is properly IDLE/hold-qualified. No frozen scheduler behavior or counter meaning was silently changed.

Remaining gates are complete-board fit and routed setup/hold, bundled CDC, separately reviewed DY71 CSR/ESP32 adapter, coordinated host contract, and controlled physical tests. The profile identity is magic/USERID/USR_ACCESS `0x44593731`, ABI `0x00010000`, local capabilities `0x0f`, tile-major64 canonical layout and cache-context display slots. Existing v35 compatibility is not advertised. The frozen 32-bit DMA cookie still requires a reviewed long-duration policy or wider successor before release.

Before another scheduler change, profile direct-DMA completion gaps and queued BG read/write bank identity during reserved idle. The second PIPE P spends approximately 8.017 ms in IDLE-qualified reservations while other physical work is pending, but removing grace indiscriminately can recreate row switching. No additional quota, grace, PHY or map tuning is selected by this handoff.

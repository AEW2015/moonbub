# BRAM codec/painter plus explicit RGB BL8: old-map control

Run: `burst-oldmap01`, pinned by `sources-burst.json` and the run's copied
inputs/source freeze. Separate result: `burst-oldmap01-cadence.json`.

The bounded control test and chronological KEY0/P1 full replay exit zero.
Each complete canonical plane set, HUD functional readback and portrait RGB565
buffer matches the independent native scoreboard. The P frame retries its
deliberately lost irreversible software COMMIT ACK without another commit.

| Transaction | Total modeled clocks | Painter clocks | Physical write beats | Read bursts | ACT / PRE | LCD underruns during transaction |
|---|---:|---:|---:|---:|---:|---:|
| KEY0 | 7,759,549 | 5,388,015 | 1,071,360 | 37,920 | 108,917 /110,647 | 0 |
| P1, concurrent scanout | 15,795,607 | 8,812,553 | 1,071,360 | 489,303 | 198,127 /179,234 | 1,316 |

These correspond to77.59549ms and157.95607ms at the **modeled**100MHz memory
clock. Final drain/scanout accounting contains1,317underruns. Functional
reconstruction/readback passes, while clean scanout cadence still fails.
No achieved FPGA clock, target timing/fit or physical playback is established.

The explicit RGB port performs48,000BL8 operations instead of384,000scalar
maskedBL8 operations. Per frame,384,000RGB physical beats +518,400canonical
beats +168,960HUD beats reconcile to1,071,360. Masked beats remain bus work;
they are not useful pixel-byte counts. HUD's scalar interface is unchanged.

The earlier old-storage/scalar-RGB baseline (`full-pin02`) required13,609,626
KEY clocks and32,112,310P clocks. This is a combined source-version comparison:
BRAM storage, painter pipelining, the RGB transaction interface and background
arbitration changed. It is not proof that one isolated edit caused all timing
differences. Raw underrun counts span different run durations and are not a
normalized quality metric; both fail the zero-normal-load-underrun gate.

The favorable cross-bank map case and the unfavorable canonical2/front1 case
must be compared separately. Matched three-frame old/new-map runs are intended
to exercise both RGB directions and the next canonical bank. Two successful
stored frames do not establish30unique clean presentations/s or validated
decoding under10ms. Native HUD CPU service, live QSPI and transport remain
outside these modeled timings.

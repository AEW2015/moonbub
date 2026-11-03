# Modeled transport-to-display latency sensitivity

This isolated experiment instruments the `network-rtl-study` bench: `decode_ready_cycle` marks the core's `pending` state after JPEG decode and memory drain. The capture/complete/commit/presentation timestamps retain their prior meanings. No production files change. See the neighboring study's README for the modeled full-frame reassembly, experimental credit QSPI/CDC, burst-memory and SDRAM assumptions and limitations.

## What causes the baseline maximum?

For frame ID 2, the observed capture-to-presentation time is **66.80075 ms** at assumed 8 Mbps L3 service:

| Stage | Duration |
| --- | ---: |
| Capture epoch to reference reassembly complete | 28.89000 ms |
| Complete-frame queue plus QSPI transfer to commit | 3.93106 ms |
| Commit through decode and memory drain | 19.51881 ms |
| Decode-ready to next frame-boundary publication | 14.46088 ms |

The core cannot publish until the decoder drains and a display boundary arrives; its `ready_state` also prevents starting the next upload while a prior frame is pending. The bench's pixel clock and LCD raster give a roughly 15.37 ms boundary interval. Thus missing a boundary can add nearly that much modeled latency, and queuing/upload time can include waiting for the previous frame to be published. Capture epoch denotes an already-compressed synthetic JPEG, so host capture, encoding and their CPU time are excluded.

## Measured comparisons

All runs use the same ten distinct 720×480 fixtures, 30 Hz source cadence, 0–300 µs synthetic jitter, no packet loss, and the experimental RTL and queue from the neighboring study. Each case presented all ten frames, with zero modeled queue drops, overflows or LCD underruns. All 40 presented frames matched the related C JPEG model pixel-for-pixel. Means and maxima are for these ten frames, not confidence bounds.

| Case | Hypothesis | Mean age | Maximum age |
| --- | --- | ---: | ---: |
| Baseline | 8 Mbps assumed L3, no phase shift | 60.30124 ms | 66.80075 ms |
| Optimistic phase | Same 8 Mbps trace shifted 14.25 ms relative to LCD | 61.41800 ms | 67.91751 ms |
| Guarded phase | Same trace shifted 13.50 ms relative to LCD | 62.16800 ms | 68.66751 ms |
| Faster link | Hypothetical 12 Mbps L3, baseline phase | 51.08118 ms | 56.63358 ms |

The phase trials are deliberately reported even though they fail to improve this trace. The optimistic shift came from extrapolating baseline decode-ready times as if processing moved rigidly with the source. The guarded shift was chosen after the optimistic trial missed the target boundary. They still miss a boundary because actual modeled decode/memory behavior changes with concurrent scanout. Their labels describe the trial intent, not a guarantee; no fixed phase is recommended based on these data. Frame-by-frame times and exact pixel checks are in `results/`; `results/summary.txt` includes each stage's aggregate.

The 12 Mbps result is a sensitivity experiment, not a measurement of Wi-Fi or ESP32 link capacity. It shows that lowering modeled serialization time can reduce age for this short trace. It does not specify how to achieve the rate, and excludes wireless MAC/PHY, retransmissions, contention, sender encoding, CPU, CRC time, actual QSPI timing, audio, input, target memory constraints, and hardware. A longer representative trace with real measurements is needed. Reducing per-frame bytes may yield similar link headroom, but image quality and packetization must be measured; no such encoding change is evaluated here.

## Reproduce

First run `../network-rtl-study/run.sh` and retain its `BUILD_DIR`. Set `BASE_BUILD_DIR` to that directory, set `BUILD_DIR` to a new empty directory, and run `./run.sh`. It compiles the instrumented bench, generates the new 12 Mbps trace through the actual Python MSV1 reference and host-compiled unmodified Rust receiver, then runs four RTL trials with a **400-second wall timeout each** and checks every RGB565 output against the related C model. Compilation, trace generation and pixel comparisons are outside those timeouts. Requirements are those of the neighboring study. The recorded `faster-link` packet and frame traces are retained under `results/`; the three 8 Mbps cases reuse `../network-rtl-study/results-clean/`.

The complete four-case wrapper was rerun successfully in the development container against the clean completed base build (exit 0). All four cases passed ten exact C-model comparisons each, and the means and maxima above reproduced exactly. Full generated output remains outside the repository at `/home/lori/gamebub-tools/network-latency-wrapper-v1` with the wrapper log at `/home/lori/gamebub-tools/network-latency-wrapper-v1.log`.

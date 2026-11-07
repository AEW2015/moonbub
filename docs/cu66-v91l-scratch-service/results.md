# Physical scratch measured results

All times below are cycle counters converted at an assumed 100 MHz; no hardware clock or complete-system latency claim.

| Source | Start → commit (ms) | Packet complete → commit (ms) | RGB stage (ms) | Serial start → RGB close (ms) |
|---|---:|---:|---:|---:|
| Key | 29.00464–29.00464 | 28.62253–28.62253 | 29.68636–29.69672 | 58.69100–58.70136 |
| Delta | 33.46038–33.46534 | 33.18342–33.18838 | 29.68215–29.69177 | 63.14749–63.15215 |

| Source | Scratch WRITE lines | Scratch READ lines | WRITE x16 words | READ x16 words | Highest line start |
|---|---:|---:|---:|---:|---:|
| Key | 3,938 | 3,938 | 31,504 | 31,504 | 55,200 |
| Delta | 3,091 | 3,091 | 24,728 | 24,728 | 47,104 |

1,668 directed check entries, 54 independently rejected corruptions, eight exact full base-RGB outputs and 8,200 actual RTL SHA jobs pass. This is two distinct native source images under two seeds and two memory-delay corners.

The prior control used a finite C++ scratch responder. The new result prices scratch traffic plus the added outer transaction arbiter; it is not a codec speedup comparison. Contention with the native display is still tested only in directed controls; native decode and RGB remain serial. Hardware 30 fps and complete validated decode below 10 ms remain open.

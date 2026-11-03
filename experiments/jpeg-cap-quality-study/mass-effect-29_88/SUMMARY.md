# Second-clip JPEG cap study (747/25 fps)

**Offline only:** 360 decoded frames from `mass-effect-2600.mp4` (1280×720); rendered to 720×480. Cap: 49,152 JPEG bytes.

| JPEG quality | Mean bytes | p95 bytes | Max bytes | Over-cap frames | Mean encode ms | p95 encode ms | Max encode ms |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 75 | 18150.4 | 18693.3 | 19560 | 0 (0.0%) | 1.352 | 1.615 | 10.168 |
| 80 | 20384.1 | 20941.0 | 21928 | 0 (0.0%) | 1.290 | 1.534 | 1.847 |
| 85 | 23670.6 | 24315.2 | 25547 | 0 (0.0%) | 1.318 | 1.571 | 2.036 |
| 90 | 29650.2 | 30449.3 | 32085 | 0 (0.0%) | 1.387 | 1.666 | 1.940 |

## q90 with one q80 retry

q90 fit/sent: 360; same-frame q80 retry: 0; dropped after retry: 0.
Chosen JPEG sizes: mean 29650.2 bytes, p95 30449.3, max 32085. Sequential q90-plus-conditional-q80 encode time: mean 1.387 ms, p95 1.666 ms.

The retry result is an offline size-policy calculation. Per-frame timing is measured sequentially and does not represent realtime capture or target hardware.

The source is a limited local prerecorded segment. Its resolution, compression, action content and scene distribution constrain generalization. These results do not establish image-quality acceptance, network delivery, receiver behavior or presentation.

Reproduce from the prototype root with `.venv/bin/python repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/mass-effect-29_88/measure.py`. `per-frame.csv` and `results.json` retain per-frame inputs and aggregate results.

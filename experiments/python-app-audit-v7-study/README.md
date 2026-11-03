# Application specific v7 evidence audit

`audit.py` independently recomputes summaries from the stored word decoder,
scheduler, ROI and dirty tile JSON artifacts. It does not rerun video
benchmarks. The implementation and tests use Python standard library only.

## Checks performed

- **RG01 ROI:** Recomputes the 16×16, 2-bit scale-map length (338 bytes at
  720×480), checks the declared 34-byte outer header plus CRC, confirms those
  bytes are included in each serialized packet length, and checks the exact
  map/header and packet totals. It pools RGB565 squared error by pixel area for
  active, ROI and background MSE, then compares each profile's mean packet
  bytes and pooled ROI/background MSE against `uniform16`. It reports both
  the study's per-input `uniform16` size budget and the separate 48 KiB packet
  cap. `budget_roi8mix` meeting its per-input reference size does not imply it
  fits 48 KiB. The 30 fps wire-rate calculation uses actual total packet bytes
  and is a hypothetical rate for those packets, not observed throughput.
- **Word decoder:** Checks the 72 packet and 216 plane records, recomputes mean
  old/word receive timing, validates declared source pins, and records each
  selected native PTS and frame hash. The paired decode optimization affects
  CPU time; it does not establish a packet-format or bitrate gain.
- **Scheduler:** Retains the source PTS/hashes, strict and eventual presented
  counts, diagnostic steady-window count/rate, and p95 age. Diagnostic IDs/s
  stays explicitly labeled as a model metric, not strict end-to-end FPS.
- **Dirty tile:** Recomputes per-scene packet means, equal-area pooled active
  MSE, 30 fps wire rate, and 48 KiB admission counts, and reconciles those
  against recorded summaries. It checks each record's source hash against the
  manifest's selected ID and hash, and reports repeated rendered source frames.
  Packet bytes and wire bytes are reported separately.
- **Causality:** An absent `oracle_used`, `future_frames_used`, or
  `lookahead_frames` field is an evidence gap. The audit does not treat absent
  metadata or source-code comments as proof of causality.

## Recomputed observations

The RG01 audit reconciles every map, area partition and active MSE. Pooled
`budget_roi8mix` is 0.998× the `uniform16` mean bytes, with ROI MSE 0.599× and
background MSE 1.032×. Its reference-size condition is per input. Two seeded
synthetic HUD inputs have packets above 48 KiB for `uniform16` and
`budget_roi8mix`, so those outcomes fail the distinct physical packet cap.
All ROI manifests lack the explicit oracle/future/lookahead declarations and
are marked unproven by this metadata audit. Fixed priority rectangles are
experiment inputs, not HUD detection.

The word decoder contains 72 paired packets and 216 paired coefficient planes;
mean whole receive time recomputes to 27.74 ms old and 24.81 ms word (10.57%
reduction). This is Python receiver timing, not concurrent real-time service.
The scheduler audit retains strict counts 55/49 for combat and 56/45 for the
second clip under assumed/Python receive service; diagnostic steady rates are
28/26 and 30/24 IDs/s respectively. Those ID rates are not end-to-end FPS.

Dirty tile has 48 records across two precompressed clips and two synthetic
HUD sequences. Every scene summary reconciles. Its real combat clip has 3/12
packets over 48 KiB; the second real clip has 7/12. The independent tile-key
packet is oversized in each real scene. Across all 48 records, tile mean packet
size is 39,126 bytes versus 29,611 bytes whole-intra and 16,031 bytes for the
immutable-anchor control. Repeated native rendered frames occur in the clips,
so those results do not show distinct-content 30 fps. Immediate ACK and
reported logical tile traffic do not establish transport, physical memory, or
end-to-end performance.

Run the audit and helper tests:

```sh
python3 experiments/python-app-audit-v7-study/audit.py
python3 -m unittest discover -s experiments/python-app-audit-v7-study -v
```

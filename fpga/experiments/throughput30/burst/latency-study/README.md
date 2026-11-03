# Offline latency analysis of simulated prefixes

`analyze.py` reads already verified JSONL and the fixture manifest. It checks ordered IDs, fixture hashes, timing arithmetic and the recorded pixel, burst and underrun checks. It does not rerun the decoder comparison or establish that a run passed. It snapshots complete lines in memory, ignoring an unfinished trailing line if a simulation is writing concurrently. SHA-256 and byte length identify the exact consumed prefix; retain that prefix for reproduction. Percentiles use nearest rank `ceil(p*N)`; the 30 Hz age deadline uses exact integer arithmetic and equality meets the deadline. The 100 MHz clock is fixed by these benches.

The bundled snapshots were copied from the active runs and are incomplete, with no conclusion about run completion. To reproduce:

```sh
cd fpga/experiments/throughput30/burst/latency-study
python3 analyze.py qspi-prefix.jsonl manifest.json
python3 analyze.py optimistic-bus-prefix.jsonl manifest.json
python3 -m unittest -v
```

The QSPI prefix has 106 presentations, first-to-last cadence 29.969 fps, and arrival-to-presentation p50/p95/p99/max of 29.70735/36.34650/37.27471/37.32194 ms; 26 of 106 exceeded 1/30 s. The optimistic register-bus prefix has 429 presentations, cadence 29.981 fps, and p50/p95/p99/max 28.77914/35.69757/36.30338/36.44097 ms; 87 of 429 exceeded the deadline. These have different observation lengths and are not a controlled comparison. Cadence counts intervals between presentations; it does not imply that individual arrival-to-presentation deadlines are met. Neither metric is an aggregate 60-second pass.

These are behavioral simulations with synthetic JPEGs, instantaneous complete-frame arrivals, a hypothetical one-frame queue and a functional SDRAM model. The QSPI run models ideal digital pins; the other uses an optimistic register bus. The shared-algorithm C model is not an independent decoder. No host capture/encoding, real network or ESP32, actual hardware timing, input-to-photon latency, or 60-second result is measured. See `../qspi-longrun/README.md` and `../longrun-study/README.md` for model details.

## Where the QSPI prefix spends time

`python3 breakdown.py qspi-prefix.jsonl manifest.json` reproduces `qspi-breakdown.json`. The bench timestamps arrival to service start as queue wait, service start to completion of the COMMIT register write as upload, and commit to observed presentation. These sum exactly to frame age. For the 26 deadline misses, queue wait is one cycle in 18 cases and above one cycle in eight (maximum 3.98862 ms); upload takes 1.40880–1.46160 ms. Commit-to-presentation takes 29.27192–35.87688 ms (median 33.95404 ms). Its range includes remaining decode, staging, memory arbitration and waiting for the display boundary; the QSPI trace has no pending timestamp and cannot split them. Decoder work may overlap upload, so upload is not an isolated decoder start time.

The consumer waits for `core.ready_state` before taking the one-slot queue and processes frames serially. For example, frame 3 had negligible queue wait, 1.44615 ms upload and 34.62106 ms after commit, for 36.06722 ms age. Frame 4 had 2.73389 ms queue wait, 1.46160 ms upload and 29.27192 ms after commit, for 33.46741 ms age. Those are observed decomposition values, not independent causal estimates: changing an early stage may move the frame across a display boundary.

The LCD model's 541 × 834 pixel refresh at 17.029 ns half-period is about 15.36677 ms. Presentation is restricted to frame boundaries: the prefix's intervals range from 30.73353 ms (two refreshes) to 46.10030 ms (three). A 30 Hz arrival period is 33.33333 ms, so source and refresh phases drift and age follows a sawtooth; near the boundary, a small change in readiness can shift presentation by a whole refresh. An earlier boundary alone does not prove the frame was ready at that point. The separate `../cadence-study` instrumented an optimistic-bus ten-frame trace: frame 3 was pending at cycle 10,775,746 and presented at 12,293,425, a 15.17679 ms boundary wait. It cannot establish the pending time for the QSPI prefix.

A concrete next experiment is to add pending/back-buffer-ready timestamps to a **new isolated QSPI bench**, then measure ready-to-boundary and commit-to-ready separately over a full run. That identifies whether decode/staging throughput or boundary phase is the actionable bottleneck; reducing upload alone cannot directly explain away a post-commit interval. As a scheduling experiment, evaluate a panel-supported approximately 60 Hz display timing, or source/display synchronization, with measured clock and panel constraints and long-run drift tests. The existing ten-frame `../cadence-study` hypothetical ~60 Hz simulation achieved a 29.809 ms maximum age, but used an optimistic bus and is too short to predict QSPI performance or support a hardware change. Overlapping the next frame's reception/processing with pending presentation may reduce queue delay for queued frames, but requires buffer ownership and memory-bandwidth design plus verification; it cannot by itself address the 18 misses with only one cycle of queue wait.

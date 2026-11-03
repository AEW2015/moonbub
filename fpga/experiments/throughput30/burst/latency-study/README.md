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

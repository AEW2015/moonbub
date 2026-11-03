# 1,800-frame QSPI RTL run: strict-window failure

**Outcome: FAIL.** The behavioral Verilator test eventually presented all
1,800 distinct synthetic 720×480 JPEGs, but only **1,799 were presented within
the fixed 60-second capture window**. The final frame appeared at cycle
6,002,258,520; the window ended at cycle 6,002,020,037. It was **238,483
cycles, or 2.38483 ms, late** at the modeled 100 MHz core clock. The terminal
simulation log contains the fatal deadline assertion and no PASS marker; the
runner exited nonzero and did not create a success summary.

The source rate was rational 30 Hz and the run checked 622,080,000 RGB565
pixels against a separately executed fixed-color C decoder and verified the
corresponding SDRAM words. All 1,800 frames were eventually presented, with
no modeled drops, queue overflows or LCD underruns before the final assertion.
The C decoder shares algorithms with the RTL; it is not a fully independent
JPEG implementation. The test checks actual frame IDs at LCD swaps and the
underrun counter, but does not individually compare every pixel emitted by the
LCD pins.

| Metric | Modeled result |
| --- | ---: |
| Frames within fixed 60-second window | 1,799/1,800 |
| Window frame count divided by 60 s | 29.98333 fps |
| First-to-last rate over 1,799 output intervals | 29.995089 fps |
| Arrival-to-swap age p50 / p95 / p99 / maximum | 29.711 / 36.626 / 37.240 / 37.382 ms |
| Frames older than nominal 33.333 ms at swap | 477/1,800 |
| Maximum modeled per-frame QSPI upload | 1.47125 ms |

All results are phase- and workload-dependent. The source assumed the complete
compressed JPEG was instantly available in a hypothetical one-frame queue at
each 30 Hz capture. The FPGA-side upload uses real QSPI parser/CDC RTL at a
modeled 40 MHz write clock and 16 MHz register reads, but ideal digital pins:
there is **no actual ESP32 firmware, real Wi-Fi or network serialization, CPU
scheduling, host capture/encode, physical SDRAM timing, hardware clock
qualification or end-to-end latency measurement**. The JPEG marker guard and
burst-memory controller are isolated research candidates, not production RTL.
These results do not prove hardware 30 fps or gameplay quality.

The direct-register 60-second run used the same input JPEG hashes; all 1,800
output dump hashes are identical. Presentation timestamps matched for 1,693
frames. The remaining 107 QSPI frames appeared one modeled LCD refresh later
(1,536,676 or 1,536,677 core cycles, ~15.367 ms); none appeared earlier. This
is a behavioral comparison on this workload, not a physical latency measurement.
Both runs missed the same strict final window by 2.38483 ms.

- `simulation.log`: complete 1,800-frame log with final fatal assertion.
- `verified.jsonl`: each completed frame's source and output hashes, exact
  C-model comparison count, timing and counters. The large generated pixel
  dumps were removed only after successful comparison and durable recording.
- `analysis.json`: aggregate metrics and hashes; `direct-comparison.json`:
  matched-frame comparison with the separate direct-register run.
- `fixture-manifest.json`: source frame identities, sizes and hashes;
  `source-sha256.txt` and `tool-version.txt`: simulation provenance.

The QSPI fixture manifest is byte-identical to the local direct-register run's
manifest (SHA-256
`0d7a566b5ce380d7f571da198573556f46f377ca5170f74422fbb89a3de445b8`). The
direct-register committed evidence already has a separate `verified.jsonl`;
it is not duplicated here. The QSPI JSONL is retained because its upload and
presentation timestamps differ.

Run `python3 fpga/experiments/throughput30/burst/qspi-longrun/test-analyze-results.py`
for analyzer status-classification tests. To re-analyze an intact run directory:

```sh
python3 fpga/experiments/throughput30/burst/qspi-longrun/analyze-results.py \
  /path/to/qspi-run --output /tmp/qspi-analysis.json
```

The analyzer intentionally exits nonzero for this failed run. It requires an
actual terminal PASS, all 1,800 records, no fatal, and matching strict-window
summary to classify a different run as PASS. See the parent README for RTL
reproduction instructions and model limitations.

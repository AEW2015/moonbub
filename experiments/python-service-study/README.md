# Reference-Python service measurement

`measure.py` times actual MT02 scale8 zero-motion preparation and receiver
decode calls on this Linux host. It uses15 consecutive native frames from
the4-second window of each existing clip, warms a separate session, then
checks every decoded image against the host reconstruction before ACK.
There are no simulated service durations in this measurement.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python measure.py
```

`results.json` binds source/helpers, input hashes/PTS, Python/NumPy versions
and per-frame costs. Existing clip inputs remain outside Git. CPU load is
uncontrolled and the other prototype studies ran concurrently; this is a
reference-program measurement, not an isolated target benchmark.

| Window | Encode-call median | Decode-call median | Complete offline-loop rate |
| --- | ---: | ---: | ---: |
| Combat held-out | 43.35 ms | 20.71 ms | 12.91 frames/s |
| Second clip held-out | 57.26 ms | 27.70 ms | 11.27 frames/s |

The loop includes the integrity oracle and ACK bookkeeping; source
decode/scale happens before timing. Network, QSPI, vblank and optical panel
response are absent. Do not add stage medians to infer the whole-loop median,
or use this as FPGA/optimized-C++ service time. The virtual studies' assumed
2 ms preparation/8 ms decode are **not measured by these Python results**.
This Python implementation does not demonstrate real-time30 fps. Native host
encoding and a hardware decoder require their own measurements and integration.

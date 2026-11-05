# V49 actual tile demand and finite-bank scheduling hypotheses

This study records actual arithmetic work per tile from96 v40 frames (first24
of each of four clips), then replays that demand through an explicitly assumed
two-stage tile schedule. It is not a cycle-accurate RTL simulation, a placed FPGA
result or end-to-end frame-rate proof.

## Exact work trace

A new reader compares eager AC-level prefetch with deferring a future event's
level until its block is needed. The run and all four arithmetic contexts remain
unchanged. Both readers reproduce all777,600 full-grid tiles, consuming752,420
actual AB38 tiles; omitted hidden tiles are zero. Independent replay checks every
tile, every per-stream counter delta, actual qmap dequantization and zero/DC counts.

The final arithmetic totals are identical:7,574,207 probability products and
6,116,124 renormalization steps. With equal zero/DC shortcuts the trace records
4,075,123 first-pass and16,790,995 second-pass mirrored products, plus1,053,307
nonzero dequantizer products. These are logical operations, not mapped DSP cycles.
All selected stream totals match the frozen AB38 encoder's retained work records.
Three reader tests and three finite-bank schedule tests pass. All source pins,
compressed trace objects and actual counters are retained.

Deferred decoding reduces some first-tile/pending-event work but provides little
benefit in the tested schedule models. It can slightly worsen the two-bank case.
There is no reason to adopt its additional control solely from these projections.

## Assumed stage service and finite buffers

The schedule consumes actual per-tile decisions/renorm counts and sparse transform
products. It assumes explicit decision and renorm costs, one shared or four
parallel arithmetic engines,4/8 MAC lanes,1/8 output pixels per cycle, eight bank
clear cycles, serial nonzero writes, two Q14 pass/control costs and serial interval
preload/guard reads. Dequantization is charged. One or two128-byte coefficient
output banks enforce producer backpressure until the inverse consumer releases
the appropriate bank. The two-bank figure256 bytes excludes all other storage.

| Assumed service profile, eager | One-bank mean / max at100MHz | Two-bank mean / max at100MHz |
| --- | ---: | ---: |
| Shared,2-cycle decisions /8 MAC /1 pixel | 8.790 /14.864 ms | 6.644 /10.067 ms |
| Four engines, same transform service | 7.935 /11.693 ms | 6.021 /7.600 ms |
| Shared,4-cycle decisions /4 MAC /1 pixel | 10.642 /20.551 ms | 7.955 /14.462 ms |
| Optimistic four engines /8 MAC /8 pixels | 2.532 /4.782 ms | 1.498 /2.803 ms |

At assumed50MHz the slow one-bank profile exceeds a33.33ms component allowance
on17/96 frames; two banks remove those component misses under the same assumptions.
This does not establish a complete30fps system: reference/output memory traffic,
compressed-port arbitration, CRC/SHA, HUD, color, scanout, network, ESP32 and QSPI
are outside the schedule. The frame input is assumed already available. Four
parallel engines require independently serviced compressed reservoirs and state;
those ports, buffers, resources and clocks are not implemented or fitted.

The result favors testing two-bank overlap before adding arithmetic engines.
Numbers describe finite Python replay under named service assumptions, not a
conservative total-system timing bound or native hardware throughput measurement.
No RTL, firmware or bitstream is changed.

```sh
python -m unittest -v test_reader
python -m unittest -v test_schedule
python benchmark.py
python verify.py
python schedule.py --check
```

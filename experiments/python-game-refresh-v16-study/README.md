# Full-resolution GM refresh and coarser refresh-key backgrounds

This finite Python study isolates periodic refresh from v15's optional SR work.
It keeps 720×480 coded / 720×405 active game content, 30 scheduled IDs/s and all
four original RGB565 display patches. It copies the v15 staged-publication,
bank-specific overlap and physical-drain model; [copy-origin.json](copy-origin.json)
records the ancestry. No existing v15 source or retained measurement is changed.

## Result

Six runs use the same 180 distinct native frames from the previously used v15
second-scene regression window (start 4 seconds). This is reused test material,
not fresh held-out validation. They pay newly measured Python service costs.

| Policy | Strict / eventual out of 180 | Distinct images in five-second window | Modeled IDs/s |
| --- | ---: | ---: | ---: |
| GM, initial key only | 174 / 177 | 149 | 29.8 |
| GM, full refresh every 30 IDs | 158 / 160 | 133 | 26.6 |
| Same refresh-30 control repeated | 160 / 162 | 134 | 26.8 |
| Refresh-30, coarser key background | 161 / 163 | 135 | 27.0 |
| Refresh-60, coarser key background | 168 / 171 | 144 | 28.8 |
| Refresh-90, coarser key background | 172 / 174 | 146 | 29.2 |

The window is [500,5500) ms. Counts are separately checked against both native
source hashes and decoded RGB hashes: duplicates cannot inflate the rates.
Every decoded frame selects all 21,120 original RGB565 UI words with zero mismatch.
The campaign has 1,080 capture events; the retained trace contains all paid stage,
reference, feedback, presentation, drop and quality records. Host wall run is
122.68 seconds, distinct from each run's six-second modeled capture interval.

The map experiment changes only refresh-key background quantization from 16 to
32. Initial keys and P maps retain background 16, and declared priority blocks
retain scale 8. The latter is a map constraint, not a source-pixel/priority RGB
error bound: chroma interpolation and subsequent reference history can change.
Selected UI words have their own independent exact source-word contract.

Five matched independent refresh keys use the same IDs [31,62,93,124,155], source
hashes and full UI coverage. Their complete bodies shrink **16.07%**, from
152,754 to 128,210 bytes total (mean 30,550.8→25,642 bytes). Repeated control keys
have identical packet hashes. Coarser backgrounds change source quality; on
matched decoded IDs the active RGB565 MSE increases by 0.3719. Future P residuals
and admission histories differ, so this key-only reduction is not a lossless or
net-wire compression gain. Coarse-30 actually sends more aggregate wire bytes
than regular-30 in this run. Quality and coverage must accompany any rate claim.

The 26.6→27.0 cadence difference is small relative to observed host variability;
it does not establish a robust policy speedup. Initial-only service now gives
29.8 versus the earlier v15 30.0, illustrating limited Python timing margin.
Longer refresh intervals reduce disruption but increase reference/recovery age.
None of these refresh profiles proves reliable 30 fps; full-key drain remains
a design problem. Do not deploy a longer interval merely to improve an FPS label.

## Ownership and fault checks

The experiment changes no AR02 syntax or publication rules. The sender still
waits for all full-key consumers/readers, validates complete caps and exact UI,
and publishes only after paid decode/ACK completion. Expiry/deadline wins over
staged completion. The new tests inject a lost first refresh chunk and a lost
refresh publication ACK. Both safely retry an independent key; unconfirmed
sender banks never become usable. The original late-ACK/decode-deadline,
conflicting feedback, lost-promotion, cap rejection and two-ingress overload
regressions remain active. All **16 tests pass**.

## Reproduction and limits

```sh
python verify.py
python analyze.py --check
python -m unittest -v test_refresh.py test_inherited.py test_ingress_feedback.py
```

Run from this folder with the project's NumPy/Pillow/PyAV environment. The
benchmark pins 31 source snapshots before execution and checks them afterward.
`analyze.py` is an explicitly untimed supplemental analysis, binding its own and
the result hashes. `benchmark.py` regenerates timings and overwrites evidence;
the commands above check the retained snapshot.

The model charges actual BOX scaling, map, GM encoding, UI/cache/validation,
transport CPU, decode, feedback, expiry and physical-release work. Independent
serialized virtual servers assume 8 Mb/s forward/reverse, 160 Mb/s QSPI,
10 ms feedback and 60 Hz vblank. Sources are precompressed 29.88 fps video loaded
offline then hypothetically scheduled at 30 IDs/s; acquisition is not measured.
Python timing variation, absent shared native CPU scheduling, unimplemented target
memory arbitration/scanout and real RF/QSPI prevent a physical 30 fps claim.
Two banks, three sender slots, two ingress slots and three display roles exclude
scratch/caches/output/copies and do not establish FPGA or external-memory fit.

Next test bank-local or sliced refresh with explicit dependency/ACK rules and a
bounded native decode/memory budget. Retain JPEG as an interoperability baseline
while AR02 is a separately negotiated experimental codec.

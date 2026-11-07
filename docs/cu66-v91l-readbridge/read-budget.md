# SDRAM read work budget

This experiment estimates read-side command work for three physical burst
sequences using the source-derived client prefill order in
`experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz`. The
fixture has 32,400 aligned logical 16-byte line misses: chroma prefill (Cb,
then Cr) followed by luma raster reads. HUD is not in this vector.

## Modeled schedules

| Schedule | Physical BL8 reads | Fetched bytes | Overfetch | ACT | PRE | REF | Response word beats | Source-FSM service cycles |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raster control | 32,400 | 518,400 | 0 | 1,854 | 1,853 | 663 | 259,200 | 508,121 |
| Tile independent | 64,800 | 1,036,800 | 518,400 | 6,420 | 6,419 | 1,363 | 518,400 | 1,038,349 |
| Tile retained | 32,400 | 518,400 | 0 | 3,065 | 3,064 | 680 | 259,200 | 517,996 |

At the assumed 10 ns source clock, those service-cycle counts correspond to
5.08121 ms, 10.38349 ms, and 5.17996 ms of this bounded prefill workload. These
are source-FSM replay times for the supplied request stream; they are not a
full-frame latency estimate, FPS result, bridge throughput result, or board
measurement.

The raster control treats each aligned logical line as one contiguous physical
BL8. Tile schedules map each logical byte through the 8x8 tile-major plane
layout (Y 720x480, Cb/Cr 360x240). The independent schedule clears the shared
response scratch per logical line and deduplicates only the two 8-byte gathers
within that request. The retained schedule follows the future-fragment filter
in `experiments/python-gamebub-v91l-tiled/verify_models.py`; it reuses retained
bytes across line requests. That upstream verifier checks byte equality for
both `actual_001` and `actual_006` across all 518,400 consumer bytes.

## Controller model

The replay follows the read-side states in the frozen
`moonshine_sdram.sv`: request acceptance only in IDLE; four independent open
bank rows; PRE on an open-row conflict; ACT and the source's two-count waits;
READ command; source delay of five before the first response; and eight response
word beats per BL8. The 750-cycle refresh threshold is charged as the source
does: refresh waits until IDLE, issues all-bank PRECHARGE, waits two counts,
issues REFRESH, clears the counter, and waits eight counts. Each PRECHARGE ALL
and REFRESH is counted. The replay starts after initialization with all rows
closed and an always-available serialized request stream. It initializes the
refresh counter to zero as an idealized accounting phase; this is not the
controller's literal post-MRS counter value.

ACT/PRE/REF and response counts are exact for this replay and the generated
burst sequences. The cycle totals model the source state transitions and
counter behavior, but omit the 20,000-cycle power-up delay and initialization
commands. They also omit bridge/client scheduling, arbitration, converter
arithmetic, hashes, scratch or shared traffic, writes, HUD traffic, and board
I/O/pin flight. Thus this comparison isolates read scheduling work only.

## Provenance and freshness

`read-budget-results.json` records the generator SHA-256, source hashes, input
vector hash and decompressed-vector hash. Run from the repository root:

```sh
python3 experiments/python-gamebub-v91l-readbridge/read_budget.py --check
```

This is a bounded Python source-FSM comparison, not RTL simulation or physical
SDRAM evidence. It does not establish full-frame latency, 30 fps, timing margin,
resource fit, or on-board behavior.

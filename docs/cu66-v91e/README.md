# V91e: reconciled timing, stage occupancy and worst-case coverage

Parent: `bebd308caae58b235263c728c4994a7340c42f73` (lettered plan).
Functional control: `c9bc0f98ef65891631ed95bab3609efc777e826a` (V91d).

**V91e instruments the existing coefficient pipeline; it does not change its
scheduling.** Both final seeds reproduce all nine V91d metrics exactly on the
original 17 cases. Expanded workloads now include the corpus's maximum packed
scratch/sparse-write source. Counters identify dense delivery/consumer hold,
memory ACK waits and merge/control as separate service costs before V91f/g.

## Qualification and unchanged behavior

| Evidence | Result |
| --- | ---: |
| Full-corpus selection scan | 457 related sources / 1,371 chunks |
| RTL cases | 20: 15 actual, four synthetic, one maximum-block directed case |
| Distinct actual source frames in RTL | 5, all from the same related walkthrough family |
| Final seeds / configurations | 910432 and 910433; four configurations each |
| Dense comparisons per seed | 9,003,776 |
| Directed recovery checks per seed | 11, preserving V91d's sequence |
| Original V91d metric comparisons | 68 rows × nine fields × two seeds = 1,224 exact matches |
| Tile trace records per seed | 140,684 |

Each case/configuration matches its entire packed image and all dense
coefficients against independent goldens. The unchanged fields are cycles,
input bytes, dense coefficients, read requests, write requests, output stalls,
metadata waits, memory-pending edges and used bytes. Thus the added counters
are not credited as another speedup. New mask/serial pairs also match the
ordered memory-service fingerprint; this diagnostic checksum excludes epoch
tags and absolute time and is not a replacement for byte goldens.

The first 17 decompressed fixture rows remain byte-identical and first, in their
original order. A scan identifies C3/f28/Y as both maximum packed allocation
(134,352 B) and maximum sparse writes (35,715). Its three plane packets append
to the fixture. Maximum encoded chunk bytes remain C3/f50/Y (27,309 B), and
maximum corpus block count remains C0/f0/Y (5,144); those sources were already
present. The synthetic 8,192-block case remains a separate boundary test.

The larger storage case does not become the slowest source-service sum:
C3/f50 remains slower in the tested scenario. Memory size, compressed size and
service cycles are different selection criteria. The expanded set is still
one precompressed source family, not a new independent game or native-30-fps
hardware qualification corpus.

## Frozen timing contract

The [machine-readable contract](../../experiments/python-gamebub-v91e/telemetry-contract.json)
defines a single simulated decoder clock and these edges:

| Event/fence | Meaning |
| --- | --- |
| Start | Excluded from service counters; subsequent active edges are numbered from 1 |
| First/last input | Actual BR88 chunk byte handshakes |
| Metadata accepted | Validated plan is accepted by scratch allocation |
| Last decoder coefficient | Last decoder→scratch handshake; historical `last_sparse_coef` also includes DC/RAW |
| Context first/last/end | Four separate band records; empty AC has no coefficient timestamps but has an end |
| Packet done observed | First parent edge observing child packet `done` already high |
| Seal accepted / scratch sealed observed | Distinct request/observed-register events; successful coefficient ownership only |
| First/last dense | Actual scalar-output acceptance |
| Integrated done | Parent completion, one edge after final dense acceptance; equals total service cycles |

Reports separate start→coefficient done, first-byte→coefficient done and
chunk-last-byte→coefficient done. **None is full-frame validated decode latency.**
Outer-frame packet-complete and validated-publication timestamps remain unset.
Their future product fence must include reconstruction, reference/HUD/hash
checks and safe publication; keep ingress and total service timing alongside
it so a short final-byte interval cannot conceal unsustainable frame service.

`*_observed` events identify the parent sampling edge after a child register
asserts. Zero timestamps mean an event did not occur. The C++ harness independently
samples boundaries and compares every RTL histogram entry, timestamp, stall
counter and storage highwater. It checks ordered fences, all context counts and
empty-context semantics.

## Every active edge is accounted for

Packet FSM occupancy and scratch FSM occupancy each independently sum to total
service cycles. They partition the **same** interval and must not be added.
The contract also gives an exclusive grouping of scratch states. Overlapping
event/stall flags remain separate from those partitions.

All valid case/configurations satisfy:

```text
sum(packet-state cycles) = sum(scratch-state cycles) = service cycles
WRITE_WAIT + READ_WAIT = external memory-pending edges
WRITE_REQ + READ_REQ = accepted requests + request-stall edges
EMIT + RAW_EXTRACT = accepted dense coefficients + dense-stall edges
packet RECEIVE = accepted input bytes + input-starved edges
integrated done = last dense acceptance + 1 = service cycles
```

State occupancy identifies where the FSM spent an edge. It is not proof that
all those edges lie exclusively on a removable causal critical path. For
example, coefficient backpressure overlaps memory waits and must not be added
to them as another independent delay.

Seed 910433, mask mode, SLOW scenario, all 15 actual packets:

| Exclusive scratch-state group | Share of 4,932,402 service cycles |
| --- | ---: |
| Dense delivery plus consumer hold | 46.67% |
| Coefficient ingest, assembly and seal control | 16.96% |
| Cache lookup and tile merge | 11.11% |
| Read ACK wait | 10.88% |
| Write ACK wait | 9.76% |
| Remaining allocation/request/clear/terminal states | 4.61% |

Percentages are rounded; the underlying exclusive counts sum exactly to service
cycles.

Dense delivery comprises 1,726,336 accepted scalar cycles and 575,737
consumer-hold cycles. Memory-pending work totals 1,018,138 edges, exactly
reconciled to read/write waits. Ingest/control occupancy includes waiting for
the coefficient producer; it is not an isolated entropy-compute measurement.

SLOW combines assumed write16/read18 response delays, deterministic 0–3-cycle
jitter and seeded input/request/output backpressure. FAST uses one-cycle ACKs
and continuous readiness. These are modeled scenarios, not calibrated SDRAM,
ESP32, Wi-Fi or display service contracts.

Observed register highwaters remain 14 partial-assembler bytes, four cached
lines, three AC heads and one accepted outstanding request. The assembler's
capacity and memory transfers are still 16 bytes: a completed line moves into
the transfer register rather than staying at occupancy 16 in the partial counter.
These observations do not establish physical BRAM/FF/DSP fit.

## Per-tile and source service traces

Each retained compressed trace records accepted first/last dense timestamps
for every block, configuration and vector identity. Trace counts and ordering
match block counts, and tile endpoints match the case timestamps. A gap between
tiles includes preparation and any first-output consumer hold, not IDCT latency.
Coded FAST tiles emit 64 consecutive scalars; RAW uses per-value fetch/extract
and can have delivery gaps even in FAST.

The three serialized chunk-service sums per actual source are below for seed
910433 mask mode. These are **component-service sums, not complete-frame
latencies**; every chunk has its own input and completion fence.

| Source | FAST start→coefficient done | SLOW start→coefficient done | SLOW sum of post-chunk-last-byte intervals |
| --- | ---: | ---: | ---: |
| C0/f0 | 770,983 | 1,067,754 | 1,044,489 |
| C0/f1 | 459,873 | 645,985 | 631,990 |
| C0/f3 | 341,132 | 476,834 | 467,806 |
| C3/f50 | 969,345 | 1,398,391 | 1,356,984 |
| C3/f28, newly added | 929,661 | 1,343,438 | 1,304,602 |

Three SLOW sums exceed the one-million-cycle *reference work budget* before the
pixel/validation stages exist. That budget assumes the roadmap's unachieved
100-MHz target; there is no measured full-frame decode time here.

As sensitivity arithmetic only, deleting the measured WRITE_WAIT bucket while
holding all other recorded work fixed leaves C3/f50 at 1,234,823 cycles and
C3/f28 at 1,184,821. This is neither an achievable schedule nor a certified
bound on architectural improvements. It supports a measured V91f write-overlap
experiment followed by V91g read/tile/output overlap, rather than promising that
assembler buffering alone closes the complete decoder budget.

## Next work and evidence limits

1. **V91f:** overlap a bounded pair of assembler buffers with memory service,
   initially keeping one accepted outstanding request. Preserve epoch/ACK drain
   and start/error recovery; compare integrated counters and exact images.
2. **V91g:** measure bounded read prefetch and next-tile preparation during
   current-tile delivery. Test consumer service independently of memory latency
   when diagnosing further gains; do not assume all SLOW holds are memory stalls.
3. **V91h and later:** replace combinational packet staging read assumptions,
   then integrate outer-frame modes, exact transforms, reconstruction and
   reference/HUD/hash publication. Keep current coefficient timestamps distinct.
4. **V100–V110:** map/route the actual top and calibrate real controllers, clocks,
   CDC and scanout before making hardware throughput or latency claims.

The new RTL counters add registers and observation fanout. Cycle parity does
not imply equal area, power or routed frequency. Packet staging remains the
V91d combinational multi-address model, and physical memory/controller timing,
live ESP32/QSPI concurrency and full pixel/publication endpoints remain open.

**Sustained hardware 720×480 at 30 distinct fps and complete validated FPGA
decoding strictly below 10 ms remain unproven.** V91e passes observability for
the implemented coefficient endpoint and freezes future fence definitions;
it does not complete the future full-frame endpoint.

- [Vector selection and full-corpus scan](../../experiments/python-gamebub-v91e/vectors/index.json)
- [RTL interface/counter contract](../../fpga/experiments/cu66-v91e/README.md)
- [Selected campaign receipt](../../fpga/experiments/cu66-v91e/pipeline-results.json)
- [Stage analysis and per-source/tile summaries](../../experiments/python-gamebub-v91e/analysis.json)
- [Independent audit](../../experiments/python-gamebub-v91e/audit.json)
- [Combined evidence](../../experiments/python-gamebub-v91e/summary.json)

## Reproduction and retained revisions

Use the existing `gamebub-cu66-v69-build` container from the repository root.
Python uses only the standard library. Compilation enables fatal Verilator
warnings, assertions, C++ `-Werror`, two jobs and watchdogs.

```sh
python3 scripts/cu66-v91e/build_vectors.py
python3 scripts/cu66-v91e/run_pipeline.py --seed 910432
python3 scripts/cu66-v91e/run_pipeline.py --seed 910433
python3 scripts/cu66-v91e/analyze.py
python3 experiments/python-gamebub-v91e/verify_results.py
python3 scripts/cu66-v91e/summarize.py --write-manifest
python3 scripts/cu66-v91e/summarize.py --check
```

The first expanded RTL run passed, but its post-analysis incorrectly required
contiguous FAST delivery for RAW as well as coded tiles. The corrected checker
requires that property only for coded tiles; both final campaigns pass. The
earlier receipt remains FAIL with its passing RTL verdict, old checker snapshot,
compressed trace and hashes intact. Its duplicate text input is represented by
the pinned gzip and exact serializer; existing unpacked local text is retained.
Restore with `python3 scripts/cu66-v91e/retain_vectors.py --restore`.

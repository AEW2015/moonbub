# V91: bounded word Rice reader and elastic RTL

V91 implements the first [post-review experiment](../literature-review-2026-11-06/experiments.md):
an unchanged-byte BR88 word-reservoir reader, an independent native realization
and a clocked elastic symbol component.

**The RTL candidate uses 29.24% fewer parser cycles on the tested real streams.
Both CPU implementations are slower than their existing controls.** Retain
the current native reader and carry the RTL candidate into integration; there
is no full-decoder or hardware frame-rate result here.

## Exact software qualification

The [new Python reader](../../experiments/python-gamebub-v91/parser.py) supports
16/32-bit refills, bounded leading-zero extraction and the existing 15-zero
literal escape (maximum 39-bit symbol). It independently checks CRC, geometry,
sizes, padding, parameters, runs, coefficient ranges, raw fallback and exact end.

| Qualification | Result |
|---|---:|
| Retained sources / residual chunks | 457 / 1,371 |
| Encoded coefficient values matched | 86,444,480 |
| Canonical coefficient-frame hashes after scatter/zero insertion | 457 / 457 |
| Complete residual-chunk bytes | 4,805,106, unchanged |
| Rice symbols / logical bits | 11,435,381 / 37,656,819 |
| Refill operations / payload bytes fetched | 1,178,979 / 4,709,136 |
| Maximum observed Python reservoir occupancy | 55 bits; implementation bound 63 |
| Independent directed/adversarial Python checks | 44,653 PASS |
| Native optimized and ASan/UBSan runs | 1,388 cases each PASS |

Native cases include all 1,371 corpus chunks, two valid synthetic packets and
15 malformed packets, compared with the frozen native reader. Coefficient
hashes serialize signed int16 explicitly little-endian. The corpus has no raw
BR88 chunks, so synthetic cases cover raw fallback. Boundary/rejection tests
include widths, truncation, unused bits, padding, invalid fields/ranges and CRC.

Refills and extraction counts are **software operations, not CPU instructions,
SDRAM commands or FPGA cycles**. The byte ledger excludes outer packets, HUD,
reconstruction, reference memory and display. The canonical coefficient hashes
are checked; the complete pixel/HUD/publication endpoint is not newly executed
as hardware in this iteration.

- [Corpus results](../../experiments/python-gamebub-v91/corpus-results.json)
- [Independent corpus audit](../../experiments/python-gamebub-v91/corpus-audit.json)
- [Directed checks](../../experiments/python-gamebub-v91/test-results.json)
- [Native and sanitizer results](../../experiments/python-gamebub-v91/native-results.json)
- [Independent native receipt/archive audit](../../experiments/python-gamebub-v91/native-audit.json)

## Clocked RTL result

The [generic RTL component](../../fpga/experiments/cu66-v91/README.md) has a
64-bit reservoir, 16/32-bit input words, ready/valid symbol requests and held
responses, bounded EOF/word checks, sticky errors and stream-start/reset abort.
A bit-serial control shares its interfaces and refill policy. Separate request,
prefix, suffix and response steps mean it does not claim one symbol per cycle.

The frozen reader exports **1,520 streams / 173,061 requests**: 48 real streams
from C0/f0, C0/f1, C0/f3 and C3/f50 plus 1,472 synthetic cases. Every symbol value
and consumed bit position is checked. Seeds 910032 and 910033 each pass eight
configurations, **1,384,488 response comparisons and 104 directed checks**.
Repeated configurations/seeds do not add distinct gameplay coverage.

Real streams contain 147,327 symbols and 517,981 bits. Seed 910033 yields:

| Refill / external stalls | Serial cycles | Word cycles | Serial / word |
|---|---:|---:|---:|
| 32-bit, all ready | 855,682 | 605,514 | 1.413× |
| 32-bit, matched seeded stalls | 904,754 | 655,024 | 1.381× |
| 16-bit, all ready | 871,866 | 621,698 | 1.402× |
| 16-bit, matched seeded stalls | 920,757 | 671,566 | 1.371× |

The fence excludes stream-start and includes every later rising edge through
final response delivery. Fast/control pairs see the same cycle-indexed
external offers/readiness; producers hold pending payloads until accepted.
Compile warnings are fatal, assertions are enabled, held responses are checked
and every test has a watchdog. Input/output stalls remain in the measured cycles.

The combined real-plus-synthetic 32-bit all-ready ratio is 1.867×. Synthetic
long codes benefit much more, so that mixed ratio is **not the gameplay result**.
This serial control is a new mode of the component, not the old AB38 decoder or
a full integrated BR88 receiver.

Both datapaths and counters remain in the runtime-selectable experiment.
Separate physical variants need synthesis/routing before comparing area,
achieved clock or throughput. Fewer cycles can carry more combinational delay.
There is no target timing/fit, CDC proof or board result.

- [RTL results and retained seed attempts](../../fpga/experiments/cu66-v91/results.json)
- [Independent RTL audit](../../fpga/experiments/cu66-v91/independent-audit.json)
- [Frozen-reader vector export](../../experiments/python-gamebub-v91/rtl-vectors/index.json)

## CPU results: retain the old reader

Paired trials use the same 12 chunks from four sources, warm-up, seven repeats
and shuffled/alternating order. Timed calls include CRC, grammar and residual
coefficient-vector construction, excluding file I/O, hashing, full-frame scatter,
transforms, HUD and publication. Native rows time 20 decodes and divide by 20
before summing one 12-chunk workload; sanitizer timings are excluded.

| Host implementation | Bit-reader median, 12 chunks | Word-reader median | Decision |
|---|---:|---:|---|
| CPython 3.14.4 | 76.756 ms | 124.558 ms | Instrumented candidate slower |
| g++ 13.3.0, `-O3` | 0.842 ms | 1.006 ms | Candidate slower; median paired bit/word ratio 0.839 |

The Python candidate always updates diagnostic dictionaries, unlike its old
control; this compares implementations with that instrumentation included.
The separately implemented native candidate has no such counters and still
loses on this host. Neither table measures one frame's complete latency, and
neither transfers to ESP32 or FPGA speed. All raw samples and earlier successful
harness/provenance revisions are retained.

## Decision and remaining work

Preserve the existing packet format, quantization and software control. Keep
the word parser as a qualified **RTL integration candidate**. No firmware,
running board or bitstream is changed by this study.

1. Add BR88 packet/context adapters, DC reset semantics, AC pending-event
   lookahead, run/scatter validation and finite coefficient-output credits.
   The current RTL consumes predeclared symbol requests, rather than deriving
   them from chunk framing itself.
2. Record per-tile/context arrivals and memory/hash/publication dependencies
   before updating the complete causal graph. Do not subtract this component
   ratio from V90 frame totals or apply it to AB38 work.
3. Advance V92's finer entropy-choice experiment using actual complete bytes
   and host costs, retaining the bounded protocol/recovery checks.
4. Keep V100–V110 dedicated to mapping, placement, routing and timing closure.
   Include BRAM latency, LUT/carry mapping, debug-counter cost and real interface
   constraints before accepting a target clock.

**Hardware 30 fps and complete validated decoding strictly below 10 ms remain
open.** The full corpus is one related walkthrough family; RTL timing covers
four selected sources. Memory/controller, reconstruction, HUD, continuous
scanout, ESP32 ingress and live host encoding still need integrated qualification.

## Reproduction

Run from the repository root; native/RTL steps use the existing
`gamebub-cu66-v69-build` container. No new Python packages are required.

```sh
python3 experiments/python-gamebub-v91/test_parser.py
python3 scripts/cu66-v91/run_corpus.py
python3 experiments/python-gamebub-v91/verify_corpus.py
python3 scripts/cu66-v91/run_native.py
python3 scripts/cu66-v91/package_native_artifacts.py
python3 experiments/python-gamebub-v91/verify_native.py
python3 scripts/cu66-v91/build_rtl_vectors.py
python3 scripts/cu66-v91/run_rtl.py --seed 910032
python3 scripts/cu66-v91/run_rtl.py --seed 910033
python3 fpga/experiments/cu66-v91/verify_results.py
python3 scripts/cu66-v91/summarize.py
```

Regeneration creates/selects new attempts and timings may vary. Source/fixture
hashes, exact commands, compiler/simulator versions and prior revisions remain
distinguishable. Native and RTL component checks complement each other; they
do not constitute an integrated hardware proof.

The [combined result](../../experiments/python-gamebub-v91/summary.json) binds the
selected audits. Native source snapshots/binaries are Git-packaged in one
compressed archive with a hash/member index; duplicate frozen input snapshots
resolve to the already-tracked original fixture. The native verifier reads that
archive rather than depending on ignored unpacked copies. No original local
artifacts are removed by packaging.

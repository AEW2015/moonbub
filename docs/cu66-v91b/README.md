# V91b: BR88 context control, sparse scatter and finite output credit

Parent: `42f84090d0f93ea2711270e29b3d5e38791a8612` (V91). This checkpoint
closes another part of E1 before the V92 entropy-selection experiment. It
preserves packet bytes and coefficients; no firmware or deployed bitstream is
changed.

**The word-parser advantage survives context integration: 26.92% fewer cycles
than the matched serial control on the tested real contexts.** Unlike V91's
predeclared symbol requests, this RTL derives DC and AC requests from metadata,
retains a pending run until its level arrives, checks bounds and maps sparse
coefficients to raster addresses. A single held output slot provides finite
credit. These are context-component cycles, not complete-frame latency.

## Functional model on all retained sources

The [Python model](../../experiments/python-gamebub-v91b/context.py) validates
BR88 packet framing and CRC in software, then opens four contexts. It reconstructs
zero-initialized coefficient scratch from sparse writes. Writes remain provisional
until every context has ended exactly; an error/abort discards publication and a
replacement epoch clears the pending slot and scratch. Its raw fallback is a
software bypass, not an RTL implementation.

| Qualification | Result |
| --- | ---: |
| Retained sources / chunks / contexts | 457 / 1,371 / 5,484 |
| Coefficient values matching the frozen decoder | 86,444,480 |
| Chunk coefficient SHA-256 matches | 1,371 / 1,371 |
| Residual-chunk bytes | 4,805,106, unchanged |
| Sparse coefficient writes per complete corpus replay | 6,393,038 |
| Zero-event AC contexts | 909 |
| Maximum pending coefficient occupancy | 1 |
| Directed model checks | 99 PASS |
| Independent packet mutations/truncations | 3,209: 21 accepted with exact parity, 3,188 rejected by both readers |

Both all-ready and stalled-consumer replays produce identical coefficients.
The stalled replay holds each output for a seeded 0–7 false-ready samples before
acceptance, totaling 22,359,009 held samples. **These samples are functional
service stimuli, not FPGA cycles or a Wi-Fi/ESP32 arrival model.** The model
does not predecode a later event while its one output is held.

The packet checks include CRC-repaired mutations so tests reach metadata and
grammar validation. A late AC failure is checked after a valid DC write has
actually entered the provisional scratch; the transaction becomes inactive,
clears its pending output and never publishes. All stored model/code/input and
case-list hashes are checked by the independent audit.

Sparse output does not make coefficient initialization free. The Python scratch
and duplicate-write bitmap are functional representations, not FPGA memory-fit
evidence. A hardware consumer still needs a zero-default/clear policy, real RAM
ports, address mapping, context completion tracking and abort invalidation.

- [Full-corpus model result](../../experiments/python-gamebub-v91b/results.json)
- [Packet checks](../../experiments/python-gamebub-v91b/packet-checks.json)
- [Independent evidence audit](../../experiments/python-gamebub-v91b/audit.json)

## Clocked RTL integration

The [RTL contract](../../fpga/experiments/cu66-v91b/README.md) and
[controller](../../fpga/experiments/cu66-v91b/br88_context.sv) reuse the unchanged
V91 Rice component. Inputs include latched context metadata and epoch plus an
MSB-first 16/32-bit ready/valid stream. The controller derives all Rice requests;
the harness supplies no predeclared request sequence.

DC outputs include each block's DC, including zero. AC outputs include only
nonzero coefficients in increasing band position. The controller checks metadata,
run bounds with widened arithmetic, signed coefficient ranges and exact final
bit consumption. It holds the sparse payload and epoch stable under stalls;
`done` occurs only after the final accepted output. A zero-event AC context
requires zero bits and completes on its start edge. Reset, abort and replacement
start flush pending requests, runs and output. Errors and completion are sticky
until a new context/reset/abort.

Frozen V88 decoding independently exports **48 actual contexts from 12 chunks
of four selected sources**, plus seven synthetic contexts. Seeds 910132 and
910133 each pass:

- 55 contexts × eight configurations: 16/32-bit input, serial/word parsing and
  ready/stalled consumer service.
- 674,120 sparse output/epoch comparisons (84,265 per configuration).
- 172 additional directed checks, including bad metadata, EOF, bad input word
  size/last/padding, coefficient/run overflows, the maximum block/index,
  exact-end errors, a held final output and reset/abort/replacement in pending
  DC, run, level and held-coefficient states. A malformed prefetched word while
  the parser is idle and a nonfinal coefficient is held must poison the next
  derived request and prevent completion.

For seed 910133, actual contexts contain 147,327 Rice symbols, 517,981 logical
bits and 84,252 sparse writes:

| Refill / external stalls | Serial cycles | Word cycles | Serial / word |
| --- | ---: | ---: | ---: |
| 32-bit, all ready | 937,735 | 685,304 | 1.368× |
| 32-bit, matched seeded stalls | 965,935 | 713,591 | 1.354× |
| 16-bit, all ready | 951,701 | 696,983 | 1.365× |
| 16-bit, matched seeded stalls | 979,692 | 724,824 | 1.352× |

The fence excludes the start edge and includes subsequent parser, adapter,
refill, stall and final output-delivery edges. Word/control pairs use the same
cycle-indexed input-offer/output-ready schedule for each context and word width;
pending input words remain stable until accepted. Their different progress
means actual accepted stalls need not be identical. The comparison is between
two modes of this adapter, not the previous AB38 decoder.

V91's 605,514 word-parser cycles on these streams rise to **685,304** with this
adapter/output fence: 79,790 additional cycles (13.18%). The serial side rises
from 855,682 to 937,735. This direct component comparison charges newly executed
work; it does not estimate a complete decoder by subtracting a parser speedup
from V90's frame graph.

The runs use Verilator 5.020 with assertions and fatal `-Wall` warnings, C++
`-Wall -Wextra -Werror`, bounded watchdogs and two build jobs. Successful and
failed setup/compile attempts remain distinguishable, with exact source
snapshots, input hashes, tool versions, commands, exits and logs. The selected
results are clean passes; early failed attempts are retained as diagnostic
history rather than silently deleted.

Two identical text fixtures retained by early failed attempts are represented
by the pinned compressed vector input and an exact serializer, rather than
168,640 duplicate text lines. Their original receipt hashes are unchanged;
`python3 scripts/cu66-v91b/retain_vectors.py --restore` recreates both files.
Existing local copies are ignored and remain on disk. The bundle checker
verifies this representation against both original failed-attempt manifests.

- [Selected RTL results and attempts](../../fpga/experiments/cu66-v91b/results.json)
- [Independent frozen-reader vectors](../../experiments/python-gamebub-v91b/context-vectors/index.json)
- [Combined machine-readable evidence](../../experiments/python-gamebub-v91b/summary.json)

## Integration limits and next work

The RTL starts after packet extraction. It does **not** check whole-packet CRC,
implement raw packets, arbitrate four contexts, zero coefficient scratch,
reconstruct pixels, access reference SDRAM, compose HUD, hash/seal a frame or
drive continuous display. A source that silently stops before its declared bit
count stalls; a real ingress owner needs timeout/abort recovery. Epoch values
are tags here, not a complete system-level wrap/ownership policy.

The consumer must share the synchronous reset/abort/replacement priority and
invalidate provisional writes from the cancelled epoch, including any old
registered-valid value present before the cancellation edge. This component
does not independently publish output into an unaware downstream consumer.

The runtime serial/word control and debug counters remain in one experimental
design. Constant-divisor scatter expressions avoid an unconstrained variable
divider in the source, but only synthesis/mapping/routing can establish their
cost and achieved clock. No target implementation, RAM-port or CDC claim follows
from generic RTL simulation. This corpus remains one related precompressed
walkthrough family; extra seeds do not add gameplay coverage.

1. Add packet/CRC ingress and the raw bypass, then integrate four-context
   arbitration with a finite, zero-default coefficient store. Track context,
   tile and epoch identity through consumer acknowledgments and aborts.
2. Record actual per-context/per-tile arrivals and integrate memory,
   reconstruction, validation and publication dependencies before changing the
   full-frame timing model. Replay long consumer stalls and transport resets.
3. Continue V92's finer AB38/BR88 selections using actual serialized bytes and
   bounded host costs; retain the existing native CPU reader after V91's
   negative CPU result.
4. Preserve V100–V110 for exact-part 7-series mapping, placement, routing and
   timing, with realistic memories and continuous display service.

**Sustained hardware 30 fps and complete validated FPGA decoding strictly
under 10 ms remain open.** This checkpoint supplies a more integrated functional
and clocked component, with enough evidence to make the next integration test
concrete; it does not establish either hardware milestone.

## Reproduction

Run from the repository root. RTL uses the existing
`gamebub-cu66-v69-build` container; the model needs no additional Python packages.

```sh
python3 scripts/cu66-v91b/build_vectors.py
python3 scripts/cu66-v91b/run_model.py
python3 experiments/python-gamebub-v91b/test_packets.py
python3 scripts/cu66-v91b/run_rtl.py --seed 910132
python3 scripts/cu66-v91b/run_rtl.py --seed 910133
python3 experiments/python-gamebub-v91b/verify_results.py
python3 scripts/cu66-v91b/summarize.py --write-manifest
python3 scripts/cu66-v91b/summarize.py --check
```

Regeneration creates new selected attempts; timestamps and measurements may
change. Rebuild the audit/summary/manifest for those attempts rather than
rewriting the retained receipts to describe a new run.

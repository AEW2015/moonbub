# V103 parser mapping review

**Scope:** read-only mapping inventory of the existing BR88 parser hierarchy and
the V102 native combined implementation. This document records RTL-derived
structure and measured reports; it contains no source changes, new synthesis,
or parser performance claim.

## Current evidence and priority

The native V102 combined routed hierarchy reports the BR88 `parser` instance
(`br88_rice_elastic`) at **1,496 LUTs, 249 FFs, no LUTRAM, no BRAM, and no DSP**.
Its parent `context_decoder` is 3,365 LUTs / 523 FFs / 1 DSP, and
`synchronous.ingress` is 5,153 LUTs / 1,892 FFs / 16 RAMB36 / 2 DSP. These are
hierarchical routed utilization figures from the combined V102 candidate. The
parent totals include their descendants, and Vivado notes that cross-hierarchy
LUT combining means child totals need not sum exactly to parent totals.

The reports do **not** expose a parser-specific critical path or isolated
parser-only candidate. V102's routed worst setup path is instead
`reconstruction/tile_reg[10]` to `reconstruction/residual_reg[1082]/CE`: 29
logic levels, 14 CARRY4, 23.687 ns data delay, and −13.976 ns WNS under the
10-ns comparison clock. The V102 predicate-only synthesis path moved into
admission's tile-to-active-cell write cone (31 levels, 15 CARRY4 and one
DSP48E1); it too is separate from the parser. See the
[V102 vendor comparison](../cu66-v102/vendor-comparison.md),
[routed hierarchy utilization](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-utilization.rpt),
and [routed setup paths](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-setup-paths.rpt).

This makes geometry/control and admission indexing the evidence-backed timing
priority. The parser remains a V103 work item from the development plan, with a
measurable LUT/control-area footprint and untested mapping alternatives. Do not
present a parser rewrite as fixing the reported V102 critical path unless a
later native path report demonstrates that relationship.

## RTL and hierarchy inventory

The mapped chain in the combined report is:

`br88_packet_ingress_sync_v91h` → `br88_context` → `br88_rice_elastic`.

Source locations:

- [`br88_rice_elastic.sv`](../../fpga/experiments/cu66-v91/br88_rice_elastic.sv)
- [`br88_context.sv`](../../fpga/experiments/cu66-v91b/br88_context.sv)
- [`br88_packet_ingress_sync_v91h.sv`](../../fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv)

### Rice parser (`br88_rice_elastic`)

- A four-state controller (`IDLE`, `PREFIX`, `SUFFIX`, `RESPONSE`) accepts one
  symbol request at a time and returns a held valid response. The `else if`
  sequencing gives request acceptance priority over input-word acceptance;
  output acceptance clears the response slot. Input is backpressured while an
  output is held, when the reservoir exceeds the refill threshold, after a
  failure, or when a symbol request is pending in `IDLE`.
- The reservoir is 64 bits with a 7-bit `available` count. Refill shifts in a
  32-bit word by `in_bits` and adds that count. `in_ready` requires
  `available<=32`; a simulation assertion checks `available<=64`. The
  `in_bits`/`expected_word` rules distinguish 16- and 32-bit words, require a
  nonzero exact final/partial word length, check `in_last` against the declared
  stream size, and reject nonzero unused low bits.
- `size_bits`, `loaded`, and `consumed` are 32 bits; bit/input/symbol/cycle and
  wait/stall counters are 64 bits. The request `k` and escape width are 5 bits;
  quotient and suffix-left are 5 bits; prefix zero count is 5 bits. Decoded
  suffix, accumulator and output value are 24 bits. The legal context constrains
  `k<=19` and decoded coefficient value to signed ±2048, while the parser has
  its own request guard `req_k<=19`, `req_escape<=24`.
- Parallel prefix mode examines a bounded window of at most 15 remaining bits.
  A source loop scans up to 15 positions using a dynamic reservoir bit index,
  producing `zeros` and `found_one`. A 15-zero prefix selects the configured
  escape width; a shorter unterminated prefix is rejected as truncated.
  Serial mode consumes one prefix bit per step, increments quotient for zeros,
  and switches to the escape suffix at quotient 15.
- Prefix and suffix extraction use a variable right shift of the 64-bit
  reservoir. The retained-bit mask is another variable shift. Suffix assembly
  left-shifts the 24-bit accumulator for serial mode; decoded value composition
  shifts the quotient by `k`. These are reasonable bounded candidates for
  alternative LUT6/mux/carry mapping, but source syntax alone does not establish
  their mapped cost or criticality.
- `count_input_wait` accounts for parser steps that cannot proceed while more
  bits remain; `count_output_stall` counts held responses. These counters and
  the 64-bit cycle/input/symbol/bit counts are public at the module boundary.
  The context and packet wrapper expose/use several diagnostics even when the
  packet wrapper ties some parser counters to unused signals. The V102 flow
  explicitly used the same public diagnostic visibility as its comparison
  builds.

### Context sequencer (`br88_context`)

`br88_context` converts parser symbols into DC or sparse coefficient events.
It sequences `REQ_*`/`WAIT_*` states and holds output in `HELD`, with reset,
abort, epoch, target-count and final-consumption checks. The 32-bit context
`position`, `limit`, `target`, and `emitted` values are wider than some legal
operational ranges; this inventory does not authorize narrowing them. For
sparse bands, block/index mapping uses constant divisors 5, 15, or 43 and a
64-entry zigzag table. The current output slot and `out_ready` stall behavior
are separate control costs from the parser primitive itself.

### Packet ingress (`br88_packet_ingress_sync_v91h`)

Ingress stages packet bytes in a synchronous backing memory, reads header,
descriptor, replay-word and raw-data windows, validates CRC and descriptor
bounds, and passes 16/32-bit words to the context. Its packet addresses,
received/cursor/size/length/count/offset/size/replay counters are predominantly
32 bits; the backing store is parameterized to 49,152 bytes, with a derived
address width for the memory index. The one-byte registered read, epoch/address
response validation, byte staging, packet CRC, and fetch FSM all belong to the
wrapper hierarchy, not the Rice prefix/refill datapath. V102's 16 RAMB36 in
this synchronous ingress subtree are packet staging storage, not parser
reservoir storage.

## Bounded parser experiments

Run these as separate scratch candidates from the V102 source baseline. Each
candidate should retain the same part, constraints, clock, source visibility,
and public diagnostics, and should first compare synthesis and setup reports.
Only route candidates that offer a meaningful area/timing tradeoff. Keep
geometry/admission variants independent so parser and non-parser effects remain
attributable.

| Rank | Microexperiment | Main uncertainty / guardrails |
|---|---|---|
| 1 | Compare the current 15-position parallel prefix scan with a factored priority/leading-zero form, preserving the exact window, escape selection, truncated-prefix rejection, and serial-mode behavior. | Likely low state risk and directly targets prefix LUT mapping. Exhaust all 15-bit windows, all shorter remaining lengths, all-zero escape boundary, and request `k`/escape combinations; compare mapped LUTs and critical paths before routing. |
| 2 | Compare alternative reservoir extraction and keep-mask forms (bounded case/mux slices or staged selection) while preserving refill, bit order, and one-symbol response timing. | Dynamic 64-bit shifts may map to mux trees, but no report proves they are critical. Cover `available` 0–64, all legal take lengths, refill at 16/32-bit boundaries, and escape suffixes; retain the no-overflow and bit-count invariants. |
| 3 | Isolate serial suffix accumulation/control, including decrement/terminal detection, without changing the parallel path. | Serial mode trades per-symbol cycles for narrow per-cycle logic. Compare full-frame cycle and stall counters; preserve the zero-run/escape transition and output backpressure. |
| 4 | Evaluate only after parser-local reports show counter fanout/cost: narrower internal counters with explicit saturation/overflow semantics, or split diagnostic counters from the decode decision cone. | Highest interface/observability risk. Public 64-bit diagnostics and declared stream-size checks are part of the current contract; do not narrow exposed counters or omit them from synthesis visibility to claim savings. Prove maximum packet/profile bounds and preserve counter values on error, reset, and abort. |
| 5 | Context-level address/index factorization or registering a precomputed sparse output address, as a separate context experiment. | This may affect context timing/area rather than the Rice parser. Prove band, event-count, position, limit, first-event and malformed-input behavior; align block/index/coefficient/epoch through stalls. Do not conflate it with admission's independent 32-bit `cell_index` cone. |

For every retained variant, run exact valid and malformed packet regressions,
including escape boundaries, short/final words, CRC/descriptor rejection,
reset/abort/epoch interruption, input starvation, and output stalls. Compare
canonical coefficient bytes/events, error code, cycles, input wait, output
stall, and all public diagnostics. A pipeline or registered lookup is a
separate latency variant and must state the cycle/occupancy change explicitly.

## Measurement limits

V102 used native Vivado 2026.1 build 6511674 for `xc7a100tcsg324-1`, with the
unchanged 10-ns comparison clock loaded before synthesis. The combined build
routes 72,867 of 72,867 routable nets with zero routing errors; final reported
utilization is 48,522 LUTs, 2,718 LUTRAMs, 34,795 FFs, 32 RAMB36, and 28 DSPs.
Its routed WNS is −13.976 ns, so this is not timing closure. OOC parent I/O and
clock-boundary limitations described in the V102 comparison remain. These
whole-build numbers establish the review baseline only; they do not measure
parser throughput, frame rate, or parser-specific timing.

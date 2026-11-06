# V91 elastic BR88 symbol component

`br88_rice_elastic.sv` is a generic synthesizable SystemVerilog experiment. It
implements the BR88 Rice symbol primitive and a bit-at-a-time control in one
module. The two modes share the same 64-bit reservoir, refill policy, request
and response interfaces, and measurement counters. This is a behavioral
component simulation; it does not implement packet framing, CRC, coefficient
range checks, run/scatter, transforms, reference memory, or publication.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/cu66-v91/run_rtl.py --seed 910032
```

The runner uses the existing `gamebub-cu66-v69-build` container, Verilator with
assertions and fatal `-Wall` warnings, and a bounded `-j 2` compile. Objects and
executables remain in `/build/v91-rtl-*` in that container. Every attempt keeps
tool versions, exact commands, source snapshots and SHA-256 pins, an immutable
copy of the reference vectors, compile output, simulation rows, and JSON
results. A failed command or final source/vector pin check records `FAIL`.
`results.json` selects the latest attempt. No Vivado implementation is run.

## Interface contract

All events occur on rising `clk` edges. `reset` is synchronous and has highest
priority. `stream_start` has next priority and atomically aborts a pending
request or held response, drops buffered bits, clears all counters and sticky
errors, and latches `stream_bits`, `word16`, and `serial_mode`. Reset leaves
both input interfaces disabled until a new start. Start enables a stream with
an unsigned 32-bit declared logical bit count. Empty streams are legal, but a
symbol request against an empty stream reports truncation.

`word16=0` selects 32-bit refills; `word16=1` selects 16-bit refills. These
settings and `serial_mode` are latched only at start. `in_data[31]` is the next
wire bit in either mode. On each `in_valid && in_ready`, `in_bits` must equal
`min(refill width, stream_bits - previously accepted bits)`. Thus only the last
word may be short, and unused low bits of `in_data` must be zero. `in_last`
must be asserted exactly for the word which reaches the declared logical end.
The interface never accepts a word past that end, and never retains more than
64 reservoir bits. Byte packing and any enclosing packet checks belong to the
caller. An early or missing `in_last`, incorrect count, or nonzero padding
poisons the stream. Absence of `in_valid` means a source stall, not EOF; an
external transport which terminates without supplying a word must abort or
restart the stream.

`req_valid && req_ready` submits one symbol with `req_k` in 0..19 and
`req_escape` in 0..24. There is at most one pending request and one held
response; requests wait until the previous response has been delivered. The
prefix is capped at 15 zero bits. A terminating one before that cap selects
`(quotient << k) | suffix`; 15 zeros select an unsigned literal of
`req_escape` bits, with **no terminating one**. A BR88 symbol therefore needs
at most 39 logical bits. The leading-zero mode inspects at most the lesser of
15 and the remaining declared logical bits, so a valid short final symbol
does not need nonexistent lookahead. The control consumes one prefix or
suffix bit per processing cycle; both modes support zero-width suffixes.

`out_valid` holds `out_value[23:0]`, cumulative `out_consumed[31:0]`, and
`out_error[3:0]` stable until `out_ready`. `out_error` values are 0 (success),
1 (invalid request widths), 2 (declared EOF truncates a prefix or suffix), and
3 (invalid source word). Errors are sticky until reset/start. A later request
on a poisoned stream receives the same error; malformed input encountered
before a request is reported on the next request. Prefix truncation consumes
its available zero prefix. Suffix truncation is detected before consuming any
of that suffix in both modes. An error response carries value zero and the
logical position reached. Errors cannot publish a successful symbol.

Refills take priority over parsing when their handshake occurs. Both modes
offer input readiness when at most 32 bits are buffered and declared input
remains. Neither prefetches while a response is held. A new request takes
priority over prefetch in the idle state. These deliberate bubbles are part
of the measured component contract; this is an initial elastic implementation,
not a one-symbol-per-cycle throughput claim.

## Counters and verification

The six 64-bit counters reset at start. `count_cycles` counts every subsequent
active rising edge, including the edge delivering the final response.
`count_inputs` counts accepted words, including malformed words.
`count_symbols` counts successfully delivered responses.
`count_bits` counts logical prefix/suffix bits actually consumed, before any
output stall. `count_input_wait` counts pending parse cycles that need more
buffered bits, have enough declared bits remaining, and accept no refill on
that edge. `count_output_stall` counts cycles with held output and low ready.
Input wait is phase dependent; all cycle counters measure this specific
microarchitecture, not the Python reader's operation counts. Empty reference
streams issue no requests and contribute zero post-start measured cycles.

The C++ harness checks every returned symbol and cumulative bit position
against frozen-reader vectors, enforces output stability under backpressure,
checks counter/handshake agreement and finite watchdogs, and asserts no input
overrun. RTL assertions check reservoir and declared bit bounds. Directed
checks include the maximum 39-bit literal with value `0xffffff`, zero-width
literal, short final prefix, empty/truncated streams, invalid widths and
words, sticky errors, extra offered input, and reset/restart with a pending
request or held response.

Each vector runs with 16/32-bit refills, leading-zero/serial parsing, and
all-ready/seeded stalls. Matched mode pairs reset the PRNG from the same case
identity, word width and seed, then draw exactly three values per cycle for
source offers, request offers and response readiness. Thus their external
offer/ready traces match at the same cycle index; each producer holds its
payload until acceptance. Different completion times truncate those traces
at different fences. Results aggregate the 48 actual source streams separately
from synthetic boundary cases and also preserve each actual source's totals.

Cycle reductions are component service measurements. No clock frequency,
whole-decoder latency, physical resource usage, timing closure, transport
throughput, CDC correctness, formal proof or board validation follows from
this simulation. Runtime mode selection also retains both parse datapaths;
physical comparisons would require separately configured builds and synthesis
and routing evidence.

## Retained component result

The final source passes the full 1,520-case bundle in all eight configurations
with seeds **910032 and 910033**: 1,384,488 reference response checks per seed,
plus 104 directed checks. Both final builds are warning-free with fatal
Verilator `-Wall` diagnostics. [results.json](results.json) selects seed 910033;
the seed 910032 run is retained in
[its attempt](attempts/20261106T165237655819Z-f1f50f29/results.json).

The **48 actual streams** contain 147,327 symbols and 517,981 logical bits.
Their aggregate component cycles, through final response delivery, are:

| Refill | Service | Leading-zero cycles | Serial cycles | Serial / leading-zero |
|---|---|---:|---:|---:|
| 32 bits | All ready | 605,514 | 855,682 | 1.41315 |
| 16 bits | All ready | 621,698 | 871,866 | 1.40239 |
| 32 bits | Matched stalls, seed 910033 | 655,024 | 904,754 | 1.38125 |
| 16 bits | Matched stalls, seed 910033 | 671,566 | 920,757 | 1.37106 |

The 32-bit all-ready pair each accepts exactly 16,206 words, delivers 147,327
symbols, and consumes 517,981 bits. With seed 910033 stalls it keeps the same
input, symbol and bit counts; leading-zero mode records 2 input-wait cycles
and 48,972 output-stall cycles, versus 2 and 48,769 for serial mode. Different
completion times sample different lengths of the same external trace.
Synthetic results are reported separately in JSON and should not be used as
the actual-corpus speed ratio. None of these numbers is a full-frame decoder
latency or a hardware clock result.

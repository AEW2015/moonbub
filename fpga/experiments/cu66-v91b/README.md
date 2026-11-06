# V91b single BR88 context RTL adapter

`br88_context.sv` derives Rice requests from one context's latched metadata and
reuses the unchanged V91 `br88_rice_elastic.sv`. DC context 0 decodes exactly
`blocks` signed Rice14 values. AC contexts 1/2/3 decode `event_count` pairs of
Rice24 run and Rice12 level-minus-one values. Runs traverse widths 5/15/43 at
zigzag bases 1/6/21; outputs map to 8x8 raster indices. Literal constant divisors
express the block/index mapping; no synthesis, resources, or timing are claimed.

This experiment begins after packet framing and metadata extraction. It checks
its own metadata parameters and stream protocol but does not establish packet
header or CRC trust, reconstruct pixels, implement HUD handling, or establish
whole-frame latency or physical timing. Sparse writes are provisional: a future
consumer must initialize coefficient scratch to zero and invalidate partial
writes on an error, abort, reset, or replacement epoch. One successful context
is not a completed tile; whole-chunk CRC and all required contexts belong to
integration outside this module.

The interface samples `blocks[16:0]`, `band/k0/k1[7:0]`, `event_count`,
`stream_bits`, `epoch`, `word16`, and `serial_mode` on `start`. Caller changes
after that edge do not alter the active context. `blocks` must be 1..65536.
Band must be 0..3. DC requires k0<=13, k1=255, event_count=blocks. AC requires
k0<=19, k1<=11, event_count<=blocks*bandwidth. Empty AC with zero coded bits
completes on the start edge; nonzero coded bits are an exact-end error.
Coefficients are signed -2048..2048; AC zero coefficients are forbidden.

The stream uses the V91 MSB-first word contract: 16 or 32 bits per ordinary
accepted input, a short final word with exactly the remaining declared bits,
`in_last` on precisely that final word, and zero unused low bits in `in_data`.
The stream declaration bounds EOF; a source which simply stops offering words
before the declared end stalls and cannot be diagnosed as EOF without a timeout
or another upstream indication. Inputs after completion/error are refused.

Sparse output is `(out_block[15:0], out_index[5:0], signed out_coefficient[15:0],
out_epoch[31:0])`. One held output slot provides finite credit. It retains its
payload while stalled; the controller issues no next event until acceptance.
The pending AC run survives arbitrary stalls until its level arrives. The
parser reservoir may prefetch input while the output is held. Final logical bit
consumption must equal `stream_bits`; a final exact-end failure suppresses that
last output. Earlier accepted sparse writes remain provisional. `done` becomes
sticky only when the final coefficient is accepted (or valid empty AC starts).

Synchronous priority is reset, abort_context, start, normal operation. Reset is
dominant over a simultaneous start. `abort_context` flushes the parser and held
output and leaves the interface idle. A new `start` replaces the prior epoch,
including a pending symbol/run or held coefficient. Both clear error and done.
`error` is sticky until one of these actions; no outputs follow an error:

| Error | Meaning |
| --- | --- |
| 0 | No error |
| 1 | Parser Rice parameter error (wrapper validation normally prevents this) |
| 2 | Declared EOF inside prefix/suffix |
| 3 | Incorrect word size, last indication, or padding |
| 4 | Invalid context metadata |
| 5 | Coefficient range/zero-level failure |
| 6 | AC run exceeds band position bounds |
| 7 | Unused coded bits at context end |

`count_cycles` excludes the start edge and includes every subsequent adapter,
parser, refill, stall, and coefficient delivery edge through final acceptance or
error detection. It stops in terminal states. This is context service time, not
a whole-frame measure. `count_outputs` counts sparse acceptance; parser symbol,
input, bit, and wait counters are also exposed. Debug state and parser counters
are verification observability, not additional downstream credit.

Run `python3 scripts/cu66-v91b/run_rtl.py --seed 910132` in the repository.
The runner builds in existing container `gamebub-cu66-v69-build` with Verilator
`--assert -Wall` (warnings fatal), C++ `-Wall -Wextra -Werror`, and `-j 2`.
Binaries and generated objects stay in container `/build`; each attempt retains
source snapshots, source/vector/index SHA-256 pins, compiler/tool versions,
commands, compile logs, simulation JSONL, and a results manifest. Failed attempts
are retained. `results.json` selects the most recent attempt. The first relative
CLI-path setup failure has its own explicit setup-failure record.

The independent vector archive contains 48 actual contexts from four selected
sources (12 chunks) plus seven synthetic contexts. Each runs under 16/32-bit
inputs, serial/word parsing, and ready/stalled operation: 440 replay cases per
seed. Every emitted sparse triplet and epoch is compared against the oracle;
full decoded coefficient hashes are retained in vector provenance. The harness
mutates all metadata after start to verify latching. Serial and word controls
use identical cycle-indexed input-offer and output-ready random schedules per
case/word width/seed; a pending input producer holds until accepted.

The additional 172 directed checks per seed cover invalid metadata and counts,
DC/AC coefficient bounds, missing prefix/suffix/level bits, malformed input
words (including latent idle-parser poison during a held output), extra coded bits, AC run overflow (including maximum 24-bit runs),
maximum block/index scatter, a final slot held for 20 edges, and reset/abort/
replacement during pending DC, pending run, retained run, pending level, or held
coefficient. Reset with simultaneous start verifies reset priority and fresh
epoch replay verifies discarded output never leaks.

The selected final source revision passed seeds 910132 and 910133 in attempts
`20261106T171846357743Z-30de16b2` and `20261106T171853215219Z-3fcffb92`. For the 48 actual contexts, ready operation used
685304 word-parser cycles versus 937735 serial-parser cycles with 32-bit inputs,
and 696983 versus 951701 with 16-bit inputs: 1.36835x and 1.36546x serial/word cycle
ratios. Stalled actual-context ratios were approximately 1.353x and 1.352x.
These include the adapter and sparse output consumption and apply only to the
selected context workload. They do not establish whole-frame speedup or a 30fps
result.

# V94 bounded rANS contract and board resource audit

This is the current partial V94 checkpoint: a bounded rANS wire/decoder
contract and a logical table/state audit. It records design bounds for the
next host and RTL experiments; it is not evidence that the full E3 gate passed.

## Scope and status

V94 follows the experiment gates in the [development plan](../gamebub-v91-v110-development-plan.md)
and [E3 experiment brief](../literature-review-2026-11-06/experiments.md).
The current candidate is byte rANS with 2 or 4 interleaved states and
normalization precision `S = 8, 9, 10` (total frequency `M = 2^S`, or 256,
512, 1,024). Those are rANS frequency precisions; they are not tANS table
sizes measured in a tANS benchmark, nor a tANS throughput claim.

The EC94 outer header remains 44 bytes. The AB0, BR1, rANS2 and rANS4 selectors
are values 0, 1, 2 and 3 in four 2-bit fields. rANS streams carry one
20-byte descriptor each: four one-byte fields (`k0`, `k1`, `scale`,
`table_mode`), followed by four 32-bit fields (`model_id`, `rans_bytes`,
`literal_bits`, `symbol_count`). `model_id` is CRC32 of the whole inline
frequency block for that stream's model or models (32 bytes for one model,
64 bytes for two AC models). `table_mode=0` means the model frequencies are
inline; every other value must reject in this checkpoint. Tables are local to
the stream transaction. There is no cache, global model update, reset opcode,
or fixed trained model implemented here.

Each model has 16 frequency entries, each an unsigned 16-bit value, summing
exactly to `2^S`. Zero-frequency categories are permitted, but every category
actually coded must have positive frequency. There is one DC model and up to
two AC models (alternating run/level). A stream's model ID validates its whole
inline frequency block. Missing tables, unsupported table modes, mismatched
IDs or bad CRCs reject that stream; later frames can use their own valid
inline tables.

The 16 categories are `min(RiceValue >> k, 15)`. The category representation
then carries the plain literal remainder; category 15 uses an explicitly
bounded full finite escape. The encoder and decoder must agree on the signed
mapping, escape width and terminal rule. A stream carries its state words
first (`N * 4` bytes for `N=2` or `4`), followed by its renormalization bytes.
The stream descriptor bounds both that byte extent and the literal-bit extent.
Decode exactly `symbol_count` symbols, reject truncated state/refill/literal
data, invalid final states, and unexplained trailing bytes or bits. No symbol
may trigger more than two refill bytes. The finite escape and input domain
must be chosen so this refill bound holds for every admitted symbol, including
the largest value; otherwise that symbol is rejected or represented by a
separate bounded fallback.

## Logical storage arithmetic

Frequency tables use 16-bit wire values even when fewer bits suffice. The
following logical payload audit assumes an RTL implementation that stores
each frequency and each of the 17 cumulative boundaries (`cdf[0..16]`) at the
minimum unsigned width that represents values from zero through `M`.
Byte counts round each packed array up independently; they exclude descriptors,
alignment, CRC logic and BRAM packing overhead.

| Precision `S` | `M` / frequency total | Frequency payload per model | CDF payload per model | Freq + CDF per model | Inline freq bytes per model | State bits: 2 / 4 lanes |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 256 | 16 × 9 = 144 bits (18 B) | 17 × 9 = 153 bits (20 B) | 297 bits (38 B) | 16 × 2 = 32 B | 64 / 128 |
| 9 | 512 | 16 × 10 = 160 bits (20 B) | 17 × 10 = 170 bits (22 B) | 330 bits (42 B) | 32 B | 64 / 128 |
| 10 | 1,024 | 16 × 11 = 176 bits (22 B) | 17 × 11 = 187 bits (24 B) | 363 bits (46 B) | 32 B | 64 / 128 |

The descriptor cost is 20 bytes per rANS stream in addition to the 44-byte
outer header. Inline table bytes are charged to the stream payload (32 bytes
per model); the model ID CRC covers the whole inline frequency block.
A DC stream has one model (32 bytes); each AC stream has two (64 bytes).
One plane's DC plus three AC streams therefore carry seven models (224 bytes).
A complete three-plane homogeneous rANS frame carries 21 models (672 bytes).
This is wire accounting, not a claim that model storage fits a particular FPGA
memory primitive. The prototype RTL stores 16 CDF starts per model rather than
17 boundaries; its actual 704-bit two-model payload is separately documented.

For an alternate dense lookup implementation, a simple per-slot record holding
symbol (4 bits), CDF start and frequency (each `S+1` bits) has width
`4 + 2(S+1)`. A single such logical table would be 256 × 22 = 5,632 bits
(704 B) at S=8; 512 × 24 = 12,288 bits (1,536 B) at S=9; and 1,024 × 26 =
26,624 bits (3,328 B) at S=10. Two AC models double those logical totals.
Replicating each table for two or four concurrent lookup ports multiplies
storage by two or four again. This is a comparison point for a dense ROM, not
a selected architecture or an inference that the table maps to BRAM/URAM.
The compact 16-frequency/CDF form may need parallel comparisons and has its
own mux/port cost; count both alternatives when synthesizing.

## Bounded arithmetic and service audit

For a 32-bit normalized state, inversion uses the bounded slot
`slot = state & (M-1)` and the selected category's frequency and CDF. The
reconstruction update is `freq * (state >> S) + slot - cdf` (with the exact
inverse transform fixed by the implementation contract). The widest product
input is 24 bits at S=8, 23 at S=9, or 22 at S=10; the largest frequency is
`M`, requiring at most 11 bits to represent at S=10. The product plus slot
therefore fits in 32 unsigned bits for all three precisions. A multiplier
operand pair up to 24 × 11 bits is within DSP48E1's nominal multiplier operand
capacity with appropriate unsigned-to-signed guard handling, so DSP use is
plausible. This is a width bound only: it is not a DSP mapping, timing, or
post-route result.

The proposed reference RTL has 16 parallel CDF comparisons per symbol and
updates one physical symbol per FSM step. It does not decode N symbols in
parallel merely because there are N interleaved states. Measure lookup latency,
refill service, literal handling and output-credit stalls in the actual
transaction. A future parallel decoder must separately budget replicated
table ports and states. The maximum two-refill-byte rule is a per-symbol bound;
packet-level refill service is bounded by `symbol_count` times that limit,
subject to initial states and stream byte extents.

Charge inline model bytes, per-stream descriptors, state words, renormalization
bytes, literal bits, CRC work, lookup logic/ports and buffering to the current
pipeline BRAM/LUT/DSP budget. Do not assume the entire model or pipeline fits
in board memory based on logical payload size. Do not infer achieved clock,
board throughput, full-path byte wins, or publication latency from this audit.

## Remaining V94 gates

The [measured checkpoint](results.md) now implements host rANS, independent
readers, table-inclusive complete-frame bytes and a real RTL symbol/table
interface with adversarial recovery checks. Those results do not close full
RTL frame decoding, integrated memory/display cycles or physical board fit.
Fixed tables trained solely on the calibration split, an acknowledged cached
model protocol, and actual tANS experiments also remain open. Promotion needs
complete-path cycle/port/resource comparisons against the retained control.
A kernel-only entropy result cannot close V94.

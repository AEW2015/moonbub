# CU71 original-cycle SHA lookahead candidate

Integration module: `cu71_sha256_bytes_lookahead`, same ports and
BUFFER_BLOCKS1/2 parameters as frozen `cu66_sha256_bytes`.

During roundt, the registered ring entry is W[t]. The same round calculates
W[t+16] from live offsets14,9,1and0, then replaces the consumed entry. Lookahead
writes occur only during rounds0–47. The first16words are fully byte-filled
before bank_full admits compression. This separates schedule expansion from
compression without adding a round or changing bank ownership. Modulo32
carry-save reductions replace the four-operand expansion and five-operand
temp1 sums. Temp2, compression-state updates and all public control stay intact.

`source-proof.json` mechanically reverses only those listed arithmetic changes
and verifies that the remaining original FSM, byte filling/padding, error,
abort/reset, counters, digest updates and port text are unchanged. No word-array
reset or initial-zero assumption is added.

Qualification checks both real RTL implementations in one Verilator wrapper.
All16public output fields—including the full256-bit digest, ready/valid,
errors, counters and debug FSM states—match every half-cycle. Both buffer
configurations passed308primary fixtures in ideal and three randomized runs:
the original98NIST/boundary/random/canonical cases plus210independent hashlib
cases. All64compression round positions were separately aborted and reset,
followed by valid retries, yielding512all-round aborts and512resets across the
eight runs. Existing malformed-last, silence, busy-start, output-stall and
retry tests remain included. Distinct nonzero private-word values after reset
confirm randomized uninitialized payload state in each peer.

| Exact-device synthesis OOC | Buffer1 | Buffer2 |
|---|---:|---:|
| Setup WNS | +1.793ns | +1.332ns |
| Setup TNS | 0 | 0 |
| Hold WHS, unplaced | −0.297ns | −0.297ns |
| LUTs | 2,335 | 3,269 |
| FFs | 1,301 | 1,823 |
| DSPs / BRAMs | 0 / 0 | 0 / 0 |

The OOC diagnostic uses xc7a100tcsg324-1,100MHz and the same1nsmax/0nsmin IO
budget as prior leaf diagnostics. Buffer2's worst word→a path is16levels with
8CARRY4s; the old full-board path was26levels with10CARRY4s. These are different
placement scopes: the synthesized setup estimates do not prove full-board
closure. Both unplaced hold reports fail and warn HD.CLK_SRC is unset. Full
board setup/hold, routing and functional integration remain required.

Reproduce with `scripts/cu66-v71/hash/export.py`, `run.py --mode functional`
for banks1/2, `run.py --mode synth` for banks1/2, `prove_source.py`, and
`verify.py`, using new unique evidence directories. The original sources and
selected board bindings were not changed. No BIT or hardware work is performed.

The first functional attempt is retained in banks2-01: Windows TSV CRLF left a
trailing CR in the C++ expected-digest string. Its visible digest matched, but
the string comparison failed. The exporter now explicitly writes LF; no RTL
correction was needed. Passing banks2-02 and banks1-01 evidence is source-frozen.

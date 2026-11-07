# V103 reconstruction geometry experiment

The isolated [candidate](../../fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv)
changes only `quant_cell` in the published V102 reconstruction source. The
public 72-port interface, complete sequential body, V102 `safe_hidden`
predicate, counters, transaction ownership and cycle schedule are unchanged.
Candidate SHA-256 is
`64f514c08d6c2ef8d7660d852109bd4796b122fabbb41512a5b7f5e1d0c97d59`.
The [change manifest](../../fpga/experiments/cu66-v103-reconstruct/change.json)
pins the baseline, candidate and unchanged source prefix/suffix.

## Architecture and arithmetic contract

For Y tiles write `t = 90*r + x`, with `0 <= x < 90`. The original cell index is
`45*floor(r/2) + floor(x/2)`, reduced to eleven bits. Let
`k = floor((t+90)/180) = ceil(r/2)`. Then
`floor(t/2) - 45*k` is exactly that cell index before the final eleven-bit
reduction. The identity holds throughout the entire thirteen-bit tile domain,
including out-of-picture tiles whose result wraps modulo 2,048. Other planes
retain the original low eleven bits of `t`.

The candidate decodes the 46 nonzero constant offset intervals in parallel,
ORs their constant eleven-bit `45*k` values, and subtracts that offset from the
low eleven bits of `floor(t/2)`. There is no runtime division, modulo or variable
multiplication in the new function. In RTL, the loop's arithmetic has only
constant integer operands. The `k=46` interval explicitly includes 8,190 and
8,191; it does not rely on an overflowing thirteen-bit `t+90` expression.
All interval constants, including the last interval's upper bound, are
elaboration-time expressions; the last upper-bound predicate is disabled by
`k==46`.

This is a LUT/comparator/subtractor mapping candidate. The parallel offset
architecture trades comparator logic for the former divider/control chain.
A shorter source expression or a successful behavioral test does not establish
smaller area or better timing; native synthesis and routing are measured in
the parent V103 comparison. No registers or extra latency were added here.

## Actual RTL and independent model results

[Selected results](../../experiments/python-gamebub-v103/reconstruct/results.json)
record **32,768 passing actual RTL comparisons**: all four two-bit plane values
times all 8,192 thirteen-bit tile values. This includes invalid plane 3,
out-of-picture tiles, every row-pair boundary and the final two tile values.
The probe has **zero clock edges**. It exhausts the combinational function;
it does not simulate the complete sequential packet/reconstruction protocol.

The original and candidate verification adapters preserve each complete
production module body and all public ports. They add only the probe inputs,
result wire and module rename. The strict bounded compile/run uses
Verilator 5.020 and GCC 13.3, `--assert -Wall`, and C++
`-Wall -Wextra -Werror`; there are no disabled assertions or downgraded
warnings. The independently computed C++ oracle uses row/column coordinates.
An additional [Python trace replay](../../experiments/python-gamebub-v103/reconstruct/trace-audit.json)
checks every actual RTL output against row/column geometry, ordered input
completeness and all declared artifact hashes. Both comparisons pass.

The historical behavioral backend is a two-state model. This is not formal
or four-state equivalence, mapped-netlist proof, a hardware frame-rate test,
or a validated decoder latency measurement. Full-pipeline paired simulation
and native implementation are separate parent-owned V103 gates.

## Reproduction

```sh
python3 scripts/cu66-v103/reconstruct.py
python3 fpga/experiments/cu66-v103-reconstruct/audit_trace.py
```

Each simulation attempt receives a fresh directory, a source snapshot, bounded
commands, compiler/simulator transcripts, a binary hash, a compressed actual
trace and receipt artifact hashes. Executables remain outside Git. The selected
attempt completed successfully; no failed compile/run attempt was needed.

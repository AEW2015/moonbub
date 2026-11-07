# V103 admission cell-index arithmetic

The isolated [candidate](../../fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv)
changes only the `cell_index` function in V102's memory-qualified admission
module. Its SHA-256 is
`10df5dba19c78d3005491f90e9ac61a08e1110d243f4865ad617ca792e6c67ed`.
The original [V102 source](../../fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv)
is pinned to baseline `6d2ca3ae9abe207215d6130cfb0087fd07928917` and remains
unchanged. The memory template, 49,152-byte capacity, state machine, public
ports, counters, reset/abort behavior and cycle schedule are untouched.

## Full-domain identity and width contract

For the Y plane, the original function computes

```text
floor(floor(t / 90) / 2) * 45 + floor((t % 90) / 2).
```

For any unsigned 32-bit `t`, write `t = 90q + r`, where `0 <= r < 90`.
Then `floor(t/2) = 45q + floor(r/2)`. Therefore the original cell is exactly

```text
floor(t/2) - 45 * ceil(q/2), where q = floor(t/90).
```

The candidate uses this identity to retain one explicit constant quotient,
a rounded half-row count, a constant multiply and a subtraction. It removes
the separate remainder expression from the source. The tool determines the
eventual primitive structure; this source rewrite alone does not establish
an area or timing improvement.

The quotient is at most 47,721,858 and fits 26 bits. The rounded half-row
count is computed as `(q >> 1) + (q & 1)`, avoiding a full-width `q+1`
overflow; its maximum is 23,860,929 and fits 25 bits. The product by 45 is
at most 1,073,741,805 and fits 31 bits. `floor(t/2)` also fits 31 bits.
Their subtraction cannot underflow because `ceil(q/2) <= q` and
`floor(t/2) = 45q + floor(r/2)`; the result fits 31 bits and is zero-extended
to the original 32-bit return. For every non-Y plane, including plane 3,
the function returns all 32 bits of `t` unchanged.

This argument covers every unsigned 32-bit tile value. It does not assume
that admission's state is thirteen bits, truncate the tile, or rely on a
reachable-state invariant. This is a mathematical derivation, not a
machine-checked formal-equivalence result; the actual RTL verification below
enumerates a bounded subset of the full 32-bit domain.

## Actual RTL and independent replay

The [selected focused report](../../experiments/python-gamebub-v103/admission/results.json)
records a clean first attempt under the existing Verilator 5.020 behavioral
backend and GCC 13.3. Assertions and `-Wall` remain enabled; the C++ checker
uses `-Wall -Wextra -Werror`. No Verilator warning suppression is added.

Both complete production module bodies are instantiated through
verification-only adapters that append function-probe ports. Removing those
probe ports, assignment and module-name substitution recovers each production
source byte-for-byte. All 64 production port names remain intact. The probe
holds the clock low, so this result has **zero clock edges** and covers the
combinational function only, rather than the sequential packet protocol.

The run passes **130,920 cases**: **32,730 distinct tile values across all
four planes**. The tile set contains every value from 0 through 8,191,
power-of-two boundaries, selected quotient/remainder boundaries at low and
high 32-bit values, the highest 512 values, and 10,000 deterministic
xorshift32 samples. Both old and new full 32-bit results equal a C++
64-bit arithmetic oracle in every case; the check does not compare only the
low eleven bits consumed by `active_cell`.

An independent Python replay regenerates the exact ordered tile set and
uses unbounded-integer `divmod(t,90)` row/column geometry to verify every
retained output. The separate [trace audit](../../experiments/python-gamebub-v103/admission/trace-audit.json)
also passes all 130,920 rows and checks the selected report, source and
artifact hashes. The gzip trace retains its raw and compressed checksums.

```sh
python3 scripts/cu66-v103/admission.py
python3 fpga/experiments/cu66-v103-admission/audit_trace.py
```

The runner snapshots all inputs, retains command logs, requires a terminal
`TEST_PASS`, uses finite compile/runtime watchdogs and runs at most two
compiler jobs. Native builds and full-pipeline baseline/candidate comparisons
are separate root-owned lanes. No component timing, achieved FPGA clock,
hardware frame rate, complete decoder latency or full packet-protocol
qualification follows from this focused result.

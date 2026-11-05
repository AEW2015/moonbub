# Bounded safety checks for the frozen three-bank owner

This package uses Yosys0.33's built-in SAT engine against the unchanged v69
`cu66_frame_bank_control.sv`. It does not require a separate SMT solver,
Artix-7 device files, or connected hardware. No toolchain was installed.

Run from any directory:

```sh
python3 fpga/experiments/cu66-v70/formal/run_bounded.py
python3 fpga/experiments/cu66-v70/formal/verify_bounded.py
```

The normal `gamebub-cu66-v69-build` tools container mounts this checkout at
its absolute path. All generated scripts, solver logs and actual reachable
witness VCDs are retained in this directory. `results.json` binds source and
script/log/witness hashes. The first development runner failure was a parser
expecting the Yosys assertion-count table in the opposite column order; its
transcript is retained. The actual solver proof in that run had succeeded.
No DUT or assertion was changed to make the parser pass.

## Assumptions and bounded interpretation

- `rst=1` at SAT solver state1; `rst=0` at every subsequent state.
- Input bits are defined two-state symbols, otherwise unconstrained. IDs,
  begin/commit/abort, vblank, scanout drain and abort drain may take any values.
  No legal-host-traffic, ready stability, fairness or eventual-service
  assumption is imposed.
- The harness's `past_valid` initializes to zero to disable assertions before
  the first reset edge. Other initial registers are defined symbolic values,
  not forced to zero; reset supplies the actual DUT initialization.
- The single-clock sequential transition is the object checked. Analog clock
  behavior, asynchronous reset crossings and metastability are not modeled.

All16 assertions remain elaborated in every job. Safety jobs use
`sat -seq N -prove-asserts -verify` for **N=8,16,24 solver states**. The
clocked assertions have one sampling-edge observer latency: in the24-state
unroll, their last predicate observes DUT state23. The reset-derived state and
earlier unrolled transitions are checked when their enables become active.
The reported bounds are solver states, not a claim of24 additional physical
cycles beyond reset, an inductive invariant, or an unbounded proof.

Reachability jobs separately constrain one cover output at state16 and require
an actual SAT model/VCD. They do not add those reachability conditions to the
safety proofs, remove assertions, or assume successful progress in all traces.

## Assertions

| IDs | Safety contract |
|---|---|
| P01–P05 | Active writer and each valid reference/front/pending/read bank is0–2 |
| P06–P08 | Active candidate write bank differs from reference, front and pending banks whenever those leases are valid |
| P09 | A valid read lease requires an active candidate transaction, including its abort-drain phase |
| P10 | Valid pending and front banks differ |
| P11 | Read bank differs from active candidate write bank |
| P12 | Aborting implies an active retained transaction lease |
| P13–P16 | After an abort input, accepted count and reference valid/bank/ID do not advance; a previous pending frame may still present independently |

The harness intentionally does not assert that presentation stops on abort.
A separate reachable witness has both `aborted` and `frame_presented` high,
confirming that the independent previous pending frame is allowed to advance.
Other witnesses reach an active candidate, a valid read lease, a pending frame
and a front frame, preventing an interpretation that only reset/idle was used.

## Recorded result and limits

All three safety bounds pass with explicit `SAT proof finished - no model
found: SUCCESS!` markers; all five reachability jobs produce actual models.
The full matrix took21.68 wall seconds. Peak reported solver memory was
478.45 MB for the24-state job. The runner caps total work at115 seconds,
each process at28 wall seconds, and each process address space at1.5 GiB.
A timeout, failed check or missing marker is not classified as PASS.

This is **bounded bank-controller safety only**. It does not establish
unbounded correctness, liveness/fairness, complete receiver or HUD commits,
actual memory/scanout operation, CDC/reset signoff, resource fit, timing closure
or physical performance. Readback/tag and memory-completion assumptions belong
to the independently tested system integration.
